#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: rag-rulebook.script.validate-context-packet.smoke-test
#   version: 1
#   status: active
#   layer: 02.rag-rulebook
#   domain: context-packets
#   disciplines:
#     - agentic
#     - architecture
#   kind: script
#   purpose: Smoke test the read-only context-packet validator.
#   portability:
#     class: reusable
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#   used_by:
#     - id: rag-rulebook.script.validate-context-packet
#       path: scripts/02.rag-rulebook/validate-context-packet/script.sh

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

CHUNKS_FILE="$TMP_DIR/rulebook-chunks.json"
PACKET_FILE="$TMP_DIR/context-packet.json"
REPORT_FILE="$TMP_DIR/context-packet-report.json"
BROKEN_PACKET_FILE="$TMP_DIR/broken-context-packet.json"

bash scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh --generate-current --pretty > "$CHUNKS_FILE"

python3 - "$CHUNKS_FILE" "$PACKET_FILE" <<'PY'
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

chunk_set = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
chunks = chunk_set["chunks"]

rule_chunks = [chunk for chunk in chunks if chunk["content_kind"] == "rule"]
check_chunks = [chunk for chunk in chunks if chunk["content_kind"] == "required-check"]
summary_chunks = [chunk for chunk in chunks if chunk["content_kind"] == "artifact-summary"]
selected = [rule_chunks[0], check_chunks[0], summary_chunks[0]]
for rank, chunk in enumerate(selected, start=1):
    chunk["rank"] = rank
    chunk["retrieval_score"] = round(1 - ((rank - 1) * 0.1), 2)
    chunk["selection_reason"] = "Smoke packet selects deterministic chunks from the generated chunk set."

selected_corpus_ids = sorted({chunk["corpus_id"] for chunk in selected})
selected_artifact_ids = sorted({chunk["artifact_id"] for chunk in selected})
selected_pack_refs = sorted({pack_ref for chunk in selected for pack_ref in chunk.get("pack_refs", [])})
selected_rule_ids = sorted({rule_id for chunk in selected for rule_id in chunk.get("rule_ids", [])})
selected_citation_ids = sorted({citation_id for chunk in selected for citation_id in chunk["citation_ids"]})
chunk_citations = {citation["id"]: citation for citation in chunk_set["citations"]}

def context_source_type(source_type: str | None) -> str:
    if source_type in {"rule", "rule-pack", "workflow", "standard", "schema", "plan"}:
        return source_type
    return "source"

citations = []
for citation_id in selected_citation_ids:
    source = chunk_citations[citation_id]
    citations.append(
        {
            "id": citation_id,
            "corpus_id": source.get("corpus_id"),
            "artifact_id": source.get("artifact_id"),
            "source_path": source.get("source_path"),
            "source_type": context_source_type(source.get("source_type")),
            "source_ref": citation_id,
        }
    )

