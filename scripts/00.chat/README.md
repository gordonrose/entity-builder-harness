<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.readme
  version: 1
  status: active
  layer: 00.chat
  domain: governance
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain the canonical script layout for the chat lifecycle layer.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.readme
    path: .agentic/00.chat/README.md
  - id: harness.architecture.adr.0017-organize-scripts-by-owner-domain-and-capability
    path: docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
-->
# 00.chat Scripts

This tree contains the canonical executable surface for the chat lifecycle
layer. It is the script side of `.agentic/00.chat/`: workflows describe the
governed process, and scripts provide deterministic checks, commands, reports,
startup, recovery, and bookkeeping.

Each capability lives in a folder:

```txt
scripts/00.chat/<domain>/<capability>/
```

The common shape is:

- `script.sh` or `script.js`: the canonical implementation
- `smoke-test.sh`: focused behavior proof, when the capability needs one
- `README.md`: human onboarding for what the capability owns

Public users should usually enter through `package.json` `chat:*` scripts.
Workflow and gate authors should point to the canonical paths in this tree.

Retired compatibility paths under `scripts/shared/chat/` and
`scripts/shared/git/` should not be reintroduced. Historical documentation may
mention them as previous locations, but live instructions should point here.

