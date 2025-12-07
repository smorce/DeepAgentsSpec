---
name: dcf_model
description: このスキルは、割引キャッシュフロー（DCF）法を使用して企業の投資分析と価値評価を行うためのスクリプト。過去の財務データ（売上、EBITDA、Capex等）と将来の予測前提（成長率、マージン、WACCパラメータ等）を入力とし、企業価値（Enterprise Value）、株式価値（Equity Value）、および株価を算出します。
---

## コア機能

### 割引キャッシュフロー（DCF）分析
- 過去財務データ（売上、EBITDA、資本支出、運転資本）の設定と分析
- 将来予測の前提設定（売上成長率、EBITDAマージン、税率、資本支出率、運転資本率、終期成長率）
- CAPMを使用した加重平均資本コスト（WACC）の計算（リスクフリーレート、ベータ、市場リスクプレミアム、負債コスト、負債/株式比率から算出）
- フリーキャッシュフロー（FCF）の予測（NOPAT、減価償却、資本支出、運転資本変動から算出）
- 永続成長法（Gordon Growth Model）またはエグジット倍数法を使用した終値の計算
- 企業価値の算出（予測期間のFCFの現在価値 + 終値の現在価値）
- 株式価値の算出（企業価値 - 純負債 + 現金）および1株当たり価値の計算
- 二方向感度分析（WACC、成長率、マージンなどの変数組み合わせによる企業価値への影響分析）

## 含まれるスクリプト

- `dcf_model.py`: 完全なDCF評価エンジン

## 入力形式

### 割引キャッシュフロー（DCF）分析
{
  "input_schema": {
    "type": "object",
    "properties": {
      "company_name": {
        "type": "string",
        "description": "Name of the company (maps to self.company_name)"
      },
      "historical_financials": {
        "type": "object",
        "description": "Data for self.historical_financials. Lists must have the same length.",
        "properties": {
          "years": {
            "type": "array",
            "items": { "type": "integer" },
            "description": "List of historical years (e.g., [2021, 2022, 2023])"
          },
          "revenue": {
            "type": "array",
            "items": { "type": "number" },
            "description": "Historical revenue"
          },
          "ebitda": {
            "type": "array",
            "items": { "type": "number" },
            "description": "Historical EBITDA"
          },
          "capex": {
            "type": "array",
            "items": { "type": "number" },
            "description": "Historical Capital Expenditure"
          },
          "nwc": {
            "type": "array",
            "items": { "type": "number" },
            "description": "Historical Net Working Capital"
          }
        },
        "required": ["years", "revenue", "ebitda", "capex", "nwc"]
      },
      "assumptions": {
        "type": "object",
        "description": "Data for self.assumptions. Growth/margin lists match projection_years.",
        "properties": {
          "projection_years": {
            "type": "integer",
            "description": "Number of years to forecast",
            "default": 5
          },
          "revenue_growth": {
            "type": "array",
            "items": { "type": "number" },
            "description": "Annual revenue growth rates (decimals)"
          },
          "ebitda_margin": {
            "type": "array",
            "items": { "type": "number" },
            "description": "Projected EBITDA margins (decimals)"
          },
          "tax_rate": {
            "type": "number",
            "description": "Corporate tax rate (decimal)",
            "default": 0.25
          },
          "capex_percent": {
            "type": "array",
            "items": { "type": "number" },
            "description": "Capex as % of revenue (decimals)"
          },
          "nwc_percent": {
            "type": "array",
            "items": { "type": "number" },
            "description": "NWC as % of revenue (decimals)"
          },
          "terminal_growth": {
            "type": "number",
            "description": "Terminal growth rate (decimal)",
            "default": 0.03
          }
        },
        "required": ["revenue_growth", "ebitda_margin"]
      },
      "wacc_parameters": {
        "type": "object",
        "description": "Parameters to calculate self.wacc_components.",
        "properties": {
          "risk_free_rate": { "type": "number" },
          "beta": { "type": "number" },
          "market_premium": { "type": "number" },
          "cost_of_debt": { "type": "number" },
          "debt_to_equity": { "type": "number" }
        },
        "required": ["risk_free_rate", "beta", "market_premium", "cost_of_debt", "debt_to_equity"]
      },
      "equity_params": {
        "type": "object",
        "description": "Additional params for final equity calculation (Bridge from EV to Equity Value).",
        "properties": {
          "net_debt": { "type": "number", "description": "Total Debt - Cash" },
          "shares_outstanding": { "type": "number", "description": "Total shares in millions" }
        },
        "required": ["net_debt", "shares_outstanding"]
      }
    },
    "required": ["company_name", "assumptions", "wacc_parameters", "equity_params"]
  }
}

## 出力形式

### 割引キャッシュフロー（DCF）分析
{
  "company_name": "Company",
  "metrics": {
    "enterprise_value": 1450.5,
    "equity_value": 1300.5,
    "value_per_share": 26.01,
    "wacc": 0.084
  },
  "details": { ... },
  "assumptions": { ... }
}

## ユーザー入力例

"添付の財務諸表を使用して、このテクノロジー企業のDCFモデルを構築してください"

## Tool Use Examples

uv run --link-mode=copy dcf_model.py \
  --company "MyTech" \
  --years 5 \
  --hist_years 2022 2023 \
  --hist_revenue 500 600 \
  --hist_ebitda 100 120 \
  --hist_capex 20 30 \
  --hist_nwc 50 60 \
  --growth 0.15 0.12 0.10 0.08 0.05 \
  --margin 0.25 \
  --beta 1.5 \
  --net_debt 150 \
  --shares 20