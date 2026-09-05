import type { QueueMessage, QueueMessageType } from "@kanbien/core/queues";
import type { Validator } from "@kanbien/core/validation";
import type { PlatformJobContext } from "./contexts";
import type { PlatformJobName } from "./identifiers";

export interface PlatformJobHandler<TMessage extends QueueMessage = QueueMessage> {
  handle(message: TMessage, context: PlatformJobContext): Promise<void> | void;
}

export interface PlatformJobRegistration<TMessage extends QueueMessage = QueueMessage> {
  readonly name: PlatformJobName;
  readonly messageType: QueueMessageType;
  readonly validator?: Validator<TMessage["payload"]>;
  readonly handler: PlatformJobHandler<TMessage>;
}
