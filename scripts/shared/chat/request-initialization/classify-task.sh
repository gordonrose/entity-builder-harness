#!/usr/bin/env bash
set -euo pipefail

TASK="${*:-}"

classify_mode() {
  case "$TASK" in
    *plan*|*proposal*|*architecture*|*approach*|*how\ should*|*how\ would*|*how\ do*)
      echo "planning"
      ;;
    *implement*|*add*|*update*|*change*|*edit*|*create*|*delete*|*remove*|*move*|*format*|*fix*)
      echo "implementation"
      ;;
    *run*|*execute*|*use*|*apply*|*start*)
      echo "execution"
      ;;
    *inspect*|*investigate*|*summarize*|*summary*|*compact*|*preserve*|*transfer*|*diagnose*|*find*|*where*|*why*|*read*|*how*|*look*|*explain*|*discuss*|*brainstorm*|*what*|*question*|*review*|*audit*|*critique*|*risk*|*bugs*|*regression*|*regressions*|*verify*|*validate*|*test*|*tests*|*check*|*checks*|*\?*)
      echo "discovery"
      ;;
    *)
      echo "unknown"
      ;;
  esac
}

if [[ -z "${TASK// }" ]]; then
  echo "Layer: unknown"
  echo "Mode: unknown"
  echo "Workflow: unknown"
  echo "Reason: missing task"
  exit 2
fi

MODE="$(classify_mode)"

case "$TASK" in
  *chat*|*branch*|*branches*|*commit*|*worktree*|*git*|*handoff*|*deployment*|*release*|*remote*|*push*|*pull*|*cherry-pick*|*origin/main*|*github*)
    echo "Layer: shared"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/shared/workflows/default.md"
    ;;
  *AGENTS.md*|*CLAUDE.md*|*.agentic*|*routing*|*workflow*|*workflows*|*mode*|*modes*|*capability*|*capabilities*|*skill*|*skills*|*agent*|*gate*|*gates*|*adapter*|*token*|*tokens*|*instruction*)
    echo "Layer: harness"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/harness/workflows/change-harness.md"
    ;;
  *code*|*feature*|*design\ system*|*auth*|*tenant*|*database*|*test*|*CI*|*CD*)
    echo "Layer: product"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/product/workflows/default.md"
    ;;
  *)
    echo "Layer: unknown"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/shared/workflows/chat-start-interview.md"
    exit 1
    ;;
esac
