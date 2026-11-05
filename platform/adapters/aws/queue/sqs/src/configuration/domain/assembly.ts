import type { SqsSenderConfiguration, SqsWorkerConfiguration } from "../contract/types";

export function assembleSqsSenderConfiguration(values: Readonly<Record<string, string | number>>): { readonly ok: true; readonly value: SqsSenderConfiguration } {
  return { ok: true, value: { queueUrl: values["queue.address"] as string, region: values["queue.region"] as string } };
}
export function assembleSqsWorkerConfiguration(values: Readonly<Record<string, string | number>>): { readonly ok: true; readonly value: SqsWorkerConfiguration } {
  return { ok: true, value: { ...assembleSqsSenderConfiguration(values).value,
    waitTimeSeconds: values["queue.receive-wait"] as number, visibilityTimeoutSeconds: values["queue.visibility-timeout"] as number } };
}
