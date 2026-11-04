import type { ConfigIssueReason } from "@kanbien/core/config";
import type { Result } from "@kanbien/core/shared";
import { postgreSqlLoginNameRule } from "./configuration/index";

export interface PostgreSqlPasswordCredentials { readonly username: string; readonly password: string }
export interface PostgreSqlCredentialIssue { readonly field: "username" | "password"; readonly reason: ConfigIssueReason }

/** Validate a parsed object, not database acceptance. Passwords are never normalized. */
export function postgreSqlPasswordCredentials(value: Readonly<Record<string, unknown>>): Result<PostgreSqlPasswordCredentials, { readonly issues: readonly PostgreSqlCredentialIssue[] }> {
  const username = Object.getOwnPropertyDescriptor(value, "username");
  const password = Object.getOwnPropertyDescriptor(value, "password");
  const issues: PostgreSqlCredentialIssue[] = [];
  const issue = (field: PostgreSqlCredentialIssue["field"], reason: ConfigIssueReason) => issues.push({ field, reason });
  if (username === undefined || ("value" in username && username.value === undefined)) issue("username", "missing");
  else if (!("value" in username) || typeof username.value !== "string") issue("username", "wrong-type");
  else if (!postgreSqlLoginNameRule.pattern.test(username.value)) {
    // Classify rejected values without changing the historical regex.
    issue("username", username.value.trim() === "" ? "blank" : username.value.trim() !== username.value ? "surrounding-whitespace" : "invalid-format");
  }
  if (password === undefined || ("value" in password && password.value === undefined)) issue("password", "missing");
  else if (!("value" in password) || typeof password.value !== "string") issue("password", "wrong-type");
  else if (password.value.length === 0) issue("password", "empty");
  else if (password.value.includes("\u0000")) issue("password", "forbidden-character");
  return issues.length > 0 ? { ok: false, error: { issues } }
    : { ok: true, value: { username: username!.value as string, password: password!.value as string } };
}
