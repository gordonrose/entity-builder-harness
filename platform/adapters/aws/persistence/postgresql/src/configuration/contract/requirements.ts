import { destinationPortConstraint, type ConfigSettingRequirement } from "@kanbien/core/config";

export const sqlIdentifierPattern = /^[a-z][a-z0-9_]{0,62}$/;
/** Login identifiers have a distinct historical policy: a leading underscore is valid. */
export const postgreSqlLoginNameRule = { kind: "text", pattern: /^[a-z_][a-z0-9_]{0,62}$/ } as const;
export const hostPattern = /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,251}[a-zA-Z0-9])?|\[[0-9a-fA-F:]+\])$/;
export const authenticationReferencePattern = /^arn:aws(?:-[a-z]+)?:(?:secretsmanager:[a-z0-9-]+:\d{12}:secret:[A-Za-z0-9/_+=.@-]+|rds-db:[a-z0-9-]+:\d{12}:dbuser:[A-Za-z0-9-]+\/[a-z_][a-z0-9_]{0,62})$/;

/** Source validation policy is shared, not copied into target implementations. */
export const postgreSqlPersistenceConfigurationTextRules = {
  host: { kind: "text", pattern: hostPattern }, database: { kind: "text", pattern: sqlIdentifierPattern },
  schema: { kind: "text", pattern: sqlIdentifierPattern }, reference: { kind: "text", pattern: authenticationReferencePattern },
} as const;

export const postgreSqlPersistenceRequirements = Object.freeze([
  { setting: "database.host", rule: postgreSqlPersistenceConfigurationTextRules.host },
  { setting: "database.port", rule: destinationPortConstraint },
  { setting: "database.name", rule: postgreSqlPersistenceConfigurationTextRules.database },
  { setting: "database.schema", rule: postgreSqlPersistenceConfigurationTextRules.schema },
  { setting: "authentication.reference", rule: postgreSqlPersistenceConfigurationTextRules.reference },
].map(item => Object.freeze(item))) satisfies readonly ConfigSettingRequirement[];
