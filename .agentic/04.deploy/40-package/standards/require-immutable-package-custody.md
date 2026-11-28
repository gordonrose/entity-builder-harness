<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.standards.package-custody-and-promotion
version: 3
status: active
layer: 04.deploy
domain: deployment.package-candidates
disciplines:
  - agentic
  - architecture
  - security
  - sre
kind: standard
purpose: Define the safe evidence and authority boundary between qualifying, publishing, and promoting an immutable package.
portability:
  class: reusable
  targets:
    - entity-builder
used_by:
  - id: deploy.workflow.package-custody-and-promotion
    path: .agentic/04.deploy/40-package/workflows/publish-immutable-package-with-custody.md
  - id: deploy.schema.package-custody-receipt.v1
    path: .agentic/04.deploy/40-package/schemas/package-custody-receipt.v1.schema.yml
created_on: "2026-10-20"
updated_on: "2026-11-27"
-->
# Require Immutable Package Custody

Package qualification, publication, and target promotion are separate
decisions. A qualified image may be stored by immutable digest without being
authorised for any workload. A later target-bound deployment control alone may
select that digest.

## Package custody requirements

A publication route must:

<!-- deterministic-check: allow reason="the target-bound workflow verifier enforces the executable publication sequence; this standard states the portable policy." -->
1. accept only an approved source revision and runnable-program/image contract;
2. run the named local qualification and package checks before publication;
3. publish an immutable digest to the declared package destination;
4. fail closed if a required scan, SBOM, provenance attestation, or digest
   binding is absent or rejected; and
5. write only a receipt conforming to the safe receipt schema.

Before publication, the exact pipeline's declared provider access must pass its
static policy-coverage check. After its delivery identity is assumed, named
safe read-only access probes must pass before a consequential publication
operation. The custody receipt records those two checks separately from image
qualification and scan evidence.

The receipt may contain stable identifiers, source revision, digest, bounded
check verdicts, timestamp, and a non-secret run reference. It must not contain
credentials, secret values, headers, request bodies, personal data, full
provider locations, raw provider responses, or vulnerability details.

## Acquiring hosted custody for a new execution

### Source-owned branch selection

The existing pipeline catalogue may enumerate additional exact approved branch
refs beside its unchanged default `permitted_source_ref`. The shared publication
owner validates this closed selection for declaration readers, preparation and
the actual publisher. Reject malformed, duplicate, wildcard, tag or unlisted
refs; neither environment text nor a dispatch input may extend that set.
An optional `custody_acquisition.source_ref` selects one member for acquisition;
omission selects the default. This is a source declaration, not a caller override.

The publisher's fixed binding identifies the catalogue row, workflow, provider
identity and destination. Its read-only source gate checks the actual workflow
ref before qualification or provider access, and publication repeats that same
check. Preserve protected-environment approval, exact source revision, qualified
payload, immutable destination, scan, SBOM and signed provenance requirements.
Acquisition binds run, artifact and certificate to the same selected exact ref;
an approved task branch cannot be relabelled as main. Source permission does not
prove that the live environment or effective provider access admits that branch.

When a deployment capability acquires hosted package evidence, use its selected
source-owned repository, publication workflow/ref and artifact contract. A local
receipt file, successful schema validation or clean registry scan does not prove
that publication produced the image. The existing receipt schema is unchanged.

The package custody acquisition owner must observe the exact successful run and
source, acquire the unique unexpired artifact by its observed identity, verify
its archive digest, and read the bounded receipt member without extracting
untrusted paths. Verify provenance with the supported signature verifier and
exact image/source/workflow restrictions; do not trust arbitrary predicate text
as certificate identity. Bind the workflow at the publication revision and
reobserve stable run/artifact identity. Require the selected region/repository,
receipt/run/source agreement and the existing immutable image/scan checks.
Missing verifier support, authentication, complete pagination or any required
binding is a failure, not permission to accept a supplied qualified flag.

Retain only non-secret immutable acquisition facts beside the unchanged receipt
in the consuming operation's existing record. Do not retain credentials, signed
download locations or raw provider responses. Acquiring evidence is read-only
and grants neither publication nor workload authority. Existing publication
source restrictions remain effective; this route cannot turn a task branch into
an approved main publication. Older fixed receipt-file consumers do not gain this
authentication merely because the shared acquisition capability exists.

## Authority boundary

A package-publication workflow may build, scan, attest, publish, and retain
safe evidence. It must not create, update, select, restart, roll back, or
verify a workload. Those actions remain target-bound deploy or run controls.

If an image is published but a later qualification proof fails, the receipt is
rejected and the workflow stops. It must not delete the immutable image or
start a compensating deployment automatically.
