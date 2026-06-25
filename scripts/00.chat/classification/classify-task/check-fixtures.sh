#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.classification.classify-task.check-fixtures
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: classification
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Validate task classifier fixtures against current classification output.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: shared.workflows.capability-resolution-workflow
#     path: .agentic/shared/workflows/capability-resolution-workflow.md
#   - id: chat.workflows.chat-start
#     path: .agentic/00.chat/workflows/chat-start.md
#   - id: chat.script.classification.classify-task.fixtures-tsv
#     path: scripts/00.chat/classification/classify-task/fixtures.tsv
#   effects:
#   - read-only

FIXTURES="${1:-scripts/00.chat/classification/classify-task/fixtures.tsv}"
FAILURES=0

if [ ! -f "$FIXTURES" ]; then
  echo "ERROR: missing fixtures file: $FIXTURES"
  exit 2
fi

while IFS=$'\t' read -r TASK EXPECTED_LAYER EXPECTED_MODE EXPECTED_WORKFLOW; do
  case "${TASK:-}" in
    ""|\#*)
      continue
      ;;
  esac

  OUTPUT="$(bash scripts/00.chat/classification/classify-task/script.sh "$TASK" || true)"
  ACTUAL_LAYER="$(printf '%s\n' "$OUTPUT" | sed -n 's/^Layer: //p')"
  ACTUAL_MODE="$(printf '%s\n' "$OUTPUT" | sed -n 's/^Mode: //p')"
  ACTUAL_WORKFLOW="$(printf '%s\n' "$OUTPUT" | sed -n 's/^Workflow: //p')"

  if [ "$ACTUAL_LAYER" != "$EXPECTED_LAYER" ] || [ "$ACTUAL_MODE" != "$EXPECTED_MODE" ]; then
    echo "FAIL: $TASK"
    echo "  expected: Layer=$EXPECTED_LAYER Mode=$EXPECTED_MODE"
    echo "  actual:   Layer=${ACTUAL_LAYER:-missing} Mode=${ACTUAL_MODE:-missing}"
    FAILURES=$((FAILURES + 1))
  fi

  if [ -n "${EXPECTED_WORKFLOW:-}" ] && [ "$ACTUAL_WORKFLOW" != "$EXPECTED_WORKFLOW" ]; then
    echo "FAIL: $TASK"
    echo "  expected: Workflow=$EXPECTED_WORKFLOW"
    echo "  actual:   Workflow=${ACTUAL_WORKFLOW:-missing}"
    FAILURES=$((FAILURES + 1))
  fi
done < "$FIXTURES"

if [ "$FAILURES" -gt 0 ]; then
  echo "Classifier fixture failures: $FAILURES"
  exit 1
fi

echo "Classifier fixtures passed."
