import type { ConfigCheckIssue, ConfigCheckFailure } from "../../contract/reporting/setting-issues";

/** Collect in observation order, retaining explicit overflow and immutable snapshots. */
export function createConfigIssueCollector<TReason extends string = string>() {
  const issues: ConfigCheckIssue<TReason>[] = [];
  let truncated = false;
  return {
    add(issue: ConfigCheckIssue<TReason>): void {
      const prototype = Object.getPrototypeOf(issue);
      const keys = Reflect.ownKeys(issue);
      const snapshot: Record<string, string | number> = {};
      if ((prototype !== Object.prototype && prototype !== null)
        || keys.some((key) => typeof key !== "string" || !["setting", "reason", "index", "attributeIndex", "relatedIndex"].includes(key))) throw new TypeError("CONFIGURATION_ISSUE_INVALID");
      for (const key of keys as string[]) {
        const field = Object.getOwnPropertyDescriptor(issue, key);
        if (!field || !("value" in field) || !field.enumerable) throw new TypeError("CONFIGURATION_ISSUE_INVALID");
        const value: unknown = field.value;
        if (key === "setting" || key === "reason") {
          if (typeof value !== "string" || !/^[a-z][a-z0-9.-]{0,127}$/.test(value)) throw new TypeError("CONFIGURATION_ISSUE_INVALID");
        } else if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0) throw new TypeError("CONFIGURATION_ISSUE_INVALID");
        snapshot[key] = value as string | number;
      }
      if (!Object.hasOwn(snapshot, "setting") || !Object.hasOwn(snapshot, "reason")) throw new TypeError("CONFIGURATION_ISSUE_INVALID");
      if (issues.length === 32) truncated = true;
      else issues.push(Object.freeze(snapshot) as unknown as ConfigCheckIssue<TReason>);
    },
    finish(): ConfigCheckFailure<TReason> { return Object.freeze({ issues: Object.freeze([...issues]), truncated }); },
  };
}
