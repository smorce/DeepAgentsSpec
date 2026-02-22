# Harness V2: 自律的ハーネスエンジニアリング改良システム

## 1. 目的

「AIエージェントによるハーネスエンジニアリングの自律的改善」を実現する。
月に3つ程度のハーネス改善がエージェント主導で実行されることを目標とする。

### V1からの根本的な変更点

| 観点 | V1（現行） | V2（新） |
|------|-----------|----------|
| Radar | ブログのタイトル/URLだけ収集 | 記事本文を読み、ハーネス改善アイデアを抽出・評価 |
| ギャップ分析 | なし | 現状→理想→差分をSoR化。捨てたアイデアも記録 |
| Backlog | 即座にEXP化、レビューなし | マルチセッションレビューループで計画を洗練 |
| Mutation | タグ付与の純関数（実質無効） | 実際のコードベース改修スクリプト |
| Implement | テンプレ生成のみ | ディレクトリ構造変更を含む大規模改修に対応 |

---

## 2. 新アーキテクチャ

### 2.1 パイプライン概要

```
[Radar] → [Analyze] → [Backlog] → [Review Loop] → [Plan] → [Execute] → [Validate] → [Garden]
```

### 2.2 Radar（情報収集 + アイデア抽出）

**目的**: 公式ブログの最新記事の「本文」を読み、ハーネスエンジニアリングに適用可能な新しいアイデアを抽出する。

**記事本文の取得方法**: Codex CLI から `chrome-devtools.new_page` MCP を使用してブログのトップページを実際にブラウザで開き、最新記事のリンクをたどって本文を取得する。

```
codex exec 'あなたは chrome-devtools.new_page が使えます。
tool `chrome-devtools.new_page({"url": "<blog_homepage>"})` で開き、
安定するまで待ってください。最新の記事1件の詳細な内容を取得してください。'
```

**フロー**:
1. `official_sources.json` の6ブログの `homepage` URLをForループで巡回
2. **各ブログのトップページを chrome-devtools MCP で開き、最新記事1件を特定**
3. 特定した記事のリンクを開き、**本文を詳細に読み取る**
4. 読み取った本文から以下を抽出:
   - 記事の詳細な要約（5-10文）
   - ハーネスエンジニアリングに関連するアイデア（0〜5個）
   - 各アイデアの適用可能性スコア（1-5）
5. 公式ブログだけでは情報不足の場合、Zenn/Qiita を chrome-devtools で検索して補足情報を収集
6. **既存ナレッジベースとの差分検出**: 蓄積済みのアイデアと重複しないか確認

**アウトプット**: `harness/agent_radar/ideas/` 配下にアイデアファイル（IDEA-NNN.json）

### 2.3 Analyze（ギャップ分析）

**目的**: 抽出したアイデアをコードベースの現状と突き合わせ、効果とリスクを分析する。

**フロー（各アイデアに対して）**:
1. **現状分析**: コードベースの該当領域を分析
2. **理想状態**: アイデアを適用した場合の理想を記述
3. **差分**: 現状→理想のギャップを具体的に記述
4. **効果分析**: メリット・デメリットを列挙
5. **判定**: 採用/不採用/要調査
6. **不採用理由**: 捨てたアイデアには理由を記録

**アウトプット**: `harness/agent_radar/analysis/` 配下にギャップ分析レポート

### 2.4 Backlog + Review Loop（計画と多段レビュー）

**目的**: 採用されたアイデアを実行計画に変換し、Codex CLIの非対話モードで多段レビューを行う。

**レビューループ設計**:
- セッションをまたいでレビューする（毎回コンテキストをリセット）
- Codex CLI (gpt-5.1-codex-mini) の `codex exec` を使用
- forループで「レビューステータスがcompleteになるまで」繰り返す
- 各セッションのレビューコメントは共通ファイルに追記

**評価軸**:
1. **ハーネス関連性** (1-5): ハーネスエンジニアリングの改良に直結するか
2. **実現可能性** (1-5): 現在のコードベースで実装可能か
3. **リスク** (1-5): 破壊的変更や副作用のリスク
4. **ROI** (1-5): 投入工数に対する改善効果
5. **SoR整合性** (1-5): 既存のSoR原則と矛盾しないか

**完了条件**: 全評価軸が3以上、かつ平均が3.5以上

**エージェント構成**:
1. **計画起草エージェント**: アイデア→実行計画の初版を作成
2. **レビューエージェント**: 計画の品質を評価軸に沿って評価・改善提案
3. **修正エージェント**: レビューコメントを反映して計画を修正

### 2.5 Execute（実行）

**目的**: レビュー完了した計画に基づいて、実際のコードベース改修を行う。

**対応範囲**:
- ファイル新規作成・編集・移動
- ディレクトリ構造変更（事前にマークダウンで構造を定義→スクリプト生成→実行）
- スクリプトの追加・修正
- 設定ファイルの変更

**安全性ガード**:
- 事前にディレクトリ構造のマークダウンを作成しSoR化
- 変更スクリプトを生成→レビュー→実行の三段階
- コミットメッセージは包括的（ロールバック可能）

