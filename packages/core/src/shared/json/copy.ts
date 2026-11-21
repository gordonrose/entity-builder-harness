import type { JsonValue } from "../contract/json-value";
import { attachCoreDiagnosticRecord, coreJsonRecord } from "../diagnostics/records";

export function copyJsonValue<TValue extends JsonValue>(value: TValue, label = "JSON value"): TValue {
  return copyJsonValueInternal(value, label, 0, []) as TValue;
}

const nativeJsonArrayMap = Array.prototype.map;
const applyJsonArrayMap = Reflect.apply;

/** Retain one method read, the original receiver and the existing custom-map policy. */
function mapWithJsonPosition<TValue, TResult>(value: readonly TValue[], visit: (item: TValue, position: number | undefined) => TResult): TResult[] {
  const map: unknown = value.map;
  const callback = (item: TValue, claimedPosition: unknown = undefined): TResult => visit(item,
    map === nativeJsonArrayMap && typeof claimedPosition === "number" && Number.isSafeInteger(claimedPosition) && claimedPosition >= 0 ? claimedPosition : undefined);
  if (typeof map !== "function") {
    // Use the same native call expression for a noncallable cached method, without
    // another read of the supplied array's getter.
    const value = { map: map as (visitItem: typeof callback) => TResult[] };
    return value.map(callback);
  }
  return applyJsonArrayMap(map, value, [callback]) as TResult[];
}

function jsonCopyFailure(message: string, reason: "non-finite-number" | "non-plain-object", depth: number, path: readonly number[], locationUnavailable: boolean): TypeError {
  const error = new TypeError(message);
  try { return attachCoreDiagnosticRecord(error, coreJsonRecord(reason, depth, path, locationUnavailable)); }
  catch { return error; }
}

function copyJsonValueInternal(value: JsonValue, label: string, depth: number, path: readonly number[], locationUnavailable = false): JsonValue {
  if (typeof value === "number" && !Number.isFinite(value)) {
    throw jsonCopyFailure(`${label} must contain only finite numbers.`, "non-finite-number", depth, path, locationUnavailable);
  }

  if (Array.isArray(value)) {
    return mapWithJsonPosition(value, (item, index) => copyJsonValueInternal(item, label, depth + 1,
      !locationUnavailable && index !== undefined && path.length < 16 ? [...path, index] : path,
      locationUnavailable || index === undefined));
  }

  if (value !== null && typeof value === "object") {
    if (Object.getPrototypeOf(value) !== Object.prototype) {
      throw jsonCopyFailure(`${label} must contain only plain objects.`, "non-plain-object", depth, path, locationUnavailable);
    }

    return Object.fromEntries(
      mapWithJsonPosition(Object.entries(value), ([key, nestedValue], index) => [key, copyJsonValueInternal(nestedValue, label, depth + 1,
        !locationUnavailable && index !== undefined && path.length < 16 ? [...path, index] : path,
        locationUnavailable || index === undefined)]),
    );
  }

  return value;
}
