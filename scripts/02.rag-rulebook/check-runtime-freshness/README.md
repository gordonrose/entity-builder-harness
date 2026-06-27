<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.check-runtime-freshness.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: runtime
disciplines:
- agentic
- architecture
kind: guide
purpose: Explain the local RAG/rulebook runtime freshness checker.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.check-runtime-freshness
  path: scripts/02.rag-rulebook/check-runtime-freshness/script.sh
-->

# Check Runtime Freshness

`script.sh` verifies that a local RAG/rulebook runtime cache still matches the
current governed inputs recorded in its manifest.

The command is read-only. It does not rebuild the runtime.

## Usage

```bash
bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh
```

```bash
bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh \
  --runtime-dir .cache/02.rag-rulebook \
  --json
```

## What It Checks

- The runtime manifest exists.
- The manifest uses `rag-rulebook/local-runtime-manifest/v1`.
- The runtime declares deterministic offline constraints.
- Manifest input fingerprints still match the current repo.
- Rulebook source roots, structured rule roots, derivation reports, index
  inputs, and chunk-generation inputs still match the manifest.
- Source projection manifests and source projection/coverage commands still
  match the manifest.
- Validation machinery that defines whether runtime inputs are trustworthy
  still matches the manifest.
- Runtime output files still exist.
- Runtime output file content still matches the manifest.
- Runtime output schemas are supported.

## Status Values

- `fresh`: runtime matches current inputs and output fingerprints.
- `missing`: runtime manifest does not exist.
- `stale`: current inputs or runtime outputs no longer match the manifest.
- `corrupt`: the manifest or runtime output shape is invalid.

In `strict-v1`, every non-fresh result is blocking. Later drift policy can
classify known minor deviations differently, but this command deliberately
fails closed for the first governed runtime freshness gate.

## Rebuild

When the command fails, rebuild the runtime:

```bash
bash scripts/02.rag-rulebook/build-local-runtime/script.sh --pretty
```

For a custom runtime directory:

```bash
bash scripts/02.rag-rulebook/build-local-runtime/script.sh \
  --output-dir <runtime-dir> \
  --pretty
```
