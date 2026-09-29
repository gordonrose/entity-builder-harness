<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.review.infrastructure-reference-source-coverage
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: review-record
purpose: Record same-tree evidence for bounded CloudFormation structural reference coverage while preserving open estate findings.
portability: {class: internal, targets: [entity-builder]}
used_by:
- id: deploy.plan.iaas-composition-and-release-control-plane
  path: .agentic/aws/plans/implementation/iaas-composition-and-release-control-plane.md
-->
# CloudFormation structural reference coverage

The existing Operational Realization Gate now resolves the bounded declarative
CloudFormation source grammar, including the existing twenty-fragment foundation
composition. It constructs scoped symbol tables without executing the renderer,
then binds resources, parameters, conditions, mappings, outputs and pseudo
parameters to explicit reference edges. Reviewed source compositions must
acknowledge every discovered reference and declare its managed resource endpoints.

[Current inventory](current-inventory.json) is safe normalized output from the
existing source collector. [Baseline collector inventory](baseline-collector-inventory.json)
uses the committed pre-extension collector on **the same current source tree**.
This is a controlled collector comparison, not the original historical repository
snapshot. Both inventories bind exactly the same 376 source records and bytes.
The comparison checked the current inventory before and after the baseline run;
the public `--discover` command then reproduced the current inventory exactly.
A final collection confirmed that source bindings had remained unchanged.

| Same-tree result | Committed collector | Extended collector |
| --- | ---: | ---: |
| Sources | 376 | 376 |
| Observations | 1,235 | 1,813 |
| Open findings | 244 | 223 |
| Unsupported-resource-file findings | 23 | 0 |
| Unresolved nonresource dependency-consumer findings | 0 | 2 |

Exactly 23 `resource-type-unsupported` findings were resolved, one per existing
template file. All 221 other baseline findings remain. Two new file-level findings
expose seven previously unaccounted-for AWS-typed parameter dependencies in the
rulebook foundation and product foundation templates. These parameters refer to
provider objects; their source consumers remain unresolved until the composition
contract can model them explicitly. They are recorded with safe identities and
value digests, without retaining raw parameter names or defaults.

The 93 existing resources span 33 recognised families, including the ten ECS task
definitions with their unchanged container requirements. This is structural
source coverage, not an AWS property-schema, policy, identity, deployed-state or
runtime qualification result.

The fresh graph contains **442 reference edges and 129 symbols**. Every reference
has an existing consumer and target observation:

| Reference kind | Edges |
| --- | ---: |
| `Ref` | 207 |
| `Sub` | 163 |
| `GetAtt` | 64 |
| `DependsOn` | 5 |
| Condition | 3 |

Both conditional branches and all substitution-map values are inspected.
`ImportValue` dependencies are recorded throughout the template, including outputs,
conditions and nested branches, using the exact owner and raw source locator.
Resource imports retain their existing identities without duplicate observations.
Nonresource imports, dynamic references and AWS-typed parameters explicitly block
coverage while the current contract cannot map their consumers. Missing,
ambiguous or cyclic references, duplicate fragment symbols, unsafe paths,
unknown intrinsic forms, executable resource families, macros and unsupported
resource metadata behavior remain blocking. No unrelated template can supply a
missing symbol. The supported grammar and its explicit limits are documented in
the [collector README](../../../../../scripts/04.deploy/release-control/discovery/README.md#cloudformation-structural-references).

The remaining categories in this snapshot are:

| Category | Open findings |
| --- | ---: |
| Opaque executable | 185 |
| Opaque package export target | 20 |
| Workflow action semantics | 6 |
| Unresolved nonresource template dependency consumer | 2 |
| Unsupported image command | 2 |
| Opaque image build | 2 |
| Symbolic container image | 2 |
| Inherited container command | 2 |
| Inherited image entrypoint | 1 |
| Unsupported YAML alias | 1 |

The baseline and current categories are reproduced in the
[verification summary](verification-summary.json), which also records individual
resolved and newly exposed source IDs, source paths, collector revisions and
inventory digests. The public discovery command correctly returned **exit 1**, with
an empty stderr, because the remaining estate findings still block source coverage.

Focused implementation verification passed 49 collector tests and 15 reference
reconciliation tests. Related regression runs passed all 279 discovery tests,
34 existing source-coverage tests and 23 triage tests; the 279-test run includes
the 49 collector cases. Independent review reran the 49 and 15 focused cases,
reproduced the original output, condition and typed-parameter omissions as blocked,
and confirmed that a nested resource import remains exactly one dependency.
The scoped whitespace check also passed. Canonical batch verification is recorded
separately in the session log.

Current inventory identity:
`sha256:bca9791be8fa14f4f881713e78a02df95f08f097bd81f85c6383d7f21d284074`.

```bash
bash scripts/04.deploy/operational-realization-gate/script.sh \
  --discover --source-root "$(pwd -P)" --json
python3 -B -m unittest discover \
  -s scripts/04.deploy/release-control/discovery \
  -p test_cloudformation_inventory.py -v
python3 -B -m unittest discover \
  -s scripts/04.deploy/operational-realization-gate \
  -p test_cloudformation_coverage.py -v
```

Phase 2 whole-estate coverage remains open, as do provider and live qualification.
The next coverage unit must address actual executable/caller and package-export
boundaries, followed by external action implementation, explicit nonresource
provider-dependency consumers and the remaining image/YAML grammars. Adoption
reviews cannot waive these findings. All source receipts remain unable to grant
release eligibility or operation authority.

Earlier receipt revisions were preserved outside Git in the batch review archive
before this final frozen-source snapshot was generated. They are superseded by
this record and must not be used as current evidence.
