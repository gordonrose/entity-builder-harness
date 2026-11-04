import { configurationDiagnostic, createDiagnosticRecord, validateConfigRequirements,
  type ConfigSource, type ConfigSettingRequirement, type CoreQueueDiagnosticOptions, type Result, type DiagnosticDefinition } from "@kanbien/core";
import { sqsSenderRequirements, sqsWorkerRequirements } from "../contract/requirements";
import { sqsSenderConfigurationDiagnostic, sqsWorkerConfigurationDiagnostic, sqsSenderConfigurationSourceDiagnostic,
  sqsWorkerConfigurationSourceDiagnostic, type SqsConfigurationFailure } from "../contract/reporting/diagnostics";
import type { SqsConfigurationCheck, SqsSenderConfiguration, SqsWorkerConfiguration } from "../contract/types";
import { assembleSqsSenderConfiguration, assembleSqsWorkerConfiguration } from "./assembly";
import { observeSqsConfiguration } from "./reporting";

export function validateSqsSenderConfiguration(source: ConfigSource, check: SqsConfigurationCheck = validateConfigRequirements,
  diagnostics?: CoreQueueDiagnosticOptions): Result<SqsSenderConfiguration, SqsConfigurationFailure> {
  const result = validate(source, sqsSenderRequirements, sqsSenderConfigurationDiagnostic, sqsSenderConfigurationSourceDiagnostic, check, diagnostics);
  return result.ok ? assembleSqsSenderConfiguration(result.value) : result;
}
export function validateSqsWorkerConfiguration(source: ConfigSource, check: SqsConfigurationCheck = validateConfigRequirements,
  diagnostics?: CoreQueueDiagnosticOptions): Result<SqsWorkerConfiguration, SqsConfigurationFailure> {
  const result = validate(source, sqsWorkerRequirements, sqsWorkerConfigurationDiagnostic, sqsWorkerConfigurationSourceDiagnostic, check, diagnostics);
  return result.ok ? assembleSqsWorkerConfiguration(result.value) : result;
}
function validate(source: ConfigSource, requirements: readonly ConfigSettingRequirement[], definition: typeof sqsSenderConfigurationDiagnostic,
  sourceDefinition: DiagnosticDefinition, check: SqsConfigurationCheck, diagnostics?: CoreQueueDiagnosticOptions): Result<Readonly<Record<string, string | number>>, SqsConfigurationFailure> {
  const checked = check({ get(name) {
    try { return source.get(name); }
    catch (cause) {
      const observation = createDiagnosticRecord(sourceDefinition, { phase: "configuration-source-read", source: name,
        reason: "unclassified-read-failure", effect: "not-assessed" });
      if (observation.ok) observeSqsConfiguration(diagnostics, observation.value, cause);
      throw cause;
    }
  } }, requirements);
  if (checked.ok) return checked;
  const record = configurationDiagnostic(definition, checked.error.issues);
  if (!record.ok) throw new TypeError("SQS_CONFIGURATION_DIAGNOSTIC_INVALID");
  observeSqsConfiguration(diagnostics, record.value);
  return { ok: false, error: { code: "PLATFORM_ADAPTER_AWS_SQS_CONFIG_INVALID", defaultMessage: "AWS SQS configuration is invalid.", diagnosticRecord: record.value } };
}
