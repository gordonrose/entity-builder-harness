<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: deploy.script.operational-realization-gate.readme
  version: 1
  status: active
  layer: 04.deploy
  domain: deployment.realization
  disciplines:
  - architecture
  - security
  - sre
  kind: readme
  purpose: Map the source, boundary, inputs, and safe outputs of the Operational Realization Gate compiler.
  portability:
    class: reusable
    targets:
    - entity-builder
  used_by:
  - id: deploy.script.operational-realization-gate
    path: scripts/04.deploy/operational-realization-gate/script.py
-->
# Operational Realization Gate Compiler

## Source map

| File | Responsibility |
| --- | --- |
| `script.py` | Generic compiler for graph completeness, proof levels, gate order, lifecycle safety, normalized evidence, and provider leakage. It uses no provider SDK, CLI, resource type, or adapter import. |
| `script.sh` | Repository-root command wrapper. |
| `smoke-test.sh` | Deterministic positive and negative contract fixtures plus the core-boundary scan. |
| `fixtures/` | Safe, provider-neutral examples. They are tests of compiler behavior, not live target specifications. |

## Commands

```bash
npm run deployment:realization:validate -- --contract path/to/contract.yml
npm run deployment:realization:validate -- --contract path/to/contract.yml --facts path/to/normalized-facts.yml --change-summary path/to/normalized-change-summary.yml
npm run deployment:realization:validate -- --contract path/to/contract.yml --facts path/to/normalized-facts.yml --change-summary path/to/normalized-change-summary.yml --through execution-preflight
npm run deployment:realization:test
```

Use `--through execution-preflight` before a proposed controlled execution;
the compiler then requires passing evidence for every preceding gate. The
compiler emits only a stable result schema, contract ID, verdict, and safe
finding codes. It does not open a network connection or invoke a provider.

## Adapter boundary

A provider adapter is responsible for converting a provider inspection or plan
into one of the two normalized input documents. The compiler only accepts
generic component IDs, gate verdicts, and operation-class counts. Adapter code
must live outside this directory and must be tested independently.
