#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.classification.classify-task
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: classification
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Classify an opening task into layer, mode, and workflow metadata.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-start
#     path: .agentic/00.chat/workflows/chat-start.md
#   - id: chat.script.classification.classify-task.check-fixtures
#     path: scripts/00.chat/classification/classify-task/check-fixtures.sh
#   - id: chat.script.startup.start-chat-session
#     path: scripts/00.chat/startup/start-chat-session/script.sh
#   effects:
#   - read-only

TASK_RAW="${*:-}"
TASK="$(printf '%s' "$TASK_RAW" | tr '[:upper:]' '[:lower:]')"

classify_mode() {
  case "$TASK" in
    *run*existing*|*use*existing*)
      echo "execution"
      ;;
    *plan*|*proposal*|*architecture*|*approach*|*how\ should*|*how\ would*|*how\ do*)
      echo "planning"
      ;;
    *implement*|*add*|*update*|*change*|*edit*|*create*|*delete*|*remove*|*move*|*rename*|*format*|*fix*|*turn*|*draft*|*generate*|*improve*|*cleanup*|*clean\ up*|*promote*|*document*|*open*chat*|*open*llm-workbench*|*bootstrap*|*seed*)
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

aws_workflow() {
  case "$MODE" in
    planning)
      echo ".agentic/aws/workflows/plan-aws-change.md"
      ;;
    implementation|execution)
      echo ".agentic/aws/workflows/execute-approved-aws-change.md"
      ;;
    *)
      echo ".agentic/aws/workflows/inspect-aws-state.md"
      ;;
  esac
}

case "$TASK" in
  *default\ branch*|*base\ branch*|*master*|*origin/main*|*origin\ main*)
    echo "Layer: shared"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/shared/workflows/change-shared-process.md"
    ;;
  *governed\ script*|*governed\ checkpoint*|*approval\ prompt*|*permission\ prompt*|*codex*approval*|*allow*bash*|*bash*permission*|*shell*permission*|*tool*permission*|*.codex*|*.claude*|*.vibe*|*codex*claude*mistral*|*vendor*adapter*)
    echo "Layer: harness"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/01.harness/workflows/change-harness.md"
    ;;
  *chat\ start*|*start\ chat*|*chat\ startup*|*unknown-classification\ prompt*|*classification\ prompt*|*session\ metadata*|*session\ log*|*session\ logs*|*chat\ session*|*chat*worktree*session*|*chat-owned\ worktree*)
    echo "Layer: chat"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/00.chat/workflows/chat-start.md"
    ;;
  *main\ refresh*|*refresh\ from\ main*|*main\ updated*|*updated\ main*)
    echo "Layer: chat"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/00.chat/workflows/chat-refresh-from-main.md"
    ;;
  *chat\ commit*|*checkpoint*|*session\ checkpoint*|*record\ chat\ commit*)
    echo "Layer: chat"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/00.chat/workflows/chat-commit.md"
    ;;
  *local\ convergence*|*promote\ to\ main*|*promote*chat*main*|*merge\ to\ main*|*merge\ chat\ branch*|*merge\ chat\ work*)
    echo "Layer: chat"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/00.chat/workflows/chat-promote-to-main.md"
    ;;
  *chat\ cleanup*|*cleanup\ chat*|*chat\ branch\ cleanup*|*preflight\ cleanup*|*worktree\ cleanup*|*clean\ up*chat*worktree*|*clean\ up\ old\ worktrees*)
    echo "Layer: chat"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/00.chat/workflows/chat-cleanup.md"
    ;;
  *chat\ report*|*chat\ reporting*|*session\ summary*|*session\ summaries*|*commit\ log\ summary*|*commit\ logs\ summary*)
    echo "Layer: chat"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/00.chat/workflows/chat-reporting.md"
    ;;
  *bootstrap*llm-workbench*|*bootstrap*chat\ workbench*|*seed*upstream*workbench*|*empty\ workbench\ repo*)
    echo "Layer: chat"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md"
    ;;
  *upstream\ reusable\ lesson*|*reusable\ lesson\ workflow*|*llm-workbench*|*workbench\ repo*)
    echo "Layer: chat"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/00.chat/workflows/chat-upstream-reusable-lesson.md"
    ;;
  *00.chat*|*chat\ lifecycle*)
    echo "Layer: chat"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/00.chat/workflows/chat-start.md"
    ;;
  *AGENTS.md*|*CLAUDE.md*|*.agentic*|*agentic\ structure*|*routing*|*workflow*|*workflows*|*mode*|*modes*|*layer*|*layers*)
    echo "Layer: harness"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/01.harness/workflows/change-harness.md"
    ;;
  *education*|*educational*|*teaching*|*teacher*|*lecture*|*lecturer*|*classroom*|*blog\ post*|*blogpost*|*talk*|*talks*|*content\ mining*|*voice\ profile*|*humor\ profile*|*humour\ profile*|*storytelling*|*teaching\ asset*|*teaching\ assets*)
    echo "Layer: education"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/education/workflows/mine-daily-learning-material.md"
    ;;
  *aws*|*AWS*|*ecs*|*ECS*|*ecr*|*ECR*|*rds*|*RDS*|*route53*|*Route\ 53*|*cloudwatch*|*CloudWatch*|*iam*|*IAM*|*app\ runner*|*App\ Runner*|*elastic\ beanstalk*|*Elastic\ Beanstalk*|*elasticache*|*ElastiCache*|*load\ balancer*|*load\ balancers*|*target\ group*|*target\ groups*|*task\ definition*|*task\ definitions*)
    echo "Layer: aws"
    echo "Mode: ${MODE}"
    echo "Workflow: $(aws_workflow)"
    ;;
  *branch*|*branches*|*commit*|*git*|*handoff*|*deployment*|*release*|*remote*|*push*|*pull*|*merge*|*conflict*|*conflicts*|*cherry-pick*|*origin/main*|*origin\ main*|*github*)
    echo "Layer: shared"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/shared/workflows/change-shared-process.md"
    ;;
  *capability*|*capabilities*|*skill*|*skills*|*agent*|*gate*|*gates*|*adapter*|*token*|*tokens*|*instruction*|*harness*)
    echo "Layer: harness"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/01.harness/workflows/change-harness.md"
    ;;
  *code*|*feature*|*design\ system*|*auth*|*tenant*|*database*|*test*|*CI*|*CD*)
    echo "Layer: product"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/product/workflows/default.md"
    ;;
  *)
    echo "Layer: unknown"
    echo "Mode: ${MODE}"
    echo "Workflow: .agentic/00.chat/workflows/chat-start.md"
    exit 1
    ;;
esac
