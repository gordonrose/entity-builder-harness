<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.bootstrap.llm-workbench-template.readme
  version: 1
  status: active
  layer: 00.chat
  domain: bootstrap
  disciplines:
  - agentic
  kind: doc
  purpose: Explain the public llm-workbench starter template files.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.bootstrap-chat-workbench-repo
    path: .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
  - id: chat.chat-workbench-public-repo-readiness
    path: docs/00.chat/chat-workbench-public-repo-readiness.md
-->
# llm-workbench Template

This folder contains source templates for the first public `llm-workbench`
repo shell.

The files under `root/` are intended to become files at the root of the public
repo after the bootstrap workflow transforms and copies them. They use a
`.template` suffix in this source repo so the template can describe public files
without pretending those files already exist here.

## How To Use

The bootstrap workflow should:

- inspect the source repo and upstream repo before writing
- copy canonical harness files listed in the readiness manifest
- transform the files in `root/` by removing the `.template` suffix
- preserve the relative paths below `root/`
- run the public install smoke test in the upstream repo before commit

The template is not a substitute for the bootstrap workflow. It is starter
material for the public product shell.

## Template Paths

- `root/AGENTS.md.template`
- `root/CONTRIBUTING.md.template`
- `root/LICENSE.template`
- `root/package.json.template`
- `root/README.md.template`
- `root/SECURITY.md.template`
- `root/.gitignore.template`
- `root/docs/concepts.md.template`
- `root/docs/install.md.template`
- `root/docs/workflows.md.template`
- `root/docs/adapting-to-your-repo.md.template`
- `root/examples/minimal-repo/README.md.template`
- `root/scripts/install.sh.template`
- `root/scripts/uninstall.sh.template`
- `root/tests/smoke-test-install.sh.template`
