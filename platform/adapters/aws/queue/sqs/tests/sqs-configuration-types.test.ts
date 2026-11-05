import { validateSqsWorkerConfiguration, createAwsSdkPlatformSqsWorkerQueueFromConfiguration,
  type SqsConfigurationCheck, type SqsWorkerConfiguration } from "../src/index";
import { recordConfigSource, validateConfigRequirements } from "@kanbien/core";
const check: SqsConfigurationCheck = validateConfigRequirements;
const result = validateSqsWorkerConfiguration(recordConfigSource({}), check);
if (result.ok) { const config: SqsWorkerConfiguration = result.value; const wait: number = config.waitTimeSeconds; void wait; }
// @ts-expect-error Typed worker options require both timings.
const incomplete: SqsWorkerConfiguration = { queueUrl: "fixture", region: "fixture" };
// @ts-expect-error Strict factory requires a readable source, not arbitrary raw fields.
createAwsSdkPlatformSqsWorkerQueueFromConfiguration({ queueUrl: "fixture" });
void incomplete;
