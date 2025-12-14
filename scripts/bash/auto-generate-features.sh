#!/usr/bin/env bash
# 自然文からエピック/フィーチャを自動生成し、feature_list.json へ追記して
# create-new-feature.sh で枠を作るユーティリティ。仕様本文は後続の /speckit.specify に委ねる。

set -euo pipefail

# ===== 引数と環境 =========================================================
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MODEL="gpt-4o-mini"
DRY_RUN=false

usage() {
  cat <<'EOF'
Usage: auto-generate-features.sh [--model MODEL] [--dry-run] [--description "text"]

Reads natural-language description (from --description or stdin), calls an LLM to
propose epics/features, merges them into harness/feature_list.json, and scaffolds
spec.md + checklist via create-new-feature.sh. Spec content is filled later by /speckit.specify.

Options:
  --model MODEL       LLM model name (default: gpt-4o-mini)
  --dry-run           Do not write feature_list.json or create files
  --description TEXT  Description text; if omitted, read from stdin
  -h, --help          Show this help
EOF
}

DESCRIPTION=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      shift
      MODEL="${1:-}"
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --description)
      shift
      DESCRIPTION="${1:-}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: Unknown option $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$DESCRIPTION" ]]; then
  DESCRIPTION="$(cat - || true)"
fi

if [[ -z "$DESCRIPTION" ]]; then
  echo "ERROR: No description provided. Use --description or pipe text via stdin." >&2
  exit 1
fi

# ===== Pythonロジックに委譲 ===============================================
python3 - "$REPO_ROOT" "$MODEL" "$DRY_RUN" <<'PY'
import json, os, re, sys, subprocess, textwrap, datetime, urllib.request

repo_root = sys.argv[1]
model = sys.argv[2]
dry_run = sys.argv[3].lower() == "true"
description = sys.stdin.read().strip()

feature_file = os.path.join(repo_root, "harness", "feature_list.json")

# 日本語コメント: JSONCを読み込むヘルパー。// 行を除去してからパース。
def load_jsonc(path):
    lines = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.lstrip().startswith("//"):
                continue
            lines.append(line)
    return json.loads("".join(lines))

# 日本語コメント: pretty printで書き戻す（コメントは消える点に留意）。
def dump_json(path, obj):
    tmp = json.dumps(obj, ensure_ascii=False, indent=2)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(tmp + "\n")

data = load_jsonc(feature_file)
existing_epic_ids = {e["id"] for e in data.get("epics", [])}
existing_feature_ids = {f["id"] for f in data.get("features", [])}

def service_code(service: str) -> str:
    base = re.split(r"[-_]", service)[0].upper()
    if base == "BILLING":
        return "BILL"
    if base == "USER":
        return "USER"
    if base == "API":
        return "API"
    return base[:4] if base else "GEN"

def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "auto"

def next_feature_id(service: str) -> str:
    code = service_code(service)
    max_num = 0
    for fid in existing_feature_ids:
        m = re.match(rf"F-{code}-([0-9]+)", fid)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"F-{code}-{max_num+1:03d}"

def next_epic_id(service: str, title: str) -> str:
    code = service_code(service)
    max_num = 0
    for eid in existing_epic_ids:
        m = re.match(rf"EPIC-{code}-([0-9]+)", eid)
        if m:
            max_num = max(max_num, int(m.group(1)))
    slug = slugify(title)
    return f"EPIC-{code}-{max_num+1:03d}-{slug.upper()}"

# 日本語コメント: LLMへリクエスト（失敗時はヒューリスティクスフォールバック）。
def call_llm(desc: str):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, "No OPENAI_API_KEY; using heuristic fallback."
    prompt = textwrap.dedent(f"""
    You are a product planner. Given a product description, split it into epics and features.
    Return ONLY JSON with keys: epics, features.
    Each epic: title, services (array), optional description.
    Each feature: epic_title (or epic_ref), title, description, services (array).
    Do not include IDs; the caller will assign them.
    Available services: api-gateway, user-service, billing-service.
    Description:
    {desc}
    """).strip()
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return JSON only, no markdown."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
        payload = json.loads(content)
        return payload, None
    except Exception as e:
        return None, f"LLM call failed: {e}"

llm_payload, llm_error = call_llm(description)

