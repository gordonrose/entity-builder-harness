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
