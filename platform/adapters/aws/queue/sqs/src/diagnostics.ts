import { sqsConfigurationDiagnosticCatalog } from "./configuration/index";
import { sqsLambdaBatchDiagnosticCatalog } from "./lambda-batch";

/** One owner selection for runtime composition; module-specific readers remain narrower. */
export const sqsDiagnosticCatalog = {
  owner: "aws-sqs",
  definitions: [...sqsConfigurationDiagnosticCatalog.definitions, ...sqsLambdaBatchDiagnosticCatalog.definitions],
} as const;
