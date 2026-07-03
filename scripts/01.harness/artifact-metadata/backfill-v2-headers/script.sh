#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.script.artifact-metadata.backfill-v2-headers
#   version: 1
#   status: active
#   layer: 01.harness
#   domain: metadata
#   disciplines:
#     - agentic
#   kind: script
#   purpose: Apply one governed artifact metadata v2 backfill batch, validate it, commit it, and checkpoint the chat session log.
#   portability:
#     class: required
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#     - stages-files
#     - commits
#   used_by:
#     - id: harness.capability.artifact-metadata
#       path: .agentic/01.harness/artifact-metadata/README.md
#     - id: harness.standard.artifact-metadata
#       path: .agentic/01.harness/artifact-metadata/standard.md
#     - id: harness.script.run-governed-script
#       path: scripts/01.harness/run-governed-script.sh

usage() {
  cat <<'EOF'
Usage:
  scripts/01.harness/artifact-metadata/backfill-v2-headers/script.sh --batch <1-15>
  scripts/01.harness/artifact-metadata/backfill-v2-headers/script.sh --record-only <sha> <message> <summary> [adr-impact]
  scripts/01.harness/artifact-metadata/backfill-v2-headers/script.sh --status
EOF
}

record_and_checkpoint() {
  local sha="$1"
  local message="$2"
  local summary="$3"
  local adr_impact="${4:-No ADR impact.}"

  bash scripts/00.chat/session-log/record-chat-commit/script.sh "$sha" "$message" "$summary" "$adr_impact"

  local dirty
  dirty="$(git status --short --untracked-files=no)"
  if [[ -n "$dirty" ]]; then
    bash scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh
  fi
}

validate_index_json() {
  local index_json="$1"
  python3 - "$index_json" <<'PY'
import json
import sys
from pathlib import Path

summary = json.loads(Path(sys.argv[1]).read_text()).get("summary", {})
checks = {
    "legacy_artifacts": summary.get("legacy_artifacts"),
    "skipped": summary.get("skipped"),
    "duplicate_ids": summary.get("duplicate_ids"),
}
errors = [f"{key}={value}" for key, value in checks.items() if value != 0]
if errors:
    raise SystemExit("artifact metadata index validation failed: " + ", ".join(errors))
print(
    "artifact metadata index ok: "
    f"artifacts={summary.get('artifacts')} "
    f"legacy={summary.get('legacy_artifacts')} "
    f"skipped={summary.get('skipped')} "
    f"duplicates={summary.get('duplicate_ids')}"
)
PY
}

