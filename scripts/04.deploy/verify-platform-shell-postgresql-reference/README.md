<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.verify-platform-shell-postgresql-reference.readme
version: 1
status: active
layer: 04.deploy
domain: persistence.operations
disciplines:
- security
- sre
- architecture
kind: capability-readme
purpose: Explain the static source boundary check for the Kanbien staging PostgreSQL relational reference.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.verify-platform-shell-postgresql-reference
  path: scripts/04.deploy/verify-platform-shell-postgresql-reference/script.sh
-->
# PostgreSQL Relational-Reference Static Verification

This command validates source only: it does not contact AWS, retrieve a secret,
start a database, or mutate a target. It proves private subnets, non-public
encrypted RDS, exact TCP 5432 security-group paths, generated credential
references, least-privilege roles, non-secret configuration, and safe RDS
operations signals through the existing alert destination.

```bash
bash scripts/04.deploy/verify-platform-shell-postgresql-reference/script.sh
```

It is also part of `npm run platform:shell:infrastructure:check`.
