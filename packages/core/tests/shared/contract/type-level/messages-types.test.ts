import { messageDescriptor, messageKey, type MessageDescriptor, type MessageKey } from "../../../../src/shared/index";

const acceptedMessageKey: MessageKey = messageKey("validation.required");
const acceptedMessageDescriptor: MessageDescriptor = messageDescriptor({
  code: "VALIDATION_REQUIRED",
  defaultMessage: "Field is required.",
  messageKey: acceptedMessageKey,
  params: { field: "email", minimum: 1, required: true, optional: null },
});
void acceptedMessageKey;
void acceptedMessageDescriptor;

// @ts-expect-error message descriptors must keep params JSON-primitive and localization-friendly.
messageDescriptor({ code: "BAD_PARAM", defaultMessage: "Bad param.", params: { nested: { value: "nope" } } });

// @ts-expect-error message descriptors require fallback/debug text for untranslated contexts.
messageDescriptor({ code: "MISSING_DEFAULT_MESSAGE" });
