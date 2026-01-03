const CONFIG = {
  baseUrl: "http://localhost:8165",
  workspace: "demo",
  chatLimit: 100,
};

const SAMPLE_DOCUMENTS = [
  {
    workspace: CONFIG.workspace,
    doc_id: "plan-apac-2026",
    title: "2026年度 APAC 調達計画",
    summary: "APAC地域向けノートPC調達の方針とタイムラインを整理した概要。",
    body: "APAC地域の調達戦略、予算配分、リスク軽減策を整理。",
    status: "in_progress",
    region: "APAC",
    priority: 1,
    created_at: "2025-10-01T08:30:00Z",
    metadata: {
      workspace: CONFIG.workspace,
      category: "planning",
      owner_department: "IT Procurement",
    },
  },
  {
    workspace: CONFIG.workspace,
    doc_id: "contract-na-2025",
    title: "北米向けサプライヤー契約書",
    summary: "北米市場向けサプライヤー契約とSLA概要。",
    body: "契約期間、価格、SLAを含む契約文書の要約。",
    status: "finalized",
    region: "NA",
    priority: 2,
    created_at: "2025-10-02T09:15:00Z",
    metadata: {
      workspace: CONFIG.workspace,
      category: "contract",
      supplier: "Quantum Systems",
    },
  },
  {
    workspace: CONFIG.workspace,
    doc_id: "supply-risk-2025",
    title: "サプライチェーンリスク分析",
    summary: "主要部品供給におけるリスクと代替サプライヤー評価。",
    body: "地政学リスクと在庫確保の観点で評価。",
    status: "draft",
    region: "Global",
    priority: 3,
    created_at: "2025-10-03T11:05:00Z",
    metadata: { workspace: CONFIG.workspace, category: "risk", year: 2025 },
  },
  {
    workspace: CONFIG.workspace,
    doc_id: "budget-review-2026",
    title: "2026年度調達予算レビュー",
    summary: "FY2026調達予算とコスト削減目標のレビュー。",
    body: "TCO削減目標と各地域への配分をまとめる。",
    status: "approved",
    region: "Global",
    priority: 1,
    created_at: "2025-10-04T14:20:00Z",
    metadata: { workspace: CONFIG.workspace, category: "budget", year: 2026 },
  },
  {
    workspace: CONFIG.workspace,
    doc_id: "ops-guideline-2025",
    title: "運用ガイドライン",
    summary: "調達プロセス運用のベストプラクティスとKPI。",
    body: "発注から納品までの運用フローとKPI定義。",
    status: "published",
    region: "APAC",
    priority: 4,
    created_at: "2025-10-05T09:45:00Z",
    metadata: { workspace: CONFIG.workspace, category: "ops", version: "1.0" },
  },
];

const state = {
  chatMessages: [],
  results: [],
  registeredCount: 0,
  lastAction: "—",
};

const chatLog = document.getElementById("chat-log");
const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const resultsContainer = document.getElementById("results");
const registerButton = document.getElementById("register-button");
const deleteAllButton = document.getElementById("delete-all-button");
const registeredCountLabel = document.getElementById("registered-count");
const lastActionLabel = document.getElementById("last-action");
const workspaceLabel = document.getElementById("workspace-label");

workspaceLabel.textContent = CONFIG.workspace;

const formatTimestamp = (date) => new Date(date).toLocaleTimeString("ja-JP", {
  hour: "2-digit",
  minute: "2-digit",
});

const addChatMessage = (role, content) => {
  const message = {
    role,
    content,
    timestamp: new Date().toISOString(),
  };
  state.chatMessages = [message, ...state.chatMessages].slice(0, CONFIG.chatLimit);
  renderChat();
};

const updateStatus = ({ registeredCount, lastAction }) => {
  if (typeof registeredCount === "number") {
    state.registeredCount = registeredCount;
  }
  if (lastAction) {
    state.lastAction = lastAction;
  }
  registeredCountLabel.textContent = String(state.registeredCount);
  lastActionLabel.textContent = state.lastAction;
};

const renderChat = () => {
  chatLog.innerHTML = "";
  if (state.chatMessages.length === 0) {
    const empty = document.createElement("div");
    empty.className = "result-empty";
    empty.textContent = "ここにチャット履歴が表示されます。";
    chatLog.appendChild(empty);
    return;
  }

  state.chatMessages
    .slice()
    .reverse()
    .forEach((message) => {
      const bubble = document.createElement("div");
      bubble.className = `chat__message chat__message--${message.role}`;
      bubble.textContent = message.content;

      const meta = document.createElement("span");
      meta.className = "chat__meta";
      meta.textContent = `${message.role.toUpperCase()} · ${formatTimestamp(
        message.timestamp
      )}`;
      bubble.appendChild(meta);
      chatLog.appendChild(bubble);
    });
};

