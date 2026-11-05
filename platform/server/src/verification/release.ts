import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { observeServerDiagnostic, serverConfigurationOmissionRecord } from "../diagnostics";

export interface PlatformReleaseIdentity {
  readonly sourceCommitSha?: string;
}

export interface PlatformReleaseVerificationResponse {
  readonly release: PlatformReleaseIdentity;
}

const safeReleaseMetadataValue = /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/;

export function resolvePlatformReleaseIdentity(sourceCommitSha: string | undefined, onDiagnostic?: (record: DiagnosticRecord) => unknown): PlatformReleaseIdentity {
  if (sourceCommitSha === undefined || !safeReleaseMetadataValue.test(sourceCommitSha)) {
    observeServerDiagnostic(onDiagnostic, serverConfigurationOmissionRecord("release.source-commit",
      sourceCommitSha === undefined ? "missing" : typeof sourceCommitSha === "string" && sourceCommitSha.length === 0 ? "empty" : "format-rejected"));
    return {};
  }

  return { sourceCommitSha };
}

export function platformReleaseVerificationResponse(
  release: PlatformReleaseIdentity,
): PlatformReleaseVerificationResponse {
  return { release };
}
