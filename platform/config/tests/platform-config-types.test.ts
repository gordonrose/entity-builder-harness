import type { ConfigSchema } from "@kanbien/core/config";
import { recordConfigSource } from "@kanbien/core/config";
import { assertPlatformConfigValid, validatePlatformConfigSchemas } from "../src/index";

const schema: ConfigSchema<{ readonly enabled: boolean }> = {
  parse: () => ({ ok: true, value: { enabled: true } }),
};

const result = validatePlatformConfigSchemas({
  source: recordConfigSource({ ENABLED: true }),
  schemas: [schema],
});
if (result.ok) {
  const values: readonly unknown[] = result.value;
  void values;
}

assertPlatformConfigValid({ source: recordConfigSource({}), schemas: [] });

// @ts-expect-error schemas must implement ConfigSchema
validatePlatformConfigSchemas({ source: recordConfigSource({}), schemas: [{}] });
