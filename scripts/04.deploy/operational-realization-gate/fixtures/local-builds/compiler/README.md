<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.fixture.local-typescript-observer
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: fixture
purpose: Supply inert positive and negative inputs for genuine locked TypeScript compiler observations.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.test.operational-realization-typescript-observer
  path: scripts/04.deploy/operational-realization-gate/test_typescript_observer.py
-->
# Genuine compiler fixtures

These inert sources are compiled by the verified Node 22.23.3 and TypeScript
5.9.3 toolchain. The positive case imports a local module and emits CommonJS;
the negative case produces a genuine type error with `noEmitOnError` enabled.
Neither fixture is executed. Tests create disposable copies and vary compiler
options, dependencies, paths and output boundaries in those copies.

The observation records local compilation, not container construction, runtime
qualification, authenticated release evidence or deployment authorization.
