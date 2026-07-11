<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: aws.architecture.adr.0002-select-cognito-for-platform-shell-auth
  version: 1
  status: active
  layer: 04.deploy
  domain: infra.ci-cd
  disciplines:
  - architecture
  - sre
  - security
  kind: adr
  purpose: Select Amazon Cognito as the first auth provider path for the platform shell staging target.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: infra.04-deploy.03-product.targets.kanbien.staging.deploy-readiness
    path: infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml
  - id: harness.architecture.plan.platform-runtime-implementation
    path: docs/harness/architecture/plans/platform-runtime-implementation-plan.md
-->
# ADR 0002: Select Cognito For Platform Shell Auth

## Status

Accepted.

## Context

Milestone 10a blocks public internet exposure until the platform shell has a
real authentication and authorization path. The current shell already has
security headers, fake-auth tests, CORS plumbing, rate-limit surfaces, and
permission checks, but fake authentication is not enough for an internet-facing
target.

The first deployment planning target is Kanbien staging on AWS ECS Fargate.
That target needs both human login and machine/API auth over time, but the
initial platform shell proof only needs a concrete JWT validation path that can
be hidden behind `platform/security`.

The platform must remain portable. App code should declare app-owned
permissions and route auth requirements; it should not import Cognito clients,
AWS SDKs, target profiles, or provider-specific identity concepts.

## Decision

Select Amazon Cognito as the first authentication provider path for the
Kanbien staging platform shell.

The implementation boundary is:

- `platform/security` validates Cognito-issued access tokens through
  provider-neutral JWT/JWKS interfaces.
- `platform/server` wires the auth hook from config/environment values and
  keeps authenticated app routes denied by default.
- App routes keep using app-declared `Permission` values.
- Target authz mappings translate Cognito groups, scopes, or claims into
  permissions declared by the apps included in the product target.
- Deployment target profiles record the Cognito user pool, app client, JWKS
  issuer, CORS allowlist, health exposure policy, rate-limit keying, secret
  source, and remaining blockers before public exposure.

For the first public-facing posture, `/livez` may remain public because it
returns minimal liveness only. `/readyz` should be treated as authenticated for
internet-facing targets unless the target records a specific load-balancer or
private-network health-check exception.

## Consequences

Kanbien staging can use an AWS-native identity service that fits the selected
AWS ECS Fargate planning target.

The platform gets real JWT signature, issuer, token-use, expiry, and app-client
validation without exposing Cognito as an app-facing API.

Permission vocabulary remains app-owned. Cognito groups/scopes/claims are
target identity facts; they grant app-declared permissions but do not define
what permissions exist.

The deployment target remains blocked until concrete Cognito pool/client
values, CORS origins, secret/config source, protected dummy-route deployment
smoke, and public exposure proof are recorded.

Future products or clients can select Auth0, Clerk, custom OIDC, private
network auth, or another provider through a new ADR and provider adapter
without changing ordinary app feature code.

## Non-Goals

This ADR does not create a Cognito user pool or app client.

This ADR does not authorize AWS mutation, public DNS, IAM changes, secret
provisioning, image publishing, or public deployment.

This ADR does not require all future clients or products to use Cognito.

This ADR does not define the final human-login UX, passkey support, SSO setup,
or client-owned identity onboarding model.
