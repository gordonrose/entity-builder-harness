import {
  PutItemCommand,
  QueryCommand,
} from "@aws-sdk/client-dynamodb";
import type { CausationId, Result } from "@kanbien/core/shared";
import type { RecordChange, RecordReference } from "@kanbien/core/persistence";
import {
  platformPersistenceError,
  type PlatformPersistenceError,
  type PlatformRecordChangeStore,
} from "@kanbien/platform-persistence";
import type { DynamoDbPersistenceCommandClient } from "./client";
import type { DynamoDbPersistenceConfiguration } from "./configuration";
import { dynamoDbPersistenceOperationError, isDynamoDbConditionalFailure } from "./errors";
import {
  itemToRecordChange,
  lineageRecordPartition,
  recordChangeToItem,
  type DynamoDbPersistenceItem,
} from "./records";

export interface DynamoDbPlatformRecordChangeStoreOptions {
  readonly configuration: DynamoDbPersistenceConfiguration;
  readonly client: DynamoDbPersistenceCommandClient;
}

export function createDynamoDbPlatformRecordChangeStore(
  options: DynamoDbPlatformRecordChangeStoreOptions,
): PlatformRecordChangeStore {
  return {
    append: async (change) => {
      try {
        await options.client.send(new PutItemCommand({
          TableName: options.configuration.tableName,
          Item: recordChangeToItem(change),
          ConditionExpression: "attribute_not_exists(#pk)",
          ExpressionAttributeNames: { "#pk": "PK" },
        }));
        return success(change);
      } catch (error) {
        if (isDynamoDbConditionalFailure(error)) {
          return failure(
            "PLATFORM_PERSISTENCE_DUPLICATE_RECORD_CHANGE",
            "Record change already exists.",
            "platform.persistence.lineage.duplicate",
          );
        }
        return { ok: false, error: dynamoDbPersistenceOperationError("append_lineage") };
      }
    },

    findByRecord: async (record) => {
      try {
        const response = await options.client.send(new QueryCommand({
          TableName: options.configuration.tableName,
          KeyConditionExpression: "#pk = :pk",
          ExpressionAttributeNames: { "#pk": "PK" },
          ExpressionAttributeValues: { ":pk": stringAttribute(lineageRecordPartition(record.kind, record.id)) },
          ScanIndexForward: true,
        }));
        return responseItems(response).map(itemToRecordChange);
      } catch {
        throw dynamoDbPersistenceOperationError("read_lineage");
      }
    },

    findByCause: async (cause) => {
      try {
        const response = await options.client.send(new QueryCommand({
          TableName: options.configuration.tableName,
          IndexName: options.configuration.lineageCauseIndexName,
          KeyConditionExpression: "#causeKey = :causeKey",
          ExpressionAttributeNames: { "#causeKey": "CauseKey" },
          ExpressionAttributeValues: { ":causeKey": stringAttribute("CAUSE#" + cause) },
          ScanIndexForward: true,
        }));
        return responseItems(response).map(itemToRecordChange);
      } catch {
        throw dynamoDbPersistenceOperationError("read_lineage");
      }
    },
  };
}

function responseItems(response: unknown): readonly DynamoDbPersistenceItem[] {
  if (typeof response !== "object" || response === null || !("Items" in response)) return [];
  const items = (response as { readonly Items?: unknown }).Items;
  return Array.isArray(items) ? items.filter(isItem) : [];
}

function isItem(value: unknown): value is DynamoDbPersistenceItem {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringAttribute(value: string): { readonly S: string } {
  return { S: value };
}

function success<TValue>(value: TValue): Result<TValue, PlatformPersistenceError> {
  return { ok: true, value };
}

function failure(
  code: PlatformPersistenceError["code"],
  defaultMessage: string,
  messageKey: string,
): Result<never, PlatformPersistenceError> {
  return { ok: false, error: platformPersistenceError({ code, defaultMessage, messageKey }) };
}
