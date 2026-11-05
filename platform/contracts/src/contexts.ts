import type { Principal } from "@kanbien/core/authn";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { ConfigSource } from "@kanbien/core/config";
import type { LocaleTag } from "@kanbien/core/i18n";
import type { Logger } from "@kanbien/core/logging";
import type { Metrics } from "@kanbien/core/monitoring";
import type { QueueDelivery, QueueMessage } from "@kanbien/core/queues";
import type { Clock, CorrelationId, CausationId, ISODateTime } from "@kanbien/core/shared";
import type { TenantContext } from "@kanbien/core/tenancy";
import type { FeatureFlagReader } from "./flags";
import type { PlatformJobName } from "./identifiers";

export interface PlatformRuntimeContext {
  readonly correlationId: CorrelationId;
  readonly causationId?: CausationId;
  readonly now: ISODateTime;
  readonly tenant?: TenantContext;
  readonly principal?: Principal;
  readonly locale?: LocaleTag;
  readonly logger: Logger;
  readonly metrics: Metrics;
  readonly config: ConfigSource;
  readonly flags: FeatureFlagReader;
  readonly clock: Clock;
  readonly abortSignal?: AbortSignal;
}

export interface PlatformRequestContext extends PlatformRuntimeContext {
  /** Internal observation through the selected route profile and catalog.
   * Absent when operational logging is opted out. Never includes raw errors or
   * changes the response; producers must not wait for diagnostic delivery.
   */
  readonly onDiagnostic?: (record: DiagnosticRecord) => unknown;
  readonly requestId: CorrelationId;
  readonly method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  readonly path: string;
}

export interface PlatformJobContext extends PlatformRuntimeContext {
  readonly jobName: PlatformJobName;
  readonly message: QueueMessage;
  readonly delivery?: QueueDelivery;
}
