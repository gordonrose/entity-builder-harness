<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: deploy.fixtures.artifact-admission.readme
  version: 1
  status: active
  layer: 04.deploy
  domain: deployment.realization
  disciplines: [architecture, security, sre]
  kind: capability-readme
  purpose: Document real public signature fixtures, pinned trust material, offline admission and remaining producer obligations.
  portability: {class: reusable, targets: [entity-builder]}
  used_by:
  - id: deploy.script.artifact-verifier-conformance
    path: scripts/04.deploy/operational-realization-gate/artifact_verifier_conformance.py
-->
# Artifact admission and real signature conformance

The existing realization gate verifies local attestation bundles using GitHub CLI
2.101.0, whose archive and executable hashes are source-locked. The real GitHub and
Sigstore public trusted roots are checked into this directory, SHA-256 locked,
and supplied explicitly. The verifier runs in a private filesystem and network
namespace with an empty environment, no GitHub/AWS credentials and bounded time
and output. It never retrieves a bundle, image, or root during verification.

Explicit public tool acquisition, outside the checkout:

```bash
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --artifact-verifier-acquire --verifier-cache /absolute/private/verifier-cache
```

This command downloads only the exact locked public archive, verifies its digest
and the selected binary bytes, and refuses to overwrite an existing invalid
cache entry. Acquisition is separate from offline verification. Linux amd64 and
Bubblewrap user/network namespace support are required. The maintained verifier
performs certificate, signature and trusted timestamp verification; this repo
implements no signature algorithm.

```bash
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --artifact-verifier-conformance --verifier-cache /absolute/private/verifier-cache
```

Conformance verifies one genuinely signed upstream wheel without executing it.
Eleven real negative cases reject wrong identity/ref/workflow/source/predicate/
subject and modified artifact/signature/payload/certificate/timestamp. This
historic upstream fixture establishes verifier behavior, not a current product
build, complete supply-chain admission, deployment eligibility, or AWS authority.
All public output is bounded safe metadata and digests; certificates, raw bundle
payloads and tool diagnostics are not copied into result output.

The fixture wheel and bundle come unchanged from the MIT-licensed official CLI
repository at the immutable revision in `sources.json`. `LICENSE.cli` preserves
the upstream license. File hashes and original names are recorded there. The
production trusted-root file was acquired using the locked CLI's built-in TUF
verification in a credential-free environment; its observation time and digest
are recorded in `artifact-verifier.lock.json`. A root snapshot cannot detect
subsequent revocation. Production policy must explicitly bound its age, and a
reviewed refresh updates its bytes, digest and acquisition timestamp together.

Official implementation references:

- [Offline verification](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/verify-attestations-offline)
- [Verifier command](https://cli.github.com/manual/gh_attestation_verify)
- [Trusted-root acquisition](https://cli.github.com/manual/gh_attestation_trusted-root)
- [Pinned upstream fixture source](https://github.com/cli/cli/tree/0cf1092493af067646fc5f3db9421c6a6ec9c938/pkg/cmd/attestation/test/data)

## Production-stage evidence interface

```bash
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --artifact-admission --verifier-cache /absolute/private/verifier-cache \
  --policy /absolute/reviewed-policy.json \
  --artifact /absolute/exact-oci-manifest.json \
  --image-config /absolute/exact-oci-config.json \
  --provenance-bundle /absolute/provenance.bundle.json \
  --sbom-bundle /absolute/sbom.bundle.json \
  --scan-bundle /absolute/scan.bundle.json
```

`--artifact` means exact single-platform OCI/Docker image **manifest bytes**, not
an image archive, tag, local Docker configuration ID or image-index descriptor.
The exact configuration bytes must match the manifest's digest and size and
establish Linux amd64. Layer descriptor shape is checked; this consumer does not
independently inspect every layer's contents. Existing exact-container proofs
and later registry publication bindings remain separate required evidence.

The closed policy fixes the existing staging repository, main branch, workflow,
registry image name and platform. It requires the current reviewed source SHA,
manifest digest, exact build/runtime base digests, accepted scanner version,
scan freshness and trusted-root freshness. Unknown scanner version/freshness
values are `null` and block before signature verification. No exception pathway
is silently introduced. CRITICAL/HIGH and undefined-severity findings block.

Each of the three bundles must contain one signed statement from that exact
repository/ref/workflow/source identity, for the exact manifest subject. A
signed provenance statement must include only the actual selected source and exact
base-image materials; desired policy pins are not evidence of observed build materials.
The SPDX 2.3 statement must contain a nonempty, internally identified package
list. This checks signed SBOM binding and basic shape, not independently complete
component enumeration. The signed scan predicate binds source, subject and bases
and requires completed, fresh scan/database timestamps and governed scanner
identity/version. The normalized database timestamp describes the snapshot used
by that scan, and cannot be later than scan completion. An AWS adapter must
establish this meaning from provider facts; the current ECR field alone is not
assumed to prove that relationship. The scan predicate contract is
`artifact-scan-predicate/v1`, under predicate type
`https://entity-builder.dev/release-control/artifact-scan/v1`.

Success means those specific authenticated evidence obligations passed. Every
result still has `authorized: false`, blocked release/operation authority and
blocked overall qualification. All three signed inputs are freshly verified on
every invocation; no preverified-result file, arbitrary executable, custom trust
root or alternate source-root override exists. If source/schema loading fails,
a distinct fixed `artifact-admission-error/v1` rejection avoids depending on the
failed loader and does not masquerade as a complete admission result.

The current publisher produces provenance and SBOM attestations, but its generic
provenance does not establish actual base-image materials and its ECR scan is not
a signed scan predicate. ECR BASIC does not expose a scanner engine version in
the currently consumed response. This source unit does not fabricate any of
those facts or modify publication. Missing producer evidence and governed
production version/freshness policy remain explicit blockers. The next producer
unit must bind real build materials and authenticated scan observations before
hosted qualification can establish a product admission pass.

Policy tests use synthetic authenticated-statement doubles to exercise semantic
rules. They are separate from the real signed-fixture conformance described
above. Tests must not be described as three successful production attestations.
