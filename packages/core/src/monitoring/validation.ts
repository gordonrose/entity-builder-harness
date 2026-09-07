export function assertDottedName(label: string, value: string, requireDot: boolean): void {
  assertNonEmpty(label, value);

  const pattern = requireDot
    ? /^[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*)+$/
    : /^[a-z][a-z0-9_-]*(?:\.[a-z][a-z0-9_-]*)*$/;

  if (!pattern.test(value)) {
    throw new TypeError(`${label} must use lowercase dot-separated segments.`);
  }
}

export function assertToken(label: string, value: string): void {
  assertNonEmpty(label, value);

  if (!/^[a-z][a-z0-9_-]*$/.test(value)) {
    throw new TypeError(`${label} must use lowercase token characters.`);
  }
}

export function assertNonEmpty(label: string, value: string): void {
  if (value.length === 0 || value.trim() !== value) {
    throw new TypeError(`${label} must be non-empty and trimmed.`);
  }
}

export function assertFiniteNumber(label: string, value: number): void {
  if (!Number.isFinite(value)) {
    throw new TypeError(`${label} must be a finite number.`);
  }
}

export function assertNonNegativeFiniteNumber(label: string, value: number): void {
  assertFiniteNumber(label, value);

  if (value < 0) {
    throw new TypeError(`${label} must be non-negative.`);
  }
}

export function assertKnownValue<TValue extends string>(
  label: string,
  value: string,
  allowedValues: readonly TValue[],
): asserts value is TValue {
  if (!allowedValues.includes(value as TValue)) {
    throw new TypeError(`${label} must be one of: ${allowedValues.join(", ")}.`);
  }
}

export function normalizeName(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}
