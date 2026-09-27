# Staging Service active drift assessment

This target-admin command refreshes one narrow fact immediately before the
PostgreSQL Stage 6 Service-stack change set: the fixed
`kanbien-staging-platform-shell-service` stack is `IN_SYNC`.

It checks the declared account and a stable Service stack, starts
CloudFormation drift detection, and polls its completion. It does not read
resource drifts, property values, secrets, stack payloads, or workload data;
its evidence contains only a timestamp and the safe `in-sync` verdict.

```bash
npm run platform:shell:service-active-drift-assessment -- \
  --execute-approved-active-service-drift-assessment \
  --evidence-file /tmp/new-safe-evidence.json --json
```

The short-lived evidence file is then required by the exact Service change-set
preflight alongside fresh classified Foundation evidence. Direct live S3
control reads still verify the artifact bucket; the Service deployment does
not rely on an old passive artifact-stack drift timestamp.
