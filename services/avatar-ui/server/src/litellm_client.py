import contextlib
import io
import logging
from typing import Any

_LITELLM_MODULE = None
_LITELLM_LOADED = False
_logger = logging.getLogger("llm")


def _load_litellm():
    global _LITELLM_MODULE, _LITELLM_LOADED
    if _LITELLM_LOADED:
        return _LITELLM_MODULE
    with contextlib.redirect_stdout(io.StringIO()):
        import litellm
    _LITELLM_MODULE = litellm
    _LITELLM_LOADED = True
    return _LITELLM_MODULE


class _ProviderListFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "Provider List:" not in record.getMessage()


def configure_litellm_logging() -> None:
    logging.getLogger("LiteLLM").addFilter(_ProviderListFilter())


def completion_with_purpose(
    *,
    purpose: str,
    model: str,
    messages: list[dict[str, Any]],
    **kwargs: Any,
):
    _logger.info("LLM呼び出し: %s (model=%s)", purpose, model)
    litellm = _load_litellm()
    return litellm.completion(
        model=model,
        messages=messages,
        **kwargs,
    )
