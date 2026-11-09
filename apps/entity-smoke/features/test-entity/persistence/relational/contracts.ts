import type { Result } from "@kanbien/core/shared";
import type { TestEntityError } from "../../contract/errors";

/** Target composition replaces the literal schema token and supplies execution.
 * Values never become SQL text. A failure is returned once, not retried. */
export interface TestEntityRelationalExecutor {
  execute(statement: {
    readonly text: string;
    readonly values: readonly unknown[];
  }, operation: "read" | "write" | "create"): Promise<Result<{
    readonly rows: readonly Readonly<Record<string, unknown>>[];
    readonly rowCount: number | null;
  }, TestEntityError>>;
}
