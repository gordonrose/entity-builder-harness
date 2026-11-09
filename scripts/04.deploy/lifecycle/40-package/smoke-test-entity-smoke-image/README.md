<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.guide.entity-smoke.image-qualification
version: 1
status: draft
created_on: "2026-11-08"
updated_on: "2026-11-09"
layer: 04.deploy
domain: deployment.entity-smoke
disciplines: [security, sre]
kind: readme
purpose: Explain actual finished-image qualification and its explicit local versus AWS proof boundary.
portability: {class: internal, targets: [kanbien-core-platform]}
used_by:
- id: deploy.command.smoke-test-entity-smoke-image
  path: scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/script.sh
-->
# Entity-smoke image qualification

This command tests the packaged feature against disposable TLS PostgreSQL 18.3,
matching the existing AWS dependency observed on 2026-11-08.
It does not publish an image, deploy AWS resources or accept a release. A source
checkpoint and complete scope/delivery declarations are prerequisites; source
availability alone does not mean those prerequisites have passed.

Run from the repository root after the governed image build:

```bash
bash scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/script.sh
```

## Responsibilities

| File | Responsibility |
| --- | --- |
| `script.sh` | Check declarations and invoke the finished-image and capability checks. |
| `verify-image.mjs` | Check immutable source/platform/non-root/effective environment; reserve resources; run actual database, migration, feature, replacement and recovery operations; observe cleanup. |
| `capability-negative-test.py` | Reject forbidden image capabilities, missing selectors, administrative credential injection and production synthetic-token use. |
| `qualification-control-test.mjs` | Test reservation and cleanup control with a simulated Docker interface. This is not container proof. |

The actual image check creates an internal network, certificate volume, two
named data volumes, disposable databases and feature containers. Its restricted
administrator has database-local grant authority, not superuser or CREATEDB.
Proof covers matching server version, checksum-preserving already-applied
migration, rejection of a changed checksum on the disposable restored fixture,
attribute mapping, lifecycle timing, effective denied SQL, original
record preservation after a duplicate ID, process replacement and explicit
runtime-access revocation/recovery. It checks normal downstream logs for
synthetic credential canaries. Dump/restore to a second PostgreSQL instance is
local fixture proof, not an RDS snapshot or AWS IAM-authentication result.
PostgreSQL 18 uses a
[versioned data directory](https://github.com/docker-library/docs/blob/master/postgres/README.md#pgdata);
the qualifier reserves and mounts the whole named PostgreSQL volume rather than
leaving an anonymous data volume behind.

## Interrupted attempts

Before resource creation the qualifier flushes a mode-0600 reservation under
`/tmp/entity-smoke-image-*`. On failure it attempts cleanup through the existing
[Docker cleanup owner](../../../shared/provider-adapters/docker/disposable-cleanup.py).
It reports success only after absence is observed. Unknown engine state is not
absence and does not authorize another qualification attempt.

For a retained reservation use the cleanup-only interface:

```bash
bash scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/script.sh \
  --cleanup-reservation /tmp/entity-smoke-image-EXAMPLE/resource-reservation.json
```

The command validates exact ownership before touching Docker. It cannot build,
qualify, publish or deploy. Keep reservation evidence if cleanup cannot be
confirmed; do not manually widen its resource names or substitute another
database. AWS replacement, snapshot restoration, recovery and release acceptance
remain separate live obligations.
