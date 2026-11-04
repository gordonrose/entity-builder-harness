import { createConfigIssueCollector } from "@kanbien/core/config";
import type { MetricKind } from "@kanbien/core/monitoring";
import type { Result } from "@kanbien/core/shared";
import { observabilityArray, observabilityConfigurationField, observabilityConfigurationObject, observabilityIntegerIssue, observabilityTextIssue,
  type ObservabilityConfigurationFailure, type ObservabilityConfigurationReason } from "./configuration";

/** Provider-neutral mapping and aggregation policy, not an exporter or provider selection. */
export interface PlatformMetricSeries {
  readonly sourceName: string; readonly sourceKind: MetricKind; readonly sourceUnit: string;
  readonly instrumentName: string; readonly description: string; readonly allowedLabelNames: readonly string[];
  readonly cardinalityLimit: number; readonly histogramBucketBoundaries?: readonly number[];
}

export function validatePlatformMetricSeries(value: unknown): Result<readonly PlatformMetricSeries[], ObservabilityConfigurationFailure> {
  const collector = createConfigIssueCollector<ObservabilityConfigurationReason>();
  const series = observabilityArray(value);
  if (!series || series.length === 0) {
    collector.add({ setting: "metrics.series", reason: value === undefined ? "missing" : !series ? "wrong-shape" : "empty" });
    return { ok: false, error: collector.finish() };
  }
  const sources = new Map<string, number>(), instruments = new Map<string, number>();
  const parsed: PlatformMetricSeries[] = [];
  for (let index = 0; index < series.length; index++) {
    const row = series[index];
    const issue = (setting: string, reason: ObservabilityConfigurationReason, attributeIndex?: number, relatedIndex?: number) => collector.add({ setting, reason, index,
      ...(attributeIndex === undefined ? {} : { attributeIndex }), ...(relatedIndex === undefined ? {} : { relatedIndex }) });
    if (!observabilityConfigurationObject(row)) { issue("metrics.series", "wrong-shape"); continue; }
    const text: Record<string, unknown> = {};
    for (const [key, setting] of [["sourceName", "series.source-name"], ["sourceKind", "series.source-kind"], ["sourceUnit", "series.source-unit"],
      ["instrumentName", "series.instrument-name"], ["description", "series.description"]] as const) {
      const raw = observabilityConfigurationField(row, key); text[key] = raw;
      const reason = observabilityTextIssue(raw); if (reason) issue(setting, reason);
      else if (key === "sourceKind" && !["counter", "gauge", "histogram", "timer"].includes(raw as string)) issue(setting, "unsupported");
      if (!reason && (key === "sourceName" || key === "instrumentName")) {
        const previous = key === "sourceName" ? sources : instruments;
        const peer = previous.get(raw as string);
        if (peer !== undefined) issue(setting, "duplicate", undefined, peer); else previous.set(raw as string, index);
      }
    }
    const cardinality = observabilityConfigurationField(row, "cardinalityLimit");
    const cardinalityReason = observabilityIntegerIssue(cardinality);
    if (cardinalityReason) issue("series.cardinality", cardinalityReason);
    else if ((cardinality as number) > 1000) issue("series.cardinality", "out-of-range");
    const rawLabels = observabilityConfigurationField(row, "allowedLabelNames"), labels = observabilityArray(rawLabels);
    if (!labels) issue("series.allowed-labels", rawLabels === undefined ? "missing" : "wrong-type");
    else {
      const names = new Map<string, number>();
      for (let member = 0; member < labels.length; member++) {
        const label = labels[member];
        if (typeof label !== "string") issue("series.allowed-labels", "wrong-type", member);
        else if (!/^[a-z][a-z0-9_]*$/.test(label)) issue("series.allowed-labels", "invalid-format", member);
        else { const peer = names.get(label); if (peer !== undefined) issue("series.allowed-labels", "duplicate", member, peer); else names.set(label, member); }
      }
    }
    const rawBuckets = observabilityConfigurationField(row, "histogramBucketBoundaries"), buckets = observabilityArray(rawBuckets);
    const distribution = text["sourceKind"] === "histogram" || text["sourceKind"] === "timer";
    if (distribution && rawBuckets === undefined) issue("series.buckets", "required-for-kind");
    if ((text["sourceKind"] === "counter" || text["sourceKind"] === "gauge") && rawBuckets !== undefined) issue("series.buckets", "forbidden-for-kind");
    if (rawBuckets !== undefined) {
      if (!buckets) issue("series.buckets", "wrong-type");
      else {
        if (distribution && buckets.length === 0) issue("series.buckets", "empty");
        for (let member = 0; member < buckets.length; member++) {
          const bucket = buckets[member], previous = buckets[member - 1];
          if (typeof bucket !== "number") issue("series.buckets", "wrong-type", member);
          else if (!Number.isFinite(bucket)) issue("series.buckets", "not-finite", member);
          else if (bucket <= 0) issue("series.buckets", "not-positive", member);
          else if (member > 0 && typeof previous === "number" && Number.isFinite(previous) && previous > 0 && bucket <= previous) issue("series.buckets", "not-strictly-increasing", member, member - 1);
        }
      }
    }
    parsed.push({ sourceName: text["sourceName"] as string, sourceKind: text["sourceKind"] as MetricKind, sourceUnit: text["sourceUnit"] as string,
      instrumentName: text["instrumentName"] as string, description: text["description"] as string, allowedLabelNames: labels as readonly string[], cardinalityLimit: cardinality as number,
      ...(rawBuckets === undefined ? {} : { histogramBucketBoundaries: buckets as readonly number[] }) });
  }
  const failure = collector.finish(); return failure.issues.length ? { ok: false, error: failure } : { ok: true, value: parsed };
}
