<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plan.release-control-local-container-review
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: plan
purpose: Record exact local image construction and server health evidence while preserving separate pending bootstrap and target obligations.
portability: {class: source-only, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->
# Exact Local Container Review — 2026-09-29

The eighth delivery unit is complete within its selected local image boundary.
The existing build and smoke wrappers now construct an image from a fresh locked
compiler/generator payload, check every application file inside that image, and
exercise its default server command under restricted local conditions. The same
image passes liveness, readiness, graceful shutdown and owned-container cleanup.

The [full normalized result](local-container-result.json) is the exact successful
public-wrapper output. The [verification summary](verification-summary.json)
records its file hash, identities, versions, counts and validation-log hash.
These are unsigned local observations. They do not grant release eligibility,
operation authorization, source closure or full release qualification.

## Acceptance

| Check | Exact result |
| --- | --- |
| Canonical clean-environment validation | Exit 0; **933 tests in 26 suites** |
| Legacy smoke and provider/network core boundaries | Passed |
| Clean validation metadata | 41 files passed |
| Full public qualification wrapper | Exit 0; fresh image compiler, generator, construction and runtime passed |
| Application payload inside exact image | 3,902 files; 19,405,615 bytes; all paths, sizes and hashes matched |
| Production package closure | 57 packages; retained and 3 excluded dependency files reconcile to the verified dependency identity |
| Liveness and readiness | Both HTTP 200; expected `live` and `ready` bodies |
| Shutdown | SIGTERM; exit 0; no out-of-memory termination |
| Temporary test containers | Owned cleanup verified |
| Profile inventory | 14 obligations: 1 local health passed, 13 pending |

The 256 added tests cover engine boundaries (63), verified payload preparation
(41), declared profile discovery (56), receipt contracts and cross-bindings (56),
and public CLI/authority behavior (40). Negative tests include modified or extra
payload files, incorrect dependency membership, altered commands and settings,
mismatched image/build metadata, skipped health checks, cleanup failure, unsafe
arguments and attempts to claim target qualification or release authority.
The prior 33 real-compiler fixture tests were not rerun in this unit and are not
included in the 933 count; this unit did perform a fresh genuine image build.

The accepted image is `sha256:5c4f1e9164a260bf26169a19957a6bec6d19c52a2c20fc9602d519bb813b891d`.
The payload identity is `sha256:6852df732e40891de3268577d5b36582d1620c424bd1b18a4ea64863d2901735` and the result identity is
`sha256:0194119d38fc994e060f681de8b2c0da0ecc5884a99b52a9499d2b29759d14b7`.
The receipt records the pre-checkpoint repository HEAD as a label; the nested
source digest and runner digest identify the actual verified source and helper
bytes, including this unit's then-uncommitted implementation. Committing the
receipt does not change those historical bindings or qualify a later rebuild.

## Construction and execution boundary

Two closed versioned schemas, an immutable runtime lock, payload/engine/profile
helpers, synthetic fixtures and the new tests extend the existing realization
gate. Existing image wrappers expose `--qualify-local` as an explicit first
argument. They do not accept an arbitrary image, command or saved success receipt.

The shared Dockerfile retains its compatible legacy build path and adds a
verified-payload path to the same final runtime recipe. The new context contains
only the verified payload, exact recipe and separately bound public trust
certificate. No application source or TypeScript files are used as a runtime
fallback. The compiler remains Node **22.23.3**, npm **10.9.9**, TypeScript
**5.9.3**; the immutable runtime base contains Node **v22.22.0**, observed from
the tested image. Those two Node versions are deliberately recorded separately.
The public base manifest and configuration digests are in the lock and receipt.

Build steps have networking disabled and use the pre-acquired base. This does
not guarantee that the Docker/BuildKit daemon makes no registry metadata calls.
Docker client/server **29.5.2** were observed; the host and engine are not a fully
pinned build toolchain. The runner binds BuildKit's configuration and manifest
identities before inspecting an immutable image ID, without a mutable tag fallback.

Runtime containers use a local daemon with an explicit clean client environment,
nonroot execution, a read-only filesystem, private temporary space, no published
ports or host mounts, no external network, no capabilities and bounded CPU,
memory, process count and timeouts. Health probes execute inside that isolated
container. The runner verifies ownership before cleanup and verifies absence
afterward. Private raw diagnostics stay outside Git; only bounded normalized
observations are saved here.

Every declared selected task and sidecar is still inventoried independently.
The nine product task-container obligations and four external sidecars remain
pending, including the five finite PostgreSQL tasks. Local default-server health
does not prove database bootstrap, migration, worker, relay, restore, target
server settings or sidecar behavior. It does not establish AWS IAM, identities,
secrets, routing, service wiring or live database state.

## Reproduction

Use persistent Linux scratch storage outside the checkout. Acquire the verified
package cache with the existing locked-build wrapper if it is not already
available. Public base acquisition is an explicit separate mode:

```bash
bash scripts/04.deploy/build-platform-shell-image/script.sh --qualify-local \
  --source-root . --scratch-root /persistent/path/container-scratch --acquire-base
bash scripts/04.deploy/smoke-test-platform-shell-image/script.sh --qualify-local \
  --source-root . --scratch-root /persistent/path/container-scratch \
  --package-cache /persistent/path/build-package-cache
TMPDIR=/persistent/path/container-scratch \
  bash scripts/04.deploy/operational-realization-gate/verify-clean-environment.sh \
  --python /usr/bin/python3
```

The accepted run used the existing verified recovery package cache and persistent
`iaas-release-control-eighth` scratch beside this worktree. The local image remains
available; ephemeral test containers were removed. No image was pushed or
published. The existing GitHub workflow still follows its legacy build route
and cannot claim this qualification. Future adoption must promote the exact
qualified image instead of rebuilding it and borrowing an earlier receipt.

## Repairs and next delivery unit

The first image attempt failed because a certificate copy still referenced the
legacy build stage. Copying the same public certificate directly from the
isolated context removed that dependency. The next attempt exposed Docker's
configuration-ID versus manifest-ID lookup distinction. The engine now checks
bounded BuildKit metadata and binds both identities before immutable lookup;
nine added regression tests cover malformed and inconsistent metadata. A fresh
complete public-wrapper rerun then passed. Failed attempts are not acceptance
proof. Transient public registry failures needed bounded retries, with no
host, Docker, proxy or DNS configuration changes.

Next, qualify the packaged finite commands separately against disposable
dependencies, retaining distinct startup and bootstrap evidence. Later AWS
preflight and controlled target execution must establish the AWS-specific
identity, secrets, network and initialization facts. PostgreSQL Stage 6 remains
paused. First hosted source validation awaits separately approved publication.
Wider source/action adoption, authenticated admission, durable operation controls
and provider adapters/stores remain open. No local stop condition exists.

Independent read-only review validated the accepted receipt against fresh source,
runner, schema, lock, certificate, generator, profile and production inventories.
The common consumer rejected it for all three purposes. The reviewer independently
counted 933 passing tests in 26 suites and found no blocker within this scope.
Receipt file SHA-256: `a4fd917cd2ca4ed8a50f738ec23356f0020acb311652d4a823084f83203385a8`.
