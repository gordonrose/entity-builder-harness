import type { JsonValue, Result } from "@kanbien/core/shared";
import type { PlatformContractError } from "@kanbien/platform-contracts";

export type PlatformRuntimeErrorCode =
  | "PLATFORM_RUNTIME_APP_MOUNT_FAILED"
  | "PLATFORM_RUNTIME_REGISTRY_INVALID"
  | "PLATFORM_RUNTIME_LIFECYCLE_FAILED"
  | "PLATFORM_RUNTIME_INVALID_STATE";

export interface PlatformRuntimeError {
  readonly code: PlatformRuntimeErrorCode;
  readonly defaultMessage: string;
  readonly details?: Readonly<Record<string, JsonValue>>;
  readonly cause?: unknown;
}

export interface PlatformRuntimeMountFailure extends PlatformRuntimeError {
  readonly code: "PLATFORM_RUNTIME_APP_MOUNT_FAILED" | "PLATFORM_RUNTIME_REGISTRY_INVALID";
  readonly contractErrors: readonly PlatformContractError[];
}

export function platformRuntimeMountFailure(
  code: PlatformRuntimeMountFailure["code"],
  contractErrors: readonly PlatformContractError[],
  details?: Readonly<Record<string, JsonValue>>,
  cause?: unknown,
): Result<never, PlatformRuntimeMountFailure> {
  return {
    ok: false,
    error: {
      code,
      defaultMessage: code === "PLATFORM_RUNTIME_REGISTRY_INVALID"
        ? "Platform runtime registry failed validation."
        : "Platform app failed during runtime mount.",
      contractErrors: [...contractErrors],
      ...(details === undefined ? {} : { details }),
      ...(cause === undefined ? {} : { cause }),
    },
  };
}

export function platformRuntimeFailure(
  code: PlatformRuntimeErrorCode,
  defaultMessage: string,
  details?: Readonly<Record<string, JsonValue>>,
  cause?: unknown,
): Result<never, PlatformRuntimeError> {
  return {
    ok: false,
    error: {
      code,
      defaultMessage,
      ...(details === undefined ? {} : { details }),
      ...(cause === undefined ? {} : { cause }),
    },
  };
}
