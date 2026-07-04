<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.docs.llm-workbench-acceptance-matrix
  version: 1
  status: active
  layer: 00.chat
  domain: portability
  disciplines:
  - agentic
  kind: doc
  purpose: Map llm-workbench public-beta invariants to enforcing artifacts and checks.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.standards.llm-workbench-public-beta-contract
    path: .agentic/00.chat/standards/llm-workbench-public-beta-contract.md
  - id: chat.script.upstream.validate-llm-workbench-portability.readme
    path: scripts/00.chat/upstream/validate-llm-workbench-portability/README.md
-->
# llm-workbench Acceptance Matrix

This matrix maps the public-beta contract to the artifacts that enforce it.

| Invariant | Primary Artifacts | Required Proof |
| --- | --- | --- |
| No durable chat classification | `chat-start.md`, `start-chat-session`, portability validator | Startup metadata has no whole-chat `layer`, `mode`, or `workflow` fields. |
| Standalone public export | Bootstrap planner, artifact metadata checker, portability validator | Generated public repo and installed target omit source-only trees/scripts and pass `check-headers --all`. |
| No source-specific generic gates | `prepare-chat-session-before-commit`, before-commit checklist, portability validator | Generic chat surfaces do not hard-code RAG/rulebook gates; optional gates use neutral hooks. |
| Provider-neutral transcript metrics | `record-chat-commit`, transcript scripts, startup templates | Missing transcript metrics are portable by default; Codex discovery is opt-in adapter behavior. |
| Provider-neutral cost metrics | `estimate-chat-cost`, `scripts/00.chat/metrics/data/`, record-commit smoke test | Default pricing is `portable-unpriced`; explicit profile overrides record cost. |
| Safe install/uninstall | Public install/uninstall templates, install smoke, portability validator | Dry run is read-only, apply preserves user files, uninstall removes only manifest-owned material. |
| Thin assistant adapters | Public adapter templates, install manifest, portability validator | Adapters route to chat-start and avoid provider-specific policy duplication. |
| CLI/code-assistant robustness | Dispatcher, startup JSON mode, portability validator | `chat:new -- --json` works; stripped executable bits do not break dispatch. |
| Temporary eval loop | Public-beta checklist, closeout evidence | Temporary evals fail first, pass after implementation, and are removed before closeout. |
| Documentation truthfulness | Public README/docs/templates | Public docs use the accepted standalone/provider-neutral claim and avoid universal-assistant overclaims. |

The permanent acceptance entrypoint is:

```bash
bash scripts/00.chat/upstream/validate-llm-workbench-portability/script.sh
```

Changes that discover a new edge case should add that edge case to the
portability validator or a focused smoke test before closeout.

Source-only public-export exclusions include `.agentic/agentic`, `.docs`,
`.scripts`, `.agentic/01.harness`, `.agentic/docs`, `.agentic/scripts`, and
`scripts/00.chat/classification`, plus maintainer-history ADR surfaces such as
`docs/00.chat/public-chat-workbench-adrs.md` and
`docs/harness/architecture/adrs/`. Public `scripts/01.harness` is limited to
portable validation and governed-runner helpers; source-maintenance migration,
taxonomy-generation, and rule-test scripts must not be exported or installed.
