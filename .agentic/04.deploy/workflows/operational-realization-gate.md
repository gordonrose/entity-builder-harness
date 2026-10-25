<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: deploy.workflow.operational-realization-gate
  version: 3
  status: active
  created_on: "2026-09-27"
  updated_on: "2026-10-25"
  layer: 04.deploy
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
  - id: deploy.standard.operational-realization-gate
    path: .agentic/04.deploy/standards/operational-realization-gate.md
  - id: harness.standards.delegated-execution-state
    path: .agentic/01.harness/standards/delegated-execution-state.md
-->
# Operational Realization Workflow

## Use When

Use this workflow before a capability first reaches a live target, before a
new execution path, migration, queue consumer, or recovery path is introduced,
and whenever its artifact, identity, configuration shape, connection, engine
semantics, or mutation shape changes.

## Authority and Applicability

Follow the [shared completion principles](../../shared/standards/require-change-completion.md)
and the [deployment proof standard](../standards/operational-realization-gate.md).
Resolve operation-specific applicability in the active provider owner before
selecting the inputs below. Record any applicable exception and its required
approvals, operation scope and executable checks. This workflow does not define
provider exceptions or grant mutation authority.

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
2. Use `npm run deployment:realization:validate -- --contract <path>
   --validate-contract` to
   reject missing graph edges, unsafe lifecycle/retry paths, insufficient proof
   requirements, unknown assumptions, and provider leakage.
3. Collect safe evidence in order: source, artifact, semantic integration,
   live-read, change-set, execution preflight. A provider adapter may collect
   target facts, but it must write normalized facts only.
4. Re-run the compiler with normalized facts. It must show all prerequisite
   gate evidence and every declared component binding passed before a provider
   mutation is proposed.
5. Obtain the separate target-specific authorization required to execute the
   reviewed mutation. This generic workflow never grants cloud authority.
6. If execution is delegated, bind the worker to a packet whose reports follow
   [delegated-execution-state](../../01.harness/standards/delegated-execution-state.md). A non-complete state must name the current
   gate, completed gates, evidence reference, next permitted action, and any
   blocker. An asynchronous provider wait is `waiting-on-external-system`,
   never `complete`.
7. Run one labelled controlled execution. Record safe terminal evidence.
8. If it reaches a terminal failure or stop, do not replay it. Define and
   review a new recovery label and use the `recovery` gate. A recovery is never
   a substitute for omitted preflight evidence.
9. Record the final safe evidence location in the capability plan and update
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
