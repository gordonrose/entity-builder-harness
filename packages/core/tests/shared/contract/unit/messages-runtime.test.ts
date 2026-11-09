import { equal } from "node:assert/strict";
import { messageDescriptor, messageKey } from "../../../../src/shared/index";

const descriptor = messageDescriptor({
  code: "VALIDATION_REQUIRED",
  defaultMessage: "Field is required.",
  messageKey: "validation.required",
  params: { field: "email" },
});
equal(descriptor.messageKey, messageKey("validation.required"));
equal(descriptor.params?.field, "email");

console.log("Core shared message unit tests passed.");
