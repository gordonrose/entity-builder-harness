import {
  entityId,
  err,
  ok,
  systemUuidGenerator,
  uuid,
  type Result,
  type UUID,
  type UuidGenerator,
} from "../../../../src/shared/index";

const identifier: UUID = "a0b1c2d3-e4f5-4a67-8b90-123456789abc" as UUID;
const generator: UuidGenerator = { generate: () => ok(identifier) };
void generator;

const parsed = uuid("a0b1c2d3-e4f5-4a67-8b90-123456789abc");
if (parsed.ok) {
  const acceptedUuid: UUID = parsed.value;
  const acceptedString: string = acceptedUuid;
  void acceptedString;
}
const generated: Result<UUID> = systemUuidGenerator.generate();
if (generated.ok) {
  const acceptedUuid: UUID = generated.value;
  void acceptedUuid;
} else {
  const acceptedErrorCode: string = generated.error.code;
  void acceptedErrorCode;
}
const failedGenerator: UuidGenerator = {
  generate: () => err({ code: "TEST_FAILURE", defaultMessage: "Expected failure." }),
};
void failedGenerator;

// @ts-expect-error UUIDs must be validated/branded, not plain strings.
const rejectedPlain: UUID = "a0b1c2d3-e4f5-4a67-8b90-123456789abc";
void rejectedPlain;

// @ts-expect-error UUID is not nullable.
const rejectedNull: UUID = null;
void rejectedNull;

// @ts-expect-error an entity ID brand is not a UUID brand.
const rejectedBrand: UUID = entityId<"FixtureId">("fixture");
void rejectedBrand;

// @ts-expect-error generators must return Result<UUID>, not Result<string>.
const rejectedUnbrandedGenerator: UuidGenerator = { generate: () => ok("not-a-checked-uuid") };
void rejectedUnbrandedGenerator;

// @ts-expect-error generators return a Result rather than a bare UUID.
const rejectedBareGenerator: UuidGenerator = { generate: () => identifier };
void rejectedBareGenerator;

// @ts-expect-error the generator contract is synchronous, not Promise<Result<UUID>>.
const rejectedAsyncGenerator: UuidGenerator = { generate: async () => ok(identifier) };
void rejectedAsyncGenerator;

// @ts-expect-error UUID validation requires a string input.
uuid(null);
