# EPIC-SYS-001 Harness Radar Design Index

## Feature Map

- F-SYS-010: 公式ブログ限定ソースレーダー
- F-SYS-011: フィードバックループと制御システム
- F-SYS-012: 状態管理・永続化・差し替え表現
- F-SYS-013: 自律実装と監視ターゲット生成

## Shared Entities

- `SourceConfig`: 収集対象URL、許可パス、収集方式の定義
- `RadarItem`: 収集した記事メタデータ（title, link, published）
- `RadarState`: 直近スナップショットと差分比較用状態
- `GoldenRule`: ハーネスへ昇格済みの恒久ルール
- `MonitoringTarget`: 自律実装後に追跡する監視シグナル

## Shared APIs / Scripts

- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode update`
- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode validate`
- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode backlog`
- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode implement`
- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode garden`
- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode cycle`
- `uv run --no-project --link-mode=copy python harness/agent_radar/radar_ops.py --mode autogrow`

## Cross-feature Flow

1. F-SYS-010 が公式ブログの更新を検知する。
2. F-SYS-011 が差分を検証し、バックログ化と品質ゲートを回す。
3. F-SYS-013 がバックログ項目を実装アーティファクト・監視ターゲット・黄金律へ反映する。
4. F-SYS-012 が状態スナップショットを退避し、会話側に差し替え表現を返す。
