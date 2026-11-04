import type { Result } from "../../../shared/index";
import type { ConfigIssueReason } from "../../contract/reporting/setting-issues";



/** Parse only; never retain supplied values or native parser messages in failures. */
export function parseConfigJsonObject(value: unknown): Result<Readonly<Record<string, unknown>>, { readonly reason: ConfigIssueReason }> {
  if (value === undefined) return { ok: false, error: { reason: "missing" } };
  if (typeof value !== "string") return { ok: false, error: { reason: "wrong-type" } };
  if (value.trim() === "") return { ok: false, error: { reason: "blank" } };
  let parsed: unknown;
  try { parsed = JSON.parse(value); }
  catch { return { ok: false, error: { reason: "invalid-json" } }; }
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) return { ok: false, error: { reason: "wrong-shape" } };
  return { ok: true, value: parsed as Readonly<Record<string, unknown>> };
}
