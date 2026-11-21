import { deepEqual, throws } from "node:assert/strict";
import { copyJsonValue } from "../../../../src/shared/index";

const copiedJson = copyJsonValue({
  id: "deal-123",
  score: 12,
  flags: [true, false],
  nested: { value: null },
});
deepEqual(copiedJson, {
  id: "deal-123",
  score: 12,
  flags: [true, false],
  nested: { value: null },
});
throws(() => copyJsonValue(Number.NaN, "test JSON value"), /finite numbers/);
throws(() => copyJsonValue(Number.POSITIVE_INFINITY, "test JSON value"), /finite numbers/);
throws(() => copyJsonValue(new Date() as never, "test JSON value"), /plain objects/);

console.log("Core shared JSON unit tests passed.");
