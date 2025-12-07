---
name: sensitivity_analysis
description: このスキルは、財務モデルにおける変数の変動が出力（企業価値やIRRなど）に与える影響を評価するためのスクリプト。一方向感度分析、二方向感度分析、トルネード分析、損益分岐点分析をサポートし、最も影響力の大きいリスク要因や価値ドライバーを特定します。
---

## コア機能

### 感度分析
- 一方向感度分析（One-way Sensitivity）：1つの変数（成長率、EBITDAマージン、WACC、終期成長率）を指定範囲で変化させ、出力指標（企業価値など）への影響を段階的に分析
- トルネード分析（Tornado Analysis）：複数の変数についてそれぞれの低値/高値での出力を計算し、影響度（impact）でソートして最も影響の大きい価値ドライバーを特定
- 主要変数のサポート：売上成長率（Revenue Growth）、EBITDAマージン、WACC、終期成長率（Terminal Growth）
- 出力指標の柔軟な指定：企業価値、株式価値、IRRなどの任意の指標を分析対象として指定可能
- 影響度の定量化：各変数の変化に対する出力の変化量と変化率（%）を計算

## 含まれるスクリプト

- `sensitivity_analysis.py`: 感度テストフレームワーク

## 入力形式

### 感度分析
{
  "input_schema": {
    "type": "object",
    "properties": {
      "analysis_type": {
        "type": "string",
        "enum": [
          "one_way",
          "two_way",
          "tornado",
          "breakeven",
          "scenario"
        ],
        "description": "The specific type of sensitivity analysis to perform."
      },
      "target_metric": {
        "type": "string",
        "description": "The output metric to measure (e.g., 'enterprise_value', 'equity_value', 'irr'). Maps to output_func."
      },
      "one_way_config": {
        "type": "object",
        "description": "Parameters for One-Way Sensitivity Analysis. Required if analysis_type is 'one_way'.",
        "properties": {
          "variable_name": { "type": "string", "description": "Name of the variable to test" },
          "base_value": { "type": "number", "description": "The base case value" },
          "range_pct": { "type": "number", "description": "Range percentage as decimal (e.g., 0.20 for +/- 20%)" },
          "steps": { "type": "integer", "description": "Number of steps in the range", "default": 5 }
        },
        "required": ["variable_name", "base_value", "range_pct"]
      },
      "two_way_config": {
        "type": "object",
        "description": "Parameters for Two-Way Sensitivity Analysis. Required if analysis_type is 'two_way'.",
        "properties": {
          "var1_name": { "type": "string" },
          "var1_values": { 
            "type": "array", 
            "items": { "type": "number" },
            "description": "List of specific values to test for variable 1"
          },
          "var2_name": { "type": "string" },
          "var2_values": { 
            "type": "array", 
            "items": { "type": "number" },
            "description": "List of specific values to test for variable 2"
          }
        },
        "required": ["var1_name", "var1_values", "var2_name", "var2_values"]
      },
      "tornado_config": {
        "type": "object",
        "description": "Parameters for Tornado Analysis. Required if analysis_type is 'tornado'.",
        "properties": {
          "variables": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "name": { "type": "string" },
                "base": { "type": "number" },
                "low": { "type": "number" },
                "high": { "type": "number" }
              },
              "required": ["name", "base", "low", "high"]
            },
            "description": "List of variables with their base, low, and high values."
          }
        },
        "required": ["variables"]
      },
      "breakeven_config": {
        "type": "object",
        "description": "Parameters for Breakeven Analysis. Required if analysis_type is 'breakeven'.",
        "properties": {
          "variable_name": { "type": "string" },
          "target_value": { "type": "number", "description": "The target output value to reach" },
          "min_search": { "type": "number", "description": "Minimum value of the variable to search" },
          "max_search": { "type": "number", "description": "Maximum value of the variable to search" }
        },
        "required": ["variable_name", "target_value", "min_search", "max_search"]
      }
    },
    "required": ["analysis_type", "target_metric"]
  }
}

## 出力形式

### 感度分析
{
  "analysis_type": "tornado",
  "range_pct": 0.1,
  "data": [
    {
      "variable": "WACC",
      "base_value": 0.08,
      "low_value": 0.072,
      "high_value": 0.088,
      "low_output": 2542.1,
      "high_output": 1980.5,
      "impact": 561.6,
      "impact_pct": 24.8
    },
    {
      "variable": "EBITDA Margin",
      "base_value": 0.2,
      "low_value": 0.18,
      "high_value": 0.22,
      "low_output": 2000.0,
      "high_output": 2444.4,
      "impact": 444.4,
      "impact_pct": 19.6
    }
    // ... 他の変数
  ]
}

## ユーザー入力例

"成長率とWACCが企業価値に与える影響を示す感度分析を作成してください"

## Tool Use Examples

uv run --link-mode=copy sensitivity_analysis.py --type tornado --range 0.10