// レンダラーのメイン処理: 設定読み込み・UI初期化・エージェント実行をまとめる
import { config, fetchConfig } from "./config";
import { createAgent } from "../core/agent";
import { loggerSubscriber } from "../core/loggerSubscriber";
import { createUiSubscriber, renderMarkdown } from "./subscriber";
import { TerminalEngine } from "./engine/TerminalEngine";
import { createAutoScrollController } from "./autoScroll";
import pkg from "../../package.json"; // バージョン情報の取得

// エージェントのインスタンスを保持する
let agentInstance = null as ReturnType<typeof createAgent> | null;

// UI 要素への参照を確保
const inputEl = document.getElementById("input") as HTMLInputElement | null;
const outputEl = document.querySelector("#pane-output .text-scroll") as HTMLElement | null;
const avatarImg = document.getElementById("avatar-img") as HTMLImageElement | null;
const metaBar = document.getElementById("meta");
const avatarLabel = document.getElementById("avatar-label");
const searchToggle = document.getElementById("search-toggle") as HTMLInputElement | null;
const webSearchToggle = document.getElementById("web-search-toggle") as HTMLInputElement | null;
const topKInput = document.getElementById("search-top-k") as HTMLInputElement | null;
const modeInputs = Array.from(
  document.querySelectorAll<HTMLInputElement>('input[name="search-mode"]'),
);
const finalizeButton = document.getElementById("finalize-button") as HTMLButtonElement | null;
const resetButton = document.getElementById("reset-button") as HTMLButtonElement | null;
const finalizeStatus = document.getElementById("finalize-status") as HTMLSpanElement | null;

type DiaryMessage = {
  role: "user" | "assistant" | "system";
  content: string;
  created_at?: string;
};

const transcript: DiaryMessage[] = [];

