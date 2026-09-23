<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.run-platform-shell-rate-limit-smoke.readme
version: 2
status: active
layer: 04.deploy
domain: runtime.operations
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the bounded aggregate-only staging rate-limit proof.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.run-platform-shell-rate-limit-smoke
  path: scripts/04.deploy/run-platform-shell-rate-limit-smoke/script.sh
-->
# Platform-shell rate-limit smoke

`script.py` has two deliberately finite modes:

- `--validate` proves the target profile still selects only the fixed public
  `GET /livez` proof and its declared limit plus one request bound.
- `--execute` waits for the next fixed-window boundary, makes at most 121
  sequential liveness requests, stops at the first `429`, and reports only
  aggregate counts, final status, and elapsed time. If the fixed window rolls
  over during the proof, it returns an explicit inconclusive result rather
  than treating a second window as a failed limit.

It sends no credential, does not read a response body, and does not call the
protected smoke route. The latter is important: a rate-limit proof is boundary
evidence, not an eligible protected-read SLO observation.

Running `--execute` changes only the existing short-lived rate-limit counter
records. It remains a governed live operation and needs current-chat approval.
