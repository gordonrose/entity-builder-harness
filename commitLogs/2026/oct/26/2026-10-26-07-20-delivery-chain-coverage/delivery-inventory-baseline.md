# Baseline delivery inventory

Revision: `3db60130493a1ad7af4bbe5c6f0adf9715e6b96c`. Method: current hardened independent census applied to immutable baseline source snapshot.

Baseline: **390 entrypoints, 3 declared requirement scopes, 83 findings**. Current report: **419 entrypoints, 6 scopes, 0 gaps**.

The same current census inspected unchanged Git baseline bytes. This does not claim the hardened checker existed or ran at that revision. Baseline findings are informational historical differences, not failures of current repaired inputs.

Two of the 83 findings are explicit nested-inspector input errors: the baseline acceptance API lacks the current `probe_commands` keyword. Those acceptance checks are unavailable in this retrospective census; their findings do not prove the old gate failed. The remaining 81 findings are the unchanged census/contract findings. No newer acceptance implementation was substituted into the snapshot.

| Baseline finding | Count |
| --- | ---: |
| `acceptance-route-validator-invalid` | 2 |
| `delivery-command-unbound` | 2 |
| `delivery-consumer-unbound` | 52 |
| `delivery-entrypoint-unregistered` | 2 |
| `requirement-proof-command-unmapped` | 16 |
| `requirement-proof-missing` | 5 |
| `runtime-configuration-validator-missing` | 2 |
| `runtime-requirements-missing` | 2 |

| Entrypoint kind | Baseline | Current |
| --- | ---: | ---: |
| ci-workflow | 8 | 9 |
| command | 174 | 184 |
| image-definition | 5 | 5 |
| package-command | 77 | 77 |
| provider-binding | 2 | 2 |
| provider-template | 27 | 27 |
| regression-command | 72 | 86 |
| runnable-program | 20 | 20 |
| scope | 3 | 6 |
| target | 2 | 3 |

Input digest: `bc732e8c41105d26d89c8306998daed8efb73ffd86f23fcfa907d60be9bc0680`. Git tree: `155530fe41fce05ab131168187d6af3654563d55`. All 2154 archived tracked blobs and Git file modes were verified before inspection. The disposable source snapshot was cleaned.

Full route, path, registration, classification, input-hash and finding details: [delivery-inventory-baseline.json](delivery-inventory-baseline.json). Current comparison: [delivery-inventory.json](delivery-inventory.json).
