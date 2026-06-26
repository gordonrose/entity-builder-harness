<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.source-material.mcp-server-deployment
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: source-material
purpose: Define production-grade source material for deploying harness or RAG/rulebook capabilities behind an MCP server through GitHub and AWS.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.corpus-gap.04-deploy.mcp-server-deployment
  path: .agentic/02.rag-rulebook/corpus-gaps/04.deploy/mcp-server-deployment.yml
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
-->
# MCP Server Deployment Source Material

## Purpose

Define the production-readiness source material for deploying harness or
RAG/rulebook capabilities behind an MCP server through GitHub and AWS.

This document is source material only. It does not authorize AWS mutation,
deployment execution, MCP server implementation, or production exposure.

## Production-Grade Bar

This source is production grade only if every important deployment claim can
later become at least one of these artifacts:

- a deploy rule
- a required check
- a stop condition
- a rollback step
- a security boundary
- an evaluation fixture
- an explicit corpus or implementation gap

Any statement that cannot be tested, cited, governed, or converted into a
structured rule should be rewritten or removed.

## Current Scope

The immediate goal is to make local RAG useful before hosted RAG or deployed MCP
server work begins.

The source covers:

- local RAG runtime as the first execution target
- remote RAG as a future context provider for committed corpus packages
- MCP as a future service boundary for resources, prompts, and tools
- GitHub as the publish and deployment-control surface
- AWS as the eventual runtime target
- explicit stop conditions for missing deploy corpus coverage

The source does not cover:

- creating or changing AWS resources
- creating production GitHub Actions workflows
- exposing public MCP endpoints
- storing secrets or credentials in the repo
- running deployment commands
- treating source material as structured rulebook coverage

## Desired Deployed Shape

The deployed RAG/rulebook service should behave as a context provider.

Normal use should look like this:

```text
Chat harness or MCP client
  -> sends prompt, repo id, commit sha, layer, mode, workflow, focused paths,
     token budget, and corpus version expectations
Remote RAG/rulebook service
  -> searches published indexes and chunks
  -> returns a validated context packet
Agent or client
  -> plans, answers, asks for approval, or stops according to the packet
```

The remote service should not read a developer's local working tree during
normal operation. It should answer from committed and published corpus packages.

Local RAG remains authoritative for uncommitted corpus changes. If the local
repo is ahead of the published remote corpus, the harness should either use
local RAG or emit a stale-corpus gap.

## MCP Boundary

MCP servers provide context and capabilities to MCP clients. In this harness,
an MCP server must expose governed capabilities rather than becoming a parallel
execution path.

The first production-safe MCP surface should be read-only:

- retrieve a validated context packet
- list corpus gaps
- inspect corpus versions
- inspect deployment readiness
- expose stable prompts for planning or review

Tool execution should come later. Any write-capable, deploy-capable, or
destructive MCP tool must have typed inputs, typed outputs, approval rules,
audit records, rollback expectations, and layer ownership before exposure.

## Deployment Phases

### Phase 0: Local RAG

The repo builds and queries a local deterministic runtime cache.

Required proof:

- generated recognition sources are current
- rulebook index generation passes
- chunk generation passes
- context packet validation passes
- selector evaluations pass
- local query can surface known gaps

No hosted service or AWS mutation is allowed in this phase.

### Phase 1: Published Corpus Package

GitHub becomes the source for committed corpus packages.

Required proof:

- corpus files have artifact metadata
- generated sources, indexes, and chunks are reproducible
- CI can detect stale generated artifacts
- corpus package versions include commit sha or content hash
- remote service can identify which corpus version it is serving

### Phase 2: Remote RAG Context Provider

The RAG/rulebook service runs remotely and serves validated context packets
from published corpus packages.

Required proof:

- request contract is documented and versioned
- response packet schema is validated
- corpus version mismatch produces a gap
- unknown or stale corpus state does not silently fall back to broad context
- service logs are useful for audit and retrieval evaluation

### Phase 3: MCP Server Read-Only Surface

The MCP server exposes RAG/rulebook resources and planning prompts.

Required proof:

- MCP protocol version is explicit
- resource, prompt, and tool contracts are separated
- read-only endpoints cannot mutate repo, GitHub, or AWS state
- authentication and authorization expectations are documented
- audit records identify the caller, request type, selected corpus versions,
  emitted packet, and emitted gaps

### Phase 4: Governed Tool Surface

Only after the read-only surface is proven may MCP tools expose operations.

Required proof:

- every tool maps to an owning layer and workflow
- every tool declares side effects
- write, deploy, and destructive tools require explicit approval
- deployment tools use the deploy workflow and AWS approval rules
- rollback and recovery are tested before production use

