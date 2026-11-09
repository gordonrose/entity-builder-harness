import type { CorrelationId } from "../identity/contracts";
import type { ISODateTime } from "./contracts";
import { isoDateTimeFromDate } from "./date-time";

export interface RequestContext {
  readonly correlationId: CorrelationId;
  readonly now: ISODateTime;
}

export function requestContext(input: { readonly correlationId: CorrelationId; readonly now: Date | ISODateTime }): RequestContext {
  return {
    correlationId: input.correlationId,
    now: input.now instanceof Date ? isoDateTimeFromDate(input.now) : input.now,
  };
}
