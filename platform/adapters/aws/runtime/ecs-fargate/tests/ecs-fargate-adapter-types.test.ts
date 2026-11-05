import { createAlbTrustedClientAddressResolver } from "../src/index";
import type { PlatformClientAddressResolverInput } from "@kanbien/platform-server";

const resolver = createAlbTrustedClientAddressResolver({ ingressMode: "alb-security-group-only" });
const observed: PlatformClientAddressResolverInput = { headers: {}, onDiagnostic(record) { const code: string = record.code; return code; } };
void resolver;
void observed;
// @ts-expect-error Trust selection remains the existing single reviewed mode.
createAlbTrustedClientAddressResolver({ ingressMode: "automatic" });
// @ts-expect-error Observation is an optional callback, not a logging switch.
const invalid: PlatformClientAddressResolverInput = { headers: {}, onDiagnostic: true };
void invalid;
