export const persistenceLeaseDurationRequirement = Object.freeze({ minimum: 1, integer: true });
export const persistenceLeaseDurationReasons = ["missing", "wrong-type", "not-finite", "invalid-integer", "not-positive"] as const;
export type PersistenceLeaseDurationReason = (typeof persistenceLeaseDurationReasons)[number];
