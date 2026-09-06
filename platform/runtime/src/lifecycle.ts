import { fixedClock, isoDateTimeFromDate, type Clock, type ISODateTime, type Result } from "@kanbien/core/shared";
import type { PlatformApp } from "@kanbien/platform-contracts";
import { platformRuntimeFailure, type PlatformRuntimeError } from "./errors";

export type PlatformRuntimeLifecycleState = "created" | "starting" | "ready" | "stopping" | "stopped" | "failed";

export type PlatformRuntimeLifecyclePhase =
  | "app.beforeStart"
  | "resource.start"
  | "app.afterStart"
  | "app.beforeStop"
  | "resource.drain"
  | "resource.close"
  | "telemetry.flush"
  | "app.afterStop";

export interface PlatformRuntimeLifecycleEvent {
  readonly phase: PlatformRuntimeLifecyclePhase;
  readonly name: string;
  readonly at: ISODateTime;
}

export interface PlatformRuntimeResource {
  readonly name: string;
  start?(): Promise<void> | void;
  drain?(): Promise<void> | void;
  close?(): Promise<void> | void;
}

export interface PlatformRuntimeTelemetry {
  readonly name: string;
  flush(): Promise<void> | void;
}

export interface PlatformRuntimeLifecycleInput {
  readonly apps: readonly PlatformApp[];
  readonly resources?: readonly PlatformRuntimeResource[];
  readonly telemetry?: readonly PlatformRuntimeTelemetry[];
  readonly clock?: Clock;
}

export interface PlatformRuntimeLifecycleController {
  state(): PlatformRuntimeLifecycleState;
  isReady(): boolean;
  events(): readonly PlatformRuntimeLifecycleEvent[];
  start(): Promise<Result<void, PlatformRuntimeError>>;
  beginDrain(): Result<void, PlatformRuntimeError>;
  shutdown(): Promise<Result<readonly PlatformRuntimeLifecycleEvent[], PlatformRuntimeError>>;
}

export function createPlatformRuntimeLifecycle(
  input: PlatformRuntimeLifecycleInput,
): PlatformRuntimeLifecycleController {
  const resources = [...(input.resources ?? [])];
  const telemetry = [...(input.telemetry ?? [])];
  const apps = [...input.apps];
  const clock = input.clock ?? fixedClock(new Date(defaultPlatformRuntimeDateTime));
  const events: PlatformRuntimeLifecycleEvent[] = [];
  let state: PlatformRuntimeLifecycleState = "created";

  function record(phase: PlatformRuntimeLifecyclePhase, name: string): void {
    events.push({ phase, name, at: isoDateTimeFromDate(clock.now()) });
  }

  async function runStep(phase: PlatformRuntimeLifecyclePhase, name: string, step: () => Promise<void> | void): Promise<void> {
    await step();
    record(phase, name);
  }

  return {
    state: () => state,
    isReady: () => state === "ready",
    events: () => [...events],
    async start() {
      if (state !== "created") {
        return platformRuntimeFailure("PLATFORM_RUNTIME_INVALID_STATE", "Runtime lifecycle can only start from the created state.", { state });
      }

      state = "starting";

      try {
        for (const app of apps) {
          if (app.lifecycle?.beforeStart !== undefined) {
            await runStep("app.beforeStart", app.id, app.lifecycle.beforeStart);
          }
        }

        for (const resource of resources) {
          if (resource.start !== undefined) {
            await runStep("resource.start", resource.name, resource.start);
          }
        }

        for (const app of apps) {
          if (app.lifecycle?.afterStart !== undefined) {
            await runStep("app.afterStart", app.id, app.lifecycle.afterStart);
          }
        }

        state = "ready";
        return { ok: true, value: undefined };
      } catch (error) {
        state = "failed";
        return platformRuntimeFailure("PLATFORM_RUNTIME_LIFECYCLE_FAILED", "Runtime startup lifecycle failed.", { state: "starting" }, error);
      }
    },
    beginDrain() {
      if (state === "stopping") {
        return { ok: true, value: undefined };
      }

      if (state !== "ready") {
        return platformRuntimeFailure("PLATFORM_RUNTIME_INVALID_STATE", "Runtime lifecycle can only begin draining from the ready state.", { state });
      }

      state = "stopping";
      return { ok: true, value: undefined };
    },
    async shutdown() {
      if (state === "created") {
        state = "stopped";
        return { ok: true, value: [...events] };
      }

      if (state === "stopped") {
        return { ok: true, value: [...events] };
      }

      if (state !== "ready" && state !== "stopping" && state !== "failed") {
        return platformRuntimeFailure("PLATFORM_RUNTIME_INVALID_STATE", "Runtime lifecycle cannot shut down from the current state.", { state });
      }

      if (state !== "stopping") {
        state = "stopping";
      }

      try {
        for (const app of apps) {
          if (app.lifecycle?.beforeStop !== undefined) {
            await runStep("app.beforeStop", app.id, app.lifecycle.beforeStop);
          }
        }

        for (const resource of resources) {
          if (resource.drain !== undefined) {
            await runStep("resource.drain", resource.name, resource.drain);
          }
        }

        for (const resource of [...resources].reverse()) {
          if (resource.close !== undefined) {
            await runStep("resource.close", resource.name, resource.close);
          }
        }

        for (const sink of telemetry) {
          await runStep("telemetry.flush", sink.name, sink.flush);
        }

        for (const app of apps) {
          if (app.lifecycle?.afterStop !== undefined) {
            await runStep("app.afterStop", app.id, app.lifecycle.afterStop);
          }
        }

        state = "stopped";
        return { ok: true, value: [...events] };
      } catch (error) {
        state = "failed";
        return platformRuntimeFailure("PLATFORM_RUNTIME_LIFECYCLE_FAILED", "Runtime shutdown lifecycle failed.", { state: "stopping" }, error);
      }
    },
  };
}

const defaultPlatformRuntimeDateTime = "2026-07-10T00:00:00.000Z";
