<!-- agentic-artifact:
schema: agentic-artifact/v3
id: product.feature.skill.create
version: 1
status: active
created_on: "2026-11-06"
updated_on: "2026-11-09"
layer: 03.product
domain: feature-governance
disciplines: [architecture, backend, agentic]
kind: skill
purpose: Provide a reusable procedure for creating a governed app feature.
portability: {class: source-only, targets: []}
used_by:
- id: product.feature.workflow.create
  path: .agentic/03.product/feature/workflows/create-feature.md
-->
# Create a product feature

Use this skill when asked to add a real product feature under `apps/`, especially one with validation, persistence, or product composition. Do not use it for the platform dummy app, platform internals, or an isolated Core helper.

Read the [feature workflow](../workflows/create-feature.md), [feature boundary](../standards/feature-boundary.md), and the selected pilot or feature plan before editing. Establish the owning app/product, explicit operations and exclusions, persistence availability, and intended proof stage.

Build only the feature concerns that exist: public contracts and runtime schemas; transport adaptation; domain services in separate use-case files; persistence mapping and app-owned migration reference; diagnostics and caller errors; public feature index; app mount/product composition; and source-backed README.

Use public Core and Platform contracts. Keep provider SDKs, AWS selection, target profiles, deployment manifests, secrets, and cloud mutation out of the feature. Treat archive, logical deletion, recovery-window restore, and purge eligibility as distinct lifecycle concepts.

Run the applicable focused checks and report local, package, target, and live evidence separately. Stop rather than improvising when a required capability, target declaration, migration route, or proof chain is absent.