selected_context_tokens = sum(chunk["token_estimate"] for chunk in selected)
packet = {
    "schema": "rag-rulebook/context-packet/v1",
    "packet_id": "packet.smoke.context-packet",
    "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "request": {
        "raw_text": "Smoke validate a context packet.",
        "normalized_summary": "Validate a small cited packet from generated chunks.",
        "focused_paths": ["scripts/02.rag-rulebook/**"],
        "open_artifact_ids": selected_artifact_ids,
    },
    "intent": {
        "id": "intent.rag-rulebook.validate-context-packet",
        "label": "Validate context packet",
        "mode": "implementation",
        "layer": "02.rag-rulebook",
        "workflow": ".agentic/02.rag-rulebook/workflows/default.md",
        "confidence": 1,
        "source": "deterministic",
        "evidence_ref_ids": selected_citation_ids,
    },
    "routing": {
        "layer": "02.rag-rulebook",
        "mode": "implementation",
        "workflow": ".agentic/02.rag-rulebook/workflows/default.md",
        "status": "ready",
        "task_type": "validate_context_packet",
        "target_paths": ["scripts/02.rag-rulebook/validate-context-packet/**"],
        "classification_source": "smoke-test",
    },
    "matched_corpora": [
        {
            "corpus_id": corpus_id,
            "owner_layer": ".".join(corpus_id.split(".")[1:3]),
            "match_reason": "Selected smoke chunk belongs to this corpus.",
            "confidence": 1,
        }
        for corpus_id in selected_corpus_ids
    ],
    "matched_rule_packs": [
        {
            "id": pack_ref,
            "corpus_id": selected[0]["corpus_id"],
            "selection_reason": "Selected smoke chunk comes from this rule pack.",
            "citation_ids": selected_citation_ids[:1],
        }
        for pack_ref in selected_pack_refs
    ],
    "matched_rulesets": [
        {
            "id": artifact_id,
            "corpus_id": next(chunk["corpus_id"] for chunk in selected if chunk["artifact_id"] == artifact_id),
            "ruleset_type": "concern" if ".concern." in artifact_id else "layer",
            "rule_ids": selected_rule_ids,
            "selection_reason": "Selected smoke chunks reference this ruleset artifact.",
            "citation_ids": selected_citation_ids[:1],
        }
        for artifact_id in selected_artifact_ids
    ],
    "selected_chunks": selected,
    "required_checks": [
        {
            "id": "check.validate-context-packet",
            "description": "Run the context-packet validator before trusting the packet.",
            "timing": "before-edit",
            "command": "bash scripts/02.rag-rulebook/validate-context-packet/script.sh --packet <packet> --chunks <chunks>",
            "citation_ids": selected_citation_ids[:1],
        }
    ],
    "forbidden_actions": [
        {
            "action": "Use uncited packet content",
            "reason": "Every selected chunk must resolve to packet and chunk-set citations.",
            "citation_ids": selected_citation_ids[:1],
        }
    ],
    "stop_conditions": [
        {
            "id": "stop.unresolved-packet-reference",
            "condition": "A selected chunk or citation cannot be resolved.",
            "severity": "blocking",
            "suggested_resolution": "Regenerate or repair the packet before using it.",
            "citation_ids": selected_citation_ids[:1],
        }
    ],
    "citations": citations,
    "confidence": {
        "overall": 1,
        "retrieval": 1,
        "routing": 1,
        "notes": ["Smoke packet is deterministic."],
    },
    "gaps": [],
    "budgets": {
        "max_context_tokens": selected_context_tokens + 1000,
        "selected_context_tokens": selected_context_tokens,
        "trim_policy": "deterministic-first",
    },
    "provenance": {
        "service_version": "smoke-test",
        "corpus_index_versions": [
            {
                "corpus_id": corpus_id,
                "index_version": chunk_set["source_index_id"],
                "content_hash": chunk_set["provenance"]["source_index_fingerprint"],
            }
            for corpus_id in selected_corpus_ids
        ],
        "retrieval_order": ["deterministic smoke fixture"],
        "generator": "scripts/02.rag-rulebook/validate-context-packet/smoke-test.sh",
    },
}
Path(sys.argv[2]).write_text(json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8")
PY

bash scripts/02.rag-rulebook/validate-context-packet/script.sh \
  --packet "$PACKET_FILE" \
  --chunks "$CHUNKS_FILE" \
  --json > "$REPORT_FILE"

python3 - "$REPORT_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert report["ok"], report
assert report["counts"]["selected_chunks"] == 3
assert report["counts"]["citations"] >= 1
PY

python3 - "$PACKET_FILE" "$BROKEN_PACKET_FILE" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

packet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
packet["selected_chunks"][0]["citation_ids"] = ["missing.citation"]
Path(sys.argv[2]).write_text(json.dumps(packet), encoding="utf-8")
PY

if bash scripts/02.rag-rulebook/validate-context-packet/script.sh \
  --packet "$BROKEN_PACKET_FILE" \
  --chunks "$CHUNKS_FILE" >/dev/null 2>&1; then
  echo "ERROR: context-packet validator accepted a broken citation" >&2
  exit 1
fi

echo "Context packet validator smoke test passed."
