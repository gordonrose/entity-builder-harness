import type { ConfigError, ConfigSchema, ConfigSource } from "@kanbien/core/config";
import type { JsonValue, Result } from "@kanbien/core/shared";

export type PlatformConfigErrorCode = "PLATFORM_CONFIG_INVALID";

export interface PlatformConfigError {
  readonly code: PlatformConfigErrorCode;
  readonly defaultMessage: string;
  readonly details: Readonly<Record<string, JsonValue>>;
}

export interface PlatformConfigValidationInput {
  readonly source: ConfigSource;
  readonly schemas: readonly ConfigSchema<unknown>[];
}

export function validatePlatformConfigSchemas(
  input: PlatformConfigValidationInput,
): Result<readonly unknown[], PlatformConfigError> {
  const parsedValues: unknown[] = [];

  for (const [schemaIndex, schema] of input.schemas.entries()) {
    const parsed = schema.parse(input.source);
    if (!parsed.ok) {
      return {
        ok: false,
        error: platformConfigError(schemaIndex, parsed.error),
      };
    }

    parsedValues.push(parsed.value);
  }

  return { ok: true, value: parsedValues };
}

export function assertPlatformConfigValid(
  input: PlatformConfigValidationInput,
): Result<void, PlatformConfigError> {
  const validated = validatePlatformConfigSchemas(input);

  if (!validated.ok) {
    return validated;
  }

  return { ok: true, value: undefined };
}

function platformConfigError(schemaIndex: number, error: ConfigError): PlatformConfigError {
  return {
    code: "PLATFORM_CONFIG_INVALID",
    defaultMessage: "Platform config validation failed before runtime startup.",
    details: {
      schemaIndex,
      configCode: error.code,
      issues: error.issues.map((issue) => ({
        path: [...issue.path],
        code: issue.code,
        defaultMessage: issue.defaultMessage,
        ...(issue.messageKey === undefined ? {} : { messageKey: String(issue.messageKey) }),
      })),
    },
  };
}
