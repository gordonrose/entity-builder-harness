<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.readme.release-control-source-discovery
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: readme
purpose: Define the bounded independent source inventory grammar and its unresolved surfaces.
portability: {class: reusable, targets: [entity-builder]}
used_by:
- id: deploy.script.operational-realization-source-coverage
  path: scripts/04.deploy/operational-realization-gate/source_coverage.py
-->
# Independent source inventory v1

Use the existing [Operational Realization Gate](../../operational-realization-gate/README.md#independent-source-discovery-and-coverage)
`--discover` or `--coverage` command. This collector supplies source observations
to the generic compiler; it does not provide another deployment command or
execute source. Its policy is `source-surface/v1`, with the collector file's
SHA-256 as its revision.

## Enumerated boundary

The fixed roots are root `package.json`, `apps/`, `products/`, `packages/`,
`platform/`, `scripts/04.deploy/`, `infra/04.deploy/`, and `.github/workflows/`.
Traversal ignores `.git`, `node_modules`, `.cache`, `build`, `dist`, `generated`,
`__pycache__`, `tests` and `fixtures`. These exclusions describe scanner scope;
they do not prove that code is nonproduction or authorize ledger exemptions.
Observed references into excluded or unsupported roots block coverage.
Within package roots, enumeration covers manifests, `*.main.*` entrypoints and
declared referenced targets. Arbitrary import traversal and default entrypoint
inference are outside v1; a scope-complete estate audit requires the next unit.

| Source | Observations and limitations |
| --- | --- |
| Package manifests | Scripts, exports, bins, main/module, browser and imports declarations. Referenced in-scope files are content-bound; declared targets remain opaque regardless of extension. Unsupported workspaces/references block. |
| Deployment scripts and infrastructure code | Source entrypoints and content hashes. Arbitrary execution, dynamic infrastructure and unsupported executable formats block. |
| GitHub workflows | Steps/actions/services and environment bindings. Shell and action semantics remain unresolved, including reusable actions. |
| Dockerfiles | Final command/configuration declarations; inherited entrypoints, opaque build commands and unsupported command forms block. Final image contents/provenance require later artifact inspection. |
| Infrastructure JSON/YAML | Literal task-definition structure, containers, commands, configuration, secrets, identity bindings and external imports. Other resource grammars/macros remain unresolved. |

The supported infrastructure grammar is deliberately narrow:
`Resources` contains `AWS::ECS::TaskDefinition` entries with a properties mapping
and nonempty `ContainerDefinitions`. Each container has a unique string name,
a literal nonempty image string and a literal nonempty string-array command
or entrypoint. Optional healthcheck commands use the same array form. Environment
and secret lists require unique names and `Value`/`ValueFrom` respectively.
Identity fields and nested imports generate separate hashed observations.
This grammar identifies declared source structure; it does not authenticate
ownership, resolve an image tag, prove its content digest or qualify a command.

Unknown resource types (including native functions, state machines and custom
resources), transforms, symbolic images/commands, inherited commands and
unsupported infrastructure formats remain explicit blocking findings. Adding
one must never quietly reduce it to an already covered resource.

## Identity, safety and review

Source IDs hash relative paths. Observation IDs hash source identity, kind and
locator; detail digests hash the relevant source subtree. Parent IDs preserve
container/task/binding relationships. The inventory digest hashes canonical JSON
excluding its own digest field and includes the collector revision, scope,
all source content hashes, observations and findings. Declarations and ledgers
cannot alter what is enumerated. File-content or collector changes invalidate
the snapshot even if the stable observation identity stays the same.

Only safe relative paths, digests, types and fixed findings leave discovery.
Commands, environment values, secret references and resource payloads are never
echoed. Review the source locally to interpret a hashed observation. Digests are
content commitments, not encrypted storage for secret values; keep actual
credentials out of repository source and declared inputs.

The parser rejects duplicate keys, aliases, unsupported tags, malformed shapes,
oversized input and excessive nesting. Symlinks and unreadable/nonregular files
block; directory-relative no-follow reads prevent symlink traversal. The scanner
does not produce an atomic repository snapshot under concurrent file edits;
run against a stable checkout and rerun after changes. A source-root directory
is an explicit caller-selected boundary, not proof that every organizational
repository or live resource has been inspected.

Coverage also requires current reviewed adoption entries, one executable per
operation, matching artifact source bindings, all configuration/authority
bindings and every external dependency consumer. No source disposition suppresses
an unresolved observation. The initial repository adoption plan remains pending;
legacy shell/action semantics need the next collector/caller unit.

## Verification

```bash
python3 -B -m unittest discover \
  -s scripts/04.deploy/release-control/discovery -p test_source_inventory.py -v
npm run deployment:realization:check
```

Tests include hidden scripts, sidecars, native executable resources, macros,
dynamic commands, referenced-file mutations, unsafe parsing, scope escapes,
symlinks and safe output. Mixed-composition mutation tests live beside the
canonical compiler. All local positives concern source coverage only.

## Selected-workflow caller inventory

`caller_inventory.py` adds a separate versioned observation shape for caller
relationships through the same gate command (`--callers --workflow ...`). It
does not alter the v1 source inventory's diagnostics or exclusions, and a caller
review cannot suppress those findings. Its revision hashes both this collector
and the shared source parser; every graph binds all collected source bytes.

The source root must be a stable, real checkout directory. Select a literal
`.github/workflows/*.yml` or `.yaml` file. Every workflow step is recorded,
including conditional and external-action steps. Unsupported run blocks stay
whole opaque subjects; the collector never partially parses a block and then
claims complete behavior. A step condition is part of its digest and is not
evaluated. The graph records potential invocations, not an execution schedule.

Supported complete command blocks contain literal newline/`&&` sequences of
root `npm run NAME`, direct `bash`/`python`/`python3`/`node` relative-file calls,
or simple terminal tool invocations. Metacharacters, substitutions, redirects,
pipelines, control flow, ambiguous npm options/forwarding and custom contexts
block. Root npm scripts recursively include implicit pre/post hooks; cycles
are explicit findings. Root `.npmrc`, custom workflow shells/working directories
and execution-selecting environment variables remain unresolved. Ambient runtime
configuration and actual executable identity require later evidence.

Referenced source files, including files under `tests/`, are content-bound.
Safe explicit targets outside supported analysis roots are also hashed before
being marked unsupported. Unreadable, protected or absent targets instead carry
an empty-content placeholder and a blocking diagnostic; that placeholder is
never proof of their bytes or behavior.
Simple literal shell bodies and the exact existing repository-root Python
dispatch wrapper can add edges. The dispatch wrapper's git-root behavior is
interpreted only under the supplied checkout-root assumption. Arbitrary script
bodies, tools and external actions remain unresolved terminals. Explicitly
unsupported paths/grammars cannot establish absence of further callees.

The graph is forward discovery from one selected workflow. It does not establish
global incoming-caller absence, analyze arbitrary imports/default entrypoints,
or authorize a historical/test-only/retirement disposition. Its reviewed source
profiles and owned pending obligations are accounting evidence only. Byte,
argument, implicit-hook or caller changes invalidate an older review.
Multiple invocations of one source subject retain distinct argument-bound edges;
later runtime composition must qualify each actual command variant. A source
subject profile alone cannot prove those variants equivalent.

Run `python3 -B -m unittest discover -s
scripts/04.deploy/release-control/discovery -p test_caller_inventory.py -v` for
focused parser/graph tests. The combined realization check also includes caller
reconciliation and triage mutation/CLI tests.

## Selected operation inputs and dependency observations

`operation_inventory.py` extends the selected caller graph through the same
gate's `--operations` mode. Its subject set is derived independently from all
script entrypoints, tool commands and unresolved action instances in that graph.
The optional in-process graph argument must match fresh caller discovery; no
saved inventory is accepted by the public command.

For each subject the collector binds every incoming invocation identity and
argument digest. Source observations include literal module imports, Python
import declarations, root-relative path references and literal script-call
candidates. Supported local references are read without following symlinks and
recursively content-bound. Ambiguous module resolution binds all discovered
candidates and retains a finding. Bare package imports, dynamic imports,
generated outputs and unsupported interpretation remain unresolved.

These are conservative source observations. Literal extraction is not a full
JavaScript, Python or shell parser; text in an assertion or comment can also
produce a candidate reference. The collector never treats such a reference as
proof of execution, complete dependency discovery or safe effects. Every script
and tool retains its unresolved semantic obligation.

For independently reached literal `tsc -p RELATIVE_PATH` invocations, the
collector binds local JSON configuration, local `extends`, explicit `files`
and simple `include` membership using bounded `*`/`**` patterns. Matching
file additions, removals and byte changes affect the inventory. This is
conservative membership accounting: TypeScript defaults, aliases, plugins,
references, exclusions, package resolution and unsupported configuration forms
remain findings. It does not infer compiler emission or read generated output.

`action_observations.py` binds each action instance's reference, explicit input
set and values, condition, upstream output expressions and inherited context.
Absent overrides are represented explicitly before hashing. Mutable references
retain a finding; full commit pins still require remote implementation and
default-input proof. No action implementation is fetched or executed, and a
workflow condition cannot be interpreted as reducing declared permissions.

Only safe relative paths, digests, fixed kinds and diagnostic codes are emitted.
Directory traversal uses no-follow descriptors; private/generated areas such
as `.git`, `.cache`, `node_modules`, credentials and dotenv files are excluded
with unresolved-input diagnostics. Collection has explicit file, depth, byte
and row limits; hard exhaustion fails the collection rather than presenting a
truncated successful report.

The collector revision binds this module, the action helper and both existing
caller/source collectors. The canonical operation compiler permits a bounded
larger internal inventory tree because a real dependency map exceeds the
ordinary source-document node budget. Public source-document byte and node
limits remain unchanged; large saved inventories are review artifacts only.

The operation-contract compiler checks every subject, invocation, observation
and dependency against a reviewed declaration consistent with caller ownership/
profile. Complete contract accounting retains source closure and runtime
qualification as blocked. This companion map cannot suppress the earlier estate
inventory, claim global caller absence or authorize adoption exclusions.

Focused tests:

```bash
python3 -B -m unittest discover -s scripts/04.deploy/release-control/discovery \
  -p test_operation_inventory.py -v
python3 -B -m unittest discover -s scripts/04.deploy/release-control/discovery \
  -p test_action_observations.py -v
```

## Workspace build and local artifact collectors

`build_inventory.py` adds independent build accounting through the existing
gate's `--builds` mode. It uses the selected caller graph rather than a manually
supplied build list. Versioned output binds configuration, workspace manifests,
source membership, supported import resolutions and output predictions to source
digests. No-emission, declaration and JavaScript builds have separate modes.
Ambiguous/unsupported resolution remains explicit; predicted output names do
not prove compiler emission.

`build_artifacts.py` compares a freshly discovered build against a local
directory using safe bounded reads. It hashes actual files and checks expected
membership, recognized generated package targets and selected runtime tests.
A local directory is not authenticated compiler provenance; output always keeps
qualification blocked and authority false, including for a matching fixture.
Neither collector executes inspected code or invokes installed build tooling.
Historical operation inventories and findings remain valid historical records;
this additional source mode does not silently clear them.

Supported artifact generator grammar is deliberately narrow. The three selected
image/server-test/product-test generators have reviewed exact helper and scaffold
identities; literal package/export maps, the recognized core-module expansion,
and immediate runtime-test directory selection are extracted as candidates.
Changing surrounding generator behavior requires renewed grammar review.
Known configuration-to-generator associations prevent a changed output-root
expression from silently removing shim obligations. This is syntax recognition,
not execution of the generator or proof that a test ran.

Artifact reads use no-follow directory/file descriptors with regular-file and
before/after metadata checks. Private path components, source fallback, symbolic
links and special files fail. Limits are 5,000 entries, depth 40, 2 MiB per file
and 32 MiB aggregate. Source bytes are rechecked before and after artifact reads;
these checks do not supply an atomic filesystem snapshot. Generated forwarding
files/manifests must match the supported source-derived bytes exactly. Other
compiled bytes are fingerprinted, not compared with a trusted compiler receipt.
A changed compiled file can therefore remain structurally accounted while its
artifact identity changes and qualification remains blocked.

Supported build grammar:

- Strict JSON configuration with one local relative extends reference. Compiler
  options merge by key and retain the declaring directory for path resolution;
  child files/include/exclude fields replace the inherited field. No default
  inclusion is guessed. Exclusion behavior remains an unresolved obligation.
- Explicit files and limited glob patterns: single-segment star and whole-segment
  double-star. Workspace manifests are independently enumerated from the root
  workspace list, and root lock bytes are bound. Duplicate names stay unresolved.
- Exact string workspace exports/subpaths in Bundler mode. Node16/NodeNext retain
  conditional-resolution uncertainty; Node10 does not assume package exports.
  Exact or one-star path aliases use longest-prefix selection and declaration
  origins. All observed competing candidates are bound; ambiguity stays blocked.
  Scoped baseUrl directory lookup is explicitly unsupported by the safe path
  grammar, while applicable workspace export candidates are still observed.
- Literal local imports, exports, require and import calls after lexical comment
  removal, including multiline imports and dotted extensionless basenames.
  Dynamic expressions, escaped specifiers and triple-slash directives remain
  unresolved. This is a lexical subset, not an AST or linker implementation.
- Bounded .ts-to-.js/.d.ts output candidates, with declaration-only and no-emission
  modes distinguished. Declaration inputs do not predict emitted files. Unknown
  options, references, alternate emission extensions, incremental/composite
  output, missing inputs, unsupported resolution and path collisions block
  predictions. Runtime-test suffixes identify candidates, not executed tests.

Build limits: 4,000 source records, 48 MiB aggregate, 50,000 bindings and 50,000
edges, depth 40, 200,000 lexical tokens and 400,000 import-scan steps. The reused
safe file reader caps individual inputs at 2 MiB; inherited glob traversal has
stricter 3,000 directory/result and depth-30 bounds. Limit exhaustion fails the
collection rather than returning a truncated success. Config values, import
specifiers and commands are hashed rather than copied into normal output.
