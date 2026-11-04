import type { ConfigSettingRequirement } from "@kanbien/core";

export const sqsReceiveWaitConstraint = Object.freeze({ kind: "integer", minimum: 0, maximum: 20 } as const);
export const sqsVisibilityTimeoutConstraint = Object.freeze({ kind: "integer", minimum: 0, maximum: 43_200 } as const);
const requiredText = Object.freeze({ kind: "text" } as const);
export const sqsSenderRequirements = Object.freeze([
  Object.freeze({ setting: "queue.address", rule: requiredText }),
  Object.freeze({ setting: "queue.region", rule: requiredText }),
] as const satisfies readonly ConfigSettingRequirement[]);
export const sqsWorkerRequirements = Object.freeze([
  ...sqsSenderRequirements,
  Object.freeze({ setting: "queue.receive-wait", rule: sqsReceiveWaitConstraint }),
  Object.freeze({ setting: "queue.visibility-timeout", rule: sqsVisibilityTimeoutConstraint }),
] as const satisfies readonly ConfigSettingRequirement[]);
