import type { Principal } from "@kanbien/core/authn";
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
  readonly requestId: CorrelationId;
  readonly method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  readonly path: string;
}

export interface PlatformJobContext extends PlatformRuntimeContext {
  readonly jobName: PlatformJobName;
  readonly message: QueueMessage;
  readonly delivery?: QueueDelivery;
}
