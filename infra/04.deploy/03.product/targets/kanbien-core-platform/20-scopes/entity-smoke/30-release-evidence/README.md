<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.entity-smoke.release-evidence.readme
version: 1
status: draft
created_on: "2026-11-08"
updated_on: "2026-11-09"
layer: 04.deploy
domain: deployment.release-evidence
disciplines: [architecture, security, sre]
kind: readme
purpose: Establish the canonical entity-smoke custody directory without inventing an accepted release or live proof.
portability: {class: internal, targets: []}
used_by:
- id: deploy.plan.entity-smoke-core-platform
  path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
-->
# Entity-smoke release evidence

A failed first deployment has no earlier accepted image to restore. Before
choosing its declared stop/preserve policy, the existing release-succession
selector must inspect this canonical directory. An absent or unreadable
directory cannot be treated as proof that the scope is new.

This README establishes the directory only. It is **not** a deployment receipt,
verified candidate, accepted release, rollback predecessor or proof of data
preservation. None of those records has been created here.

## Policy selection and later acceptance

The existing [release-succession command](../../../../../../../../scripts/04.deploy/lifecycle/60-run/release-succession/script.sh)
owns selection and immutable custody. From the repository root:

```bash
bash scripts/04.deploy/lifecycle/60-run/release-succession/script.sh \
  --operation select-recovery \
  --scope-contract infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/declaration-contract.yml \
  --evidence-root infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/30-release-evidence \
  --json
```

This is read-only local policy selection, not AWS permission or live recovery.
The selected initial policy is possible only while the canonical declaration
and independent candidate ownership are valid and no current, historical or
legacy accepted custody exists. Orphaned history or malformed records block
selection instead of being mistaken for an initial release.

The [verify/accept/restore workflow](../../../../../../../../.agentic/04.deploy/60-run/workflows/verify-accept-or-restore-release.md)
requires fresh selection at execution. The bounded controller uses the existing
`.release-succession.lock` to serialize with normal promotion; that generated
coordination file is ignored only at this exact scope location. Accepted records
and other evidence files are not ignored or exempt from committed-source checks.

When actual required proofs exist, the owning collector will retain a verified
candidate here and normal succession may promote it with an expected predecessor
of `none`. Missing live proof cannot be replaced with hand-authored receipts.
After first acceptance, selection must use the compatible accepted-image policy,
not stop/preserve as a permanent exception. Do not overwrite an accepted record.

Working reservations and local observations remain under
`.cache/entity-smoke-live/<proof-label>/`; local test reports use
`.cache/test-runs/`. The chat session records bounded outcomes and references,
not raw provider responses, secrets or copied private-cache reports.