async function initApp() {
  if (!inputEl || !outputEl || !avatarImg || !avatarLabel) {
    throw new Error("UI elements missing");
  }

  // メタバーはプロダクト名 + バージョン（package.json 由来）
  if (metaBar) {
    metaBar.textContent = `${pkg.name} v${pkg.version}`;
  }

  // 1. サーバーから設定を取得（サーバー起動前でも落とさずに待機）
  inputEl.disabled = true;
  outputEl.textContent = "";
  {
    const line = document.createElement("div");
    line.className = "text-line text-line--system";
    line.textContent = "> Starting server...";
    outputEl.appendChild(line);
  }

  const sleep = (ms: number) => new Promise<void>(resolve => setTimeout(resolve, ms));
  let retryDelayMs = 250;
  while (true) {
    try {
      await fetchConfig({ silent: true });
      break;
    } catch {
      await sleep(retryDelayMs);
      retryDelayMs = Math.min(Math.round(retryDelayMs * 1.6), 5000);
    }
  }

  // 設定が取れたら通常表示へ
  outputEl.textContent = "";
  inputEl.disabled = false;
  inputEl.focus();

  // 2. UI初期化 (設定ロード後)
  // アバター枠内のラベルはエージェント名 (設定連動)
  avatarLabel.textContent = config.ui.nameTags.avatar;

  // ---------------------------------------------------------
  // カラーテーマ適用ロジック (CSS変数へ注入)
  // ---------------------------------------------------------
  const root = document.documentElement;

  // HEX -> RGB 変換ヘルパー（CSS変数への注入用）
  const hexToRgb = (hex: string): { r: number; g: number; b: number } | null => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16),
        }
      : null;
  };

  // テーマカラー適用
  if (config.ui.themeColor) {
    const rgb = hexToRgb(config.ui.themeColor);
    if (rgb) {
      root.style.setProperty("--theme-color-r", String(rgb.r));
      root.style.setProperty("--theme-color-g", String(rgb.g));
      root.style.setProperty("--theme-color-b", String(rgb.b));
    }
  }

  // ユーザーカラー適用
  if (config.ui.userColor) {
    const rgb = hexToRgb(config.ui.userColor);
    if (rgb) {
      root.style.setProperty("--user-color-r", String(rgb.r));
      root.style.setProperty("--user-color-g", String(rgb.g));
      root.style.setProperty("--user-color-b", String(rgb.b));
    }
  }

  // ツールカラー適用
  if (config.ui.toolColor) {
    const rgb = hexToRgb(config.ui.toolColor);
    if (rgb) {
      root.style.setProperty("--tool-color-r", String(rgb.r));
      root.style.setProperty("--tool-color-g", String(rgb.g));
      root.style.setProperty("--tool-color-b", String(rgb.b));
    }
  }

  // 透過設定を適用
  if (config.ui.opacity !== undefined) {
    document.body.style.backgroundColor = `rgba(0, 0, 0, 0.0)`; // bodyを完全透過
    root.style.setProperty("--ui-opacity", String(config.ui.opacity));
  }

  // アバターオーバーレイの濃さ（テーマ色で着色）
  if (config.ui.avatarOverlayOpacity !== undefined) {
    root.style.setProperty("--avatar-overlay-opacity", String(config.ui.avatarOverlayOpacity));
  }
  if (config.ui.avatarBrightness !== undefined) {
    root.style.setProperty("--avatar-brightness", String(config.ui.avatarBrightness));
  }
  if (config.ui.glowText !== undefined) {
    root.style.setProperty("--glow-text-alpha1", String(0.6 * config.ui.glowText)); // 強めのグロー係数
    root.style.setProperty("--glow-text-alpha2", String(0.4 * config.ui.glowText)); // 弱めのグロー係数
  }
  if (config.ui.glowBox !== undefined) {
    root.style.setProperty("--glow-box-alpha1", String(0.4 * config.ui.glowBox)); // 外枠の強めグロー係数
    root.style.setProperty("--glow-box-alpha2", String(0.2 * config.ui.glowBox)); // 外枠の弱めグロー係数
  }
  if (config.ui.brightness !== undefined) {
    root.style.setProperty("--ui-brightness", String(config.ui.brightness));
  }

  // 3. UIエンジン (Game Loop) の初期化
  // これひとつでタイプライター・アニメーション・音声すべてを制御する
  const autoScroll = createAutoScrollController(outputEl);
  const engine = new TerminalEngine(outputEl, avatarImg, renderMarkdown, autoScroll);

  // 4. エージェント初期化（サーバ設定に従う）
  agentInstance = createAgent({
    agentId: config.agent.agentId,
    url: config.agent.url,
    threadId: config.agent.threadId,
  });
  agentInstance.subscribe(loggerSubscriber);

  const serverBase = config.agent.url.replace(/\/agui\/?$/, "");
  const diaryWorkspace = config.minirag.workspace;
  const allowedSearchModes = ["naive", "mini", "light"] as const;
  const normalizeSearchModes = (modes: string[]) => {
    const unique: string[] = [];
    for (const mode of modes) {
      if (!allowedSearchModes.includes(mode as (typeof allowedSearchModes)[number])) {
        continue;
      }
      if (unique.includes(mode)) {
        continue;
      }
      unique.push(mode);
      if (unique.length >= 3) {
        break;
      }
    }
    return unique;
  };
  const fallbackModes = normalizeSearchModes(config.minirag.searchModesDefault ?? ["mini"]);
  const ensureAtLeastOneMode = (modes: string[]) => {
    if (modes.length > 0) {
      return modes;
    }
    return fallbackModes.length > 0 ? fallbackModes : ["mini"];
  };
  const diarySearchSettings = {
    enabled: config.minirag.searchEnabledDefault,
    top_k: config.minirag.topKDefault,
    modes: ensureAtLeastOneMode(normalizeSearchModes(config.minirag.searchModesDefault ?? [])),
  };
  const webSearchSettings = {
    enabled: config.webSearch.enabledDefault,
  };

  // テキスト行を追加（エンジンを介さない即時表示用）
  const appendLine = (className: string, text: string) => {
    const line = document.createElement("div");
    line.className = `text-line ${className}`;
    line.textContent = text;
    outputEl.appendChild(line);
    outputEl.scrollTop = outputEl.scrollHeight;
  };

  const appendSystemBanners = () => {
    const fullName = config.ui.nameTags.avatarFullName || config.ui.nameTags.avatar || "AGENT";
    if (config.ui.systemMessages.banner1) {
      const banner1 = config.ui.systemMessages.banner1.replace("{avatarFullName}", fullName);
      appendLine("text-line--system", `> ${banner1}`);
    }
    if (config.ui.systemMessages.banner2) {
      appendLine("text-line--system", `> ${config.ui.systemMessages.banner2}`);
    }
  };

  let isRunning = false; // 多重実行防止フラグ
  let isFinalizing = false;

  const updateFinalizeStatus = (
    text: string,
    tone: "default" | "warning" | "error" = "default",
  ) => {
    if (!finalizeStatus) return;
    finalizeStatus.textContent = text;
    if (tone === "error") {
      finalizeStatus.style.color = "rgba(255, 102, 102, 1)";
    } else if (tone === "warning") {
      finalizeStatus.style.color = "rgba(255, 196, 102, 1)";
    } else {
      finalizeStatus.style.color = "";
    }
  };

  const applySearchSettings = async () => {
    if (!config.agent.threadId) {
      return;
    }
    try {
      const response = await fetch(`${serverBase}/agui/diary/search-settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          thread_id: config.agent.threadId,
          settings: diarySearchSettings,
        }),
      });
      if (!response.ok) {
        throw new Error(`Search settings update failed: ${response.status}`);
      }
      updateFinalizeStatus("検索設定を更新しました");
    } catch (error) {
      updateFinalizeStatus(
        `検索設定の更新に失敗しました: ${error instanceof Error ? error.message : String(error)}`,
        "error",
      );
    }
  };

  const applyWebSearchSettings = async () => {
    if (!config.agent.threadId) {
      return;
    }
    try {
      const response = await fetch(`${serverBase}/agui/web-search/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          thread_id: config.agent.threadId,
          settings: webSearchSettings,
        }),
      });
      if (!response.ok) {
        throw new Error(`Web search settings update failed: ${response.status}`);
      }
      updateFinalizeStatus("Web検索設定を更新しました");
    } catch (error) {
      updateFinalizeStatus(
        `Web search settings update failed: ${error instanceof Error ? error.message : String(error)}`,
        "error",
      );
    }
  };

  if (searchToggle) {
    searchToggle.checked = diarySearchSettings.enabled;
    searchToggle.addEventListener("change", async () => {
      diarySearchSettings.enabled = searchToggle.checked;
      await applySearchSettings();
    });
  }
  if (webSearchToggle) {
    webSearchToggle.checked = webSearchSettings.enabled;
    webSearchToggle.addEventListener("change", async () => {
      webSearchSettings.enabled = webSearchToggle.checked;
      await applyWebSearchSettings();
    });
  }

  if (topKInput) {
    topKInput.value = String(diarySearchSettings.top_k);
    topKInput.addEventListener("change", async () => {
      const value = Number(topKInput.value);
      diarySearchSettings.top_k = Number.isNaN(value)
        ? config.minirag.topKDefault
        : Math.min(Math.max(value, 1), 10);
      topKInput.value = String(diarySearchSettings.top_k);
      await applySearchSettings();
    });
  }

  if (modeInputs.length > 0) {
    const applyModeSelection = (modes: string[]) => {
      for (const input of modeInputs) {
        input.checked = modes.includes(input.value);
      }
    };
    applyModeSelection(diarySearchSettings.modes);
    modeInputs.forEach((input) => {
      input.addEventListener("change", async (event) => {
        const selected = modeInputs
          .filter((item) => item.checked)
          .map((item) => item.value);
        const normalized = normalizeSearchModes(selected);
        const ensured = ensureAtLeastOneMode(normalized);
        if (ensured.length !== selected.length || ensured.length !== normalized.length) {
          applyModeSelection(ensured);
          const target = event.currentTarget as HTMLInputElement | null;
          if (target && ensured.includes(target.value) === false && selected.length > 0) {
            target.checked = false;
          }
        }
        diarySearchSettings.modes = ensured;
        await applySearchSettings();
      });
    });
  }

  if (searchToggle || topKInput || modeInputs.length > 0) {
    await applySearchSettings();
  }
  if (webSearchToggle) {
    await applyWebSearchSettings();
  }

  // ユーザー入力を処理してエージェントに送信
  inputEl.addEventListener("keydown", async (event) => {
    if (event.isComposing || event.key !== "Enter") {
      return;
    }
    event.preventDefault();

    if (isRunning) {
      return;
    }

    const value = inputEl.value.trim();
    if (!value) {
      return;
    }

    // ユーザー入力の表示: 設定されたユーザータグを使う
    const userTag = config.ui.nameTags.user ? `${config.ui.nameTags.user}> ` : "> ";
    appendLine("text-line--user", `${userTag}${value}`);
    inputEl.value = "";

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user" as const,
      content: value,
    };

    agentInstance!.messages.push(userMessage);
    transcript.push({
      role: "user",
      content: value,
      created_at: new Date().toISOString(),
    });

    isRunning = true;
    try {
      await agentInstance!.runAgent(
        {
          runId: crypto.randomUUID(),
        },
        createUiSubscriber({
          outputEl,
          engine, // エンジンを渡す
          autoScroll,
          onAssistantMessageComplete: (message) => {
            transcript.push({
              role: "assistant",
              content: message,
              created_at: new Date().toISOString(),
            });
          },
        }),
      );
    } catch (error) {
      // エージェント実行エラーの表示
      console.error(error);
      appendLine(
        "text-line--error",
        `❌ ${error instanceof Error ? error.message : String(error)}`,
      );
    } finally {
      isRunning = false;
    }
  });

  if (finalizeButton) {
    finalizeButton.addEventListener("click", async () => {
      if (isFinalizing) {
        return;
      }
      if (!transcript.length) {
        appendLine("text-line--error", "❌ 会話履歴がありません。");
        return;
      }
      isFinalizing = true;
      finalizeButton.disabled = true;
      updateFinalizeStatus("会話を確定しています...");
      try {
        const response = await fetch(`${serverBase}/agui/diary/finalize`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            workspace: diaryWorkspace,
            thread_id: config.agent.threadId,
            messages: transcript,
            search_settings: diarySearchSettings,
          }),
        });
        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          throw new Error(payload.detail || `Finalize failed: ${response.status}`);
        }
        const payload = await response.json();
        appendLine(
          "text-line--system",
          `> 日記を登録しました: ${payload.doc_id} (重要度 ${payload.analysis.importance_score})`,
        );
        appendLine(
          "text-line--system",
          `> サマリー: ${payload.analysis.summary}`,
        );
        updateFinalizeStatus("会話確定が完了しました");
        if (payload.profiling?.status === "ok") {
          const appliedCount = Number(payload.profiling.applied ?? 0);
          if (appliedCount > 0) {
            appendLine(
              "text-line--system",
              `> プロファイルを更新しました (${appliedCount} 件)`,
            );
          }
        }
        if (payload.profiling?.status === "failed") {
          const reason =
            typeof payload.profiling.message === "string" && payload.profiling.message
              ? ` (${payload.profiling.message})`
              : "";
          appendLine(
            "text-line--warning",
            `⚠️ プロファイリングに失敗しました${reason}`,
          );
          updateFinalizeStatus("プロファイリングに失敗しました", "warning");
        }
      } catch (error) {
        appendLine(
          "text-line--error",
          `❌ 会話確定に失敗しました: ${error instanceof Error ? error.message : String(error)}`,
        );
        updateFinalizeStatus("会話確定に失敗しました", "error");
      } finally {
        isFinalizing = false;
        finalizeButton.disabled = false;
      }
    });
  }

  if (resetButton) {
    resetButton.addEventListener("click", async () => {
      if (isRunning || isFinalizing) {
        return;
      }
      resetButton.disabled = true;
      try {
        const response = await fetch(`${serverBase}/agui/session/reset`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            thread_id: config.agent.threadId,
          }),
        });
        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          throw new Error(payload.detail || `Reset failed: ${response.status}`);
        }
        const payload = await response.json().catch(() => ({}));
        transcript.length = 0;
        if (agentInstance?.messages) {
          agentInstance.messages.length = 0;
        }
        engine.reset();
        outputEl.textContent = "";
        if (finalizeStatus) {
          finalizeStatus.textContent = "";
          finalizeStatus.style.color = "";
        }
        appendSystemBanners();
        appendLine("text-line--system", "> 会話履歴をリセットしました。");
        if (payload?.cleared === false) {
          appendLine("text-line--warning", "⚠️ サーバ側のセッションが見つかりませんでした。");
        }
        inputEl.focus();
      } catch (error) {
        appendLine(
          "text-line--error",
          `❌ 履歴リセットに失敗しました: ${error instanceof Error ? error.message : String(error)}`,
        );
      } finally {
        resetButton.disabled = false;
      }
    });
  }
  
  // 初期メッセージ: 設定されたシステムメッセージを使う
  appendSystemBanners();
}

// アプリ起動
initApp().catch(err => console.error("Fatal Error:", err));
