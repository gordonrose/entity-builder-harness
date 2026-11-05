<!-- agentic-artifact:
schema: agentic-artifact/v3
id: repo.module-structure.readme
version: 4
status: active
created_on: "2026-11-01"
updated_on: "2026-11-02"
layer: 03.product
domain: architecture
disciplines: [architecture, agentic]
kind: documentation
purpose: Explain public-index, dependency and narrow configuration-access checks and their proof limits.
portability: {class: source-only, targets: []}
used_by:
- id: product.standard.public-module-structure
  path: .agentic/03.product/standards/public-module-structure.md
-->
# Public module index checks

A file such as `packages/core/src/config/index.ts` tells other code which parts
of the config module it can use. The functions themselves belong in named files.
This checker catches implementation being added to a governed index. The
[product standard](../../../.agentic/03.product/standards/public-module-structure.md)
owns the rule and its treatment of refactoring; this guide explains the tools.

## What each file does

- [script.sh](script.sh) runs the read-only repository check from any working
  directory. It accepts no arguments and does not change files.
- [check.mjs](check.mjs) finds source indexes, reads their TypeScript syntax and
  returns fixed finding codes with repository-relative locations. It never
  executes the product code it inspects or prints its source text.
- [legacy.v1.json](legacy.v1.json) records the exact existing non-export code in
  23 mixed indexes. This is a temporary allowance, not permission to add logic.
  There is no refresh command; changing an allowance needs the approval and
  review described in the standard. Config has no allowance.
- [smoke-test.sh](smoke-test.sh) runs [smoke-test.mjs](smoke-test.mjs), which tests
  valid exports, rejected declarations, legacy changes and the actual config
  index. Its counterexample adds a function to a copy in memory and proves the
  check rejects it; it does not modify the real index.

## Example: what gets checked

```typescript
// Valid public index: makes another file's function available.
export { numberConfigValue } from "./domain/value-readers";
```

```typescript
// Invalid public index: implements a function here.
export function numberConfigValue() { return 3; }
```

The second example produces `MODULE_INDEX_IMPLEMENTATION` with the file path
and line number. It does not include function text, supplied values or native
parser/error messages. Move implementation into the appropriate file; do not
change the allowance simply to suppress the finding.

```text
TypeScript source indexes + exact legacy allowances
                    |
                    v
     check.mjs reads syntax, not product behaviour
                    |
       +------------+---------------+
       |                            |
 no prohibited new code       a violation or unreadable input
       |                            |
 JSON counts, exit 0          JSON findings, nonzero exit
```

## Configuration source access

Configuration is information supplied to tell a program how to run. Node exposes
environment variables through process.env. Reading that global in a business
handler can bypass its checked configuration, even when a checker exists.

The same command now runs inspectConfigurationAccess() from check.mjs. It uses
TypeScript syntax, not an import-presence rule or source-text regular expression.
The [configuration standard](../../../.agentic/03.product/standards/config-runtime-settings.md#configuration-checking-responsibilities)
owns the policy. Detected violations produce
CONFIGURATION_SOURCE_ACCESS_OUTSIDE_LOADER with a safe path/line, never the key,
source text or supplied value. Invalid syntax in this scope fails closed with
CONFIGURATION_ACCESS_SYNTAX_INVALID.

Covered: TS/TSX under packages/*/src, platform/**/src, apps/*/src and
products/*/src, including new files. Direct process.env and literal bracket
forms, globalThis.process.env, default/namespace/named-env imports from process
or node:process, and direct CommonJS require equivalents are recognised. Simple
lexical declarations distinguish local parameters/objects from Node's process.
Type-only references, comments, strings, test/fixture directories and source
files named *.test.ts(x) or *.spec.ts(x) do not count as runtime source access.

Permitted global-access owners are platform/config/src/** and the existing
platform/server/src/main.ts and platform/workers/src/main.ts. Infra/target
entrypoints are outside this source-access rule and retain binding ownership.
Injected source bags, callers of checked loaders, checked-value consumers and
specialised security validators need no otherwise unused Core import.

Limits: this is not complete alias/data-flow analysis. Arbitrary aliases, dynamic
property names, exotic scope/hoisting, other source APIs, JavaScript, Python,
shell and scripts/bin are not proved by this check. Review and actual caller
tests establish checked-value consumption, failure-before-work and context.
Passing it does not prove a permitted loader checks its inputs. The current
actual source tree and prohibited/permitted future callers are fixture-tested.

## Running it

Use the registered checks for final proof:

```bash
bash scripts/repo/check-selection/script.sh --checks module-index-structure module-index-structure-regression --execute-local --json
```

For a narrow exploratory run:

```bash
bash scripts/repo/module-structure/script.sh
bash scripts/repo/module-structure/smoke-test.sh
```

Successful repository output includes `findings: []`, `indexes` (how many source
indexes were checked) and `legacy` (how many exact existing allowances matched).
An unchanged legacy index counts as allowed debt, not as structurally compliant.

`MODULE_INDEX_LEGACY_CHANGED` means a pinned index's non-export code changed;
new re-exports alone do not cause it. `MODULE_INDEX_LEGACY_STALE` means an old
allowance must be removed after cleanup/removal. Missing or invalid baseline,
unreadable source, syntax and unexpected checking failures are nonzero results,
not a successful empty scan. Output excludes native failure messages.

## Coverage and limits

The checker discovers `src/**/index.ts` and `index.tsx` within `packages/`,
`platform/`, `apps/` and `products/`, including new modules. It excludes test,
fixture, dependency, Git and build directories. It fails on symbolic-link source
traversal. Other languages/source layouts need an explicit review decision;
they are not claimed covered. Exact legacy hashes intentionally require review
even for changes to existing implementation, including internal formatting.

Syntax does not reveal whether a destination file is well designed or whether
moving code preserved behaviour. The owning source review and public-import
type/runtime tests must prove those separately. The standard, catalog, fixtures
and Core boundary integration keep this lesson reusable beyond config.

## Contract/capability dependency proof

The same command discovers TypeScript source under the four workspace roots
and `infra/`. A module with an index.ts and actual contract/ or domain/ source
adopts the role checks without a new manifest. Contracts cannot reach capabilities,
including through another internal file; internal files cannot import their
own public index; file dependency cycles, including type-only cycles, fail.
External consumers use its index, not private contracts or capabilities. The
exact Core catalog-to-config-diagnostic import is the recorded assembly exception.
Its exact destination is
`packages/core/src/config/contract/reporting/diagnostics.ts`, not the whole
reporting folder. Recursive discovery also checks deeper responsibility groups:
the fixtures reject nested contract-to-capability edges, private imports,
own-index imports and type-only cycles. The checker does not prescribe folder
names or decide whether the grouping matches the module's work.

Workspace aliases come from string-valued package exports. Relative imports,
type imports, re-exports, literal require and literal dynamic imports are checked.
Computed dynamic imports inside adopted modules and unresolved relative imports
fail closed. Conditional/wildcard exports, arbitrary runtime loaders, other
languages and undiscovered roots need explicit review; this is not universal
program analysis. Config is the first adopted role module; legacy indexes retain
their existing allowances. Successful output also names the adopted module count.

The fixtures include an independent future module, transitive contract violations,
private aliases, type cycles and the exact catalog exception. Core's boundary
test checks its actual source graph. These checks do not establish meaningful
file responsibilities, public compatibility or diagnostic truth: real consumer
and type/runtime tests and source review still provide those proofs.
