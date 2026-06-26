<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: aws.readme
  version: 1
  status: active
  layer: 04.deploy
  domain: infra.ci-cd
  disciplines:
  - agentic
  - sre
  kind: guide
  purpose: Document AWS Layer.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: repo.agents
    path: AGENTS.md
-->
# AWS Layer

The AWS layer governs cloud infrastructure, environments, runtime operations,
and AWS deployment targets for this repo.

Use this layer for work that inspects, plans, or changes AWS resources such as:

- accounts, profiles, regions, and environment inventory
- ECS, ECR, RDS, ElastiCache, Route 53, load balancers, App Runner, or Elastic
  Beanstalk resources
- task definitions, services, clusters, repositories, images, parameters, and
  secrets references
- runtime logs, deployed configuration, health checks, and operational status
- cloud deployment targets and infrastructure change plans
- cost, security, access, and blast-radius review for AWS resources

AWS work should name the account or profile, region, and environment before
changing cloud state. Discovery work may inspect AWS state, but mutating AWS
commands require explicit user approval for the current chat.

Do not store secrets in this repo. It is acceptable to document secret names,
parameter names, ARNs, resource identifiers, and configuration conventions when
they are needed for repeatable operations.

## Workflows

- `workflows/inspect-aws-state.md` - inspect AWS resources without changing
  cloud state.
- `workflows/plan-aws-change.md` - prepare an AWS change plan, including
  profile, region, environment, evidence, risk, and rollback notes.
- `workflows/execute-approved-aws-change.md` - run an explicitly approved AWS
  change and record the result.

## Supporting Artifacts

Add scripts, gates, templates, or runbooks only after repeated need or a clear
safety reason. Prefer deterministic scripts for repeatable AWS checks.

## Output Locations

- `docs/04.deploy/` stores RAG-readable deploy corpus source material and
  future structured deploy rules.
- `docs/aws/architecture/adrs/` stores durable AWS-layer decisions.
- `docs/aws/runbooks/` stores repeatable operational procedures when they are
  too detailed for a workflow.
- `docs/aws/inventory/` stores non-secret environment and resource notes.

## AWS ADRs

Use an AWS ADR for durable decisions about environment shape, resource
ownership, deployment targets, access boundaries, operational conventions, or
infrastructure tradeoffs.
