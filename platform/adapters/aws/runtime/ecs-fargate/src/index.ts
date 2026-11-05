import { isIP } from "node:net";
import {
  observeServerDiagnostic,
  serverClientAddressFallbackRecord,
  serverClientAddressTrustConfigurationRecord,
  type PlatformClientAddressResolver,
  type PlatformClientAddressResolverInput,
} from "@kanbien/platform-server";

export interface AlbTrustedClientAddressResolverOptions {
  readonly ingressMode: "alb-security-group-only";
}

export const adapterMetadata = {
  provider: "aws",
  capability: "runtime",
  implementation: "ecs-fargate",
  packageName: "@kanbien/platform-adapter-aws-runtime-ecs-fargate",
} as const;

export function createAlbTrustedClientAddressResolver(
  options: AlbTrustedClientAddressResolverOptions,
): PlatformClientAddressResolver {
  if (options.ingressMode !== "alb-security-group-only") {
    throw Object.assign(new RangeError("ECS Fargate client-address trust requires ALB-only task ingress."), {
      diagnosticRecord: serverClientAddressTrustConfigurationRecord(),
    });
  }

  return {
    resolve: (input) => {
      const forwarded = finalValidForwardedAddress(input);
      if (forwarded.address !== undefined) return forwarded.address;
      const fallback = input.socketPeerAddress;
      // Resolve the original fallback before optional observation. Never read
      // the peer twice or let an observer affect the selected address.
      try {
        const observer = Object.getOwnPropertyDescriptor(input, "onDiagnostic");
        if (observer && "value" in observer && typeof observer.value === "function") {
          observeServerDiagnostic(observer.value, serverClientAddressFallbackRecord(forwarded.reason, fallback === undefined ? "unavailable" : "socket-peer"));
        }
      } catch { /* Optional evidence cannot change trust selection. */ }
      return fallback;
    },
  };
}

function finalValidForwardedAddress(input: PlatformClientAddressResolverInput):
  | { readonly address: string }
  | { readonly address?: undefined; readonly reason: "forwarded-header-missing" | "forwarded-final-address-invalid" } {
  const forwarded = firstHeaderValue(input.headers, "x-forwarded-for");
  if (forwarded === undefined) {
    return { reason: "forwarded-header-missing" };
  }

  const finalAddress = forwarded.split(",").map((value) => value.trim()).at(-1);
  return finalAddress !== undefined && isIP(finalAddress) !== 0 ? { address: finalAddress } : { reason: "forwarded-final-address-invalid" };
}

function firstHeaderValue(
  headers: Readonly<Record<string, string | readonly string[]>>,
  name: string,
): string | undefined {
  const entry = Object.entries(headers).find(([key]) => key.toLowerCase() === name);
  const value = entry?.[1];
  return typeof value === "string" ? value : value?.[0];
}