if llm_payload is None:
    # 日本語コメント: 最小限のフォールバック（1エピック1フィーチャ）
    primary_service = "api-gateway"
    text_lower = description.lower()
    if any(k in text_lower for k in ["user", "signup", "login", "auth"]):
        primary_service = "user-service"
    if any(k in text_lower for k in ["billing", "payment", "invoice"]):
        primary_service = "billing-service"
    llm_payload = {
        "epics": [
            {"title": "Generated epic", "description": description[:160], "services": [primary_service]}
        ],
        "features": [
            {"epic_title": "Generated epic", "title": "Generated feature", "description": description[:160], "services": [primary_service]}
        ]
    }

# 日本語コメント: エピックタイトル→ID対応を構築
epic_title_to_id = {}
new_epics = []
for epic in llm_payload.get("epics", []):
    title = epic.get("title") or "Untitled Epic"
    services = epic.get("services") or ["api-gateway"]
    primary_service = services[0]
    eid = next_epic_id(primary_service, title)
    epic_id = eid
    # 日本語コメント: 既存と被る場合はスキップ
    if epic_id in existing_epic_ids:
        epic_title_to_id[title.lower()] = epic_id
        continue
    epic_obj = {
        "id": epic_id,
        "title": title,
        "category": f"service:{primary_service}",
        "services": services,
        "exec_plan_path": f"plans/services/{primary_service}/{epic_id.lower()}/exec-plan.md",
    }
    new_epics.append(epic_obj)
    epic_title_to_id[title.lower()] = epic_id
    existing_epic_ids.add(epic_id)

# 日本語コメント: フィーチャ生成
new_features = []
skipped = []
for feat in llm_payload.get("features", []):
    title = feat.get("title") or "Untitled Feature"
    desc = feat.get("description") or ""
    services = feat.get("services") or ["api-gateway"]
    primary_service = services[0]
    # 日本語コメント: epic紐付け
    epic_title = (feat.get("epic_title") or feat.get("epic_ref") or "").lower()
    epic_id = epic_title_to_id.get(epic_title)
    if not epic_id:
        # 日本語コメント: サービスごとにデフォルトエピックを作成
        fallback_title = f"Autogen {primary_service}"
        if fallback_title.lower() not in epic_title_to_id:
            eid = next_epic_id(primary_service, fallback_title)
            epic_obj = {
                "id": eid,
                "title": fallback_title,
                "category": f"service:{primary_service}",
                "services": [primary_service],
                "exec_plan_path": f"plans/services/{primary_service}/{eid.lower()}/exec-plan.md",
            }
            new_epics.append(epic_obj)
            epic_title_to_id[fallback_title.lower()] = eid
            existing_epic_ids.add(eid)
        epic_id = epic_title_to_id[fallback_title.lower()]

    fid = next_feature_id(primary_service)
    if fid in existing_feature_ids:
        skipped.append({"title": title, "reason": "ID collision"})
        continue
    feature_obj = {
        "id": fid,
        "epic_id": epic_id,
        "title": title,
        "description": desc,
        "services": services,
        "status": "failing",
        "tags": feat.get("tags") or [],
        "spec_path": f"plans/services/{primary_service}/{epic_id.lower()}/features/{fid}/spec.md",
        "checklist_path": f"plans/services/{primary_service}/{epic_id.lower()}/features/{fid}/checklists/requirements.md",
    }
    new_features.append(feature_obj)
    existing_feature_ids.add(fid)

# 日本語コメント: 追記
if new_epics:
    data.setdefault("epics", []).extend(new_epics)
if new_features:
    data.setdefault("features", []).extend(new_features)

if dry_run:
    result = {
        "dry_run": True,
        "new_epics": new_epics,
        "new_features": new_features,
        "skipped": skipped,
        "llm_error": llm_error,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)

dump_json(feature_file, data)

# 日本語コメント: create-new-feature.sh を呼び出して枠生成
created = []
failed = []
for feat in new_features:
    fid = feat["id"]
    title = feat["title"]
    try:
        subprocess.run(
            ["bash", os.path.join(repo_root, "scripts/bash/create-new-feature.sh"), "--feature-id", fid, title],
            cwd=repo_root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        created.append(fid)
    except subprocess.CalledProcessError as e:
        failed.append({"id": fid, "error": e.stderr.decode("utf-8", errors="ignore")})

result = {
    "dry_run": False,
    "new_epics": new_epics,
    "new_features": new_features,
    "created_feature_scaffolds": created,
    "failed_feature_scaffolds": failed,
    "skipped": skipped,
    "llm_error": llm_error,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
PY
