import { deepEqual, equal } from "node:assert/strict";
import {
  combineValidationResults,
  invalidResult,
  isInvalid,
  isValid,
  validationIssue,
  validResult,
  withValidationPathPrefix,
} from "../src/validation/index";

const missingName = validationIssue({
  path: ["profile", "name"],
  code: "REQUIRED",
  message: "Name is required.",
});

deepEqual(missingName, {
  path: ["profile", "name"],
  code: "REQUIRED",
  message: "Name is required.",
});

const failed = invalidResult(missingName);
equal(failed.valid, false);
equal(isInvalid(failed), true);
equal(failed.issues[0].code, "REQUIRED");

equal(isValid(validResult), true);
deepEqual(validResult.issues, []);

const prefixed = withValidationPathPrefix(["body"], missingName);
deepEqual(prefixed.path, ["body", "profile", "name"]);

const combinedValid = combineValidationResults([validResult, validResult]);
equal(combinedValid.valid, true);

const combinedInvalid = combineValidationResults([validResult, failed]);
equal(combinedInvalid.valid, false);
if (!isInvalid(combinedInvalid)) {
  throw new Error("Expected combined validation result to be invalid.");
}
equal(combinedInvalid.issues.length, 1);
equal(combinedInvalid.issues[0].message, "Name is required.");

console.log("packages/core validation runtime test passed.");
