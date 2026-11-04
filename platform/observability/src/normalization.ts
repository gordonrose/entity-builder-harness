import { defaultRedactedValue, defaultSensitiveLogFieldNames } from "@kanbien/core/logging";
import type { JsonValue } from "@kanbien/core/shared";
import { platformErrorClassification, platformErrorClassDeclarations, type PlatformErrorClassificationOptions } from "@kanbien/platform-contracts";

export type PlatformSafeLogFields = Readonly<Record<string, JsonValue>>;

export interface PlatformValueNormalizationOptions extends PlatformErrorClassificationOptions {
  readonly additionalSensitiveKeys?: readonly string[];
  readonly redactedValue?: string;
  readonly maxDepth?: number;
  readonly maxArrayItems?: number;
  readonly maxObjectKeys?: number;
  readonly maxStringLength?: number;
}

interface NormalizationState {
  readonly options: Required<PlatformValueNormalizationOptions>;
  readonly sensitiveKeys: ReadonlySet<string>;
  readonly seen: WeakSet<object>;
}

export function normalizePlatformLogFields(
  fields: Readonly<Record<string, unknown>>,
  options: PlatformValueNormalizationOptions = {},
): PlatformSafeLogFields {
  const state = createNormalizationState(options);
  return normalizeRecord(fields, state, 0);
}

export function normalizePlatformValue(
  value: unknown,
  options: PlatformValueNormalizationOptions = {},
): JsonValue {
  return normalizeUnknown(value, createNormalizationState(options), 0);
}

export function normalizePlatformError(error: unknown, options?: PlatformErrorClassificationOptions): PlatformSafeLogFields {
  try {
    if (!isObjectLike(error)) return { type: "non-error-value" };
    const code = Object.getOwnPropertyDescriptor(error, "code");
    const native = nativeErrorClass(error);
    if (native !== "unknown") return { name: native,
      ...(code === undefined ? {} : { code: "value" in code ? platformErrorClassification(code.value, options) : "unknown" }) };
    const name = Object.getOwnPropertyDescriptor(error, "name");
    return { type: "non-error-object",
      ...(code === undefined ? {} : { code: "value" in code ? platformErrorClassification(code.value, options) : "unknown" }),
      ...(name === undefined ? {} : { name: "value" in name ? platformErrorClassification(name.value, options) : "unknown" }) };
  } catch { return { type: "non-error-object" }; }
}

export function platformErrorClass(error: unknown, options?: PlatformErrorClassificationOptions): string {
  try {
    if (!isObjectLike(error)) return "unknown";
    const code = Object.getOwnPropertyDescriptor(error, "code");
    // A present unsupported code is not evidence of a native error cause.
    if (code !== undefined) return "value" in code ? platformErrorClassification(code.value, options) : "unknown";
    return nativeErrorClass(error);
  } catch { return "unknown"; }
}

function nativeErrorClass(error: object): string {
  if (error instanceof EvalError) return "EvalError";
  if (error instanceof RangeError) return "RangeError";
  if (error instanceof ReferenceError) return "ReferenceError";
  if (error instanceof SyntaxError) return "SyntaxError";
  if (error instanceof TypeError) return "TypeError";
  if (error instanceof URIError) return "URIError";
  if (error instanceof AggregateError) return "AggregateError";
  return error instanceof Error ? "Error" : "unknown";
}

function createNormalizationState(options: PlatformValueNormalizationOptions): NormalizationState {
  const normalizedOptions: Required<PlatformValueNormalizationOptions> = {
    additionalSensitiveKeys: options.additionalSensitiveKeys ?? [],
    redactedValue: options.redactedValue ?? defaultRedactedValue,
    maxDepth: options.maxDepth ?? 4,
    maxArrayItems: options.maxArrayItems ?? 20,
    maxObjectKeys: options.maxObjectKeys ?? 50,
    maxStringLength: options.maxStringLength ?? 256,
    errorClasses: platformErrorClassDeclarations(options) ?? [],
  };

  return {
    options: normalizedOptions,
    sensitiveKeys: new Set(
      [...defaultSensitiveLogFieldNames, ...normalizedOptions.additionalSensitiveKeys].map(normalizeKey),
    ),
    seen: new WeakSet<object>(),
  };
}

function normalizeRecord(
  record: Readonly<Record<string, unknown>>,
  state: NormalizationState,
  depth: number,
): PlatformSafeLogFields {
  const result: Record<string, JsonValue> = {};
  const entries = Object.entries(record).slice(0, state.options.maxObjectKeys);

  for (const [key, value] of entries) {
    result[key] = isSensitiveKey(key, state)
      ? state.options.redactedValue
      : normalizeUnknown(value, state, depth + 1);
  }

  if (Object.keys(record).length > state.options.maxObjectKeys) {
    result["truncatedKeys"] = Object.keys(record).length - state.options.maxObjectKeys;
  }

  return result;
}

function normalizeUnknown(value: unknown, state: NormalizationState, depth: number): JsonValue {
  if (value === undefined) {
    return null;
  }

  if (value === null || typeof value === "boolean") {
    return value;
  }

  if (typeof value === "string") {
    return value.length > state.options.maxStringLength
      ? `${value.slice(0, state.options.maxStringLength)}...[truncated]`
      : value;
  }

  if (typeof value === "number") {
    return Number.isFinite(value) ? value : String(value);
  }

  if (typeof value === "bigint" || typeof value === "symbol" || typeof value === "function") {
    return `[${typeof value}]`;
  }

  if (value instanceof Date) {
    return value.toISOString();
  }

  if (value instanceof Error) {
    return normalizePlatformError(value, state.options);
  }

  if (depth > state.options.maxDepth) {
    return "[MaxDepth]";
  }

  if (Array.isArray(value)) {
    return value.slice(0, state.options.maxArrayItems).map((item) => normalizeUnknown(item, state, depth + 1));
  }

  if (!isObjectLike(value)) {
    return String(value);
  }

  if (state.seen.has(value)) {
    return "[Circular]";
  }

  state.seen.add(value);
  const normalized = normalizeRecord(value as Readonly<Record<string, unknown>>, state, depth);
  state.seen.delete(value);

  return normalized;
}

function isSensitiveKey(key: string, state: NormalizationState): boolean {
  const normalized = normalizeKey(key);

  for (const sensitiveKey of state.sensitiveKeys) {
    if (normalized === sensitiveKey || normalized.includes(sensitiveKey)) {
      return true;
    }
  }

  return false;
}

function normalizeKey(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function isObjectLike(value: unknown): value is object {
  return typeof value === "object" && value !== null;
}
