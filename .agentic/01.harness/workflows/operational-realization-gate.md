<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: harness.workflow.operational-realization-gate
  version: 1
  status: active
  layer: 01.harness
  domain: deployment.realization
  disciplines:
  - architecture
  - security
  - sre
  kind: workflow
  purpose: Govern complete provider-neutral operational realization before a live capability operation.
  portability:
    class: reusable
    targets:
    - entity-builder
  used_by:
  - id: harness.standard.operational-realization-gate
    path: .agentic/01.harness/standards/operational-realization-gate.md
-->
# Operational Realization Workflow

## Use When

Use this workflow before a capability first reaches a live target, before a
new execution path, migration, queue consumer, or recovery path is introduced,
and whenever its artifact, identity, configuration shape, connection, engine
semantics, or mutation shape changes.

## Inputs

- a versioned provider-neutral realization contract;
- safe source and artifact evidence;
- normalized facts produced by a separately governed provider adapter;
- a reviewed change summary, where a provider mutation is proposed; and
- current target approval under the owning provider execution workflow.

## Procedure

1. Copy the template and declare the complete execution graph. Do not use an
   external resource name, provider type, credential value, endpoint, or raw
   provider response in the contract.
2. Use `npm run deployment:realization:validate -- --contract <path>` to
   reject missing graph edges, unsafe lifecycle/retry paths, insufficient proof
   requirements, unknown assumptions, and provider leakage.
3. Collect safe evidence in order: source, artifact, semantic integration,
   live-read, change-set, execution preflight. A provider adapter may collect
   target facts, but it must write normalized facts only.
4. Re-run the compiler with normalized facts. It must show all prerequisite
   gate evidence passed before a provider mutation is proposed.
5. Obtain the separate target-specific authorization required to execute the
   reviewed mutation. This generic workflow never grants cloud authority.
6. Run one labelled controlled execution. Record safe terminal evidence.
7. If it reaches a terminal failure or stop, do not replay it. Define and
   review a new recovery label and use the `recovery` gate. A recovery is never
   a substitute for omitted preflight evidence.
8. Record the final safe evidence location in the capability plan and update
   the contract's proof states only after the relevant proof actually passes.

## Stop Conditions

Stop before any provider mutation if the compiler fails, evidence is stale or
missing, an assumption is unknown, a dependency is undeclared, the change
summary exceeds its allowed shape, a normalized fact conflicts with the
contract, or the lifecycle permits replay.

## Output

The output is a contract ID, a safe structured validation result, and
append-only evidence references. The provider-specific plan remains the source
of target, cost, permission, rollback, and execution authority.
