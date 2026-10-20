# Server Verification Source Map

This folder defines the safe application-side release identity response used by
an internal verifier. It does not identify a cloud workload, prove an image
digest, select a route, or accept a deployment.

| File | Responsibility |
| --- | --- |
| `release.ts` | Filters release metadata to a bounded safe shape and forms the verification response. |
| `index.ts` | Deliberate public verification exports. |

A later target verifier must join this response with independent workload and
package-custody evidence before treating a release as verified.
