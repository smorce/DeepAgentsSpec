const CONFIG = {
  baseUrl: "http://localhost:8000",
  apiKeyHeader: "X-Demo-Api-Key",
  apiKeyValue: "demo-key",
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
    metadata: { category: "planning", owner_department: "IT Procurement" },
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
    metadata: { category: "contract", supplier: "Quantum Systems" },
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
    metadata: { category: "risk", year: 2025 },
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
    metadata: { category: "budget", year: 2026 },
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
    metadata: { category: "ops", version: "1.0" },
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

  state.results.forEach((result) => {
    const card = document.createElement("div");
    card.className = "result-card";

    const title = document.createElement("h3");
    title.textContent = result.title;
    card.appendChild(title);

    const summary = document.createElement("p");
    summary.textContent = result.summary;
    card.appendChild(summary);

    const meta = document.createElement("div");
    meta.className = "result-card__meta";
    meta.innerHTML = `
      <span>doc_id: ${result.doc_id}</span>
      <span>relevance: ${result.relevance}</span>
      <span>source_fields: ${
        result.source_fields && result.source_fields.length
          ? result.source_fields.join(", ")
          : "-"
      }</span>
    `;
    card.appendChild(meta);

    const actions = document.createElement("div");
    actions.className = "result-card__actions";
    const deleteButton = document.createElement("button");
    deleteButton.className = "ghost";
    deleteButton.textContent = "この結果を削除";
    deleteButton.dataset.docId = result.doc_id;
    deleteButton.addEventListener("click", () => handleDeleteSingle(result.doc_id));
    actions.appendChild(deleteButton);
    card.appendChild(actions);

    resultsContainer.appendChild(card);
  });
};

const apiRequest = async ({ path, method, body }) => {
  const url = `${CONFIG.baseUrl}${path}`;
  const options = {
    method,
    headers: {
      "Content-Type": "application/json",
      [CONFIG.apiKeyHeader]: CONFIG.apiKeyValue,
    },
  };
  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(url, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload.message || "APIエラーが発生しました。";
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
        workspace: CONFIG.workspace,
        documents: SAMPLE_DOCUMENTS,
      },
    });

    updateStatus({
      registeredCount: response.registered_count,
      lastAction: "登録完了",
    });
    addChatMessage(
      "system",
      `登録が完了しました。registered_count: ${response.registered_count}`
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
        workspace: CONFIG.workspace,
        query: trimmed,
        top_k: 5,
      },
    });

    state.results = response.results || [];
    renderResults();

    const note = response.note ? ` (${response.note})` : "";
    addChatMessage(
      "system",
      `検索が完了しました。count: ${response.count}${note}`
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
      `削除が完了しました。deleted_count: ${response.deleted_count}`
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
      `削除が完了しました。deleted_count: ${response.deleted_count}`
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
