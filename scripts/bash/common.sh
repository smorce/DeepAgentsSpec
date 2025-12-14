#!/usr/bin/env bash
# スクリプト間で共有する共通関数群（長期稼働リポジトリ用）

# Git リポジトリルートを特定する
get_repo_root() {
    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
    else
        local script_dir
        script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        (cd "$script_dir/../.." && pwd)
    fi
}

# 現在のブランチ名を取得する（Git が無い場合は仮値を返す）
get_current_branch() {
    if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
        git rev-parse --abbrev-ref HEAD
    elif [[ -n "${SPECIFY_FEATURE:-}" ]]; then
        echo "$SPECIFY_FEATURE"
    else
        echo "unknown"
    fi
}

# Git 利用可否
has_git() {
    git rev-parse --show-toplevel >/dev/null 2>&1
}

# Python コマンドを検出する
detect_python_cmd() {
    if command -v python3 >/dev/null 2>&1; then
        echo "python3"
    elif command -v python >/dev/null 2>&1; then
        echo "python"
    else
        echo ""
    fi
}

# ブランチ名からフィーチャーIDを推測する（F-USER-001 など）
extract_feature_hint_from_branch() {
    local branch="$1"
    if [[ "$branch" =~ (F-[A-Za-z0-9-]+) ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        echo ""
    fi
}

# FEATURE_* 環境変数やブランチからヒント文字列を集める
get_feature_hint() {
    local branch="$1"
    if [[ -n "${FEATURE_DIR:-}" ]]; then
        echo "$FEATURE_DIR"
        return
    fi
    if [[ -n "${FEATURE_SPEC:-}" ]]; then
        echo "$(dirname "$FEATURE_SPEC")"
        return
    fi
    if [[ -n "${FEATURE_ID:-}" ]]; then
        echo "$FEATURE_ID"
        return
    fi
    if [[ -n "${SPECIFY_FEATURE:-}" ]]; then
        echo "$SPECIFY_FEATURE"
        return
    fi
    extract_feature_hint_from_branch "$branch"
}

# フィーチャーディレクトリを JSON（harness/feature_list.json）やファイルパスから決定する
resolve_feature_dir() {
    local repo_root="$1"
    local hint="$2"

    if [[ -z "$hint" ]]; then
        echo ""
        return
    fi

    local python_cmd
    python_cmd="$(detect_python_cmd)"
    if [[ -z "$python_cmd" ]]; then
        echo ""
        return
    fi

    "$python_cmd" - "$repo_root" "$hint" <<'PY'
import json, os, re, sys

repo_root = os.path.abspath(sys.argv[1])
hint = sys.argv[2].strip()
feature_file = os.path.join(repo_root, "harness", "feature_list.json")

def normalize(path):
    if not path:
        return ""
    if os.path.isabs(path):
        return os.path.normpath(path)
    return os.path.normpath(os.path.join(repo_root, path))

def emit(path):
    if path:
        print(path)
        sys.exit(0)

if not hint:
    sys.exit(0)

candidate = normalize(hint)
if os.path.isdir(candidate):
    emit(candidate)
if os.path.isfile(candidate):
    emit(os.path.dirname(candidate))

explicit_path_prefixes = ("plans/", "./plans/", "../plans/", "services/", "./services/", "../services/")
if hint.startswith(explicit_path_prefixes):
    candidate = normalize(hint)
    if candidate.endswith(".md"):
        candidate = os.path.dirname(candidate)
    emit(candidate)

match = re.search(r'(F-[A-Za-z0-9-]+)', hint, re.IGNORECASE)
target_id = match.group(1).upper() if match else None

if target_id and os.path.exists(feature_file):
    try:
        data = json.load(open(feature_file, encoding="utf-8"))
    except Exception:
        data = {}
    for feat in data.get("features", []):
        if str(feat.get("id", "")).upper() == target_id:
            spec_path = feat.get("spec_path")
            if spec_path:
                emit(normalize(os.path.dirname(spec_path)))

plans_root = os.path.join(repo_root, "plans")
if os.path.isdir(plans_root):
    target_lower = hint.lower()
    for root, dirs, _ in os.walk(plans_root):
        for d in dirs:
            if d.lower() == target_lower:
                emit(os.path.join(root, d))

sys.exit(0)
PY
}

# 適切なブランチ名かどうか検証する
check_feature_branch() {
    local branch="$1"
    local has_git_repo="$2"

    if [[ "$has_git_repo" != "true" ]]; then
        echo "[specify] Git リポジトリが検出されなかったため、ブランチ検証をスキップします。" >&2
        return 0
    fi

    if [[ "$branch" == "main" || "$branch" == "master" ]]; then
        echo "ERROR: 作業は feature ブランチ上で行ってください。現在: $branch" >&2
        return 1
    fi

    if [[ "$branch" =~ ^[0-9]{3}- ]] || [[ "$branch" =~ F-[A-Za-z0-9-]+ ]]; then
        return 0
    fi

    echo "ERROR: フィーチャーブランチを判別できませんでした。例: 004-signup-flow や F-USER-001-onboarding" >&2
    return 1
}

# フィーチャーパス情報をエクスポートする
get_feature_paths() {
    local repo_root
    repo_root="$(get_repo_root)"
    local current_branch
    current_branch="$(get_current_branch)"

    local has_git_repo="false"
    if has_git; then
        has_git_repo="true"
    fi

    local feature_hint
    feature_hint="$(get_feature_hint "$current_branch")"
    local feature_dir
    feature_dir="$(resolve_feature_dir "$repo_root" "$feature_hint")"

    if [[ -z "$feature_dir" ]]; then
        echo "ERROR: フィーチャーディレクトリを特定できませんでした。SPECIFY_FEATURE か FEATURE_DIR/FEATURE_ID を設定してください。" >&2
        exit 1
    fi

    local feature_spec="$feature_dir/spec.md"
    local impl_plan="$feature_dir/impl-plan.md"
    local tasks_file="$feature_dir/tasks.md"
    local research_file="$feature_dir/research.md"
    local data_model_file="$feature_dir/data-model.md"
    local quickstart_file="$feature_dir/quickstart.md"
    local contracts_dir="$feature_dir/contracts"
    local feature_id
    feature_id="$(basename "$feature_dir")"

    printf "REPO_ROOT=%q\n" "$repo_root"
    printf "CURRENT_BRANCH=%q\n" "$current_branch"
    printf "HAS_GIT=%q\n" "$has_git_repo"
    printf "FEATURE_DIR=%q\n" "$feature_dir"
    printf "FEATURE_ID=%q\n" "$feature_id"
    printf "FEATURE_SPEC=%q\n" "$feature_spec"
    printf "IMPL_PLAN=%q\n" "$impl_plan"
    printf "TASKS=%q\n" "$tasks_file"
    printf "RESEARCH=%q\n" "$research_file"
    printf "DATA_MODEL=%q\n" "$data_model_file"
    printf "QUICKSTART=%q\n" "$quickstart_file"
    printf "CONTRACTS_DIR=%q\n" "$contracts_dir"
}

# ファイル存在状況を整形表示
check_file() {
    local path="$1"
    local label="$2"
    if [[ -f "$path" ]]; then
        echo "  ✓ $label"
    else
        echo "  ✗ $label"
    fi
}

# ディレクトリ内にファイルが存在するかを整形表示
check_dir() {
    local path="$1"
    local label="$2"
    if [[ -d "$path" ]] && find "$path" -mindepth 1 -print -quit >/dev/null 2>&1; then
        echo "  ✓ $label"
    else
        echo "  ✗ $label"
    fi
}
