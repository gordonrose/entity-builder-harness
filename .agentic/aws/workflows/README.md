<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: aws.workflows.readme
  version: 1
  status: active
  created_on: "2026-06-19"
  updated_on: "2026-10-21"
  layer: 04.deploy
  domain: infra.ci-cd
  disciplines:
  - agentic
  - sre
  kind: workflow
  purpose: Document AWS Workflows.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: repo.agents
    path: AGENTS.md
-->
# AWS Workflows

## Workflows

- `inspect-aws-state.md` - inspect AWS resources without changing cloud state.
- `plan-aws-change.md` - prepare a proposed AWS change before execution.
- `execute-approved-aws-change.md` - run an explicitly approved AWS change and
  record the result.
- `deploy-rag-rulebook-service.md` - govern GitHub-to-AWS deployment of the
  RAG/rulebook MCP service after readiness proof and explicit approval.
- [Review and execute ECS runtime update](../50-deploy/workflows/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/review-and-execute-ecs-runtime-update.md) - govern fixed-target
  UPDATE, verification, accepted-release recording, and restoration.
