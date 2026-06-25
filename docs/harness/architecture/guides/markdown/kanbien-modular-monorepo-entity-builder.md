<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: harness.architecture.guides.markdown.kanbien-modular-monorepo-entity-builder
  version: 1
  status: active
  layer: 01.harness
  domain: architecture
  disciplines:
  - architecture
  kind: guide
  purpose: Document Kanbien Modular Monorepo Entity Builder.
  portability:
    class: required
    targets:
    - llm-workbench
    - entity-builder
    - design-system-builder
  used_by:
  - id: harness.workflows.change-harness
    path: .agentic/01.harness/workflows/change-harness.md
-->
# Kanbien Modular Monorepo Entity Builder

> Source PDF: `Kanbien_Modular_Monorepo_Entity_Builder.pdf`

Strict layer ownership structure
A modular monorepo with strict layer ownership.
# Table of Contents

1. Repo root
2. packages/design-system
3. packages/frontend-kit
4. platform/
5. packages/core
6. apps/
7. harness/
8. tools/build
9. Persistence
10. Infra
11. The core entity flow
<!-- page 2 -->

# 1. Repo root

```text
 kanbien/
   apps/
   packages/
   platform/
   infra/
   harness/
   tools/
   docs/
```

<!-- page 3 -->

# 2. packages/design-system

Owns all visual primitives.
```text
 packages/design-system/
   tokens/
     foundations/
     builders/
     resolved/
   primitives/
   patterns/
   components/
   resolvers/
```

Rule: only the design-system harness layer can edit this. Apps consume it only.
Flow:
```text
 design label -> foundation tokens -> builder tokens -> primitives -> patterns -> app UI
```

<!-- page 4 -->

# 3. packages/frontend-kit

Portable React feature shell.
```text
 packages/frontend-kit/
   entity-pages/
   crud-layouts/
   forms/
   tables/
   navigation/
```

This knows how to render entities, but not what a User or Invoice is.
<!-- page 5 -->

# 4. platform/

Thin runtime layer.
```text
 platform/
   server/
     http.ts
     cors.ts
     rate-limit.ts
     auth.ts
     routes.ts
   mount.ts
```

Features/apps register through:
```text
 mount(app)
```

Keep this boring.
<!-- page 6 -->

# 5. packages/core

Reusable backend capabilities.
```text
 packages/core/
   jobs/
   files/
   auth/
   audit/
   notifications/
   validation/
   persistence/
```

No business features here.
<!-- page 7 -->

# 6. apps/

Actual product code.
```text
 apps/crm/
   entities/
     user/
       entity.schema.ts
       rules.ts
       permissions.ts
       ui.ts
       api.ts
       tests/
   features/
   migrations/
   app.mount.ts
```

Each app can run alone, but can also mount into the platform.
<!-- page 8 -->

# 7. harness/

The entity builder brain.
```text
 harness/
   entity-definition/
   prompts/
   validators/
   generators/
   contracts/
   layer-rules/
```

This captures:
```text
 entity -> fields -> rules -> permissions -> workflows -> persistence -> UI config
```

Then emits deterministic code.
<!-- page 9 -->

# 8. tools/build

Code generation only.
```text
 tools/build/
   generate-entity.ts
   generate-crud.ts
   generate-migration.ts
   generate-tests.ts
```

Important: generation should be idempotent. Running it twice should not bloat the repo.
<!-- page 10 -->

# 9. Persistence

Use central migration ownership per app:
```text
 apps/crm/migrations/
```

Entity folders can define desired persistence shape, but migrations should be generated into one
ordered app migration stream.
Use Prisma, Drizzle, or Kysely. My bias: Drizzle + SQL migrations.
<!-- page 11 -->

# 10. Infra

```text
 infra/
   terraform/
     aws/
       network/
       app/
       database/
       secrets/
       ci-cd/
```

Deployment should consume app manifests:
```text
 apps/crm/app.manifest.ts
```

<!-- page 12 -->

# 11. The core entity flow

```text
 chat
  -> harness captures entity definition
  -> validates contract
  -> generates backend schema/api/tests/migration
  -> generates frontend config
  -> mounts feature into app
  -> platform mounts app
  -> CI runs checks
  -> Terraform deploys staging
  -> promote to prod
```

The biggest correction: don't let features own everything. Let entities define intent, generators produce
implementation, apps own business composition, and platform own runtime concerns.
