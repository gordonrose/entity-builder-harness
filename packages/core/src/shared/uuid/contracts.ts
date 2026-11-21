import type { Brand } from "../contract/branding";
import type { Result } from "../contract/results";

export type UUID = Brand<string, "UUID">;

/** Features receive this capability as a dependency rather than calling ambient randomness. */
export interface UuidGenerator {
  generate(): Result<UUID>;
}
