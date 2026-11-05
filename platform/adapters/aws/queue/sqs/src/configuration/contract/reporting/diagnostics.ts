import { configReasonNames as reason, defineConfigurationDiagnostic, defineDiagnostic,
  type DiagnosticRecord } from "@kanbien/core";
import { sqsSenderRequirements, sqsWorkerRequirements } from "../requirements";

const textReasons = [reason.missing, reason.wrongType, reason.blank, reason.surroundingWhitespace] as const;
export const sqsSenderConfigurationDiagnostic = defineConfigurationDiagnostic("aws-sqs.sender-configuration-invalid",
  sqsSenderRequirements.map(item => item.setting), textReasons);
export const sqsWorkerConfigurationDiagnostic = defineConfigurationDiagnostic("aws-sqs.worker-configuration-invalid",
  sqsWorkerRequirements.map(item => item.setting), [...textReasons, reason.invalidInteger, reason.outOfRange]);
const sourceDetail = { type: "object", properties: {
  phase: { type: "enum", values: ["configuration-source-read"] },
  reason: { type: "enum", values: ["unclassified-read-failure"] },
  effect: { type: "enum", values: ["not-assessed"] },
} } as const;
const classification = { failureKind: "configuration", failureSource: "unknown", severity: "error", recovery: "manual_investigation" } as const;
export const sqsSenderConfigurationSourceDiagnostic = defineDiagnostic({ code: "aws-sqs.sender-configuration-source-failed", version: 1, classification,
  detail: { ...sourceDetail, properties: { ...sourceDetail.properties, source: { type: "enum", values: sqsSenderRequirements.map(item => item.setting) } } },
} as const);
export const sqsWorkerConfigurationSourceDiagnostic = defineDiagnostic({ code: "aws-sqs.worker-configuration-source-failed", version: 1, classification,
  detail: { ...sourceDetail, properties: { ...sourceDetail.properties, source: { type: "enum", values: sqsWorkerRequirements.map(item => item.setting) } } },
} as const);
export const sqsConfigurationDiagnosticCatalog = Object.freeze({ owner: "aws-sqs", definitions: Object.freeze([
  sqsSenderConfigurationDiagnostic, sqsWorkerConfigurationDiagnostic, sqsSenderConfigurationSourceDiagnostic, sqsWorkerConfigurationSourceDiagnostic,
]) });
export interface SqsConfigurationFailure {
  readonly code: "PLATFORM_ADAPTER_AWS_SQS_CONFIG_INVALID";
  readonly defaultMessage: "AWS SQS configuration is invalid.";
  readonly diagnosticRecord: DiagnosticRecord;
}
