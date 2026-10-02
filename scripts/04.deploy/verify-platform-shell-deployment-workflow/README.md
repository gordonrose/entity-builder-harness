<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.verify-platform-shell-deployment-workflow.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the static supply-chain gate for the Kanbien staging platform-shell deployment workflow.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.verify-platform-shell-deployment-workflow
  path: scripts/04.deploy/verify-platform-shell-deployment-workflow/script.sh
-->
# Verify Platform-Shell Deployment Workflow

`script.sh` is a read-only check of the GitHub Actions workflow that publishes
the Kanbien staging platform-shell image. It makes the intended supply-chain order
machine-checkable:

```text
publish immutable image
        ↓
wait for ECR to create the asynchronous scan record, then complete scan with zero critical and high findings
        ↓
generate SPDX SBOM
        ↓
attest provenance and the SBOM for that exact digest
        ↓
record the publication evidence for a separately reviewed deployment
```

The check also requires the narrowly scoped GitHub permissions used by the
attestation action. The real workflow publishes the signed provenance and SBOM
attestations beside the immutable ECR image and records their GitHub URLs in
the run summary. It does not upload a separate SBOM artifact or request broad
repository-write permission; the attested SBOM is the durable evidence.

This command does not call GitHub or AWS, build an image, or alter repository
files.

Run it with:

```bash
npm run platform:shell:deployment-workflow:check
```

This check guards the workflow shape. The workflow itself remains responsible
for evaluating the actual scan result, generating the SBOM, and creating the
signed attestations during an approved hosted publication.

The workflow verifies the locked compiler closure and pins the minimal non-root
image which becomes the final deployable artifact.
The scan gate evaluates the latter. A scan record can appear a few seconds
after an ECR push, so the workflow has a bounded five-minute wait for record
creation before using the AWS completion waiter. That is intentionally not a
retry of a failed scan: a completed scan with any critical or high finding still
blocks publication acceptance.


## Selected action and tool pins

Reviewed against official upstream Git refs and immutable source on 2026-09-30.
The validator requires these exact commits at their existing step names and
rejects tags, unreviewed commits, and additional action steps. The manual trigger,
main-only source check, staging environment, OIDC condition, permissions, scan
thresholds, normalized receipt uploads, and exact-digest attestation subjects
remain required. No hosted execution or publication is evidenced by this source
check.

