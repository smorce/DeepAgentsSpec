#!/usr/bin/env bash

set -euo pipefail

# リポジトリルートを解決する
if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  ROOT_DIR="$git_root"
else
  ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

cd "$ROOT_DIR"

CONFIG_FILE="$ROOT_DIR/harness/harness-config.yaml"
PROGRESS_FILE="$ROOT_DIR/harness/AI-Agent-progress.txt"

timestamp() {
  date -u +"%Y-%m-%d %H:%MZ"
}

log() {
  echo "[init.sh] $*"
}

warn() {
  echo "[init.sh] WARN: $*" >&2
}

record_progress() {
  if [ -f "$PROGRESS_FILE" ]; then
    echo "[$(timestamp)] init: $*" >> "$PROGRESS_FILE"
  fi
}

# 実行スキップ用フラグ（1 でスキップ）
SKIP_FORMAT_OR_LINT="${SKIP_FORMAT_OR_LINT:-0}"
SKIP_VALIDATE_SPEC="${SKIP_VALIDATE_SPEC:-0}"
SKIP_VALIDATE_PLAN="${SKIP_VALIDATE_PLAN:-0}"
SKIP_UNIT_TESTS="${SKIP_UNIT_TESTS:-0}"
SKIP_E2E_TESTS="${SKIP_E2E_TESTS:-0}"
RUN_INTEGRATION_TESTS="${RUN_INTEGRATION_TESTS:-0}"

log "リポジトリルート: $ROOT_DIR"
record_progress "start"

# 基本ディレクトリの存在確認
required_dirs=(
  "architecture"
  "docs"
  "harness"
  "plans"
  "scripts"
  "services"
  "tests"
)

missing_dirs=()
for dir in "${required_dirs[@]}"; do
  if [ ! -d "$ROOT_DIR/$dir" ]; then
    missing_dirs+=("$dir")
  fi
done

if [ "${#missing_dirs[@]}" -gt 0 ]; then
  warn "必須ディレクトリが見つかりません: ${missing_dirs[*]}"
  record_progress "failed (missing dirs: ${missing_dirs[*]})"
  exit 1
fi

log "基本ディレクトリの存在確認: OK"

SERVICES=()
SERVICE_PATHS=()

# harness-config.yaml からサービス一覧を読み取る（簡易パース）
if [ -f "$CONFIG_FILE" ]; then
  current_name=""
  while IFS= read -r line; do
    case "$line" in
      "  - name:"*)
        current_name="${line#*: }"
        ;;
      "    path:"*)
        current_path="${line#*: }"
        if [ -n "$current_name" ]; then
          SERVICES+=("$current_name")
          SERVICE_PATHS+=("$current_path")
          current_name=""
        fi
        ;;
    esac
  done < "$CONFIG_FILE"
else
  warn "harness-config.yaml が見つからないため、サービス一覧をスキップします。"
fi

if [ "${#SERVICES[@]}" -gt 0 ]; then
  log "検出したサービス: ${SERVICES[*]}"
else
  warn "サービス一覧が空です（harness-config.yaml を確認してください）。"
fi

run_script_if_exists() {
  local label="$1"
  local script_path="$2"

  if [ -f "$script_path" ]; then
    log "実行: $label ($script_path)"
    bash "$script_path"
  else
    warn "スキップ: $label（$script_path が見つかりません）"
  fi
}

log "Step 1: フォーマット / Lint"
if [ "$SKIP_FORMAT_OR_LINT" = "1" ]; then
  log "スキップ: format_or_lint"
else
  run_script_if_exists "format_or_lint" "$ROOT_DIR/scripts/format_or_lint.sh"
fi

log "Step 2: Spec 品質ゲート"
if [ "$SKIP_VALIDATE_SPEC" = "1" ]; then
  log "スキップ: validate_spec"
else
  run_script_if_exists "validate_spec" "$ROOT_DIR/scripts/validate_spec.sh"
fi

log "Step 3: Plan 品質ゲート"
if [ "$SKIP_VALIDATE_PLAN" = "1" ]; then
  log "スキップ: validate_plan"
else
  run_script_if_exists "validate_plan" "$ROOT_DIR/scripts/validate_plan.sh"
fi

log "Step 4: Unit テスト"
if [ "$SKIP_UNIT_TESTS" = "1" ]; then
  log "スキップ: unit tests"
else
  if [ -f "$ROOT_DIR/scripts/run_all_unit_tests.sh" ]; then
    run_script_if_exists "run_all_unit_tests" "$ROOT_DIR/scripts/run_all_unit_tests.sh"
  else
    warn "run_all_unit_tests.sh が見つからないため、サービス単位で実行します。"
    for idx in "${!SERVICE_PATHS[@]}"; do
      service_path="$ROOT_DIR/${SERVICE_PATHS[$idx]}"
      run_script_if_exists "${SERVICES[$idx]} unit tests" "$service_path/scripts/run_unit_tests.sh"
    done
  fi
fi

if [ "$RUN_INTEGRATION_TESTS" = "1" ]; then
  log "Step 5: Integration テスト（サービス単位）"
  for idx in "${!SERVICE_PATHS[@]}"; do
    service_path="$ROOT_DIR/${SERVICE_PATHS[$idx]}"
    run_script_if_exists "${SERVICES[$idx]} integration tests" "$service_path/scripts/run_integration_tests.sh"
  done
else
  log "Step 5: Integration テストはスキップ（RUN_INTEGRATION_TESTS=1 で有効化）"
fi

log "Step 6: E2E テスト"
if [ "$SKIP_E2E_TESTS" = "1" ]; then
  log "スキップ: e2e tests"
else
  run_script_if_exists "run_all_e2e_tests" "$ROOT_DIR/scripts/run_all_e2e_tests.sh"
fi

record_progress "complete"
log "初期化スクリプト完了"