validate_yaml_paths() {
  local paths_file="$1"
  python3 - "$paths_file" <<'PY'
import sys
from pathlib import Path

try:
    import yaml
except Exception as exc:
    raise SystemExit(f"PyYAML is required for YAML validation: {exc}")

paths = [Path(line.strip()) for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
yaml_paths = [path for path in paths if path.suffix.lower() in {".yml", ".yaml"}]
for path in yaml_paths:
    with path.open("r", encoding="utf-8") as handle:
        yaml.safe_load(handle)
if yaml_paths:
    print(f"yaml parse ok: {len(yaml_paths)} files")
else:
    print("yaml parse skipped: no YAML files in batch")
PY
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

case "$1" in
  --record-only)
    if [[ $# -lt 4 ]]; then
      usage
      exit 2
    fi
    record_and_checkpoint "$2" "$3" "$4" "${5:-No ADR impact.}"
    exit 0
    ;;
  --status)
    python3 - <<'PY'
from pathlib import Path

ROOTS = [Path(".agentic"), Path("docs"), Path("scripts")]
EXTENSIONS = {".md", ".yml", ".yaml", ".sh"}
counts = {"v2": 0, "legacy": 0, "missing": 0}
for root in ROOTS:
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
            continue
        text = path.read_text(encoding="utf-8")
        if "schema: agentic-artifact/v2" in text and "agentic-artifact:" in text:
            counts["v2"] += 1
        elif "agentic-artifact:" in text or "agentic-script:" in text:
            counts["legacy"] += 1
        else:
            counts["missing"] += 1
print(f"v2={counts['v2']} legacy={counts['legacy']} missing={counts['missing']}")
PY
    exit 0
    ;;
  --batch)
    if [[ $# -ne 2 ]]; then
      usage
      exit 2
    fi
    batch="$2"
    ;;
  *)
    usage
    exit 2
    ;;
esac

paths_file="$(mktemp)"
index_json="$(mktemp)"
trap 'rm -f "$paths_file" "$index_json"' EXIT

python3 - "$batch" > "$paths_file" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

batch = int(sys.argv[1])
EXTENSIONS = {".md", ".yml", ".yaml", ".sh"}
ALLOWED_REF_PREFIXES = (".agentic/", "docs/00.chat/", "docs/harness/", "scripts/")
ALL_TARGETS = ["llm-workbench", "entity-builder", "design-system-builder"]

SPECIAL_IDS = {
    "AGENTS.md": "repo.agents",
    ".agentic/00.chat/README.md": "chat.readme",
    "docs/00.chat/README.md": "chat.docs.readme",
    ".agentic/01.harness/README.md": "harness.readme",
    ".agentic/01.harness/artifact-metadata/README.md": "harness.capability.artifact-metadata",
    ".agentic/01.harness/artifact-metadata/index-schema.md": "harness.artifact-metadata.index-schema",
    ".agentic/01.harness/artifact-metadata/migration-plan.md": "harness.artifact-metadata.migration-plan",
    ".agentic/01.harness/artifact-metadata/standard.md": "harness.standard.artifact-metadata",
    ".agentic/routing-policy.yaml": "shared.routing-policy",
    ".agentic/shared/standards/upstream-repo-bootstrap.md": "shared.standard.upstream-repo-bootstrap",
    "scripts/01.harness/run-governed-script.sh": "harness.script.run-governed-script",
}

DISCIPLINE_BY_DOMAIN = {
    "architecture": "architecture",
    "backend": "backend",
    "frontend": "frontend",
    "requirements": "requirements",
}


def all_artifacts() -> list[Path]:
    paths: list[Path] = []
    for root in (Path(".agentic"), Path("docs"), Path("scripts")):
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in EXTENSIONS:
                paths.append(path)
    return sorted(paths, key=lambda item: item.as_posix())


def strip_comment(line: str) -> str:
    stripped = line.lstrip()
    if stripped.startswith("# "):
        return stripped[2:]
    if stripped.startswith("#"):
        return stripped[1:]
    if stripped.startswith("// "):
        return stripped[3:]
    if stripped.startswith("//"):
        return stripped[2:]
    return line


def parse_header(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()[:120]
    for index, line in enumerate(lines):
        if "agentic-artifact:" not in line and "agentic-script:" not in line:
            continue
        if line.lstrip().startswith("<!--"):
            marker = line.replace("<!--", "", 1).strip()
            body_lines = []
            for following in lines[index + 1:]:
                if "-->" in following:
                    before_end = following.split("-->", 1)[0]
                    if before_end.strip():
                        body_lines.append(before_end)
                    break
                body_lines.append(following)
            header_lines = [marker]
            header_lines.extend(f"  {body_line}" if body_line.strip() else body_line for body_line in body_lines)
        else:
            header_lines = [strip_comment(line)]
            for following in lines[index + 1:]:
                stripped = following.lstrip()
                if stripped.startswith("#") or stripped.startswith("//"):
                    header_lines.append(strip_comment(following))
                    continue
                if not following.strip():
                    break
                break
        parsed = yaml.safe_load("\n".join(header_lines)) or {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def existing_metadata(path: Path) -> dict[str, Any]:
    parsed = parse_header(path)
    artifact = parsed.get("agentic-artifact")
    script = parsed.get("agentic-script")
    if isinstance(artifact, dict):
        return artifact
    if isinstance(script, dict):
        return script
    return {}


def has_v2(path: Path) -> bool:
    return existing_metadata(path).get("schema") == "agentic-artifact/v2"


def selected_for_batch(path: Path) -> bool:
    s = path.as_posix()
    if has_v2(path):
        return False
    if batch == 1:
        return s in {
            ".agentic/01.harness/README.md",
            ".agentic/01.harness/manifest.yml",
            ".agentic/01.harness/standards/agentic-artifact-standards.md",
            ".agentic/01.harness/standards/artifact-metadata-headers.md",
            ".agentic/01.harness/standards/artifact-path-migrations.md",
            ".agentic/01.harness/standards/governed-script-permissions.md",
            ".agentic/01.harness/standards/missing-governance-stop-condition.md",
            ".agentic/routing-policy.yaml",
            ".agentic/shared/standards/README.md",
            ".agentic/shared/standards/upstream-repo-bootstrap.md",
            ".agentic/shared/workflows/README.md",
            ".agentic/shared/workflows/capability-resolution-workflow.md",
            ".agentic/shared/workflows/change-shared-process.md",
        }
    if batch == 2:
        return s.startswith((
            ".agentic/01.harness/checklists/",
            ".agentic/01.harness/prompts/",
            ".agentic/01.harness/state/",
            ".agentic/01.harness/templates/",
            ".agentic/01.harness/workflows/",
        )) or s == ".agentic/01.harness/operator-guide.md"
    if batch == 3:
        return s.startswith("docs/harness/architecture/adrs/")
    if batch == 4:
        return s.startswith("docs/harness/architecture/rules/")
    if batch == 5:
        return s.startswith("docs/harness/architecture/") and not s.startswith("docs/harness/architecture/adrs/") and not s.startswith("docs/harness/architecture/rules/")
    if batch == 6:
        return s.startswith(".agentic/00.chat/") or s.startswith("docs/00.chat/")
    if batch == 7:
        return s.startswith(("scripts/00.chat/session-log/", "scripts/00.chat/startup/", "scripts/00.chat/worktree/"))
    if batch == 8:
        return s.startswith(("scripts/00.chat/git/", "scripts/00.chat/local-merge/", "scripts/00.chat/main-refresh/", "scripts/00.chat/recovery/"))
    if batch == 9:
        return s.startswith((
            "scripts/00.chat/bootstrap/",
            "scripts/00.chat/closeout/",
            "scripts/00.chat/command/",
            "scripts/00.chat/metrics/",
            "scripts/00.chat/migration/",
            "scripts/00.chat/reporting/",
            "scripts/00.chat/support/",
            "scripts/00.chat/transcript/",
            "scripts/00.chat/upstream/",
        ))
    if batch == 10:
        return s.startswith((".agentic/aws/", ".agentic/product/"))
    if batch == 11:
        return s == ".agentic/education/README.md" or s.startswith((".agentic/education/agents/", ".agentic/education/workflows/"))
    if batch == 12:
        return s.startswith((".agentic/education/profiles/", ".agentic/education/prompts/", ".agentic/education/references/"))
    if batch == 13:
        return s.startswith((".agentic/education/feedback/", ".agentic/education/templates/"))
    if batch == 14:
        return s.startswith("scripts/01.harness/") and "/artifact-metadata/" not in s
    if batch == 15:
        return s == "scripts/00.chat/README.md" or s.startswith(("docs/aws/", "docs/education/"))
    raise SystemExit(f"Unknown batch: {batch}")


def title_from_markdown(path: Path) -> str | None:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip().rstrip(".")
    return None


def humanize(name: str) -> str:
    return " ".join(part for part in re.split(r"[-_]+", name) if part).title()


def purpose_for(path: Path, metadata: dict[str, Any]) -> str:
    purpose = metadata.get("purpose")
    if isinstance(purpose, str) and purpose.strip():
        return purpose.strip().rstrip(".") + "."
    s = path.as_posix()
    if path.suffix == ".sh":
        leaf = humanize(path.parent.name if path.name == "script.sh" else path.stem)
        return f"Run the {leaf} governed helper."
    if path.suffix in {".yml", ".yaml"}:
        leaf = humanize(path.stem)
        if s.startswith("docs/harness/architecture/rules/"):
            return f"Define the {leaf} architecture rule artifact."
        return f"Define the {leaf} configuration artifact."
    title = title_from_markdown(path) or humanize(path.stem)
    if s.startswith("docs/harness/architecture/adrs/"):
        return f"Record the {title} architecture decision."
    return f"Document {title}."


def layer_for(path: Path, metadata: dict[str, Any]) -> str:
    existing = metadata.get("layer")
    if isinstance(existing, str) and re.match(r"^\d{2}\.[a-z0-9-]+$", existing):
        return existing
    s = path.as_posix()
    if s.startswith((".agentic/00.chat/", "docs/00.chat/", "scripts/00.chat/")):
        return "00.chat"
    if s.startswith((".agentic/01.harness/", "docs/harness/", "scripts/01.harness/")):
        return "01.harness"
    if s.startswith((".agentic/02.rag-rulebook/", "scripts/02.rag-rulebook/")):
        return "02.rag-rulebook"
    if s.startswith(".agentic/product/"):
        return "03.product"
    if s.startswith((".agentic/aws/", "docs/aws/")):
        return "04.deploy"
    if s.startswith((".agentic/education/", "docs/education/")):
        return "05.education"
    return "06.shared"


def domain_for(path: Path, metadata: dict[str, Any]) -> str:
    existing = metadata.get("domain")
    if isinstance(existing, str) and existing:
        return existing.replace("-", ".") if existing in {"ci-cd"} else existing
    s = path.as_posix()
    if "artifact-metadata" in s:
        return "metadata"
    if s.startswith("docs/harness/architecture/"):
        return "architecture"
    if s.startswith(".agentic/product/"):
        return "requirements"
    if s.startswith((".agentic/aws/", "docs/aws/")):
        return "infra.ci-cd"
    if s.startswith((".agentic/education/", "docs/education/")):
        return "education"
    if s.startswith((".agentic/00.chat/", "docs/00.chat/", "scripts/00.chat/")):
        return "chat"
    return "platform"


def disciplines_for(domain: str, metadata: dict[str, Any]) -> list[str]:
    existing = metadata.get("disciplines")
    if isinstance(existing, list) and existing:
        return [str(item) for item in existing if item]
    return [DISCIPLINE_BY_DOMAIN.get(domain, "agentic")]


def kind_for(path: Path, metadata: dict[str, Any]) -> str:
    existing = metadata.get("kind")
    if isinstance(existing, str) and existing:
        return existing
    s = path.as_posix()
    if path.suffix == ".sh":
        return "script"
    if path.suffix in {".yml", ".yaml"}:
        return "rule" if s.startswith("docs/harness/architecture/rules/") else "config"
    if "template" in s:
        return "template"
    if "workflow" in s:
        return "workflow"
    if "checklist" in s:
        return "checklist"
    if "/adrs/" in s:
        return "adr"
    if "standard" in s:
        return "standard"
    return "guide"


def status_for(metadata: dict[str, Any]) -> str:
    existing = metadata.get("status")
    if isinstance(existing, str) and existing:
        return existing
    return "active"


def version_for(metadata: dict[str, Any]) -> int:
    existing = metadata.get("version")
    if isinstance(existing, int) and existing > 0:
        return existing
    if isinstance(existing, str) and existing.isdigit() and int(existing) > 0:
        return int(existing)
    return 1


def portability_for(path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    existing = metadata.get("portability")
    if isinstance(existing, dict):
        klass = existing.get("class") or "required"
        targets = existing.get("targets") if isinstance(existing.get("targets"), list) else []
        return {"class": klass, "targets": [str(target) for target in targets]}
    if isinstance(existing, str):
        if existing == "source-only":
            return {"class": "source-only", "targets": []}
        if existing == "internal":
            return {"class": "internal", "targets": []}
        if existing == "llm-workbench-compatibility":
            return {"class": "compatible", "targets": ["llm-workbench"]}
        if existing == "llm-workbench-validation":
            return {"class": "reusable", "targets": ["llm-workbench"]}
        if existing == "llm-workbench-required":
            return {"class": "required", "targets": ["llm-workbench"]}
    s = path.as_posix()
    if s.startswith(".agentic/aws/"):
        return {"class": "source-only", "targets": []}
    if s.startswith((".agentic/aws/", "docs/aws/")):
        return {"class": "source-only", "targets": []}
    if s.startswith(".agentic/product/"):
        return {"class": "required", "targets": ["entity-builder"]}
    if s.startswith((".agentic/education/", "docs/education/")):
        return {"class": "required", "targets": ["llm-workbench"]}
    return {"class": "required", "targets": ALL_TARGETS}


def allowed_ref(ref: str) -> bool:
    if ref == "AGENTS.md":
        return Path(ref).exists()
    if not ref.startswith(ALLOWED_REF_PREFIXES):
        return False
    return Path(ref).exists()


def slug(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def artifact_id(path: Path | str) -> str:
    s = path if isinstance(path, str) else path.as_posix()
    if s in SPECIAL_IDS:
        return SPECIAL_IDS[s]
    no_ext = s
    for ext in (".md", ".yml", ".yaml", ".sh"):
        if no_ext.endswith(ext):
            no_ext = no_ext[: -len(ext)]
            break
    if no_ext.endswith("/script"):
        no_ext = no_ext[: -len("/script")]
    parts = []
    for part in no_ext.split("/"):
        if part in {".agentic", "docs", "scripts"}:
            continue
        if part in {"00.chat", "01.harness", "education", "shared", "aws", "product"}:
            parts.append(part.replace("00.", "").replace("01.", ""))
        elif part == "adrs":
            parts.append("adr")
        else:
            parts.append(slug(part))
    result = ".".join(part for part in parts if part).replace("..", ".").strip(".")
    if s.startswith("scripts/") and ".script." not in result:
        pieces = result.split(".")
        result = ".".join([pieces[0], "script", *pieces[1:]]) if len(pieces) >= 2 else f"script.{result}"
    return result


def used_by_for(path: Path, metadata: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    raw = metadata.get("used_by")
    if isinstance(raw, list):
        for entry in raw:
            if isinstance(entry, dict):
                ref_path = entry.get("path")
                ref_id = entry.get("id")
                if isinstance(ref_path, str) and allowed_ref(ref_path):
                    refs.append({"id": str(ref_id) if ref_id else artifact_id(ref_path), "path": ref_path})
            elif isinstance(entry, str) and allowed_ref(entry):
                refs.append({"id": artifact_id(entry), "path": entry})
    if refs:
        unique: dict[str, dict[str, str]] = {}
        for ref in refs:
            unique[ref["path"]] = ref
        return list(unique.values())
    s = path.as_posix()
    if s.startswith("docs/harness/architecture/rules/"):
        ref = ".agentic/01.harness/workflows/change-harness.md"
    elif s.startswith("docs/harness/architecture/adrs/"):
        ref = "docs/harness/architecture/adrs/README.md"
    elif s.startswith("docs/harness/architecture/"):
        ref = ".agentic/01.harness/workflows/change-harness.md"
    elif s.startswith((".agentic/00.chat/", "docs/00.chat/")):
        ref = "AGENTS.md"
    elif s.startswith("docs/aws/"):
        ref = ".agentic/aws/README.md"
    elif s.startswith("docs/education/"):
        ref = ".agentic/education/README.md"
    elif s.startswith("scripts/00.chat/"):
        ref = ".agentic/00.chat/README.md"
    elif s.startswith("scripts/01.harness/"):
        ref = ".agentic/01.harness/README.md"
    elif s.startswith(".agentic/education/") and s != ".agentic/education/README.md":
        ref = ".agentic/education/README.md"
    else:
        ref = "AGENTS.md"
    return [{"id": artifact_id(ref), "path": ref}]


def effects_for(path: Path, metadata: dict[str, Any]) -> list[str]:
    raw = metadata.get("effects") or metadata.get("effect")
    values: list[str] = []
    if isinstance(raw, list):
        values = [str(item) for item in raw if item]
    elif isinstance(raw, str) and raw:
        values = [raw]
    aliases = {"opens-gui": "read-only", "temporary-files": "writes-files", "write-files": "writes-files"}
    normalized: list[str] = []
    for value in values:
        for token in value.split(","):
            token = token.strip()
            if token:
                normalized.append(aliases.get(token, token))
    if normalized:
        return sorted(dict.fromkeys(normalized))
    if path.suffix == ".sh":
        return ["read-only"]
    return []


def v2_payload(path: Path) -> dict[str, Any]:
    metadata = existing_metadata(path)
    domain = domain_for(path, metadata)
    payload: dict[str, Any] = {
        "schema": "agentic-artifact/v2",
        "id": artifact_id(path),
        "version": version_for(metadata),
        "status": status_for(metadata),
        "layer": layer_for(path, metadata),
        "domain": domain,
        "disciplines": disciplines_for(domain, metadata),
        "kind": kind_for(path, metadata),
        "purpose": purpose_for(path, metadata),
        "portability": portability_for(path, metadata),
        "used_by": used_by_for(path, metadata),
    }
    effects = effects_for(path, metadata)
    if effects:
        payload["effects"] = effects
    return payload


def render_comment_header(payload: dict[str, Any]) -> str:
    yaml_text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=False).rstrip()
    lines = ["# agentic-artifact:"]
    lines.extend(f"#   {line}" if line else "#" for line in yaml_text.splitlines())
    return "\n".join(lines) + "\n\n"


def render_html_header(payload: dict[str, Any]) -> str:
    yaml_text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=False).rstrip()
    body = "\n".join(f"  {line}" if line else line for line in yaml_text.splitlines())
    return f"<!-- agentic-artifact:\n{body}\n-->\n"


def header_span(text: str) -> tuple[int, int] | None:
    lines = text.splitlines(keepends=True)
    offset = 0
    for index, line in enumerate(lines[:120]):
        if "agentic-artifact:" not in line and "agentic-script:" not in line:
            offset += len(line)
            continue
        start = offset
        end = offset + len(line)
        if line.lstrip().startswith("<!--"):
            for following in lines[index + 1:]:
                end += len(following)
                if "-->" in following:
                    break
        else:
            for following in lines[index + 1:]:
                stripped = following.lstrip()
                if stripped.startswith("#") or stripped.startswith("//"):
                    end += len(following)
                    continue
                break
        if end < len(text):
            next_newline = text.find("\n", end)
            # Drop one blank separator line after the old header when present.
            if text[end:next_newline + 1].strip() == "" and next_newline != -1:
                end = next_newline + 1
        return start, end
    return None


def insert_position_for_script(text: str) -> int:
    lines = text.splitlines(keepends=True)
    offset = 0
    index = 0
    if lines and lines[0].startswith("#!"):
        offset += len(lines[0])
        index = 1
    while index < len(lines) and (lines[index].strip() == "" or lines[index].startswith("set ")):
        offset += len(lines[index])
        index += 1
    return offset


def replace_header(path: Path, payload: dict[str, Any]) -> None:
    text = path.read_text(encoding="utf-8")
    header = render_comment_header(payload) if path.suffix in {".sh", ".yml", ".yaml"} else render_html_header(payload)
    span = header_span(text)
    if span:
        start, end = span
        path.write_text(text[:start] + header + text[end:].lstrip("\n"), encoding="utf-8")
        return
    if path.suffix == ".sh":
        position = insert_position_for_script(text)
        path.write_text(text[:position] + "\n" + header + text[position:].lstrip("\n"), encoding="utf-8")
        return
    path.write_text(header + text.lstrip("\n"), encoding="utf-8")

selected = [path for path in all_artifacts() if selected_for_batch(path)]
if not selected:
    raise SystemExit(f"Batch {batch} has no remaining non-v2 artifacts.")
for path in selected:
    replace_header(path, v2_payload(path))
for path in selected:
    print(path.as_posix())
PY

mapfile -t changed_paths < "$paths_file"
if [[ "${#changed_paths[@]}" -eq 0 ]]; then
  echo "No paths changed for batch $batch."
  exit 0
fi

echo "Backfilled batch $batch (${#changed_paths[@]} files)."

bash scripts/01.harness/artifact-metadata/check-headers/script.sh --paths "${changed_paths[@]}"
bash scripts/01.harness/artifact-metadata/generate-index/script.sh --paths "${changed_paths[@]}" --strict > "$index_json"
validate_index_json "$index_json"
validate_yaml_paths "$paths_file"

git add -- "${changed_paths[@]}"
bash scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh

commit_message="$(python3 - "$batch" <<'PY'
import sys
messages = {
    1: "Backfill governance root metadata headers",
    2: "Backfill harness operator metadata headers",
    3: "Backfill harness ADR metadata headers",
    4: "Backfill harness rulebook metadata headers",
    5: "Backfill harness guide metadata headers",
    6: "Backfill chat documentation metadata headers",
    7: "Backfill chat startup metadata headers",
    8: "Backfill chat merge metadata headers",
    9: "Backfill chat support metadata headers",
    10: "Backfill deploy product metadata headers",
    11: "Backfill education core metadata headers",
    12: "Backfill education profile metadata headers",
    13: "Backfill education template metadata headers",
    14: "Backfill harness script metadata headers",
    15: "Backfill docs spillover metadata headers",
}
print(messages[int(sys.argv[1])])
PY
)"

commit_summary="$(python3 - "$batch" <<'PY'
import sys
summaries = {
    1: "Backfilled artifact metadata v2 headers for harness/shared governance root artifacts.",
    2: "Backfilled artifact metadata v2 headers for harness operator, state, prompt, workflow, and template artifacts.",
    3: "Backfilled artifact metadata v2 headers for harness architecture ADR artifacts.",
    4: "Backfilled artifact metadata v2 headers for harness architecture YAML rulebook artifacts.",
    5: "Backfilled artifact metadata v2 headers for harness architecture guide artifacts.",
    6: "Backfilled artifact metadata v2 headers for chat documentation and agentic chat prose artifacts.",
    7: "Backfilled artifact metadata v2 headers for chat session, startup, and worktree scripts.",
    8: "Backfilled artifact metadata v2 headers for chat merge, refresh, git, and recovery scripts.",
    9: "Backfilled artifact metadata v2 headers for chat command, reporting, bootstrap, transcript, and support scripts.",
    10: "Backfilled artifact metadata v2 headers for deploy and product layer artifacts.",
    11: "Backfilled artifact metadata v2 headers for education core, agent, and workflow artifacts.",
    12: "Backfilled artifact metadata v2 headers for education profile, prompt, and reference artifacts.",
    13: "Backfilled artifact metadata v2 headers for education template and feedback artifacts.",
    14: "Backfilled artifact metadata v2 headers for remaining harness scripts.",
    15: "Backfilled artifact metadata v2 headers for remaining AWS, education, and chat script README artifacts.",
}
print(summaries[int(sys.argv[1])])
PY
)"

git commit -m "$commit_message"
commit_sha="$(git rev-parse --short HEAD)"
record_and_checkpoint "$commit_sha" "$commit_message" "$commit_summary" "No ADR impact."

echo "Completed batch $batch at $commit_sha."
