import { deepEqual, equal, throws } from "node:assert/strict";
import { metricName, metricUnit, metricLabels, type MetricValidationObservation } from "../src/monitoring/index";

const cases: readonly [() => unknown, MetricValidationObservation][] = [
  [() => metricName("", observe), { field: "name", reason: "empty" }],
  [() => metricName(" x.y", observe), { field: "name", reason: "untrimmed" }],
  [() => metricName("X.y", observe), { field: "name", reason: "invalid-format" }],
  [() => metricUnit("", observe), { field: "unit", reason: "empty" }],
  [() => metricUnit("count ", observe), { field: "unit", reason: "untrimmed" }],
  [() => metricUnit("Count", observe), { field: "unit", reason: "invalid-format" }],
  [() => metricLabels({ safe: 1, Bad: "canary" }, {}, observe), { field: "label", reason: "invalid-format", index: 1 }],
  [() => metricLabels({ tenant_id: "canary" }, {}, observe), { field: "label", reason: "unsafe-name", index: 0 }],
  [() => metricLabels({ safe: Infinity }, {}, observe), { field: "label", reason: "not-finite", index: 0 }],
  [() => metricLabels({ safe: "" }, {}, observe), { field: "label", reason: "empty", index: 0 }],
  [() => metricLabels({ safe: "x".repeat(129) }, {}, observe), { field: "label", reason: "too-long", index: 0 }],
];
let observations: MetricValidationObservation[] = [];
function observe(value: MetricValidationObservation): void { observations.push(value); }
for (const [invoke, expected] of cases) {
  observations = [];
  throws(invoke, TypeError);
  deepEqual(observations, [expected]);
  equal(Object.isFrozen(observations[0]), true);
}
observations = [];
equal(metricName("valid.name-1", observe), "valid.name-1");
equal(metricUnit("ms", observe), "ms");
deepEqual(metricLabels({ safe: "x".repeat(128), finite: -1, zero: 0, truth: false }, {}, observe),
  { safe: "x".repeat(128), finite: -1, zero: 0, truth: false });
deepEqual(observations, []);
throws(() => metricName("", () => { throw new Error("observer-canary"); }), /^TypeError: metric name must be non-empty and trimmed\.$/);
let previous: unknown;
try { metricName(""); } catch (error) { previous = error; }
observations = [];
const hostile = { length: 1, trim() { throw previous; } } as unknown as string;
throws(() => metricName(hostile, observe), (error) => error === previous);
deepEqual(observations, [], "a prior actual predicate error rethrown from input cannot become a current observation");
console.log("Core metric predicate observations preserve validation and current-invocation evidence.");
