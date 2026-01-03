const http = require("http");
const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer");
const puppeteerConfig = require("../puppeteer.config");

const UI_ROOT = path.resolve(
  __dirname,
  "../../../services/frontend/EPIC-API-001-minirag-demo-ui/public"
);

const contentTypes = {
  ".html": "text/html",
  ".css": "text/css",
  ".js": "text/javascript",
};

const sampleDocuments = [
  {
    workspace: "demo",
    doc_id: "plan-apac-2026",
    title: "2026年度 APAC 調達計画",
    summary: "APAC地域向けノートPC調達の方針とタイムラインを整理した概要。",
    body: "APAC地域の調達戦略、予算配分、リスク軽減策を整理。",
    status: "in_progress",
    region: "APAC",
    priority: 1,
    created_at: "2025-10-01T08:30:00Z",
    metadata: { category: "planning" },
  },
  {
    workspace: "demo",
    doc_id: "contract-na-2025",
    title: "北米向けサプライヤー契約書",
    summary: "北米市場向けサプライヤー契約とSLA概要。",
    body: "契約期間、価格、SLAを含む契約文書の要約。",
    status: "finalized",
    region: "NA",
    priority: 2,
    created_at: "2025-10-02T09:15:00Z",
    metadata: { category: "contract" },
  },
  {
    workspace: "demo",
    doc_id: "supply-risk-2025",
    title: "サプライチェーンリスク分析",
    summary: "主要部品供給におけるリスクと代替サプライヤー評価。",
    body: "地政学リスクと在庫確保の観点で評価。",
    status: "draft",
    region: "Global",
    priority: 3,
    created_at: "2025-10-03T11:05:00Z",
    metadata: { category: "risk" },
  },
  {
    workspace: "demo",
    doc_id: "budget-review-2026",
    title: "2026年度調達予算レビュー",
    summary: "FY2026調達予算とコスト削減目標のレビュー。",
    body: "TCO削減目標と各地域への配分をまとめる。",
    status: "approved",
    region: "Global",
    priority: 1,
    created_at: "2025-10-04T14:20:00Z",
    metadata: { category: "budget" },
  },
  {
    workspace: "demo",
    doc_id: "ops-guideline-2025",
    title: "運用ガイドライン",
    summary: "調達プロセス運用のベストプラクティスとKPI。",
    body: "発注から納品までの運用フローとKPI定義。",
    status: "published",
    region: "APAC",
    priority: 4,
    created_at: "2025-10-05T09:45:00Z",
    metadata: { category: "ops" },
  },
];

const searchResults = [
  {
    doc_id: "plan-apac-2026",
    title: "2026年度 APAC 調達計画",
    summary: "APAC地域向けノートPC調達の方針とタイムラインを整理した概要。",
    relevance: 0.92,
    source_fields: ["summary"],
  },
  {
    doc_id: "budget-review-2026",
    title: "2026年度調達予算レビュー",
    summary: "FY2026調達予算とコスト削減目標のレビュー。",
    relevance: 0.84,
    source_fields: ["summary"],
  },
];

const createServer = () =>
  new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const requestPath = req.url === "/" ? "/index.html" : req.url;
      const filePath = path.join(UI_ROOT, requestPath.split("?")[0]);

      fs.readFile(filePath, (error, data) => {
        if (error) {
          res.writeHead(404);
          res.end("Not found");
          return;
        }
        const extension = path.extname(filePath);
        res.writeHead(200, { "Content-Type": contentTypes[extension] || "text/plain" });
        res.end(data);
      });
    });

    server.listen(0, () => {
      resolve(server);
    });
  });

const run = async () => {
  const server = await createServer();
  const { port } = server.address();
  const baseUrl = `http://localhost:${port}`;

  const browser = await puppeteer.launch(puppeteerConfig.launch);
  const page = await browser.newPage();
  await page.setViewport(puppeteerConfig.defaultViewport);

  await page.setRequestInterception(true);
  page.on("request", (request) => {
    const url = request.url();
    if (!url.startsWith("http://localhost:8000")) {
      request.continue();
      return;
    }

    if (url.includes("/minirag/documents/bulk") && request.method() === "POST") {
      request.respond({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          registered_count: sampleDocuments.length,
          documents: sampleDocuments,
        }),
      });
      return;
    }

    if (url.includes("/minirag/search") && request.method() === "POST") {
      request.respond({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          count: searchResults.length,
          results: searchResults,
        }),
      });
      return;
    }

    if (url.includes("/minirag/documents/") && request.method() === "DELETE") {
      request.respond({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          deleted_count: 1,
        }),
      });
      return;
    }

    if (url.includes("/minirag/documents") && request.method() === "DELETE") {
      request.respond({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          deleted_count: sampleDocuments.length,
        }),
      });
      return;
    }

    request.respond({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ message: "Not mocked" }),
    });
  });

  await page.goto(baseUrl, { waitUntil: "networkidle0" });

  await page.click("[data-testid='search-button']");
  await page.waitForSelector("[data-testid='chat-log'] .chat__message--error");

  await page.click("[data-testid='register-button']");
  await page.waitForFunction(
    () => document.getElementById("registered-count").textContent === "5"
  );

  await page.type("[data-testid='search-input']", "調達");
  await page.click("[data-testid='search-button']");
  await page.waitForSelector("[data-testid='search-results'] .result-card");

  const resultCount = await page.$$eval(
    "[data-testid='search-results'] .result-card",
    (nodes) => nodes.length
  );
  if (resultCount !== 2) {
    throw new Error(`Expected 2 results, got ${resultCount}`);
  }

  await page.click("[data-testid='search-results'] .result-card button");
  await page.waitForFunction(
    () =>
      document.querySelectorAll("[data-testid='search-results'] .result-card")
        .length === 1
  );

  await page.click("[data-testid='delete-all-button']");
  await page.waitForSelector("[data-testid='search-results'] .result-empty");

  await browser.close();
  server.close();
};

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
