"""
Sensitivity analysis module for financial models.
Tests impact of variable changes on key outputs.
"""

import argparse
import json
import sys
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

# dcf_model.py から DCFModel をインポート (同じディレクトリにある前提)
try:
    from dcf_model import DCFModel
except ImportError:
    # 動作確認用にダミーモデルを定義 (dcf_modelがない場合)
    class DCFModel:
        def __init__(self, name="Test"): 
            self.assumptions = {"terminal_growth": 0.03}
            self.wacc_components = {"wacc": 0.10}
            self.valuation_results = {"enterprise_value": 1000}
        def project_cash_flows(self): pass
        def calculate_enterprise_value(self): return {"enterprise_value": 1000}


class SensitivityAnalyzer:
    """Perform sensitivity analysis on financial models."""

    def __init__(self, base_model: Any):
        self.base_model = base_model
        self.base_output = None
        self.sensitivity_results = {}

    def one_way_sensitivity(
        self,
        variable_name: str,
        base_value: float,
        range_pct: float,
        steps: int,
        output_func: Callable,
        model_update_func: Callable,
    ) -> pd.DataFrame:
        min_val = base_value * (1 - range_pct)
        max_val = base_value * (1 + range_pct)
        test_values = np.linspace(min_val, max_val, steps)

        results = []
        # Store original output for comparison
        base_output_val = output_func()

        for value in test_values:
            model_update_func(value)
            output = output_func()
            results.append(
                {
                    "variable": variable_name,
                    "value": value,
                    "pct_change": (value - base_value) / base_value * 100 if base_value != 0 else 0,
                    "output": output,
                    "output_change": output - base_output_val,
                }
            )

        # Reset to base
        model_update_func(base_value)
        return pd.DataFrame(results)

    def tornado_analysis(
        self, variables: dict[str, dict[str, Any]], output_func: Callable
    ) -> pd.DataFrame:
        self.base_output = output_func()
        tornado_data = []

        for var_name, var_info in variables.items():
            # Test low
            var_info["update_func"](var_info["low"])
            low_output = output_func()

            # Test high
            var_info["update_func"](var_info["high"])
            high_output = output_func()

            # Reset
            var_info["update_func"](var_info["base"])

            impact = high_output - low_output
            
            tornado_data.append(
                {
                    "variable": var_name,
                    "base_value": var_info["base"],
                    "low_value": var_info["low"],
                    "high_value": var_info["high"],
                    "low_output": low_output,
                    "high_output": high_output,
                    "impact": abs(impact),
                    "impact_pct": abs(impact) / self.base_output * 100 if self.base_output != 0 else 0,
                }
            )

        df = pd.DataFrame(tornado_data)
        return df.sort_values("impact", ascending=False)


# --- ヘルパー関数: 文字列からモデル操作へのマッピング ---

def get_output_metric(model: DCFModel, metric_name: str = "enterprise_value") -> float:
    """モデルの状態から指定された指標を取り出す"""
    # 再計算を実行
    model.project_cash_flows()
    results = model.calculate_enterprise_value()
    return results.get(metric_name, 0.0)

def update_model_variable(model: DCFModel, var_name: str, value: float):
    """変数名に応じてモデルを更新する"""
    if var_name == "terminal_growth":
        model.assumptions["terminal_growth"] = value
    elif var_name == "margin":
        # 全期間のマージンを一律変更
        years = model.assumptions["projection_years"]
        model.assumptions["ebitda_margin"] = [value] * years
    elif var_name == "growth":
        # 全期間の成長率を一律変更
        years = model.assumptions["projection_years"]
        model.assumptions["revenue_growth"] = [value] * years
    elif var_name == "wacc":
        # WACCを直接上書き
        model.wacc_components["wacc"] = value
    elif var_name == "beta":
        # Betaを変更してWACC再計算が必要だが、簡易的にcomponentを更新
        model.wacc_components["beta"] = value
        # 本来は calculate_wacc を再実行すべき箇所
        # 簡易化のためWACC自体を再計算するロジックは省略し、パラメータ更新のみとする
        pass 


