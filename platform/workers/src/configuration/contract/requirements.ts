export const workerDefaultMaxAttempts = 3;
export const workerRetryConfigurationReasons = ["wrong-type", "not-finite", "invalid-integer", "not-positive", "not-callable"] as const;
export const workerRetryDelayReasons = ["missing", "wrong-type", "not-finite", "negative"] as const;
export type WorkerRetryConfigurationReason = (typeof workerRetryConfigurationReasons)[number];
export type WorkerRetryDelayReason = (typeof workerRetryDelayReasons)[number];
export interface WorkerRetryConfigurationInput {
  readonly maxAttempts?: number;
  readonly retryBackoffMs?: (attempt: number) => number;
}
export interface CheckedWorkerRetryConfiguration {
  readonly maxAttempts: number;
  readonly retryBackoffMs: (attempt: number) => number;
}
