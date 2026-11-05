import type { MessageDescriptor } from "../shared/index";
import type { MonitoringComponentRef, MonitoringSignalName } from "./identifiers";
import { metricKinds, type MonitoringMetricDefinition } from "./metrics";
import { assertKnownValue, assertNonEmpty } from "./validation";
import type { CoreMonitoringDiagnosticOptions } from "./boundary-diagnostics";
import { MonitoringObservation } from "./observations";

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
}, diagnostics?: CoreMonitoringDiagnosticOptions): MonitoringSignalDefinition {
  const observation = new MonitoringObservation("signal-definition", diagnostics);
  return observation.run(() => {
    const category = observation.at("input-projection", "signal-category", () => input.category);
    observation.at("predicate-invocation", "signal-category", () => assertKnownValue("monitoring signal category", category, monitoringSignalCategories, (message, reason) => observation.reject(message, "signal-category", reason)));
    const owner = observation.at("input-projection", "signal-owner", () => input.owner);
    observation.at("predicate-invocation", "signal-owner", () => assertNonEmpty("monitoring signal owner", owner, undefined, undefined, (message, reason) => observation.reject(message, "signal-owner", reason)));
    if (observation.at("input-projection", "signal-intents", () => input.intents.length) === 0) throw observation.reject("monitoring signal intents must include at least one intent.", "signal-intents", "empty");
    let ordinal = 0;
    observation.at("intent-iteration", "signal-intents", () => {
      for (const intent of input.intents) {
        observation.at("predicate-invocation", "signal-intent", () => assertKnownValue("monitoring signal intent", intent, monitoringSignalIntents, (message, reason) => observation.reject(message, "signal-intent", reason, ordinal)));
        ordinal++;
        // The next iterator step is not another predicate invocation.
        observation.at("intent-iteration", "signal-intents", () => undefined);
      }
    });
    if (observation.at("input-projection", "metric", () => input.metric) !== undefined) {
      const kind = observation.at("input-projection", "metric-kind", () => input.metric!.kind);
      observation.at("predicate-invocation", "metric-kind", () => assertKnownValue("metric kind", kind, metricKinds, (message, reason) => observation.reject(message, "metric-kind", reason)));
    }
    return {
      name: observation.at("result-copy", "name", () => input.name),
      category: observation.at("result-copy", "signal-category", () => input.category),
      owner: observation.at("result-copy", "signal-owner", () => input.owner),
      intents: observation.at("intent-iteration", "signal-intents", () => [...input.intents]),
      ...(observation.at("input-projection", "component", () => input.component) === undefined ? {} : { component: observation.at("component-copy", "component", () => ({ ...input.component! })) }),
      ...(observation.at("input-projection", "metric", () => input.metric) === undefined ? {} : { metric: observation.at("result-copy", "metric", () => ({ ...input.metric! })) }),
      ...(observation.at("input-projection", "description", () => input.description) === undefined ? {} : { description: observation.at("result-copy", "description", () => input.description) }),
    };
  });
}
