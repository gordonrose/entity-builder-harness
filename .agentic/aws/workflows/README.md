<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: aws.workflows.readme
  version: 1
  status: active
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
