import { deepEqual, equal, match } from "node:assert/strict";
import {
  createDynamoDbFixedWindowPlatformRateLimiter,
  createDynamoDbFixedWindowPlatformRateLimiterFromEnv,
  dynamoDbRateLimitKeyHash,
  type DynamoDbFixedWindowIncrement,
} from "../src/index";

async function main(): Promise<void> {
  const increments: DynamoDbFixedWindowIncrement[] = [];
  const limiter = createDynamoDbFixedWindowPlatformRateLimiter({
    tableName: "kanbien-staging-platform-shell-rate-limits",
    limit: 3,
    windowMs: 60_000,
    clock: { now: () => new Date("2026-09-06T00:00:45.000Z") },
    store: {
      increment: async (input) => {
        increments.push(input);
        return increments.length === 1 ? "allowed" : "limited";
      },
    },
  });

  const first = await limiter.check("principal:operator-123");
  deepEqual(first, { allowed: true });
  const second = await limiter.check("principal:operator-123");
  deepEqual(second, { allowed: false, retryAfterMs: 15_000 });
  equal(increments[0]?.keyHash.includes("operator-123"), false);
  match(increments[0]?.keyHash ?? "", /^[a-f0-9]{64}$/);
  equal(increments[0]?.windowStartedAtMs, Date.parse("2026-09-06T00:00:00.000Z"));
  equal(increments[0]?.expiresAtEpochSeconds, Date.parse("2026-09-06T00:02:00.000Z") / 1_000);
  equal(dynamoDbRateLimitKeyHash("principal:operator-123"), increments[0]?.keyHash);

  const configured = createDynamoDbFixedWindowPlatformRateLimiterFromEnv({
    PLATFORM_RATE_LIMIT_DYNAMODB_TABLE: "kanbien-staging-platform-shell-rate-limits",
    PLATFORM_RATE_LIMIT_DYNAMODB_REGION: "eu-west-1",
    PLATFORM_RATE_LIMIT_LIMIT: "60",
    PLATFORM_RATE_LIMIT_WINDOW_MS: "60000",
  }, {
    store: { increment: async () => "allowed" },
  });
  equal(configured.ok, true);

  const missing = createDynamoDbFixedWindowPlatformRateLimiterFromEnv({});
  equal(missing.ok, false);
  if (!missing.ok) {
    equal(missing.error.code, "PLATFORM_ADAPTER_AWS_DYNAMODB_RATE_LIMIT_CONFIG_INVALID");
    equal(missing.error.details.path, "PLATFORM_RATE_LIMIT_DYNAMODB_TABLE");
  }

  console.log("DynamoDB shared rate-limit adapter runtime test passed.");
}

main()
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
