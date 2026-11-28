<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.image.environment-session-controller.readme
version: 1
status: draft
created_on: "2026-11-28"
updated_on: "2026-11-28"
layer: 04.deploy
domain: deployment.environment-lifecycle
disciplines: [architecture, security, sre]
kind: readme
purpose: Explain the controller image build boundary and distinguish package proof from live cleanup proof.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: infra.image.environment-session-controller.contract
  path: infra/04.deploy/03.product/image/environment-session-controller/image-contract.yml
-->
# Temporary-session controller image

Cleanup must still work if the developer's terminal disappears. This image
packages the fixed controller code for that independent worker; it does not
contain an application server or grant permission to remove existing services.

[Dockerfile](Dockerfile) combines digest-pinned Python and AWS CLI images,
installs hash-pinned [requirements](requirements.txt), and runs the controller
under user/group `65532:65532` in `/opt/controller`. It exposes no port or HTTP
health endpoint: command exit status and the controller's bounded reports carry
the result. Session input is data, not executable Python or a replacement image.

The [image contract](image-contract.yml) lists the committed source selections.
The builder streams their Git archive as a repository-root-shaped context;
[Dockerfile.dockerignore](Dockerfile.dockerignore) additionally excludes local
credentials, editor state, logs, caches and temporary output. Do not build from
an unrestricted working-directory context or copy credentials into this image.

From a clean committed checkout with Docker available, the local build command is:

```bash
bash scripts/04.deploy/lifecycle/40-package/build-environment-session-controller-image/script.sh --tag kanbien-environment-session-controller:qualification --receipt /tmp/controller-qualified-image.json
```

The builder checks the installed AWS CLI and runs controller fixtures in the
finished image with networking disabled and a read-only filesystem. It writes
the qualification receipt only after those checks pass; missing Docker blocks
the build. This command does not publish or deploy.

The protected [publication workflow](../../../../../.github/workflows/publish-kanbien-core-platform-environment-session-controller.yml)
additionally requires an immutable registry digest, clean scan, software
inventory and signed provenance before issuing package evidence. A task-branch
push only registers the workflow; publishing requires manual dispatch and the
existing environment approval. Package evidence is not proof that independent
expiry or live cleanup works. The [delivery plan](../../../../../docs/04.deploy/plans/disposable-test-environments.md)
tracks those pending rehearsals and existing-resource retirement separately.
