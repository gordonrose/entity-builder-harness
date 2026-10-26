<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.script.verify-platform-shell-deploy-readiness.readme
version: 1
status: active
created_on: "2026-07-10"
updated_on: "2026-10-26"
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: capability-readme
purpose: Explain the read-only platform shell deploy-readiness verifier.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.script.verify-platform-shell-deploy-readiness
  path: scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh
-->
# Verify Platform Shell Deploy Readiness

`script.sh` validates a product platform shell deploy-readiness manifest without
mutating GitHub or AWS.

The verifier fails closed by default. A manifest with unresolved deployment
proof must include explicit blockers and exits non-zero unless the caller uses
planning or explanation mode.

## Usage

```bash
bash scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh \
  --manifest infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml
```

For planning or human explanation, allow blocked evidence explicitly:

```bash
bash scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh \
  --manifest infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml \
  --allow-blocked \
  --caller-intent planning
```

The command is read-only. It checks manifest shape, optional reusable target
profile references, target profile identity, source provider, GitHub workflow
presence, GitHub OIDC permission, protected workflow environment selection,
cloud provider, selected runtime family, adapter selection, auth
provider/readiness evidence, CORS allowlist source, health exposure policy,
rate-limit keying, local file references, local smoke evidence, blocker
coverage, and whether the manifest can be treated as ready or blocked.

A `ready` manifest must identify the same source commit, publication workflow,
workflow run and repository in `source`, `github` and `artifacts`. It must also
name repository-relative `acceptance.evidence_root`,
`acceptance.current_observation` and `acceptance.package_custody_receipt` paths.
The candidate preflight validates the existing package-custody schema and exact
source commit, digest and publication run before provider mutation. The runtime
producer durably copies that receipt into the immutable proof set, so later
readiness does not depend on an expiring workflow download. The evidence root contains generic
`release-candidates/`, `proof-receipts/`, `accepted-releases/` and
`current-accepted-release.yml` artifacts owned by the existing
`lifecycle/60-run/release-succession` command. A collection without promotion is
not an accepted release; a scope activation is not a release promotion.

The provider observer uses `release_evidence.py` to capture a safe, immutable
runtime receipt and emit `deploy/release-candidate/v1`. Its observation schema is
`deploy/platform-shell-runtime-observation/v1`, containing exactly target,
scope, UTC observation time, source revision, image digest, publication run,
workflow and repository, verdict, evidence class, checks and source-input hashes.
The four checks are runtime health, image identity, configuration and
permissions. Target profile, CloudFormation and IAM inputs are hashed from the
existing source artifacts. Raw provider output and secret values are never
accepted in the receipt schema.

Promote a verified candidate with the generic command after successful runtime
verification, supplying `--expected-predecessor none` for first acceptance or
the currently accepted release ID for a successor. The compare-and-swap protects
concurrent or interrupted acceptance and retries safely after an archive was
written. Historical candidates and receipts remain immutable. Reading history
does not require the old provider task to exist or old configuration hashes to
match the current checkout.

Readiness independently requires a current observation no more than 900 seconds
old, with at most 60 seconds future clock skew, and current source-input hashes.
A fresh observation cannot replace missing retained acceptance; retained proof
cannot replace fresh current-state checks. Changed current configuration or
permissions blocks readiness until the applicable current proof is renewed.
The canonical blocked manifest remains planning evidence and is not advanced by
this verifier. `--allow-blocked` is only a planning/explanation exit override;
its JSON report remains `ok: false` and never authorizes a mutation.

The smoke suite uses `--rehearsal-root` only for a disposable directory outside
the repository. Reports and receipts are explicitly `simulated`; production
consumers reject them. Run `bash scripts/04.deploy/verify-platform-shell-deploy-readiness/smoke-test.sh`
for the actual readiness/succession subprocess regressions.

For a retained release whose configuration and permission input bytes are
unchanged, record an additive compatibility decision before a rollback:

```bash
bash scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh \
  --manifest <retained-release-manifest> \
  --record-rollback-compatibility <retained-release-id> --json
```

This validates retained accepted lineage, both immutable receipts and exact
publication identity, then uses the generic rollback compatibility record owner.
It never promotes a release or changes historical evidence. Repeating the
command preserves existing receipt bytes. Changed configuration or permission
inputs require a separately governed isolated qualification of the retained
image under the proposed boundary; this reuse command blocks until that proof
exists. A planning override cannot bypass compatibility validation.
