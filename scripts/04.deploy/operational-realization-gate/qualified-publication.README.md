<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.readme.qualified-image-publication
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: capability-readme
purpose: Explain exact same-host qualified-image publication, its receipt bindings and retained authority boundaries.
portability: {class: internal, targets: [kanbien-staging]}
used_by:
- id: deploy.script.qualified-image-publication
  path: scripts/04.deploy/operational-realization-gate/qualified_publication.py
-->
# Publish the image that was qualified

The existing staging image workflow can qualify one final product image and
publish that same image from the same Docker daemon. It uses the existing
locked compiler, verified payload, final-image inventory, health checks,
shutdown and cleanup. The legacy Docker source-build path is not used by this
workflow: U16's direct generator now needs the complete source/schema/Python
preparation environment, which the legacy Docker build context does not supply.

The local qualification wrapper accepts one optional output directory:

```bash
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh --qualify-local \
  --source-root . --scratch-root /persistent/owned-scratch \
  --package-cache /persistent/verified-packages \
  --publication-directory /persistent/owned-scratch/new-handoff
```

The publication directory must be a new direct child of the selected persistent
scratch directory. Existing files/directories and links are refused. The wrapper
writes the complete unchanged `local-container-result/v1` and a closed
`qualified-image-handoff/v1` there, with private permissions. Runtime containers
must have verified cleanup. The already-built image remains in the daemon,
consistent with prior local qualification; this option does not retain running
containers or export a portable image archive.

The handoff records the actual BuildKit manifest and configuration digests
separately from Docker's inspectable image ID. Classic and containerd image
stores can expose different members of that verified tuple. No mutable tag is
used to select the image for qualification. The product build now carries the
source-revision labels already required by the staging publisher.

```bash
python3 -I -B scripts/04.deploy/operational-realization-gate/qualified_publication.py \
  --source-root . --scratch-root /persistent/owned-scratch \
  --publication-directory /persistent/owned-scratch/new-handoff
```

This checks the full container receipt, current source/commit/helper/lock/profile
bindings, exact current daemon image settings and its payload bytes. It emits
safe normalized metadata. It never builds, tags, pushes, logs in, calls AWS,
contacts GitHub, or grants release/operation authority. Payload inspection uses
the existing owned isolated container inventory operation and cleanup.

The existing workflow calls this check again before tagging the exact immutable
image ID. An existing tag may be reused only when its registry digest equals the
newly qualified manifest; it cannot skip fresh qualification. Following a push,
the workflow requires the registry digest to equal that qualified manifest and
retrieves one ECR BatchGetImage response. The optional `--published-image` input
checks the response's registry/repository/digest and hashes its exact manifest
string bytes, binding the manifest's configuration descriptor to the recorded
BuildKit configuration digest. It does not hash a reserialized manifest or a
newline-terminated AWS CLI text rendering. An index, changed representation or
different manifest fails; no digest substitution or rebuild fallback exists.

The host workflow uses the supported exact Node/Python versions and the complete
hash-locked Python requirements. It retains main-only source, the staging
environment, existing conditional OIDC role, explicit publication toggle,
linux/amd64, zero CRITICAL/HIGH ECR findings, digest-bound SBOM and existing
GitHub provenance/SBOM attestations. The target's build strategy changes to
`locked-toolchain-verified-payload`; runtime, scan severity and provider policy
remain unchanged.

These are unsigned local handoff observations inside a trusted workflow run,
not authenticated release decisions or authority tokens. The existing generic
artifact-admission contract still has separate producer/policy obligations;
this bridge does not fabricate build materials, scanner versions, scan age,
trusted-root freshness, complete SBOM coverage or a signed scan predicate.

No cross-host image transfer is implemented. Running the hosted workflow,
publishing an image, or changing hosted settings remains separately authorized
external work. Offline/mock tests establish source behavior; a first hosted run
must prove daemon compatibility, namespace support, registry manifest stability
and actual existing scan/attestation behavior. Missing prerequisites fail closed.

Focused tests use the existing closed synthetic container fixture and synthetic
Docker/registry responses, with no Docker or cloud execution. They cover current
source drift, altered receipt/configuration/payload, unknown fields, authority
claims, link/overwrite refusal, manifest/configuration identity differences,
registry substitution, preserved workflow controls and public safe errors.

## Hosted receipt retention

The workflow uploads two explicitly named normalized qualification files after
qualification succeeds: `container-result.json` and `handoff.json`. After exact
registry verification succeeds, it separately uploads `publication-check.json`.
Both uploads happen before later scan/attestation steps, preserving verified
observations if those later steps fail. A failed producer does not upload its
partial files. Raw ECR responses, credentials, build context and diagnostics are
not upload paths; no directory or wildcard is selected.

The seven-day CI retention is explicit, hidden files are excluded, missing files
fail the upload, and overwrite is disabled. Names include workflow run and retry
identities. This short CI retention is not a production journal/evidence-retention
policy. Summary links identify the retained artifacts. Expiration or deletion of
the artifact/run removes access; users must preserve required long-term release
evidence through the later governed store.

The new action is pinned to official `actions/upload-artifact` v4.6.2 commit
`ea165f8d65b6e75b540449e92b4886f43607fa02`. Its
[official release](https://github.com/actions/upload-artifact/releases/tag/v4.6.2),
[immutable commit](https://github.com/actions/upload-artifact/commit/ea165f8d65b6e75b540449e92b4886f43607fa02)
and [input contract](https://github.com/actions/upload-artifact/blob/ea165f8d65b6e75b540449e92b4886f43607fa02/action.yml)
were inspected for retention, hidden-file, missing-file and overwrite behavior.
This source change does not invoke the action or alter hosted configuration.
