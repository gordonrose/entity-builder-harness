import type { MessageDescriptor } from "../shared/index";
import type { MonitoringComponentRef, MonitoringSignalName } from "./identifiers";
import { metricKinds, type MonitoringMetricDefinition } from "./metrics";
import { assertKnownValue, assertNonEmpty } from "./validation";

export const monitoringSignalCategories = [
  "traffic",
  "latency",
  "errors",
  "saturation",
  "dependency",
  "queue",
  "job",
  "business-critical-path",
  "security",
  "cost",
] as const;
export type MonitoringSignalCategory = (typeof monitoringSignalCategories)[number];

export const monitoringSignalIntents = [
  "health-detection",
  "alerting",
  "capacity-planning",
  "debugging",
  "service-level-indicator",
  "cost-control",
] as const;
export type MonitoringSignalIntent = (typeof monitoringSignalIntents)[number];

export interface MonitoringSignalDefinition {
  readonly name: MonitoringSignalName;
  readonly category: MonitoringSignalCategory;
  readonly owner: string;
  readonly intents: readonly MonitoringSignalIntent[];
  readonly component?: MonitoringComponentRef;
  readonly metric?: MonitoringMetricDefinition;
  readonly description?: MessageDescriptor;
}

export function monitoringSignalDefinition(input: {
  readonly name: MonitoringSignalName;
  readonly category: MonitoringSignalCategory;
  readonly owner: string;
  readonly intents: readonly MonitoringSignalIntent[];
  readonly component?: MonitoringComponentRef;
  readonly metric?: MonitoringMetricDefinition;
  readonly description?: MessageDescriptor;
}): MonitoringSignalDefinition {
  assertKnownValue("monitoring signal category", input.category, monitoringSignalCategories);
  assertNonEmpty("monitoring signal owner", input.owner);

  if (input.intents.length === 0) {
    throw new TypeError("monitoring signal intents must include at least one intent.");
  }

  for (const intent of input.intents) {
    assertKnownValue("monitoring signal intent", intent, monitoringSignalIntents);
  }

  if (input.metric !== undefined) {
    assertKnownValue("metric kind", input.metric.kind, metricKinds);
  }

  return {
    name: input.name,
    category: input.category,
    owner: input.owner,
    intents: [...input.intents],
    ...(input.component === undefined ? {} : { component: { ...input.component } }),
    ...(input.metric === undefined ? {} : { metric: { ...input.metric } }),
    ...(input.description === undefined ? {} : { description: input.description }),
  };
}
