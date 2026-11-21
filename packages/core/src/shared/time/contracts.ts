import type { Brand } from "../contract/branding";

export type ISODateTime = Brand<string, "ISODateTime">;

export interface Clock {
  now(): Date;
}
