import { isoDateTimeFromDate } from "@kanbien/core/shared";
import type { TestEntity } from "../contract/types";

/** A deliberately short, disposable rule used only by the Entity Smoke feature. */
export const testEntityRetentionWindowMs = 5 * 60_000;

export function testEntityRetentionSatisfied(entity: TestEntity, asOf: Date): boolean {
  if (entity.lifecycle.state !== "deleted") return false;
  return Date.parse(isoDateTimeFromDate(asOf)) > Date.parse(entity.lifecycle.deletedAt) + testEntityRetentionWindowMs;
}

/** The cleanup job is eligible one millisecond after the strict retention rule. */
export function testEntityExpiredPurgeDueAt(entity: TestEntity): Date | undefined {
  if (entity.lifecycle.state !== "deleted") return undefined;
  return new Date(Date.parse(entity.lifecycle.deletedAt) + testEntityRetentionWindowMs + 1);
}
