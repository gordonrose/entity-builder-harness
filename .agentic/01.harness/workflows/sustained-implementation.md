<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.workflow.sustained-implementation
version: 1
status: active
layer: 01.harness
domain: delivery.autonomy
disciplines: [agentic, sre]
kind: workflow
purpose: Keep authorised source implementation moving through complete delivery units.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->
# Sustained implementation workflow

For a `source-batch`, keep a visible queue of delivery units. For each unit:

1. implement its contract and source;
2. run focused checks and repair ordinary failures;
3. update affected documentation and session evidence;
4. checkpoint only when authorised; and
5. immediately begin the next queued unit.

Do not yield after routine progress. Yield only at a declared stop condition or
after the approved programme is complete.
