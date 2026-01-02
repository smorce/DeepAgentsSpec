const http = require("http");
const https = require("https");
const { URL } = require("url");
const { execSync } = require("child_process");

const baseUrl = process.env.MINIRAG_BASE_URL || "http://localhost:8000";
const apiKey = process.env.MINIRAG_DEMO_API_KEY || "demo-key";
const workspace = "demo";

const sampleDocuments = [
  {
    workspace,
    doc_id: "doc-001",
    title: "APAC laptop procurement plan FY2026",
    summary: "Plan to procure 5,000 laptops across APAC with cost optimization.",
    body: "The plan outlines timeline, budget, and supplier evaluation for laptops.",
    status: "in_progress",
    region: "APAC",
    priority: 1,
    created_at: "2025-10-01T08:30:00Z",
    metadata: { category: "plan", year: 2026 },
  },
  {
    workspace,
    doc_id: "doc-002",
    title: "North America supplier contract 2025",
    summary: "Exclusive laptop supply contract with Quantum Systems Inc.",
    body: "Contract covers pricing, delivery SLA, and support terms.",
    status: "finalized",
    region: "NA",
    priority: 1,
    created_at: "2025-10-02T09:15:00Z",
    metadata: { category: "contract", year: 2025 },
  },
  {
    workspace,
    doc_id: "doc-003",
    title: "EU device refresh schedule",
    summary: "Refresh schedule for EU region devices including laptops and tablets.",
    body: "Schedule includes replacement cycles and inventory checks.",
    status: "draft",
    region: "EU",
    priority: 2,
    created_at: "2025-09-18T11:00:00Z",
    metadata: { category: "schedule", year: 2025 },
  },
  {
    workspace,
    doc_id: "doc-004",
    title: "APAC keyboard accessory budget",
    summary: "Accessory budget for keyboards and docking stations.",
    body: "Covers vendor shortlist and budget allocation by site.",
    status: "in_progress",
    region: "APAC",
    priority: 3,
    created_at: "2025-09-25T07:45:00Z",
    metadata: { category: "budget", year: 2025 },
  },
  {
    workspace,
    doc_id: "doc-005",
    title: "Global laptop refresh highlights",
    summary: "Highlights from the global laptop refresh initiative.",
    body: "Includes key milestones, risk mitigation, and inventory notes.",
    status: "published",
    region: "Global",
    priority: 2,
    created_at: "2025-08-20T16:05:00Z",
    metadata: { category: "report", year: 2025 },
  },
];

const headers = {
  "Content-Type": "application/json",
  "X-Demo-Api-Key": apiKey,
};

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const requestJson = (method, targetUrl, body, extraHeaders = {}) =>
  new Promise((resolve, reject) => {
    const url = new URL(targetUrl);
    const client = url.protocol === "https:" ? https : http;
    const payload = body ? JSON.stringify(body) : null;
    const requestHeaders = { ...headers, ...extraHeaders };
    if (payload) {
      requestHeaders["Content-Length"] = Buffer.byteLength(payload);
    }

    const req = client.request(
      {
        method,
        hostname: url.hostname,
        port: url.port,
        path: url.pathname + url.search,
        headers: requestHeaders,
      },
      (res) => {
        let raw = "";
        res.on("data", (chunk) => {
          raw += chunk;
        });
        res.on("end", () => {
          let json;
          try {
            json = raw ? JSON.parse(raw) : {};
          } catch (error) {
            reject(new Error("Failed to parse JSON response."));
            return;
          }
          if (res.statusCode && res.statusCode >= 400) {
            reject(
              new Error(
                `Request failed: ${res.statusCode} ${JSON.stringify(json)}`
              )
            );
            return;
          }
          resolve(json);
        });
      }
    );

    req.on("error", (error) => reject(error));
    if (payload) {
      req.write(payload);
    }
    req.end();
  });

const assertTopResults = (results, expectedIds) => {
  const topIds = results.slice(0, 3).map((item) => item.doc_id);
  const hit = expectedIds.some((id) => topIds.includes(id));
  if (!hit) {
    throw new Error("Top results do not include expected documents.");
  }
};

const main = async () => {
  await requestJson("POST", `${baseUrl}/minirag/documents/bulk`, {
    workspace,
    documents: sampleDocuments,
  });

  const start = Date.now();
  const search = await requestJson("POST", `${baseUrl}/minirag/search`, {
    workspace,
    query: "laptop",
    top_k: 5,
  });
  const elapsed = Date.now() - start;
  if (elapsed > 3000) {
    throw new Error("Search exceeded 3 seconds.");
  }
  if (search.count < 1) {
    throw new Error("Search returned no results.");
  }
  assertTopResults(search.results, ["doc-001", "doc-002", "doc-005"]);

  if (process.env.MINIRAG_RESTART_COMMAND) {
    execSync(process.env.MINIRAG_RESTART_COMMAND, { stdio: "inherit" });
    await sleep(2000);
    const afterRestart = await requestJson(
      "POST",
      `${baseUrl}/minirag/search`,
      { workspace, query: "laptop", top_k: 5 }
    );
    if (afterRestart.count < 1) {
      throw new Error("Search after restart returned no results.");
    }
  }

  const deleteSingle = await requestJson(
    "DELETE",
    `${baseUrl}/minirag/documents/doc-002?workspace=${workspace}`
  );
  if (deleteSingle.deleted_count < 0) {
    throw new Error("Delete count should be non-negative.");
  }

  await requestJson(
    "DELETE",
    `${baseUrl}/minirag/documents?workspace=${workspace}`
  );

  const afterDelete = await requestJson(
    "POST",
    `${baseUrl}/minirag/search`,
    { workspace, query: "laptop", top_k: 5 }
  );
  if (afterDelete.count !== 0 || afterDelete.note !== "0件") {
    throw new Error("Expected zero results after delete.");
  }
};

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
