<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.release-control-source-validation-review
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Preserve a separately dated source review candidate after validation hardening.
portability: {class: source-only, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->
# Source validation review candidate — 2026-09-29

This source-only snapshot follows the fourth reliability slice. The original
273-source/169-finding baseline and the later 282-source/175-finding snapshot
remain unchanged historical records. Neither is current source acceptance.

The [fresh inventory](current-inventory.json) contains **293 sources, 1,093
observations and 185 unresolved findings**. All 185
[intake assignments](current-triage.json) remain open: 180 for Phase 2 source
semantics and five for Phase 3 artifact proof. The
[triage result](current-triage-result.json) is classification complete while
coverage remains blocked and authorization remains false.

The ten additional findings come from this slice's seven Python implementation/
test modules, the clean-environment shell wrapper, and the validation workflow's
opaque command and external actions. Local tests and pinned dependencies do not
give the source collector new semantic capabilities. No earlier finding was
silently closed or converted into a provider problem.

## Selected staging caller review

The [caller graph](staging-caller-graph.json) still has 11 bound source files,
54 subjects, 53 edges and 38 unresolved boundaries. Its only changed source
binding is `package.json`. The package diff adds the clean-check command and
expands the realization check's metadata paths; all fourteen commands reachable
from the staging publication workflow retain their earlier text.

The new graph was compared with the previous snapshot: subject records, edges
and findings are identical. On that basis the existing declared source profiles
were retained in a new [review candidate](staging-caller-review.json), with the
new graph identity. This is a bounded source review, not authenticated approval
or proof of actual effects. The [accounting result](staging-caller-result.json)
is accounted, qualification blocked, authorization false.

The nine script bodies, seven tools, thirteen opaque command blocks and nine
external action boundaries remain unresolved. The new validation workflow is
included in source finding intake; this slice does not add a reviewed caller
map for that workflow or declare its opaque behavior qualified.

## Reproduce the candidate

Recorded source identities:

- Inventory: `sha256:08e7346b42cf8b97658821ec21ca75421d3e4a999f2dba62247d48936a567c36`.
- Caller graph: `sha256:40bf4c1259ebf3a1136bca8db48b2fde221524fea97e306c47266ed415ef6717`.
- Caller accounting: `sha256:b1fe4787ca4c6efac71b3a6a58ed0a9529e3291b44b6886cb2cd161cd9b9f2df`.

From the repository root:

```bash
candidate=docs/04.deploy/plans/release-control-source-adoption/2026-09-29-source-validation
gate=scripts/04.deploy/operational-realization-gate/script.sh

bash "$gate" --triage --source-root . \
  --finding-triage "$candidate/current-triage.json"

bash "$gate" --callers --source-root . \
  --workflow .github/workflows/deploy-platform-shell-staging.yml \
  --caller-review "$candidate/staging-caller-review.json"

bash "$gate" --consume-result "$candidate/current-triage-result.json" \
  --purpose source-analysis -- --triage --source-root . \
  --finding-triage "$candidate/current-triage.json"

bash "$gate" --consume-result "$candidate/staging-caller-result.json" \
  --purpose source-analysis -- --callers --source-root . \
  --workflow .github/workflows/deploy-platform-shell-staging.yml \
  --caller-review "$candidate/staging-caller-review.json"
```

These commands recollect source. Saved inventories and graphs are review
artifacts; they are not a replacement for discovery. Both producer checks and
source-analysis consumers should return zero for this unchanged candidate.
Changing either consumer purpose to `release-eligibility` or
`operation-authorization` returns one with explicit blocked authority.
Future source, policy or collector changes can invalidate this dated snapshot.

## Remaining delivery queue

Next: source contracts, caller/profile/argument semantics and build/import
closure for the selected nine script terminals and external actions. Then
expand supported operation families and reviewed adoption, and implement
exact-artifact proof as its source inputs become known. Phase 2 estate closure
and later evidence admission/authorization remain open.

The validation-only CI workflow is prepared locally. Publishing it or changing
repository required-check settings is an external activation step, outside this
source-only slice. AWS adapters/stores, PostgreSQL Stage 6 and live target
qualification remain later work.