def run_sensitivity_cli(args: argparse.Namespace) -> dict[str, Any]:
    """CLI引数に基づいて感度分析を実行し、結果辞書を返す"""

    # 1. ベースモデルの準備 (簡易化のためデフォルト値を使用)
    # 本番では dcf_model.py の引数解析ロジックと統合するか、
    # 設定ファイルからベースモデルを読み込むのが望ましい
    model = DCFModel("SensitivityCorp")
    
    # デフォルトの前提条件をセット
    years = 5
    model.set_historical_financials(
        revenue=[1000], ebitda=[200], capex=[50], nwc=[100], years=[2024]
    )
    model.set_assumptions(
        projection_years=years,
        revenue_growth=[0.10] * years,
        ebitda_margin=[0.20] * years,
        terminal_growth=0.03
    )
    # ベースのWACC (WACCは入力として扱うか、計算させるか)
    base_wacc = 0.08
    model.wacc_components["wacc"] = base_wacc

    # Analyzer初期化
    analyzer = SensitivityAnalyzer(model)

    # 出力指標を取り出す関数
    output_func = lambda: get_output_metric(model, "enterprise_value")

    result_data = {}

    if args.analysis_type == "one_way":
        # 変数のマッピング
        var_name = args.variable
        base_val = 0.0
        
        # ベース値の取得 (簡易ロジック)
        if var_name == "terminal_growth": base_val = 0.03
        elif var_name == "margin": base_val = 0.20
        elif var_name == "growth": base_val = 0.10
        elif var_name == "wacc": base_val = 0.08
        else:
            return {"error": f"Unknown variable: {var_name}"}

        # 更新関数の作成
        update_func = lambda x: update_model_variable(model, var_name, x)

        # 分析実行
        df = analyzer.one_way_sensitivity(
            variable_name=var_name,
            base_value=base_val,
            range_pct=args.range,
            steps=args.steps,
            output_func=output_func,
            model_update_func=update_func
        )
        
        result_data = {
            "analysis_type": "one_way",
            "variable": var_name,
            "base_value": base_val,
            "data": df.to_dict(orient="records")
        }

    elif args.analysis_type == "tornado":
        # トルネード分析用に主要変数を定義
        # ベース値 ± range% でテスト
        range_pct = args.range
        
        vars_config = {
            "Terminal Growth": {
                "base": 0.03, 
                "low": 0.03 * (1 - range_pct), 
                "high": 0.03 * (1 + range_pct),
                "update_func": lambda x: update_model_variable(model, "terminal_growth", x)
            },
            "EBITDA Margin": {
                "base": 0.20, 
                "low": 0.20 * (1 - range_pct), 
                "high": 0.20 * (1 + range_pct),
                "update_func": lambda x: update_model_variable(model, "margin", x)
            },
            "WACC": {
                "base": 0.08, 
                "low": 0.08 * (1 - range_pct), 
                "high": 0.08 * (1 + range_pct),
                "update_func": lambda x: update_model_variable(model, "wacc", x)
            },
             "Revenue Growth": {
                "base": 0.10, 
                "low": 0.10 * (1 - range_pct), 
                "high": 0.10 * (1 + range_pct),
                "update_func": lambda x: update_model_variable(model, "growth", x)
            }
        }

        df = analyzer.tornado_analysis(vars_config, output_func)
        
        result_data = {
            "analysis_type": "tornado",
            "range_pct": range_pct,
            "data": df.to_dict(orient="records")
        }

    return result_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Financial Sensitivity Analysis CLI")
    
    # 分析タイプの選択
    parser.add_argument(
        "--type", 
        dest="analysis_type", 
        choices=["one_way", "tornado"], 
        default="tornado",
        help="Type of sensitivity analysis to perform"
    )
    
    # One-way用の設定
    parser.add_argument(
        "--variable", 
        type=str, 
        default="wacc", 
        choices=["growth", "margin", "wacc", "terminal_growth"],
        help="Variable to test for one-way analysis"
    )
    
    # 共通設定
    parser.add_argument("--range", type=float, default=0.20, help="Sensitivity range (decimal, e.g. 0.20 for 20%)")
    parser.add_argument("--steps", type=int, default=5, help="Number of steps for one-way analysis")

    args = parser.parse_args()

    # 分析実行
    result = run_sensitivity_cli(args)

    # 強制的にJSON出力
    print(json.dumps(result, indent=2))