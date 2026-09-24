import { brand, type Brand } from "../shared/index";

export type ConcurrencyToken = Brand<string, "ConcurrencyToken">;

export function concurrencyToken(value: string): ConcurrencyToken {
  return brand<string, "ConcurrencyToken">(value);
}
