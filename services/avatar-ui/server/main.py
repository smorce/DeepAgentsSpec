# AG-UI サーバーのエントリーポイント（FastAPI + Google ADK）
import inspect
import json
import logging
import re
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk import Runner
from google.adk.agents import LlmAgent
from google.adk.agents import RunConfig as ADKRunConfig
from google.adk.agents.run_config import StreamingMode
from google.adk.artifacts import InMemoryArtifactService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
from google.adk import tools as adk_tools
from google.adk.models.lite_llm import LiteLlm
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.adk.tools import FunctionTool
from google.genai import types
from litellm import completion

from src import config
from src.diary_service import get_web_search_settings
from src.routes.diary import router as diary_router, search_diary

# 検索サブエージェントを使う場合は GOOGLE_API_KEY が必須
if config.SEARCH_SUBAGENT_ENABLED and not config.GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY is not set. Please add it to .env in project root")

# ---------- ロギング設定 ----------
logs_dir = Path(__file__).resolve().parent / "logs"
logs_dir.mkdir(exist_ok=True)
log_file = logs_dir / "app.log"

log_level = logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[RotatingFileHandler(log_file, maxBytes=config.LOG_MAX_BYTES, backupCount=config.LOG_BACKUP_COUNT)],
)
logger = logging.getLogger("agui-adk-bridge")

# ---------- エージェント構築 ----------

def build_openrouter_completion_kwargs(provider: str) -> dict | None:
    if provider.lower() != "openrouter":
        return None
    if not config.REASONING_ENABLED:
        return None
    return {
        "reasoning": {"enabled": True},
        "include_reasoning": True,
    }


def resolve_model(provider: str, model: str):
    """プロバイダに応じたモデルインスタンスを返す（gemini は直接、他は LiteLlm 経由）"""
    provider = provider.lower()
    if provider == "gemini":
        return model
    completion_kwargs = build_openrouter_completion_kwargs(provider)
    if provider == "openrouter":
        resolved_model = model if model.startswith("openrouter/") else f"openrouter/{model}"
        if completion_kwargs:
            return LiteLlm(model=resolved_model, completion_kwargs=completion_kwargs)
        return LiteLlm(model=resolved_model)
    # openai / anthropic などは LiteLlm 経由
    if "/" in model:
        if completion_kwargs:
            return LiteLlm(model=model, completion_kwargs=completion_kwargs)
        return LiteLlm(model=model)
    if completion_kwargs:
        return LiteLlm(model=f"{provider}/{model}", completion_kwargs=completion_kwargs)
    return LiteLlm(model=f"{provider}/{model}")


def build_agent(
    *,
    provider: str | None = None,
    model: str | None = None,
    enable_tools: bool = True,
) -> ADKAgent:
    """メインエージェントを構築（検索サブエージェント付きの場合あり）"""
    provider = provider or config.LLM_PROVIDER
    model = model or config.LLM_MODEL
    search_subagent_tool = None
    if enable_tools and config.SEARCH_SUBAGENT_ENABLED:
        search_model = resolve_model(config.SEARCH_SUBAGENT_PROVIDER, config.SEARCH_SUBAGENT_MODEL)
        search_agent = LlmAgent(
            name="search_agent",
            model=search_model,
            description="Performs web searches using Google Search",
            instruction=(
                "Search the web and return concise results. "
                "Use the same language as the latest user message. Phrase the search query in that language."
            ),
            tools=[GoogleSearchTool(bypass_multi_tools_limit=True)],
        )
        search_subagent_tool = AgentTool(agent=search_agent)

    main_model = resolve_model(provider, model)
    tools = []
    if enable_tools:
        tools = [
            adk_tools.preload_memory,
            FunctionTool(search_diary),
        ]
        if search_subagent_tool:
            tools.append(search_subagent_tool)

    main_agent = LlmAgent(
        name="assistant",
        model=main_model,
        instruction=config.SYSTEM_PROMPT,
        tools=tools,
    )

    return ADKAgent(
        adk_agent=main_agent,
        app_name="agents",
        user_id="cli_user",
        use_in_memory_services=True,
        session_timeout_seconds=config.SESSION_TIMEOUT_SECONDS,
        cleanup_interval_seconds=config.CLEANUP_INTERVAL_SECONDS,
    )