const renderResults = () => {
  resultsContainer.innerHTML = "";

  if (state.results.length === 0) {
    const empty = document.createElement("div");
    empty.className = "result-empty";
    empty.textContent = "検索結果はまだありません。";
    resultsContainer.appendChild(empty);
    return;
  }

  const formatSourceLabel = (source, index) => {
    if (source && typeof source === "object") {
      return source.doc_id || source.id || `source-${index + 1}`;
    }
    return `source-${index + 1}`;
  };

  const formatSourceText = (source) => {
    if (!source) {
      return "詳細なし";
    }
    if (typeof source === "string") {
      return source.length > 180 ? `${source.slice(0, 180)}…` : source;
    }
    if (typeof source === "object") {
      const candidates = [source.title, source.summary, source.body, source.text, source.content];
      const first = candidates.find((item) => typeof item === "string" && item.trim());
      if (first) {
        return first.length > 180 ? `${first.slice(0, 180)}…` : first;
      }
      if (Array.isArray(source.body)) {
        const joined = source.body.join(" ");
        return joined.length > 180 ? `${joined.slice(0, 180)}…` : joined;
      }
      const asJson = JSON.stringify(source);
      return asJson.length > 180 ? `${asJson.slice(0, 180)}…` : asJson;
    }
    return String(source);
  };

  state.results.forEach((result) => {
    const card = document.createElement("div");
    card.className = "result-card";

    const title = document.createElement("h3");
    title.textContent = result.mode ? `mode: ${result.mode}` : "result";
    card.appendChild(title);

    const answer = document.createElement("p");
    answer.className = "result-card__answer";
    answer.textContent = result.answer || "回答がありません。";
    card.appendChild(answer);

    const meta = document.createElement("div");
    meta.className = "result-card__meta";
    const sources = Array.isArray(result.sources) ? result.sources : [];
    meta.textContent = `sources: ${sources.length}`;
    card.appendChild(meta);

    if (sources.length > 0) {
      const sourcesWrap = document.createElement("div");
      sourcesWrap.className = "result-card__sources";

      sources.forEach((source, index) => {
        const item = document.createElement("div");
        item.className = "result-source";

        const header = document.createElement("div");
        header.className = "result-source__header";

        const label = document.createElement("span");
        label.textContent = formatSourceLabel(source, index);
        header.appendChild(label);

        if (source && typeof source === "object" && source.doc_id) {
          const deleteButton = document.createElement("button");
          deleteButton.className = "ghost";
          deleteButton.textContent = "削除";
          deleteButton.dataset.docId = source.doc_id;
          deleteButton.addEventListener("click", () => handleDeleteSingle(source.doc_id));
          header.appendChild(deleteButton);
        }

        const detail = document.createElement("div");
        detail.className = "result-source__detail";
        detail.textContent = formatSourceText(source);

        item.appendChild(header);
        item.appendChild(detail);
        sourcesWrap.appendChild(item);
      });

      card.appendChild(sourcesWrap);
    }

    resultsContainer.appendChild(card);
  });
};

const apiRequest = async ({ path, method, body }) => {
  const url = `${CONFIG.baseUrl}${path}`;
  const options = {
    method,
    headers: {
      "Content-Type": "application/json",
    },
  };
  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload.detail || payload.message || "APIエラーが発生しました。";
    throw new Error(message);
  }
  return payload;
};

const handleRegister = async () => {
  addChatMessage("system", "サンプルデータを登録しています...");
  try {
    const response = await apiRequest({
      path: "/minirag/documents/bulk",
      method: "POST",
      body: {
        documents: SAMPLE_DOCUMENTS,
        overwrite: true,
      },
    });

    updateStatus({
      registeredCount: response.inserted,
      lastAction: "登録完了",
    });
    addChatMessage(
      "system",
      `登録が完了しました。inserted: ${response.inserted}`
    );
  } catch (error) {
    updateStatus({ lastAction: "登録失敗" });
    addChatMessage("error", `登録に失敗しました: ${error.message}`);
  }
};

const handleSearch = async (query) => {
  const trimmed = query.trim();
  if (!trimmed) {
    addChatMessage("error", "検索クエリが空です。入力してから実行してください。");
    return;
  }

  addChatMessage("user", trimmed);
  addChatMessage("system", "検索中...結果を取得しています。");

  try {
    const response = await apiRequest({
      path: "/minirag/search",
      method: "POST",
      body: {
        query: trimmed,
        modes: ["mini"],
        top_k: 5,
        include_provenance: true,
        metadata_filter: { workspace: CONFIG.workspace },
      },
    });

    state.results = response.results || [];
    renderResults();

    const totalSources = state.results.reduce(
      (sum, result) => sum + (result.sources ? result.sources.length : 0),
      0
    );
    const note = response.note ? ` (${response.note})` : "";
    addChatMessage(
      "system",
      `検索が完了しました。sources: ${totalSources}${note}`
    );
    updateStatus({ lastAction: "検索完了" });
  } catch (error) {
    updateStatus({ lastAction: "検索失敗" });
    addChatMessage("error", `検索に失敗しました: ${error.message}`);
  }
};

const handleDeleteAll = async () => {
  addChatMessage("system", "全件削除を実行しています...");
  try {
    const response = await apiRequest({
      path: `/minirag/documents?workspace=${encodeURIComponent(CONFIG.workspace)}`,
      method: "DELETE",
    });

    state.results = [];
    renderResults();
    updateStatus({ registeredCount: 0, lastAction: "全件削除" });
    addChatMessage(
      "system",
      `削除が完了しました。deleted: ${response.deleted}`
    );
  } catch (error) {
    updateStatus({ lastAction: "削除失敗" });
    addChatMessage("error", `削除に失敗しました: ${error.message}`);
  }
};

const handleDeleteSingle = async (docId) => {
  addChatMessage("system", `doc_id ${docId} を削除しています...`);
  try {
    const response = await apiRequest({
      path: `/minirag/documents/${encodeURIComponent(
        docId
      )}?workspace=${encodeURIComponent(CONFIG.workspace)}`,
      method: "DELETE",
    });

    state.results = state.results.filter((item) => item.doc_id !== docId);
    renderResults();
    updateStatus({ lastAction: "個別削除" });
    addChatMessage(
      "system",
      `削除が完了しました。deleted: ${response.deleted}`
    );
  } catch (error) {
    updateStatus({ lastAction: "削除失敗" });
    addChatMessage("error", `削除に失敗しました: ${error.message}`);
  }
};

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  handleSearch(searchInput.value);
  searchInput.value = "";
});

registerButton.addEventListener("click", handleRegister);
deleteAllButton.addEventListener("click", handleDeleteAll);

renderChat();
renderResults();