| Existing major | Reviewed immutable commit and official source | Selected use |
| --- | --- | --- |
| `actions/checkout@v4` | [`11d5960a326750d5838078e36cf38b85af677262`](https://github.com/actions/checkout/commit/11d5960a326750d5838078e36cf38b85af677262); [action definition](https://github.com/actions/checkout/blob/11d5960a326750d5838078e36cf38b85af677262/action.yml) | Pinned in the workflow. |
| `actions/setup-node@v4` | [`49933ea5288caeca8642d1e84afbd3f7d6820020`](https://github.com/actions/setup-node/commit/49933ea5288caeca8642d1e84afbd3f7d6820020); [action definition](https://github.com/actions/setup-node/blob/49933ea5288caeca8642d1e84afbd3f7d6820020/action.yml) | Pinned in the workflow. |
| `actions/setup-python@v5` | [`a26af69be951a213d495a4c3e4e4022e16d87065`](https://github.com/actions/setup-python/commit/a26af69be951a213d495a4c3e4e4022e16d87065); [action definition](https://github.com/actions/setup-python/blob/a26af69be951a213d495a4c3e4e4022e16d87065/action.yml) | Pinned in the workflow. |
| `docker/setup-buildx-action@v3` | [`8d2750c68a42422c14e847fe6c8ac0403b4cbd6f`](https://github.com/docker/setup-buildx-action/commit/8d2750c68a42422c14e847fe6c8ac0403b4cbd6f); [action definition](https://github.com/docker/setup-buildx-action/blob/8d2750c68a42422c14e847fe6c8ac0403b4cbd6f/action.yml) | Pinned in the workflow. |
| `aws-actions/configure-aws-credentials@v4` | [`7474bc4690e29a8392af63c5b98e7449536d5c3a`](https://github.com/aws-actions/configure-aws-credentials/commit/7474bc4690e29a8392af63c5b98e7449536d5c3a); [action definition](https://github.com/aws-actions/configure-aws-credentials/blob/7474bc4690e29a8392af63c5b98e7449536d5c3a/action.yml) | Pinned in the workflow. |
| `aws-actions/amazon-ecr-login@v2` | [`03f1aad4c6c7ffd436567f42f9384779290529bd`](https://github.com/aws-actions/amazon-ecr-login/commit/03f1aad4c6c7ffd436567f42f9384779290529bd); [action definition](https://github.com/aws-actions/amazon-ecr-login/blob/03f1aad4c6c7ffd436567f42f9384779290529bd/action.yml) | Pinned in the workflow. |
| `anchore/sbom-action@v0` | [`e22c389904149dbc22b58101806040fa8d37a610`](https://github.com/anchore/sbom-action/commit/e22c389904149dbc22b58101806040fa8d37a610); [action definition](https://github.com/anchore/sbom-action/blob/e22c389904149dbc22b58101806040fa8d37a610/action.yml) | Direct verified Syft replaces this action; see below. |
| `actions/attest@v4` | [`1e69f48acb82d1966a394da916b4c1698aa569d6`](https://github.com/actions/attest/commit/1e69f48acb82d1966a394da916b4c1698aa569d6); [action definition](https://github.com/actions/attest/blob/1e69f48acb82d1966a394da916b4c1698aa569d6/action.yml) | Pinned in the workflow. |

`configure-aws-credentials@v4` is an annotated tag: the pin is its peeled commit,
not the tag-object ID. The previously reviewed `upload-artifact` v4.6.2 commit
`ea165f8d65b6e75b540449e92b4886f43607fa02` stays fixed for both receipt uploads.

The selected-source review found two executable acquisition defaults that an
action SHA alone would not fix:

- The [Buildx action download path](https://github.com/docker/setup-buildx-action/blob/8d2750c68a42422c14e847fe6c8ac0403b4cbd6f/src/main.ts)
  can select `latest`, while its container driver starts a separately acquired
  BuildKit image. The workflow now selects [Buildx v0.37.2](https://github.com/docker/buildx/releases/tag/v0.37.2)
  and official [BuildKit v0.33.1](https://github.com/moby/buildkit/releases/tag/v0.33.1)
  as `moby/buildkit@sha256:cec9f139f45e93c5c69c60f8b07cfad9f43f4ef6b6a6cd917527fea5ff2e3dea`.
  That digest was independently recomputed over the bytes returned by the
  [official registry manifest endpoint](https://registry-1.docker.io/v2/moby/buildkit/manifests/v0.33.1).
- The pinned [SBOM action installer path](https://github.com/anchore/sbom-action/blob/e22c389904149dbc22b58101806040fa8d37a610/src/github/SyftGithubAction.ts)
  downloads and executes `anchore/syft/main/install.sh`. Its fixed
  [default Syft version](https://github.com/anchore/sbom-action/blob/e22c389904149dbc22b58101806040fa8d37a610/src/SyftVersion.ts)
  does not pin that installer. The existing `Generate image SBOM` step therefore
  directly downloads the same Syft **1.42.3** Linux AMD64 release, verifies its
  archive before extraction and its binary before execution, checks its reported
  version, and scans the previously pulled immutable Docker image. No mutable
  installer, action-cache fallback, release upload, or extra artifact uploader is
  involved; the SPDX file and both existing attestations are preserved.

The [official Syft release checksums](https://github.com/anchore/syft/releases/download/v1.42.3/syft_1.42.3_checksums.txt)
name archive SHA256
`0d6be741479eddd2c8644a288990c04f3df0d609bbc1599a005532a9dff63509` for
[syft_1.42.3_linux_amd64.tar.gz](https://github.com/anchore/syft/releases/download/v1.42.3/syft_1.42.3_linux_amd64.tar.gz).
Review independently verified those archive bytes and derived the contained
`syft` binary SHA256
`6c1eb5c6f15c177fa3dd727ee186c61a660a3939a4e1dc1bc4b3e00eafec098e`.
The shell accepts only a digest image reference and stops before scanning on
archive, binary, or version mismatch. Update checks are disabled.

Node and Python inputs retain exact versions 22.23.3 and 3.14.4. The other selected
actions use their checked-in JavaScript entrypoints; this bounded review found
no comparable selected-path remote installer. This is not an attestation of the
hosted runner image, every transitive dependency, or a completed hosted run.
Buildx selects a fixed release version; this amendment does not independently
content-lock that action's release downloader. Future tool or action updates need
source review and the focused guard tests.

Focused verification:

```bash
python3 -B scripts/04.deploy/operational-realization-gate/test_qualified_publication_workflow.py -v
```

The tests include static gate regressions and an offline benign Syft stand-in
that exercises archive, executable, version, image-input, and SPDX-output checks.
They execute neither downloaded Syft nor a hosted job, and provide no live
scan, signature, publication, or deployment evidence.


Qualification checks the checkout before and after the build; publication repeats
those checks before verifying the handoff and pushing. HEAD must equal
`GITHUB_SHA`, both index and worktree diffs must be empty, and no nonignored
untracked path may exist. NUL-separated path output also rejects unusual filenames
without printing source names. Ignored caches remain allowed. Disposable Git
fixtures verify clean/ignored acceptance and staged, unstaged, untracked,
unusual-name, and wrong-HEAD refusal at both entry boundaries.

If the local qualification fails, the workflow writes only its normalized,
redacted JSON result to the hosted log before stopping. It neither uploads the
scratch directory nor exposes raw container, package, or provider output.

The runner installs the documented bubblewrap prerequisite before obtaining AWS
credentials. The local qualifier still requires its existing namespace probe;
installation does not permit host execution or a relaxed isolation policy.
A missing or non-executable sandbox and fixed locked-toolchain failures retain
safe diagnostic codes. Raw paths, exception messages and tool output stay private.
