#!/usr/bin/env bash
set -euo pipefail

TASK="${*:-}"

classify_mode() {
  case "$TASK" in
    *plan*|*proposal*|*architecture*|*approach*|*how\ should*|*how\ would*|*how\ do*)
      echo "planning"
      ;;
    *implement*|*add*|*update*|*change*|*edit*|*create*|*delete*|*remove*|*move*|*format*|*fix*|*turn*|*draft*|*generate*|*improve*)
      echo "implementation"
      ;;
    *run*|*execute*|*use*|*apply*|*start*)
      echo "execution"
      ;;
    *inspect*|*investigate*|*summarize*|*summary*|*compact*|*preserve*|*transfer*|*diagnose*|*find*|*where*|*why*|*read*|*how*|*look*|*explain*|*discuss*|*brainstorm*|*what*|*question*|*review*|*audit*|*critique*|*risk*|*bugs*|*regression*|*regressions*|*verify*|*validate*|*test*|*tests*|*check*|*checks*|*mine*|*analyze*|*analyse*|*\?*)
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
  *AGENTS.md*|*CLAUDE.md*|*.agentic*|*agentic\ structure*|*routing*|*workflow*|*workflows*|*mode*|*modes*|*layer*|*layers*)
    echo "Layer: harness"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/harness/workflows/change-harness.md"
    ;;
  *education*|*educational*|*teaching*|*teacher*|*lecture*|*lecturer*|*classroom*|*blog\ post*|*blogpost*|*talk*|*talks*|*content\ mining*|*voice\ profile*|*humor\ profile*|*humour\ profile*|*storytelling*|*teaching\ asset*|*teaching\ assets*)
    echo "Layer: education"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/education/workflows/mine-daily-learning-material.md"
    ;;
  *chat*|*branch*|*branches*|*commit*|*worktree*|*git*|*handoff*|*deployment*|*release*|*remote*|*push*|*pull*|*merge*|*conflict*|*conflicts*|*cherry-pick*|*origin/main*|*origin\ main*|*github*)
    echo "Layer: shared"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/shared/workflows/change-shared-process.md"
    ;;
  *capability*|*capabilities*|*skill*|*skills*|*agent*|*gate*|*gates*|*adapter*|*token*|*tokens*|*instruction*|*harness*)
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
