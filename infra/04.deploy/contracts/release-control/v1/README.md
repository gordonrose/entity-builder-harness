<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.readme.release-control-contracts.v1
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: readme
purpose: Explain versioned source release and acceptance matrix schema composition.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.script.operational-realization-release-compiler
  path: scripts/04.deploy/operational-realization-gate/release_compiler.py
-->
# Release contracts v1

These are YAML-encoded JSON Schemas using Draft 2020-12. The existing
[Operational Realization Gate](../../../../../scripts/04.deploy/operational-realization-gate/README.md#source-release-compilation)
loads and validates both schemas, then checks immutable bindings and graph
references against its existing realization contract.

- `release-definition.schema.yml` requires immutable revisions, the complete
  artifact and operation bindings, and a versioned acceptance matrix.
- `acceptance-matrix.schema.yml` defines the exact seventeen ordered gates and
  every row's owner, operation, evidence, invalidation, failure, recovery,
  cleanup and verdict fields.

Validation of just the release schema is insufficient: its matrix envelope
deliberately delegates the row contract to the standalone matrix schema. The
public compiler applies both plus semantic checks; generic JSON Schema success
is not compilation, evidence acceptance, or permission to operate a target.

All object shapes are closed. Values are symbolic IDs, immutable digests,
enumerated states and bounded numbers. No credentials, endpoints, raw responses,
request bodies or free-text overrides belong in these contracts.

Only v1 is supported. Unknown versions and remote schema references fail closed.
Introduce a new version for incompatible changes, with explicit migration and
positive/negative fixtures; never silently upgrade an input or reinterpret a
previous compiled release. Loaded schema digests participate in the immutable
compiled release identity. The release compiler accepts only unstarted rows
and rejects all submitted not-applicable claims. Source coverage generates
separate scoped obligations; evidence admission remains a later unit.

Independent source coverage loads three additional closed schemas:

- `source-inventory.schema.yml`: collector revision, fixed scope, safe paths,
  content hashes, typed observations with parent identities, and finding codes.
- `source-composition.schema.yml`: immutable artifact declarations, individual
  operations and profiles, observation bindings and resource ownership/effects.
- `source-adoption-ledger.schema.yml`: one current source entry per path,
  reviewed disposition, owner and any temporary compatibility deadline/profile.

The public coverage command always rediscovers source. The internal API accepts
collector output for testing, not as a trust boundary for untrusted evidence.
Canonical inventory hashing excludes only its own `inventory_digest` field.
Coverage identity includes inventory, composition, ledger, schema digests, the
coverage rule implementation hash and evaluation date. These source bindings
cannot prove a real artifact, authority, caller exclusion or successful gate.

The third source unit adds:

- `source-finding-triage.schema.yml`: an exact current assignment for each
  source/code finding, bound to collector/policy/source identity and always open.
- `caller-inventory.schema.yml`: independently discovered workflow subjects,
  source bytes, invocation edges and unresolved boundaries.
- `source-caller-review.schema.yml`: current subject-to-operation/profile/owner
  assignments and complete edge acknowledgment. Generated reviews remain pending.

Triage completion and caller accounting are distinct from coverage or execution
qualification. The canonical gate always recollects source for validation; saved
graphs are review artifacts, never trusted public evidence input. None of these
contracts admits runtime success, exemptions or mutation authority.

The fourth source unit adds `source-result-consumption.schema.yml`. It defines
a closed decision for consuming a successful source result after fresh local
recomputation. Its only accepted purpose is `source-analysis`; release
eligibility and operation authorization remain blocked in every decision.
The decision binds its schema, consumer policy and accepted source-result
digest, and copies only recognized scope/verdict identifiers. It is not runtime
evidence admission, a signature or an execution permit. An unavailable or
invalid schema yields a safe rejection without claiming contract validation.

The fifth source unit adds:

- `source-operation-inventory.schema.yml`: selected script/action/tool subjects,
  incoming invocation identities, independent source observations and dependency
  edges, bound to current caller graph/source/collector identities.
- `source-operation-contracts.schema.yml`: an exact per-subject review of those
  observations and argument variants, consistent with the caller profile and
  carrying mandatory completion, failure, recovery and evidence requirements.

Source-contract completion keeps semantic closure and qualification blocked.
The existing consumption contract additionally recognizes this producer for
fresh source analysis only. Runtime admission and the full seventeen-stage
matrix remain separate requirements; no source declaration can assert a passed
gate or grant an exception.

## Build accounting contracts

- `source-build-inventory.schema.yml` defines independent workspace/compiler/
  import observations and bounded expected output membership. All builds remain
  subject to exact compiler/artifact evidence.
- `source-build-artifact.schema.yml` defines read-only local file accounting,
  including actual file digests, source mappings, generated package forwarding
  targets and runtime-test membership. Accounting completion never grants
  authority or establishes provenance/runtime qualification.

The existing realization gate loads these closed versioned schemas before
returning normal results. No remote schema references or saved build inventories
are accepted by its public build mode. Optional expected digests detect changed
observations. These outputs are not supported evidence-admission producers and
cannot be consumed as release eligibility or operation authorization.
