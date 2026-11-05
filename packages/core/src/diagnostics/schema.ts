/** Closed, serializable schemas for approved diagnostic detail, not raw errors. */
export type DiagnosticDetailSchema =
  | { readonly type: "enum"; readonly values: readonly string[] }
  | { readonly type: "boolean" }
  | { readonly type: "integer" | "number"; readonly minimum: number; readonly maximum: number }
  | { readonly type: "array"; readonly items: DiagnosticDetailSchema; readonly minItems: number; readonly maxItems: number }
  | { readonly type: "object"; readonly properties: Readonly<Record<string, DiagnosticDetailSchema>>; readonly optional?: readonly string[] };

export type DiagnosticDetail<S extends DiagnosticDetailSchema> =
  S extends { readonly type: "enum"; readonly values: readonly (infer V extends string)[] } ? V :
  S extends { readonly type: "boolean" } ? boolean :
  S extends { readonly type: "integer" | "number" } ? number :
  S extends { readonly type: "array"; readonly items: infer I extends DiagnosticDetailSchema } ? readonly DiagnosticDetail<I>[] :
  S extends { readonly type: "object"; readonly properties: infer P extends Readonly<Record<string, DiagnosticDetailSchema>> } ?
    { readonly [K in Exclude<keyof P, S extends { readonly optional: readonly (infer O)[] } ? O : never>]: DiagnosticDetail<P[K]> } &
    { readonly [K in Extract<keyof P, S extends { readonly optional: readonly (infer O)[] } ? O : never>]?: DiagnosticDetail<P[K]> } : never;

const forbiddenKeys = new Set(["__proto__", "prototype", "constructor"]);

/** Do not execute accessors, toJSON methods or provider class methods. */
export function diagnosticObject(value: unknown): value is Readonly<Record<string, unknown>> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) return false;
  return Reflect.ownKeys(value).every((key) => typeof key === "string" && !forbiddenKeys.has(key)
    && Object.getOwnPropertyDescriptor(value, key)?.enumerable === true
    && Object.getOwnPropertyDescriptor(value, key)?.get === undefined
    && Object.getOwnPropertyDescriptor(value, key)?.set === undefined);
}

function diagnosticArray(value: unknown, maximum: number): value is unknown[] {
  return Array.isArray(value) && Object.getPrototypeOf(value) === Array.prototype && value.length <= maximum
    && Reflect.ownKeys(value).length === value.length + 1
    && Array.from({ length: value.length }, (_, index) => Object.getOwnPropertyDescriptor(value, String(index)))
      .every((field) => field !== undefined && "value" in field && field.enumerable === true);
}

function exactKeys(value: Readonly<Record<string, unknown>>, required: readonly string[], optional: readonly string[] = []): boolean {
  return required.every((key) => Object.hasOwn(value, key))
    && Object.keys(value).every((key) => required.includes(key) || optional.includes(key));
}

export function validDiagnosticSchema(value: unknown, depth = 0, seen = new Set<object>()): value is DiagnosticDetailSchema {
  if (depth > 8 || !diagnosticObject(value) || seen.has(value)) return false;
  const next = new Set(seen).add(value);
  switch (value["type"]) {
    case "enum": return exactKeys(value, ["type", "values"]) && diagnosticArray(value["values"], 256)
      && value["values"].length > 0 && value["values"].length <= 256
      && value["values"].every((item) => typeof item === "string" && /^[A-Za-z][A-Za-z0-9_.-]{0,127}$/.test(item))
      && new Set(value["values"]).size === value["values"].length;
    case "boolean": return exactKeys(value, ["type"]);
    case "number": case "integer": return exactKeys(value, ["type", "minimum", "maximum"])
      && typeof value["minimum"] === "number" && Number.isFinite(value["minimum"])
      && typeof value["maximum"] === "number" && Number.isFinite(value["maximum"])
      && value["minimum"] <= value["maximum"]
      && (value["type"] !== "integer" || (Number.isSafeInteger(value["minimum"]) && Number.isSafeInteger(value["maximum"])));
    case "array": return exactKeys(value, ["type", "items", "minItems", "maxItems"])
      && Number.isInteger(value["minItems"]) && Number.isInteger(value["maxItems"])
      && (value["minItems"] as number) >= 0 && (value["maxItems"] as number) <= 64
      && (value["minItems"] as number) <= (value["maxItems"] as number)
      && validDiagnosticSchema(value["items"], depth + 1, next);
    case "object": {
      if (!exactKeys(value, ["type", "properties"], ["optional"]) || !diagnosticObject(value["properties"])) return false;
      const properties = value["properties"];
      const keys = Object.keys(properties);
      return keys.length <= 32 && keys.every((key) => /^[a-z][a-zA-Z0-9_]{0,63}$/.test(key)
        && validDiagnosticSchema(properties[key], depth + 1, next))
        && (value["optional"] === undefined || (diagnosticArray(value["optional"], 32)
          && new Set(value["optional"]).size === value["optional"].length
          && value["optional"].every((key) => typeof key === "string" && keys.includes(key))));
    }
    default: return false;
  }
}

/** Copy only fields approved by the schema. Never return rejected input. */
export function copyDiagnosticDetail(schema: DiagnosticDetailSchema, value: unknown, budget = { nodes: 512 }, depth = 0): unknown {
  if (--budget.nodes < 0 || depth > 8) throw new TypeError("DIAGNOSTIC_DETAIL_LIMIT");
  switch (schema.type) {
    case "enum": if (typeof value === "string" && schema.values.includes(value)) return value; break;
    case "boolean": if (typeof value === "boolean") return value; break;
    case "number": case "integer":
      if (typeof value === "number" && Number.isFinite(value) && value >= schema.minimum && value <= schema.maximum
        && (schema.type !== "integer" || Number.isSafeInteger(value))) return value;
      break;
    case "array":
      if (diagnosticArray(value, schema.maxItems)
        && value.length >= schema.minItems && value.length <= schema.maxItems
      ) {
        return Object.freeze(value.map((item) => copyDiagnosticDetail(schema.items, item, budget, depth + 1)));
      }
      break;
    case "object":
      if (diagnosticObject(value) && Object.keys(value).every((key) => Object.hasOwn(schema.properties, key))) {
        const result: Record<string, unknown> = {};
        for (const [key, child] of Object.entries(schema.properties)) {
          if (!Object.hasOwn(value, key) && schema.optional?.includes(key)) continue;
          if (!Object.hasOwn(value, key)) throw new TypeError("DIAGNOSTIC_DETAIL_INVALID");
          result[key] = copyDiagnosticDetail(child, value[key], budget, depth + 1);
        }
        return Object.freeze(result);
      }
  }
  throw new TypeError("DIAGNOSTIC_DETAIL_INVALID");
}
