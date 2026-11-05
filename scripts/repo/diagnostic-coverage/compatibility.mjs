// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.diagnostics.catalog-compatibility
//   version: 1
//   status: active
//   created_on: "2026-10-27"
//   updated_on: "2026-10-27"
//   layer: 06.shared
//   domain: diagnostics
//   disciplines: [architecture, security, sre]
//   kind: script
//   effects: [read-only]
//   purpose: Prevent changing or deleting a committed diagnostic identity without preserving its existing versioned reader contract.
//   portability: {class: source-only, targets: []}
//   used_by:
//   - id: repo.diagnostics.export-catalogs
//     path: scripts/repo/diagnostic-coverage/export-catalogs.mjs
const canonical = (value) => Array.isArray(value) ? value.map(canonical)
  : value !== null && typeof value === "object" ? Object.fromEntries(Object.entries(value).sort(([a], [b]) => a.localeCompare(b)).map(([key, child]) => [key, canonical(child)])) : value;

/** Existing identities remain readable. Add a new version; do not edit the old one. */
export function catalogCompatible(previous, current) {
  if (previous?.schema !== "core/diagnostic-catalog-export/v1" || current?.schema !== previous.schema
    || previous.catalog?.owner !== current.catalog?.owner || !Array.isArray(previous.catalog?.definitions) || !Array.isArray(current.catalog?.definitions)) return false;
  return previous.catalog.definitions.every((definition) => {
    const candidates = current.catalog.definitions.filter((candidate) => candidate.code === definition.code && candidate.version === definition.version);
    return candidates.length === 1 && JSON.stringify(canonical(candidates[0])) === JSON.stringify(canonical(definition));
  });
}
