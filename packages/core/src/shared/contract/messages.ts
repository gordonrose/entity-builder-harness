import { brand, type Brand } from "./branding";

export type MessageKey = Brand<string, "MessageKey">;
export type MessageParamValue = string | number | boolean | null;
export type MessageParams = Readonly<Record<string, MessageParamValue>>;

export interface MessageDescriptor {
  readonly code: string;
  readonly defaultMessage: string;
  readonly messageKey?: MessageKey;
  readonly params?: MessageParams;
}

export function messageKey(value: string): MessageKey {
  return brand<string, "MessageKey">(value);
}

export function messageDescriptor(input: {
  readonly code: string;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
}): MessageDescriptor {
  return {
    code: input.code,
    defaultMessage: input.defaultMessage,
    ...(input.messageKey === undefined ? {} : { messageKey: messageKey(input.messageKey) }),
    ...(input.params === undefined ? {} : { params: input.params }),
  };
}
