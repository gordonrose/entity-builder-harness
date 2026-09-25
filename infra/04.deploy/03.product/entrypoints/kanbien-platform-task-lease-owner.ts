// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: infra.04-deploy.03-product.entrypoint.kanbien-platform-task-lease-owner
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: persistence
//   disciplines:
//   - security
//   - sre
//   kind: code
//   purpose: Derive a non-sensitive unique durable lease owner for one Kanbien staging Fargate task.
//   portability:
//     class: target-specific
//     targets:
//     - kanbien/staging

import { createHash } from "node:crypto"; // Hash the provider task identity before it becomes a lease-owner component.
import { // Keep durable coordination types inside the provider-neutral persistence package.
  platformPersistenceLeaseOwner, // Brand the final owner only after a safe local component exists.
  type PlatformPersistenceLeaseOwner, // State the provider-neutral value returned to relay and worker composition.
} from "@kanbien/platform-persistence"; // Do not expose an AWS task identifier outside this target boundary.

export interface TargetTaskLeaseOwnerError { // Give callers a stable safe configuration error shape.
  readonly path: string; // Name the controlled configuration source without echoing its value.
  readonly reason: string; // Describe the expected safe form without including provider data.
}

type TargetLeaseOwnerPrefix = // Limit the helper to the two reviewed durable coordination roles.
  | "kanbien.relay.instance-" // Identify a one-shot outbox relay task.
  | "kanbien.worker.instance-"; // Identify a long-running queue-worker task.

export async function targetTaskLeaseOwnerFromEnvironment( // Resolve a unique owner without trusting a mutable container hostname on Fargate.
  env: NodeJS.ProcessEnv, // Read only process-local deployment configuration.
  prefix: TargetLeaseOwnerPrefix, // Preserve the reviewed role namespace in the resulting provider-neutral owner.
): Promise< // Return a branded owner or a safe field-level configuration error.
  | { readonly ok: true; readonly value: PlatformPersistenceLeaseOwner }
  | { readonly ok: false; readonly error: TargetTaskLeaseOwnerError }
> {
  const metadataEndpoint = env["ECS_CONTAINER_METADATA_URI_V4"]; // Fargate injects this endpoint for each running task.
  if (metadataEndpoint !== undefined) return taskLeaseOwnerFromFargateMetadata(metadataEndpoint, prefix); // Prefer the Fargate task identity when the task declares it.

  const hostname = env["HOSTNAME"]; // Retain a narrowly validated local-only fallback for compiled-image checks.
  if (hostname === undefined || !/^[a-z0-9-]+$/i.test(hostname)) { // Reject an absent or unsafe shared fallback identity.
    return taskLeaseOwnerError("HOSTNAME", "A lowercase alphanumeric or hyphenated container hostname is required outside Fargate."); // Do not echo the hostname.
  }
  const owner = platformPersistenceLeaseOwner(prefix + hostname.toLowerCase()); // Brand the fallback with the approved role namespace.
  if (!owner.ok) return taskLeaseOwnerError("HOSTNAME", "The container hostname could not form a durable lease owner."); // Preserve a stable non-sensitive failure.
  return owner; // Return the provider-neutral owner to the caller.
}

async function taskLeaseOwnerFromFargateMetadata( // Resolve one task-specific owner from the injected link-local endpoint.
  metadataEndpoint: string, // Receive the environment-provided endpoint only for exact validation below.
  prefix: TargetLeaseOwnerPrefix, // Preserve the reviewed role namespace after hashing the task identity.
): Promise< // Never return the raw task identity.
  | { readonly ok: true; readonly value: PlatformPersistenceLeaseOwner }
  | { readonly ok: false; readonly error: TargetTaskLeaseOwnerError }
> {
  let endpoint: URL; // Hold the parsed URI only in process memory.
  try {
    endpoint = new URL(metadataEndpoint); // Parse first so the target can reject malformed configuration.
    endpoint.pathname = endpoint.pathname.replace(/\/?$/, "/") + "task"; // Request the documented task metadata resource rather than a caller-supplied path.
    endpoint.search = ""; // Prevent query data from influencing the fixed metadata request.
    endpoint.hash = ""; // Prevent fragment data from influencing the fixed metadata request.
  } catch {
    return taskLeaseOwnerError("ECS_CONTAINER_METADATA_URI_V4", "The Fargate task metadata endpoint must be a valid URL."); // Keep malformed endpoint detail out of logs.
  }
  if (endpoint.protocol !== "http:" || endpoint.hostname !== "169.254.170.2" || endpoint.port !== "" || endpoint.username !== "" || endpoint.password !== "") { // Permit only the expected link-local ECS metadata service.
    return taskLeaseOwnerError("ECS_CONTAINER_METADATA_URI_V4", "The Fargate task metadata endpoint must remain the unauthenticated link-local service."); // Prevent arbitrary outbound metadata fetches.
  }

  const controller = new AbortController(); // Bound the metadata dependency so task startup cannot hang indefinitely.
  const timeout = setTimeout(() => controller.abort(), 1_000); // Keep the link-local read short and deterministic.
  try {
    const response = await fetch(endpoint, { signal: controller.signal }); // Fetch only the fixed validated metadata location.
    const metadata = await response.json(); // Parse the documented small task metadata object in memory.
    const taskArn = typeof metadata === "object" && metadata !== null && "TaskARN" in metadata // Check the expected key without logging the object.
      ? (metadata as { readonly TaskARN?: unknown }).TaskARN // Read only the candidate task identity.
      : undefined; // Reject a response without the expected stable key.
    if (!response.ok || typeof taskArn !== "string" || taskArn.length === 0) { // Require one successful task identity response.
      return taskLeaseOwnerError("ECS_CONTAINER_METADATA_URI_V4", "The Fargate task metadata endpoint must provide one task identity."); // Keep provider response data out of the result.
    }
    const fingerprint = createHash("sha256").update(taskArn).digest("hex").slice(0, 24); // Convert the raw identifier to a bounded non-reversible local component.
    const owner = platformPersistenceLeaseOwner(prefix + fingerprint); // Brand the hashed component for the selected durable role.
    if (!owner.ok) return taskLeaseOwnerError("ECS_CONTAINER_METADATA_URI_V4", "The Fargate task identity could not form a durable lease owner."); // Fail closed if the provider-neutral validation changes.
    return owner; // Return only the safe branded owner.
  } catch {
    return taskLeaseOwnerError("ECS_CONTAINER_METADATA_URI_V4", "The Fargate task metadata endpoint could not supply a durable lease identity."); // Avoid exposing network or parser failures.
  } finally {
    clearTimeout(timeout); // Release the short-lived startup timer on every outcome.
  }
}

function taskLeaseOwnerError( // Construct the common safe error without accepting arbitrary error payloads.
  path: string, // Name the only permitted configuration field.
  reason: string, // State the controlled expectation.
): { readonly ok: false; readonly error: TargetTaskLeaseOwnerError } {
  return { ok: false, error: { path, reason } }; // Return no endpoint, hostname, task identity, or provider payload.
}
