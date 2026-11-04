import type { ConfigSettingRule } from "@kanbien/core/config";

export const persistenceAcceptanceProof = Object.freeze({
  recordId: Object.freeze({ kind: "text", pattern: /^core-persistence-[a-z0-9-]{8,80}$/ } as const satisfies ConfigSettingRule),
  fingerprint: Object.freeze({ kind: "text", pattern: /^[a-f0-9]{64}$/ } as const satisfies ConfigSettingRule),
});