def build_search_llm_agent() -> LlmAgent:
    search_model = resolve_model(config.SEARCH_SUBAGENT_PROVIDER, config.SEARCH_SUBAGENT_MODEL)
    return LlmAgent(
        name="search_agent",
        model=search_model,
        description="Performs web searches using Google Search",
        instruction=(
            "Search the web and return concise results with sources. "
            "Use the same language as the latest user message."
        ),
        tools=[GoogleSearchTool(bypass_multi_tools_limit=True)],
    )


def _extract_response_text(response) -> str:
    if response is None:
        return ""
    choices = getattr(response, "choices", None)
    if choices:
        message = getattr(choices[0], "message", None)
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content
        content = getattr(message, "content", None)
        if isinstance(content, str):
            return content
    if isinstance(response, dict):
        choices = response.get("choices") or []
        if choices and isinstance(choices[0], dict):
            message = choices[0].get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content
    return ""


def _extract_json_payload(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def decide_web_search(user_text: str) -> tuple[bool, str]:
    system_prompt = (
        "You decide whether web search is required to answer the user's message accurately.\n"
        "Respond with JSON only: {\"needs_web_search\": true/false, \"query\": \"\"}.\n"
        "If search is not needed, set needs_web_search=false and query to empty string."
    )
    response = completion(
        model=config.LITELLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
    )
    text = _extract_response_text(response)
    payload = _extract_json_payload(text)
    needs = bool(payload.get("needs_web_search"))
    query = str(payload.get("query") or "").strip()
    return needs, query


async def run_web_search(query: str) -> str:
    query = query.strip()
    if not query:
        return ""
    if not config.SEARCH_SUBAGENT_ENABLED:
        return ""
    search_agent = build_search_llm_agent()
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="agents",
        agent=search_agent,
        session_service=session_service,
        artifact_service=InMemoryArtifactService(),
        memory_service=InMemoryMemoryService(),
        credential_service=InMemoryCredentialService(),
    )
    run_config = ADKRunConfig(streaming_mode=StreamingMode.SSE)
    search_message = types.Content(parts=[types.Part(text=query)], role="user")
    session_id = f"web-search-{uuid.uuid4().hex}"
    chunks: list[str] = []
    try:
        await session_service.create_session(
            app_name="agents",
            user_id="web_search_user",
            session_id=session_id,
        )
        try:
            async for adk_event in runner.run_async(
                user_id="web_search_user",
                session_id=session_id,
                new_message=search_message,
                run_config=run_config,
            ):
                content = getattr(adk_event, "content", None)
                parts = getattr(content, "parts", None) if content else None
                if parts:
                    for part in parts:
                        text = getattr(part, "text", None)
                        if text:
                            chunks.append(text)
                is_final = False
                if hasattr(adk_event, "is_final_response") and callable(adk_event.is_final_response):
                    is_final = adk_event.is_final_response()
                elif hasattr(adk_event, "is_final_response"):
                    is_final = bool(adk_event.is_final_response)
                if is_final or getattr(adk_event, "turn_complete", False):
                    break
        except Exception as exc:
            logger.warning("Web search failed: %s", exc)
            return ""
    finally:
        close_method = getattr(runner, "close", None)
        if callable(close_method):
            try:
                result = close_method()
                if inspect.isawaitable(result):
                    await result
            except Exception:
                pass
    return "".join(chunks).strip()


def _extract_latest_user_message(input_data) -> tuple[object | None, str]:
    messages = getattr(input_data, "messages", None)
    if not messages:
        return None, ""
    for message in reversed(messages):
        role = getattr(message, "role", None)
        content = getattr(message, "content", None)
        if role == "user" and isinstance(content, str):
            return message, content
        if isinstance(message, dict) and message.get("role") == "user":
            content = message.get("content")
            if isinstance(content, str):
                return message, content
    return None, ""


