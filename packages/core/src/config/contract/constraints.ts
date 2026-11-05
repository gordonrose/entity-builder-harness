import type { ConfigSettingRule } from "./types";

/** Destination ports exclude listener-only port 0; consumers choose their own source binding. */
export const destinationPortConstraint = Object.freeze({
  kind: "integer", minimum: 1, maximum: 65_535,
} as const satisfies ConfigSettingRule);
