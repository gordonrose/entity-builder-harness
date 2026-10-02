<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: deploy.script.selected-control-plane.readme
  version: 1
  status: active
  layer: 04.deploy
  domain: deployment.realization
  disciplines: [architecture, security, sre]
  kind: readme
  purpose: Describe the selected journal/evidence source contract and bounded authenticated transport.
  portability: {class: internal, targets: [kanbien/staging]}
  used_by:
  - id: deploy.script.selected-control-plane
    path: scripts/04.deploy/release-control/selected_control_plane.py
-->
# Selected control plane

The selected staging control plane is a four-resource source contract:

- one encrypted DynamoDB journal with point-in-time recovery and no TTL;
- one private, versioned, AES-256 evidence bucket with no automatic deletion;
- one bucket policy that requires TLS and conditional evidence creation;
- one GitHub OIDC controller role that can use only the selected journal and
  evidence prefix.

The source validator loads the versioned schema, policy configuration and
CloudFormation template. It rejects an extra resource, changed retention,
broadened action, alternate account or region, unpinned trust, or any attempt
to treat this source result as release or operation authority.

The authenticated transport verifies the dedicated assumed-role identity before
it permits only transactional journal reads/writes and version-specific evidence
put/get requests. Evidence writes require an expected bucket owner, AES-256,
a SHA-256 checksum and conditional create. A malformed, denied or uncertain
provider result is not success. The existing selected store performs
version-specific readback and refuses a mismatched evidence record.

These are local source contracts. P21 is the separate approved operation that
may create the journal, bucket and role; P22 proves the behavior against those
resources. Until then the adapter has no credentials, live store, or execution
authority.

