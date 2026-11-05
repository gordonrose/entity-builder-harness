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
  type PlatformPersistenceDiagnosticOptions,
} from "@kanbien/platform-persistence";
import type { DynamoDbPersistenceCommandClient } from "./client";
import type { DynamoDbPersistenceConfiguration } from "./configuration/index";
import { isDynamoDbConditionalFailure } from "./errors";
import {
  itemToRecordChange,
  lineageRecordPartition,
  recordChangeToItem,
} from "./records";
import { dynamoDbObservation, attributeObservation, responseItems, type DynamoDbObservation } from "./observations";

export interface DynamoDbPlatformRecordChangeStoreOptions extends PlatformPersistenceDiagnosticOptions {
  readonly configuration: DynamoDbPersistenceConfiguration;
  readonly client: DynamoDbPersistenceCommandClient;
}

export function createDynamoDbPlatformRecordChangeStore(
  options: DynamoDbPlatformRecordChangeStoreOptions,
): PlatformRecordChangeStore {
  return {
    append: async (change) => {
      const observed = dynamoDbObservation(options, "append_lineage");
      try {
        await observed.send(options, () => new PutItemCommand({
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
            observed.evidence(),
          );
        }
        return { ok: false, error: observed.error("append_lineage") };
      }
    },

    findByRecord: async (record) => {
      const observed = dynamoDbObservation(options, "read_lineage");
      const attributes = attributeObservation(options, "read_lineage", "returned");
      try {
        const response = await observed.send(options, () => new QueryCommand({
          TableName: options.configuration.tableName,
          KeyConditionExpression: "#pk = :pk",
          ExpressionAttributeNames: { "#pk": "PK" },
          ExpressionAttributeValues: { ":pk": stringAttribute(lineageRecordPartition(record.kind, record.id)) },
          ScanIndexForward: true,
        }));
        const items = observed.at("response", () => responseItems(response, attributes));
        return observed.decode(attributes, () => items.map((item, ordinal) => { attributes.row(ordinal); return itemToRecordChange(item, attributes); }));
      } catch {
        throw observed.error("read_lineage");
      } finally { attributes.flush(); }
    },

    findByCause: async (cause) => {
      const observed = dynamoDbObservation(options, "read_lineage");
      const attributes = attributeObservation(options, "read_lineage", "returned");
      try {
        const response = await observed.send(options, () => new QueryCommand({
          TableName: options.configuration.tableName,
          IndexName: options.configuration.lineageCauseIndexName,
          KeyConditionExpression: "#causeKey = :causeKey",
          ExpressionAttributeNames: { "#causeKey": "CauseKey" },
          ExpressionAttributeValues: { ":causeKey": stringAttribute("CAUSE#" + cause) },
          ScanIndexForward: true,
        }));
        const items = observed.at("response", () => responseItems(response, attributes));
        return observed.decode(attributes, () => items.map((item, ordinal) => { attributes.row(ordinal); return itemToRecordChange(item, attributes); }));
      } catch {
        throw observed.error("read_lineage");
      } finally { attributes.flush(); }
    },
  };
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
  evidence: ReturnType<DynamoDbObservation["evidence"]> = {},
): Result<never, PlatformPersistenceError> {
  return { ok: false, error: platformPersistenceError({ code, defaultMessage, messageKey, ...evidence }) };
}
