import type { MessageDescriptor } from "../shared/index";

export const dataSensitivities = ["public", "internal", "confidential", "restricted", "secret"] as const;
export type DataSensitivity = (typeof dataSensitivities)[number];

export const sensitiveValueKinds = [
  "credential",
  "token",
  "api-key",
  "private-key",
  "secret",
  "personal-data",
  "tenant-data",
  "financial-data",
  "security-evidence",
] as const;
export type SensitiveValueKind = (typeof sensitiveValueKinds)[number];

export interface DataClassification {
  readonly kind: SensitiveValueKind;
  readonly sensitivity: DataSensitivity;
  readonly reason?: MessageDescriptor;
}

export function dataClassification(input: {
  readonly kind: SensitiveValueKind;
  readonly sensitivity: DataSensitivity;
  readonly reason?: MessageDescriptor;
}): DataClassification {
  assertKnownValue("sensitive value kind", input.kind, sensitiveValueKinds);
  assertKnownValue("data sensitivity", input.sensitivity, dataSensitivities);

  return {
    kind: input.kind,
    sensitivity: input.sensitivity,
    ...(input.reason === undefined ? {} : { reason: input.reason }),
  };
}

function assertKnownValue<TValue extends string>(
  label: string,
  value: string,
  allowedValues: readonly TValue[],
): asserts value is TValue {
  if (!allowedValues.includes(value as TValue)) {
    throw new TypeError(`${label} must be one of: ${allowedValues.join(", ")}.`);
  }
}
