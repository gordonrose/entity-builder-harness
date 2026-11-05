# AWS ECS Fargate Runtime Adapter

This package contains target-composition helpers for ECS Fargate. It does not
provision AWS resources or expose provider details to apps.

| File | Responsibility |
| --- | --- |
| src/index.ts | Accept the final ALB-appended client address only when the task network policy guarantees ALB-only ingress. |
| tests/ | Prove address selection and prevent app/infra dependency leaks. |

The generic server never trusts forwarded headers by default. A deployment
target may inject this resolver only together with the matching service
security-group policy.

An unsupported constructor mode retains its RangeError and adds a Server-owned
configuration record. Optional resolver-input observations describe only the
fallback reason and whether the socket peer or no address was selected. They
contain no address or header value and do not change resolution or trust policy.

The server delivers these records only under its explicit decision-diagnostics
option, once through the selected route's operational-log
policy. Normal target CLIs keep that option disabled. Compiled process/shell
fixtures exercise explicit opt-in; they do not claim enabled CLI logging or
prove that deployed networking actually restricts ingress to the ALB.
