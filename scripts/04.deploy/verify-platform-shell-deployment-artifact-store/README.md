<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.script.verify-platform-shell-deployment-artifact-store.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- security
- sre
kind: capability-readme
purpose: Explain the static source check for the private Kanbien staging CloudFormation deployment-artifact store.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: deploy.script.verify-platform-shell-deployment-artifact-store
  path: scripts/04.deploy/verify-platform-shell-deployment-artifact-store/script.sh
-->
# Deployment-Artifact Store Static Verification

CloudFormation accepts templates larger than 51,200 bytes only through a
private S3 URL. This check proves that the separately bootstrapped staging
artifact store is not a product-data store: it has one encrypted bucket,
public access blocks, bucket-owner-enforced object ownership, a TLS-only deny
policy, no granting bucket policy, retained infrastructure, and a 30-day
lifecycle for the `change-sets/` prefix.

It is source-only and never contacts AWS:

```bash
npm run platform:shell:deployment-artifact-store:check
```

The bucket is created and reviewed as its own small CloudFormation stack before
it is used to upload the larger, separately reviewed foundation template.