## GitHub Deployment Boundary

GitHub should provide the release-control plane, not hidden deployment magic.

Production-grade GitHub deployment requires:

- protected deployment environments
- required reviewers for sensitive environments
- branch or tag restrictions for deployable refs
- environment-scoped variables and secrets
- preferably OIDC-based cloud authentication rather than long-lived cloud
  credentials stored as GitHub secrets
- workflow run logs and deployment history retained for audit
- explicit separation between build, publish corpus, deploy service, verify,
  and rollback jobs

GitHub workflow changes should not be treated as production-ready until the
workflow names the target environment, required approvals, secret names or OIDC
role assumptions, artifact provenance, health checks, rollback plan, and failure
notifications.

## AWS Deployment Boundary

AWS deployment must name the profile or account, region, environment, service
target, resource ownership, and rollback path before mutation.

Production-grade AWS deployment requires:

- least-privilege IAM or short-lived GitHub OIDC credentials
- explicit environment separation for local, staging, and production
- no secrets in repository files
- secret names or parameter names documented without secret values
- network exposure reviewed before public endpoints exist
- health checks at load balancer, service, container, and application level
- deployment failure detection
- rollback target and rollback command path
- logs and metrics for request rate, error rate, latency, task health,
  deployment state, and authorization failures

For ECS-style service deployment, rollback behavior should be explicit. If a
deployment controller supports a circuit breaker or blue/green rollout, the
source material and later rules should define how failure is detected, who or
what initiates rollback, and what evidence proves rollback completed.

## Security Requirements

Deployment guidance is unsafe unless the security boundary is explicit.

Required security claims:

- MCP tools can execute arbitrary operations and must be treated as high-risk.
- Hosts or users must consent before data access or tool invocation.
- Resource data must not be transmitted beyond its intended boundary.
- Tool descriptions and annotations are not enough to prove safety.
- Authentication, authorization, and audit behavior must be defined before
  remote or production use.
- GitHub and AWS credentials must be short-lived where possible.
- Secret values must never be written to source material, rules, logs, context
  packets, or evaluation fixtures.

## Observability Requirements

The system is not production-ready if failure cannot be seen quickly.

Required observability:

- RAG request id
- repo id and commit sha
- corpus versions used
- selected chunks and citations
- emitted gaps
- MCP caller identity or client identity when available
- GitHub run id for deployment work
- AWS account/profile, region, service, and deployment id
- health check results
- rollback action and result

Logs must redact secrets and unrelated user or repo content.

## Stop Conditions

Deployment planning or execution must stop when:

- the requested action has no owning layer or workflow
- the deploy corpus is missing required source material, rules, chunks, or
  selector evaluations
- local repo state and remote corpus version do not match and no local RAG
  fallback is selected
- AWS account, profile, region, or environment is ambiguous
- GitHub environment protections are absent or unknown for production
- authentication, authorization, or consent behavior is unspecified
- rollback target or health check is missing
- a requested MCP tool would mutate state without approval
- secrets would need to be copied into repo files

Stopping is the safe behavior. The output should name the gap and the smallest
next governed step.

## Source-To-Rule Conversion Targets

The next structured YAML rules should cover:

- MCP server deployment ownership
- remote RAG context provider contract
- GitHub-to-AWS deployment boundary
- AWS runtime and rollback boundary
- deployment observability and audit requirements
- stale remote corpus handling
- deploy execution stop conditions

## Known Gaps

- First deploy-layer YAML rules now exist for MCP server deployment.
- The rulebook index now scans `docs/04.deploy/rules/` and emits
  `corpus.04.deploy` chunks.
- Selector evaluations now prove planning prompts can select
  `corpus.04.deploy` retrieval when a governed corpus gap matches.
- GitHub deployment workflow requirements now have structured release-control
  rules but do not yet have an executable workflow.
- AWS runtime target choice is not yet decided, so runtime-specific deploy
  execution remains blocked.
- MCP server read-only endpoint contract is not yet specified.
- No production deployment or rollback procedure is approved.

## External References

- MCP specification, version 2025-11-25: https://modelcontextprotocol.io/specification/2025-11-25
- MCP architecture overview: https://modelcontextprotocol.io/docs/learn/architecture
- GitHub Actions environments: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments
- GitHub Actions secrets: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets
- GitHub Actions OpenID Connect: https://docs.github.com/en/actions/concepts/security/openid-connect
- AWS Well-Architected identity and access management: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-and-access-management.html
- Amazon ECS deployment circuit breaker: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html
- Amazon ECS blue/green deployments: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-bluegreen.html
