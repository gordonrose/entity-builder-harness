<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.standard.identity-security-baseline.v1
version: 1
status: active
layer: 03.product
domain: identity-access
disciplines:
- security
- architecture
- requirements
kind: standard
purpose: Define the approved initial identity-security floor, versioned default, and tenant-tightening rules for the Entity Builder production reference target.
portability:
  class: source-only
  targets: []
used_by:
- id: product.plan.production-reference-target-baseline
  path: .agentic/03.product/plans/implementation/production-reference-target-baseline.md
- id: product.plan.product-harness-foundation
  path: .agentic/03.product/plans/implementation/product-harness-foundation.md
-->
# Identity Security Baseline v1

## Status And Boundary

`identity-security-baseline.v1` is the approved initial security policy for
human identity. It is a requirements and adoption artifact, not a working
identity provider, tenant-policy database, mail service, password store, or
AWS configuration.

The initial human sign-in method is verified email and password. The current
Cognito adapter is machine-to-machine evidence only. A product or target must
not claim this baseline is implemented until it has a human identity flow, a
server-side policy resolver, a scoped authorisation model, safe telemetry, and
the target evidence required by the Production Reference Target Baseline.

This standard does not authorise cloud mutation, collection of medical data,
or a change to the initial no-MFA decision.

## How The Effective Policy Is Formed

Every human identity decision must satisfy all applicable layers:

```text
platform security floor
  + adopted product baseline version
  + tenant restriction
  = effective policy
```

`PlatformRoot` owns the platform floor, publishes approved baseline versions,
and owns the formal exception process. `TenantRoot` may adopt an approved
baseline for its verified tenant and choose supported stricter settings. A
tenant cannot weaken this baseline by changing a configuration value.

An exception cannot weaken a platform invariant. A permitted relaxation of a
non-invariant setting requires an explicit owner, reason, expiry, scope,
approval, and durable evidence. It must be evaluated before it becomes
effective and must never be an undocumented database edit or hidden checkbox.

Tenant policy records contain version references and non-secret settings only.
They never contain passwords, password hashes, reset tokens, session tokens,
mail-provider credentials, or cloud-provider secrets.

## Control Defaults

The values below are the v1 default. “Tenant may tighten” means a tenant may
choose a supported value that is at least as restrictive; it does not mean the
tenant can provide arbitrary identity-provider configuration.

| Control | v1 requirement | Tenant may tighten | Tenant may not do |
| --- | --- | --- | --- |
| Sign-in | Human identities use verified email and password. Authentication and policy enforcement happen server-side. | Add an available, approved factor when the platform supports it. | Treat an unverified email, a client-side check, or a token claim alone as tenant membership or authorisation. |
| Password length | Require at least 15 characters; accept at least 64 characters without truncation. | Require a longer minimum supported by the selected provider. | Set a shorter minimum or silently truncate a password. |
| Password usability | Permit spaces, Unicode, paste, password managers, and browser autofill. Do not require arbitrary character-class composition rules. | None, except an approved accessibility-preserving provider constraint. | Ban password managers, paste, Unicode, or add cosmetic composition rules. |
| Password screening | Reject common, breached, product/tenant-name, and email-derived passwords when a password is set or changed. Password material is never logged. | Add an approved contextual blocklist. | Turn off required screening or retain raw password material. |
| Password lifetime | Do not force periodic password changes. Require a change after confirmed compromise, recovery, or authorised administrative revocation. | Require a change sooner after a tenant-confirmed security incident. | Add routine expiry as a substitute for breach detection and recovery controls. |
| Email verification | Every human identity verifies its email before it can become active. A self-service signup does so before it can enter pending approval. | Add a tenant-approved verified-domain requirement where supported. | Activate a human identity before verification or bypass verification with a tenant setting. |
| Verification and reset links | Use separate `verify-email` and `reset-password` purposes. Tokens are cryptographically strong, single-use, expire after 15 minutes, and are invalidated after use. | Shorten lifetime or add approved delivery restrictions. | Reuse a token, extend it beyond 15 minutes, use one purpose for another, or log/referrer-leak it. |
| Reset outcome | After a successful reset, revoke every active session for that identity. Do not automatically authenticate the reset browser; require ordinary sign-in with the new password. Send a safe post-reset notice. | Add an approved tenant notice or stricter recovery step. | Keep any prior session active or disclose credential/token material in a notice. |
| Sessions | Enforce a 15-minute idle limit and an 8-hour absolute limit server-side. Rotate the session identifier after authentication and after a privilege-changing event. | Shorten either lifetime or require reauthentication more often. | Extend either limit or rely solely on client-side expiry. |
| Step-up reauthentication | Require current-password reauthentication before password/email change, privileged role grant/revoke, tenant policy change, and ordinary privileged recovery administration. The replacement-root migration is a separate protected path, not a normal session action. | Require reauthentication for more high-risk actions. | Remove it from the listed actions. |
| Login-abuse response | Use generic responses and progressive server-side delay after repeated failures. The default begins at five failures in a rolling 15-minute window, escalates through 30 seconds, 1 minute, 5 minutes, and at most 15 minutes, then decays after a quiet period. Never use a permanent automatic lockout. | Lower the threshold, lengthen cooldowns within the 15-minute maximum, or add a supported risk signal. | Disable per-account defence, expose whether an account exists, or create a permanent automatic lockout. |
| Reset-request abuse response | Return a uniform response and timing whether or not the identity exists. Limit sends to three per identity per hour and requests from a trusted client source to ten per 15 minutes. | Lower either limit. | Reveal account existence, trust a spoofable client-address header, or remove all reset-request limits. |
| Audit and security evidence | Emit allowlisted audit facts for root lifecycle, tenant-root grants/revocations, tenant-policy version changes, and completed password resets. Record escalating failed login/reset patterns as security signals. | Add approved tenant-specific security notifications. | Store passwords, tokens, raw headers, raw request bodies, or personal business data in these records. |
| Notifications | Notify the identity after a completed reset and after a material account/privilege change when a safe delivery path is available. Do not send a notice for every failed login. | Add additional safe notices. | Put credentials, reset URLs/tokens, or sensitive tenant content in a notice. |
| MFA posture | MFA is not initially enforced. The baseline is deliberately single-factor and is not a claim that MFA support exists. | Require MFA only once an approved, tested MFA capability is available. | Represent MFA as enforced before the target can actually enrol, challenge, recover, and audit it. |

