export type Brand<Value, Name extends string> = Value & { readonly __brand: Name };

export function brand<Value, Name extends string>(value: Value): Brand<Value, Name> {
  return value as Brand<Value, Name>;
}
