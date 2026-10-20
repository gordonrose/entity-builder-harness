export interface PlatformReleaseIdentity {
  readonly sourceCommitSha?: string;
}

export interface PlatformReleaseVerificationResponse {
  readonly release: PlatformReleaseIdentity;
}

const safeReleaseMetadataValue = /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/;

export function resolvePlatformReleaseIdentity(sourceCommitSha: string | undefined): PlatformReleaseIdentity {
  if (sourceCommitSha === undefined || !safeReleaseMetadataValue.test(sourceCommitSha)) {
    return {};
  }

  return { sourceCommitSha };
}

export function platformReleaseVerificationResponse(
  release: PlatformReleaseIdentity,
): PlatformReleaseVerificationResponse {
  return { release };
}
