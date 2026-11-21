import { copyJsonValue, type JsonValue } from "../../../../src/shared/index";

const acceptedJsonValue: JsonValue = {
  id: "deal-123",
  flags: [true, false],
  nested: { value: null },
};

// @ts-expect-error JSON values must stay plain and serializable.
const rejectedJsonValue: JsonValue = new Date();
void rejectedJsonValue;
void copyJsonValue(acceptedJsonValue);