## Implementation Rules Behind The Policy

The policy describes outcomes; an implementation must still prove how it
achieves them.

- Password verification must use an approved adaptive password-hashing scheme
  or a managed provider that demonstrably provides equivalent protection. Raw
  passwords and password-equivalent material must never leave the identity
  boundary in application logs, audit records, traces, or error payloads.
- The selected target must use a trusted proxy/address resolver before it
  applies a client-source rate limit. A forwarded header supplied directly by
  an internet client is not a trusted source identity.
- Link tokens are credential-like data. They must be removed from application
  URLs before further navigation and excluded from telemetry, analytics,
  referrer-bearing requests, support tickets, and error capture.
- Reset and sign-in responses must be intentionally indistinguishable where
  their difference would reveal whether an account exists. Equal wording alone
  is not enough when timing or delivery behaviour leaks the answer.
- Session revocation must be enforceable across every active session type,
  including browser, API, mobile, and remembered sessions. Merely deleting a
  browser cookie does not meet this rule.
- A policy-version change is a security change. Its authorised actor, scope,
  before/after version, validation result, effective time, and session/pending
  signup impact must be audit-recorded using allowlisted facts.

## Required Safe Evidence

At minimum, the eventual human identity implementation must retain separate
record classes rather than one oversized “identity log”:

| Record class | Required examples | Must not contain |
| --- | --- | --- |
| Audit event | `PlatformRoot` creation/recovery/disablement; `TenantRoot` grant/revoke; baseline adoption or tenant-policy version change; password reset completed. | Credentials, tokens, raw request bodies, personal business records, or provider error payloads. |
| Security signal | Escalating sign-in or reset failures, suspected reset abuse, root/policy change requiring operator attention. | Repeated password guesses, full raw client headers, or a copy of the audit event’s sensitive context. |
| Operational record | Delivery-provider failure category, rate-limit dependency unavailable, session-revocation subsystem failure. | Identity credentials, recovery links, or full provider response bodies. |

The general audit, security-signal, and observability profiles remain the
source of truth for record shape, retention, residency, and access controls.
This baseline only states the minimum identity facts that must be represented.

## Medical And Sensitive-Data Gate

Personal-data onboarding remains separately subject to privacy, legal,
residency, and operational proof. Medical or other special-category data must
not be accepted until an MFA-capable identity baseline and target are available
and the required privileged roles are actually protected by it. A future MFA
policy must cover enrolment, challenge, recovery, revocation, audit evidence,
and safe failure behaviour; adding an “MFA required” checkbox is not enough.

## Adoption, Change, And Completion

An app or product explicitly references the adopted baseline version. The
tenant policy resolver calculates only supported tenant restrictions and
rejects a setting that would weaken the effective policy. An existing session
or pending signup affected by a policy change is handled according to the
approved migration/transition rule; policy changes do not silently leave old
security assumptions in force.

Before the baseline can be called implemented for the production reference
target, the target must prove all of the following:

1. a selected human-identity adapter and configuration satisfy each v1 control;
2. tenant baseline adoption, tightening, validation, and audit behaviour work
   at the server boundary;
3. approval, membership, group/permission, and resource authorisation remain
   independent from authentication;
4. verification, reset, session invalidation, reauthentication, and abuse
   controls have negative and recovery tests;
5. safe audit, security-signal, notification, and operational records are
   delivered according to their separate target policies; and
6. deployment, incident, and replacement-root recovery runbooks have an owner
   and target evidence.

Until then, the correct maturity state is `requirements captured`.

## Explicit Non-Goals

This standard does not select Cognito settings, a mail provider, a database
schema, a secret manager, an AWS region, an authentication UI, or a concrete
MFA technology. Those are later adapter, target, and deployment decisions.
It also does not grant product permissions, define tenant group membership, or
replace a resource-level authorisation policy.
