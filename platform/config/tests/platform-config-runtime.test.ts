import { deepEqual, equal } from "node:assert/strict";
import { configError, recordConfigSource, stringConfigValue, type ConfigSchema } from "@kanbien/core/config";
import { validationIssue } from "@kanbien/core/validation";
import { assertPlatformConfigValid, validatePlatformConfigSchemas } from "../src/index";

async function main(): Promise<void> {
  const validSchema: ConfigSchema<{ readonly name: string }> = {
    parse: (source) => {
      const value = stringConfigValue(source, "APP_NAME");
      return value.ok
        ? { ok: true, value: { name: value.value } }
        : value;
    },
  };

  const valid = validatePlatformConfigSchemas({
    source: recordConfigSource({ APP_NAME: "platform" }),
    schemas: [validSchema],
  });
  equal(valid.ok, true);
  if (valid.ok) {
    deepEqual(valid.value, [{ name: "platform" }]);
  }

  const invalidSchema: ConfigSchema<never> = {
    parse: () => ({
      ok: false,
      error: configError("CONFIG_INVALID", [
        validationIssue({
          path: ["config", "SECRET_TOKEN"],
          code: "CONFIG_INVALID_SECRET",
          defaultMessage: "Secret config is invalid.",
          params: { token: "do-not-leak" },
        }),
      ]),
    }),
  };
  const invalid = assertPlatformConfigValid({
    source: recordConfigSource({ SECRET_TOKEN: "secret" }),
    schemas: [invalidSchema],
  });
  equal(invalid.ok, false);
  if (!invalid.ok) {
    equal(invalid.error.code, "PLATFORM_CONFIG_INVALID");
    equal(invalid.error.details["schemaIndex"], 0);
    deepEqual(invalid.error.details["issues"], [{
      path: ["config", "SECRET_TOKEN"],
      code: "CONFIG_INVALID_SECRET",
      defaultMessage: "Secret config is invalid.",
    }]);
  }
}

main()
  .then(() => {
    console.log("platform/config runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
