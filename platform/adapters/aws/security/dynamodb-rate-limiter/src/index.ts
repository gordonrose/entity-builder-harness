import { createHash } from "node:crypto";
import {
  DynamoDBClient,
  UpdateItemCommand,
} from "@aws-sdk/client-dynamodb";
import type { Clock, Result } from "@kanbien/core";
import type {
  PlatformRateLimitDecision,
  PlatformRateLimiter,
} from "@kanbien/platform-security";

export interface DynamoDbFixedWindowIncrement {
  readonly tableName: string;
  readonly keyHash: string;
  readonly windowStartedAtMs: number;
  readonly expiresAtEpochSeconds: number;
  readonly limit: number;
}

export interface DynamoDbFixedWindowStore {
  increment(input: DynamoDbFixedWindowIncrement): Promise<"allowed" | "limited">;
}

export interface DynamoDbFixedWindowPlatformRateLimiterOptions {
  readonly tableName: string;
  readonly limit: number;
  readonly windowMs: number;
  readonly store: DynamoDbFixedWindowStore;
  readonly clock?: Clock;
}

export interface AwsSdkDynamoDbFixedWindowStoreOptions {
  readonly region: string;
}

export interface DynamoDbRateLimiterEnvironmentOptions {
  readonly store?: DynamoDbFixedWindowStore;
  readonly clock?: Clock;
}

export interface DynamoDbRateLimiterConfigurationError {
  readonly code: "PLATFORM_ADAPTER_AWS_DYNAMODB_RATE_LIMIT_CONFIG_INVALID";
  readonly defaultMessage: string;
  readonly details: Readonly<{
    readonly path: string;
    readonly reason: string;
  }>;
}

export const adapterMetadata = {
  provider: "aws",
  capability: "security",
  implementation: "dynamodb-rate-limiter",
  packageName: "@kanbien/platform-adapter-aws-security-dynamodb-rate-limiter",
} as const;

export function createDynamoDbFixedWindowPlatformRateLimiter(
  options: DynamoDbFixedWindowPlatformRateLimiterOptions,
): PlatformRateLimiter {
  assertNonEmpty("tableName", options.tableName);
  assertPositiveInteger("limit", options.limit);
  assertPositiveInteger("windowMs", options.windowMs);
  const clock = options.clock ?? { now: () => new Date() };

  return {
    check: async (key): Promise<PlatformRateLimitDecision> => {
      const nowMs = clock.now().getTime();
      const windowStartedAtMs = Math.floor(nowMs / options.windowMs) * options.windowMs;
      const expiresAtEpochSeconds = Math.ceil((windowStartedAtMs + (2 * options.windowMs)) / 1_000);
      const incremented = await options.store.increment({
        tableName: options.tableName,
        keyHash: dynamoDbRateLimitKeyHash(key),
        windowStartedAtMs,
        expiresAtEpochSeconds,
        limit: options.limit,
      });
      if (incremented === "allowed") {
        return { allowed: true };
      }

      return {
        allowed: false,
        retryAfterMs: Math.max(0, windowStartedAtMs + options.windowMs - nowMs),
      };
    },
  };
}

export function createAwsSdkDynamoDbFixedWindowStore(
  options: AwsSdkDynamoDbFixedWindowStoreOptions,
): DynamoDbFixedWindowStore {
  assertNonEmpty("region", options.region);
  const client = new DynamoDBClient({ region: options.region });

  return {
    increment: async (input) => {
      try {
        await client.send(new UpdateItemCommand({
          TableName: input.tableName,
          Key: {
            keyHash: { S: input.keyHash },
            windowStartedAtMs: { N: String(input.windowStartedAtMs) },
          },
          UpdateExpression: "SET #count = if_not_exists(#count, :zero) + :one, #expiresAt = :expiresAt",
          ConditionExpression: "attribute_not_exists(#count) OR #count < :limit",
          ExpressionAttributeNames: {
            "#count": "count",
            "#expiresAt": "expiresAt",
          },
          ExpressionAttributeValues: {
            ":zero": { N: "0" },
            ":one": { N: "1" },
            ":limit": { N: String(input.limit) },
            ":expiresAt": { N: String(input.expiresAtEpochSeconds) },
          },
        }));
        return "allowed";
      } catch (error) {
        if (isConditionalLimit(error)) {
          return "limited";
        }
        throw new Error("DynamoDB shared rate-limit operation failed.");
      }
    },
  };
}

export function createDynamoDbFixedWindowPlatformRateLimiterFromEnv(
  env: Readonly<Record<string, string | undefined>>,
  options: DynamoDbRateLimiterEnvironmentOptions = {},
): Result<PlatformRateLimiter, DynamoDbRateLimiterConfigurationError> {
  const tableName = requiredEnv(env, "PLATFORM_RATE_LIMIT_DYNAMODB_TABLE");
  const region = requiredEnv(env, "PLATFORM_RATE_LIMIT_DYNAMODB_REGION");
  const limit = positiveIntegerEnv(env, "PLATFORM_RATE_LIMIT_LIMIT");
  const windowMs = positiveIntegerEnv(env, "PLATFORM_RATE_LIMIT_WINDOW_MS");
  if (!tableName.ok) {
    return tableName;
  }
  if (!region.ok) {
    return region;
  }
  if (!limit.ok) {
    return limit;
  }
  if (!windowMs.ok) {
    return windowMs;
  }

  return {
    ok: true,
    value: createDynamoDbFixedWindowPlatformRateLimiter({
      tableName: tableName.value,
      limit: limit.value,
      windowMs: windowMs.value,
      store: options.store ?? createAwsSdkDynamoDbFixedWindowStore({ region: region.value }),
      ...(options.clock === undefined ? {} : { clock: options.clock }),
    }),
  };
}

export function dynamoDbRateLimitKeyHash(key: string): string {
  return createHash("sha256").update("platform-rate-limit:v1:").update(key).digest("hex");
}

function requiredEnv(
  env: Readonly<Record<string, string | undefined>>,
  path: string,
): Result<string, DynamoDbRateLimiterConfigurationError> {
  const value = env[path];
  if (value !== undefined && value.length > 0) {
    return { ok: true, value };
  }
  return configurationError(path, "Required environment value is missing.");
}

function positiveIntegerEnv(
  env: Readonly<Record<string, string | undefined>>,
  path: string,
): Result<number, DynamoDbRateLimiterConfigurationError> {
  const value = env[path];
  if (value === undefined || value.length === 0) {
    return configurationError(path, "Required positive integer environment value is missing.");
  }
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    return configurationError(path, "Expected a positive integer environment value.");
  }
  return { ok: true, value: parsed };
}

function configurationError(
  path: string,
  reason: string,
): Result<never, DynamoDbRateLimiterConfigurationError> {
  return {
    ok: false,
    error: {
      code: "PLATFORM_ADAPTER_AWS_DYNAMODB_RATE_LIMIT_CONFIG_INVALID",
      defaultMessage: "DynamoDB shared rate-limit adapter configuration is invalid.",
      details: { path, reason },
    },
  };
}

function isConditionalLimit(error: unknown): boolean {
  return typeof error === "object"
    && error !== null
    && "name" in error
    && (error as { readonly name?: unknown }).name === "ConditionalCheckFailedException";
}

function assertNonEmpty(name: string, value: string): void {
  if (value.length === 0) {
    throw new RangeError(name + " must not be empty.");
  }
}

function assertPositiveInteger(name: string, value: number): void {
  if (!Number.isInteger(value) || value <= 0) {
    throw new RangeError(name + " must be a positive integer.");
  }
}
