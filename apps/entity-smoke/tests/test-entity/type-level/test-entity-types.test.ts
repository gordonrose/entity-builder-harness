import type { CreateTestEntityInput, TestEntity, UpdateTestEntityInput } from "../../../src/index";

const create = {
  integerValue: 1, uuidValue: "validated-at-runtime", occurredAt: "2026-11-07T00:00:00Z",
  label: "smoke", status: "draft", enabled: true, categories: ["alpha"], notes: ["free text"],
  description: null, reviewedAt: null, secondaryCategories: null,
} satisfies CreateTestEntityInput;
const update: UpdateTestEntityInput = { description: null, secondaryCategories: [], enabled: false };
const emptyUpdate: UpdateTestEntityInput = {};
// @ts-expect-error nullable does not mean undefined
const undefinedUpdate: UpdateTestEntityInput = { description: undefined };
// @ts-expect-error nullable create fields must still be present
const missingCreate: CreateTestEntityInput = { integerValue: 1 };
// @ts-expect-error enum entries are closed
const invalidCategory: UpdateTestEntityInput = { categories: ["unknown"] };
// @ts-expect-error numeric attributes do not accept strings
const invalidInteger: UpdateTestEntityInput = { integerValue: "1" };
// @ts-expect-error identifiers on stored entities are branded
const unvalidatedId: TestEntity["id"] = "not-an-entity-id";
void [create, update, emptyUpdate, undefinedUpdate, missingCreate, invalidCategory, invalidInteger, unvalidatedId];