### 2.6 SoRファイル構成（新規）

```
harness/agent_radar/
├── ideas/                          # 記事から抽出したアイデア
│   ├── IDEA-001.json               # アイデアごとのファイル
│   └── rejected/                   # 不採用アイデア（理由付き）
│       └── IDEA-R001.json
├── analysis/                       # ギャップ分析レポート
│   └── GAP-001.json
├── reviews/                        # レビューセッション記録
│   └── REV-EXP-084/
│       ├── plan.md                 # 実行計画
│       ├── review-session-001.md   # レビューセッション記録
│       └── status.json             # レビューステータス
├── executions/                     # 実行記録
│   └── EXEC-EXP-084/
│       ├── dir-structure.md        # 変更予定のディレクトリ構造
│       ├── change-script.py        # 変更スクリプト
│       └── result.json             # 実行結果
└── knowledge_base.json             # 蓄積されたナレッジ（重複検出用）
```

---

## 3. レビューループ詳細設計

### 3.1 セッションフロー

```
while review_status != "complete":
    session_id = generate_session_id()
    review_result = codex_exec(review_prompt, plan, past_reviews)
    append_to_review_file(session_id, review_result)
    if all_criteria_met(review_result):
        review_status = "complete"
    else:
        fix_result = codex_exec(fix_prompt, plan, review_result)
        update_plan(fix_result)
```

### 3.2 レビューエージェントプロンプト

```
あなたはハーネスエンジニアリングのレビュー担当エージェントです。

## レビュー対象
{plan_content}

## 評価観点
以下の5軸で1-5のスコアを付けてください。
1. ハーネス関連性: ハーネスエンジニアリングの改良に直結するか
2. 実現可能性: 現在のコードベースで実装可能か
3. リスク: 破壊的変更や副作用のリスク（高いほど低リスク）
4. ROI: 投入工数に対する改善効果
5. SoR整合性: 既存のSoR原則と矛盾しないか

## 過去のレビューメモ
{past_review_notes}

## 出力形式（JSON）
{
  "scores": {"harness_relevance": N, "feasibility": N, "risk": N, "roi": N, "sor_consistency": N},
  "verdict": "approve" | "revise" | "reject",
  "comments": "具体的な改善提案やコメント",
  "focus_areas": ["修正が必要な箇所のリスト"]
}
```

### 3.3 完了判定

- verdict が "approve" かつ全スコアが3以上かつ平均3.5以上 → complete
- verdict が "reject" → rejected（不採用理由を記録）
- それ以外 → 修正エージェントが計画を改善し、次のセッションへ

### 3.4 最大セッション数

レビューループの無限回避のため、最大5セッションとする。
5セッション経過しても complete にならない場合は "needs_human_review" とする。

---

## 4. 失敗時ポリシー（Self-Heal）

V2の各フェーズは「スキップして次へ進む」を基本戦略とする。V1のように同一ステップをリトライするのではなく、個別のアイデア/分析/レビュー単位で失敗を隔離する。

| フェーズ | 失敗時の挙動 |
|---------|-------------|
| Radar（記事分析） | 該当記事をスキップし、次の記事へ進む。エラーは progress log に記録。 |
| Analyze（ギャップ分析） | 該当アイデアをスキップし、エラーを progress log に記録。 |
| Review（レビュー） | 該当セッションをスキップし、次のセッションへ進む。Codex exec 失敗は即座に次へ。 |
| Review（修正） | 修正失敗時は前回の計画を維持したまま次のセッションへ。 |
| Execute（実行） | 変更は部分適用され `result.json` に `partial` ステータスで記録。`rollback-script.py` が利用可能。 |
| Post-execute validate | 失敗時はV1のself-heal（境界修復等）を試行。 |
| Post-execute garden | 失敗時はplaceholder自動置換とautonomous-growth.md同期を試行。 |

## 5. V2 監視メトリクス

パイプライン実行ごとに `metrics/latest.json` へ以下のメトリクスを追記する。

| メトリクス名 | 説明 |
|-------------|------|
| `v2.ideas_extracted` | 抽出されたアイデアの総数 |
| `v2.analyses_completed` | ギャップ分析が完了した数 |
| `v2.ideas_adopted` | 採用されたアイデアの数 |
| `v2.ideas_rejected` | 不採用アイデアの数 |
| `v2.reviews_approved` | レビュー通過した計画の数 |
| `v2.executions_completed` | 実行が成功した数 |
| `v2.avg_review_sessions` | レビュー通過までの平均セッション数 |

## 6. 捨てたアイデアの記録形式

```json
{
  "id": "IDEA-R001",
  "source_article": "記事タイトル",
  "source_url": "https://...",
  "idea_summary": "アイデアの概要",
  "rejected_at": "2026-02-22T...",
  "rejection_reason": "このコードベースではXXXの理由で適用困難",
  "rejection_category": "infeasible|low_roi|out_of_scope|already_implemented|too_risky",
  "scores": { ... },
  "reconsider_trigger": "XXXが変わった場合に再検討"
}
```
