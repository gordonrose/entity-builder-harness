<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.fixture.estate-callers.readme
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: reference
purpose: Explain inert caller fixtures proving dispatch structure while preserving unqualified children.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.test.release-control-estate-caller-inventory
  path: scripts/04.deploy/release-control/discovery/test_estate_caller_inventory.py
-->
# Estate caller fixture

The tests materialize `sources.json` in disposable directories and inspect the
files without executing them. It contains three root package commands, one
workflow and an exact Python dispatch wrapper. The wrapper and literal command
bodies are structurally accountable. The Python/JavaScript children, workflow
behavior and runtime/tool/environment semantics remain unqualified.

Mutation cases add omitted roots, automatic and explicit hook contexts, hidden
wrapper commands, non-shell whitespace, altered inputs and false test-only
labels. No file name or review status establishes a successful proof.
