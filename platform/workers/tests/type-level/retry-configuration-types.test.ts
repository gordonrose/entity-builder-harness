import { validateWorkerRetryConfiguration, validateWorkerRetryDelay, type CheckedWorkerRetryConfiguration } from "../../src/index";
const result = validateWorkerRetryConfiguration({ maxAttempts: 3, retryBackoffMs: attempt => attempt * 1000 });
if (result.ok) {
  const checked: CheckedWorkerRetryConfiguration = result.value;
  // @ts-expect-error Checked retry instructions cannot be reassigned.
  checked.maxAttempts = 0;
}
// @ts-expect-error Public instructions require an actual number.
validateWorkerRetryConfiguration({ maxAttempts: "3" });
// @ts-expect-error Public instructions require a callable delay calculator.
validateWorkerRetryConfiguration({ retryBackoffMs: 1 });
const delay = validateWorkerRetryDelay(undefined);
if (delay.ok) { const milliseconds: number = delay.value; void milliseconds; }
