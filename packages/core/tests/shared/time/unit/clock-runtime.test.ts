import { equal, notEqual } from "node:assert/strict";
import { fixedClock } from "../../../../src/shared/index";

const fixedNow = new Date("2026-07-06T12:00:00Z");
const clock = fixedClock(fixedNow);
const firstReading = clock.now();
const secondReading = clock.now();
equal(firstReading.toISOString(), "2026-07-06T12:00:00.000Z", "fixed clock returns the supplied instant");
equal(secondReading.toISOString(), "2026-07-06T12:00:00.000Z", "repeated reads do not advance the clock");
notEqual(firstReading, fixedNow, "fixed clock does not expose its input Date");
notEqual(firstReading, secondReading, "each clock read returns a distinct Date");

firstReading.setUTCFullYear(2030);
equal(fixedNow.toISOString(), "2026-07-06T12:00:00.000Z", "mutating a reading does not mutate the input");
equal(secondReading.toISOString(), "2026-07-06T12:00:00.000Z", "mutating a reading does not mutate another reading");
equal(clock.now().toISOString(), "2026-07-06T12:00:00.000Z", "mutating a reading does not affect future reads");

console.log("packages/core shared time clock unit tests passed.");
