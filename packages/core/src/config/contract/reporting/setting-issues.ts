/** Shared names, not an automatic allowed-reason selection for any diagnostic. */
export const configReasonNames = Object.freeze({
  missing: "missing", blank: "blank", surroundingWhitespace: "surrounding-whitespace",
  wrongType: "wrong-type", invalidFormat: "invalid-format", invalidInteger: "invalid-integer",
  outOfRange: "out-of-range", inconsistentSettings: "inconsistent-settings",
  invalidJson: "invalid-json", wrongShape: "wrong-shape", empty: "empty", forbiddenCharacter: "forbidden-character",
  unsupportedValue: "unsupported-value",
} as const);
export type ConfigIssueReason = (typeof configReasonNames)[keyof typeof configReasonNames];

/** Fixed compatibility exports. New definitions select names explicitly instead. */
export const configIssueReasons = [
  configReasonNames.missing, configReasonNames.blank, configReasonNames.surroundingWhitespace,
  configReasonNames.wrongType, configReasonNames.invalidFormat, configReasonNames.invalidInteger,
  configReasonNames.outOfRange, configReasonNames.inconsistentSettings,
] as const;
export const configValueIssueReasons = [
  configReasonNames.missing, configReasonNames.blank, configReasonNames.surroundingWhitespace,
  configReasonNames.wrongType, configReasonNames.invalidFormat, configReasonNames.invalidInteger,
  configReasonNames.outOfRange, configReasonNames.inconsistentSettings,
  configReasonNames.invalidJson, configReasonNames.wrongShape, configReasonNames.empty, configReasonNames.forbiddenCharacter,
] as const;
export interface ConfigSettingIssue { readonly setting: string; readonly reason: ConfigIssueReason }
/** Logical locations only. Positions are zero-based; no submitted values belong here. */
export interface ConfigCheckIssue<TReason extends string = string> {
  readonly setting: string;
  readonly reason: TReason;
  readonly index?: number;
  readonly attributeIndex?: number;
  readonly relatedIndex?: number;
}
export interface ConfigCheckFailure<TReason extends string = string> {
  readonly issues: readonly ConfigCheckIssue<TReason>[];
  readonly truncated: boolean;
}

/** A failed comparison contains logical references only, never compared values. */
export interface ConfigRelationshipIssue {
  readonly relationship: string;
  readonly rule: "must-differ";
  readonly left: string;
  readonly right: string;
}
