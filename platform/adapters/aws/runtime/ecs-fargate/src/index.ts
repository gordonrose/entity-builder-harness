import { isIP } from "node:net";
import type {
  PlatformClientAddressResolver,
  PlatformClientAddressResolverInput,
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
    throw new RangeError("ECS Fargate client-address trust requires ALB-only task ingress.");
  }

  return {
    resolve: (input) => finalValidForwardedAddress(input) ?? input.socketPeerAddress,
  };
}

function finalValidForwardedAddress(input: PlatformClientAddressResolverInput): string | undefined {
  const forwarded = firstHeaderValue(input.headers, "x-forwarded-for");
  if (forwarded === undefined) {
    return undefined;
  }

  const finalAddress = forwarded.split(",").map((value) => value.trim()).at(-1);
  return finalAddress !== undefined && isIP(finalAddress) !== 0 ? finalAddress : undefined;
}

function firstHeaderValue(
  headers: Readonly<Record<string, string | readonly string[]>>,
  name: string,
): string | undefined {
  const entry = Object.entries(headers).find(([key]) => key.toLowerCase() === name);
  const value = entry?.[1];
  return typeof value === "string" ? value : value?.[0];
}
