<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.report-artifact-retrieval-profile-coverage.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the read-only artifact retrieval-profile coverage report command.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.report-artifact-retrieval-profile-coverage
  path: scripts/02.rag-rulebook/report-artifact-retrieval-profile-coverage/script.sh
- id: rag-rulebook.plan.artifact-metadata-retrieval-profile-migration
  path: .agentic/02.rag-rulebook/plans/artifact-metadata-retrieval-profile-migration.md
-->
# Report Artifact Retrieval Profile Coverage

`script.sh` reads the artifact metadata index and reports whether each indexed
artifact has enough deterministic metadata to derive useful retrieval-profile
signals.

The command is diagnostic. It does not mutate headers, generated recognition
sources, chunks, or runtime caches.

## Usage

Generate the current strict artifact index and report coverage:

```bash
bash scripts/02.rag-rulebook/report-artifact-retrieval-profile-coverage/script.sh --current
```

Report from a saved index:

```bash
bash scripts/01.harness/artifact-metadata/generate-index/script.sh --all --pretty --strict >/tmp/artifact-index.json
bash scripts/02.rag-rulebook/report-artifact-retrieval-profile-coverage/script.sh --index /tmp/artifact-index.json --pretty
```

Use `--json` for compact machine-readable output and `--pretty` for indented
JSON.

## Coverage Buckets

- `strong`: metadata is sufficient for specific roles and process signals.
- `partial`: identity is present, but process meaning is thinner.
- `weak`: required identity or derivable process signals are missing.
- `excluded`: intentionally not treated as a retrieval target, such as
  deprecated artifacts.

## Repair Sources

The report suggests where repair should happen:

- `header`: authored metadata should change.
- `generator-rule`: deterministic profile derivation should become smarter.
- `none`: current metadata is enough.

The report does not inspect body text as authority. That boundary keeps it from
quietly replacing governed metadata and generator rules with ad hoc guessing.