async def enrich_input_with_web_search(input_data):
    if config.LLM_PROVIDER.lower() != "openrouter":
        return input_data
    message, user_text = _extract_latest_user_message(input_data)
    if not message or not user_text:
        return input_data
    try:
        settings = get_web_search_settings(input_data.thread_id)
    except Exception:
        settings = None
    if not settings or not settings.enabled:
        return input_data
    if "検索結果:" in user_text:
        return input_data
    if config.WEB_SEARCH_AUTO_DECISION:
        try:
            needs_search, query = decide_web_search(user_text)
        except Exception as exc:
            logger.warning("Web search decision failed: %s", exc)
            return input_data
        if not needs_search:
            return input_data
        search_query = query or user_text
    else:
        search_query = user_text
    search_results = await run_web_search(search_query)
    if not search_results:
        return input_data
    appended = f"{user_text}\n\n検索結果:\n{search_results}"
    if isinstance(message, dict):
        message["content"] = appended
    else:
        setattr(message, "content", appended)
    return input_data


# エージェントインスタンス（サーバー起動時に構築）
agent = None
openrouter_agent = None
if config.LLM_PROVIDER.lower() == "openrouter":
    openrouter_agent = build_agent(enable_tools=False)
else:
    agent = build_agent(enable_tools=True)


def select_agent(input_data):
    if config.LLM_PROVIDER.lower() != "openrouter":
        return agent
    return openrouter_agent

# ---------- FastAPI アプリケーション ----------
app = FastAPI(title="AG-UI ADK Bridge")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストログ用ミドルウェア（dev 時のみボディを記録）
@app.middleware("http")
async def log_agui_request(request: Request, call_next):
    if request.url.path == "/agui" and request.method == "POST":
        if config.APP_ENV == "dev" or config.LOG_BODY is True:
            body = await request.body()
            logger.info("AGUI request body: %s", body.decode("utf-8", errors="replace"))
            request._body = body
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        logger.exception("Unhandled server error")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# Config API Endpoint
@app.get("/agui/config")
def get_config():
    """
    UI用の設定を返すエンドポイント。
    Server設定(config.py)から、UIに必要な部分だけを抽出して返す。
    """
    # UI設定に加えて、クライアント側ログの詳細可否フラグとエージェント接続情報も返す
    return {
        "ui": config._ui_settings,
        "clientLogVerbose": config.CLIENT_LOG_VERBOSE,
        "minirag": {
            "workspace": config.MINIRAG_WORKSPACE,
            "searchEnabledDefault": config.MINIRAG_SEARCH_ENABLED_DEFAULT,
            "topKDefault": config.MINIRAG_TOP_K_DEFAULT,
            "searchModesDefault": config.MINIRAG_SEARCH_MODES_DEFAULT,
        },
        "webSearch": {
            "enabledDefault": config.WEB_SEARCH_ENABLED_DEFAULT,
            "autoDecision": config.WEB_SEARCH_AUTO_DECISION,
        },
        "agent": {
            "url": config.AGENT_URL,
            "agentId": config.AGENT_ID,
            "threadId": config.THREAD_ID,
        },
    }


app.include_router(diary_router)

# AG-UI プロトコルのエンドポイントを登録
add_adk_fastapi_endpoint(
    app,
    agent,
    path="/agui",
    agent_selector=select_agent,
    input_transformer=enrich_input_with_web_search,
)

# ヘルスチェック（ロードバランサー等から使用）
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# ルートパス（API の存在確認用）
@app.get("/")
def root():
    return {"status": "ok", "endpoint": "/agui"}

# スクリプトとして起動する場合は .env の値でバインドする
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=config.SERVER_BIND_HOST,
        port=config.SERVER_PORT,
        reload=(config.APP_ENV == "dev"),
    )
