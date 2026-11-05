import { fixedClock, isoDateTimeFromDate, type Clock, type ISODateTime, type Result } from "@kanbien/core/shared";
import type { PlatformApp } from "@kanbien/platform-contracts";
import { platformRuntimeFailure, type PlatformRuntimeError } from "./errors";
import { runtimeBoundaryEvidence, runtimeStateEvidence, type PlatformRuntimeDiagnosticOptions, type RuntimeBoundaryDetail } from "./diagnostics";

export type PlatformRuntimeLifecycleState = "created" | "starting" | "ready" | "stopping" | "stopped" | "failed";
export type PlatformRuntimeLifecyclePhase =
  | "app.beforeStart" | "resource.start" | "app.afterStart" | "app.beforeStop"
  | "resource.drain" | "resource.close" | "telemetry.flush" | "app.afterStop";
export interface PlatformRuntimeLifecycleEvent { readonly phase: PlatformRuntimeLifecyclePhase; readonly name: string; readonly at: ISODateTime }
export interface PlatformRuntimeResource {
  readonly name: string; start?(): Promise<void> | void; drain?(): Promise<void> | void; close?(): Promise<void> | void;
}
export interface PlatformRuntimeTelemetry { readonly name: string; flush(): Promise<void> | void }
export interface PlatformRuntimeLifecycleInput extends PlatformRuntimeDiagnosticOptions {
  readonly apps: readonly PlatformApp[];
  readonly resources?: readonly PlatformRuntimeResource[];
  readonly telemetry?: readonly PlatformRuntimeTelemetry[];
  readonly clock?: Clock;
}
export interface PlatformRuntimeLifecycleController {
  state(): PlatformRuntimeLifecycleState; isReady(): boolean; events(): readonly PlatformRuntimeLifecycleEvent[];
  start(): Promise<Result<void, PlatformRuntimeError>>;
  beginDrain(): Result<void, PlatformRuntimeError>;
  shutdown(): Promise<Result<readonly PlatformRuntimeLifecycleEvent[], PlatformRuntimeError>>;
}
type Tracking = { -readonly [K in keyof RuntimeBoundaryDetail]: RuntimeBoundaryDetail[K] };

export function createPlatformRuntimeLifecycle(input: PlatformRuntimeLifecycleInput): PlatformRuntimeLifecycleController {
  let construction: RuntimeBoundaryDetail["phase"] = "resources-snapshot";
  try {
    const resources = [...(input.resources ?? [])];
    construction = "telemetry-snapshot";
    const telemetry = [...(input.telemetry ?? [])];
    construction = "apps-snapshot";
    const apps = [...input.apps];
    construction = "clock-selection";
    const clock = input.clock ?? fixedClock(new Date(defaultPlatformRuntimeDateTime));
    const events: PlatformRuntimeLifecycleEvent[] = [];
    let state: PlatformRuntimeLifecycleState = "created";

    function record(tracking: Tracking, phase: PlatformRuntimeLifecyclePhase, name: string): void {
      let date: Date;
      let at: ISODateTime;
      tracking.boundary = "event-selection";
      tracking.effect = "step-completed-event-unrecorded";
      events.push({ phase, name, at: (
        tracking.boundary = "event-clock", date = clock.now(),
        tracking.boundary = "event-normalization", at = isoDateTimeFromDate(date),
        tracking.boundary = "event-append", tracking.effect = "step-completed-event-outcome-unknown", at
      ) });
    }
    async function runStep(tracking: Tracking, phase: PlatformRuntimeLifecyclePhase, name: string, step: () => Promise<void> | void): Promise<void> {
      tracking.boundary = "invocation";
      tracking.effect = "step-completion-unobserved";
      let completion: Promise<void> | void;
      await (completion = step(), tracking.boundary = "completion", completion);
      record(tracking, phase, name);
    }
    function beginPhase(tracking: Tracking, phase: PlatformRuntimeLifecyclePhase, subject: Tracking["subject"]): void {
      tracking.phase = phase; tracking.subject = subject;
      tracking.boundary = "iteration"; tracking.effect = "boundary-outcome-unknown"; delete tracking.ordinal;
    }
    function select(tracking: Tracking, ordinal: number): void {
      tracking.ordinal = ordinal; tracking.boundary = "selection"; tracking.effect = "step-not-invoked";
    }
    function advance(tracking: Tracking): void {
      tracking.boundary = "iteration"; tracking.effect = "boundary-outcome-unknown"; delete tracking.ordinal;
    }
    function projection(operation: "events" | "shutdown"): RuntimeBoundaryDetail {
      return { operation, phase: "events-projection", subject: "runtime", boundary: "projection",
        effect: "boundary-outcome-unknown" };
    }
    return {
      state: () => state,
      isReady: () => state === "ready",
      events: () => {
        try { return [...events]; }
        catch (error) { runtimeBoundaryEvidence(input, projection("events"), error); throw error; }
      },
      async start() {
        if (state !== "created") return platformRuntimeFailure("PLATFORM_RUNTIME_INVALID_STATE", "Runtime lifecycle can only start from the created state.", { state }, undefined,
          runtimeStateEvidence(input, { operation: "start", state, effect: "state-unchanged" }));
        state = "starting";
        const tracking: Tracking = { operation: "start", phase: "app.beforeStart", subject: "app", boundary: "iteration", effect: "boundary-outcome-unknown" };
        try {
          let ordinal = 0;
          for (const app of apps) {
            select(tracking, ordinal++);
            if (app.lifecycle?.beforeStart !== undefined) await runStep(tracking, "app.beforeStart", app.id, app.lifecycle.beforeStart);
            advance(tracking);
          }
          beginPhase(tracking, "resource.start", "resource"); ordinal = 0;
          for (const resource of resources) {
            select(tracking, ordinal++);
            if (resource.start !== undefined) await runStep(tracking, "resource.start", resource.name, resource.start);
            advance(tracking);
          }
          beginPhase(tracking, "app.afterStart", "app"); ordinal = 0;
          for (const app of apps) {
            select(tracking, ordinal++);
            if (app.lifecycle?.afterStart !== undefined) await runStep(tracking, "app.afterStart", app.id, app.lifecycle.afterStart);
            advance(tracking);
          }
          state = "ready";
          return { ok: true, value: undefined };
        } catch (error) {
          state = "failed";
          return platformRuntimeFailure("PLATFORM_RUNTIME_LIFECYCLE_FAILED", "Runtime startup lifecycle failed.", { state: "starting" }, error,
            runtimeBoundaryEvidence(input, tracking, error));
        }
      },
      beginDrain() {
        if (state === "stopping") return { ok: true, value: undefined };
        if (state !== "ready") return platformRuntimeFailure("PLATFORM_RUNTIME_INVALID_STATE", "Runtime lifecycle can only begin draining from the ready state.", { state }, undefined,
          runtimeStateEvidence(input, { operation: "begin-drain", state, effect: "state-unchanged" }));
        state = "stopping";
        return { ok: true, value: undefined };
      },
      async shutdown() {
        if (state === "created") {
          state = "stopped";
          try { return { ok: true, value: [...events] }; }
          catch (error) { runtimeBoundaryEvidence(input, projection("shutdown"), error); throw error; }
        }
        if (state === "stopped") {
          try { return { ok: true, value: [...events] }; }
          catch (error) { runtimeBoundaryEvidence(input, projection("shutdown"), error); throw error; }
        }
        if (state !== "ready" && state !== "stopping" && state !== "failed") return platformRuntimeFailure("PLATFORM_RUNTIME_INVALID_STATE", "Runtime lifecycle cannot shut down from the current state.", { state }, undefined,
          runtimeStateEvidence(input, { operation: "shutdown", state, effect: "state-unchanged" }));
        if (state !== "stopping") state = "stopping";
        const tracking: Tracking = { operation: "shutdown", phase: "app.beforeStop", subject: "app", boundary: "iteration", effect: "boundary-outcome-unknown" };
        try {
          let ordinal = 0;
          for (const app of apps) {
            select(tracking, ordinal++);
            if (app.lifecycle?.beforeStop !== undefined) await runStep(tracking, "app.beforeStop", app.id, app.lifecycle.beforeStop);
            advance(tracking);
          }
          beginPhase(tracking, "resource.drain", "resource"); ordinal = 0;
          for (const resource of resources) {
            select(tracking, ordinal++);
            if (resource.drain !== undefined) await runStep(tracking, "resource.drain", resource.name, resource.drain);
            advance(tracking);
          }
          beginPhase(tracking, "resource.close", "resource"); ordinal = 0;
          for (const resource of [...resources].reverse()) {
            select(tracking, ordinal++);
            if (resource.close !== undefined) await runStep(tracking, "resource.close", resource.name, resource.close);
            advance(tracking);
          }
          beginPhase(tracking, "telemetry.flush", "telemetry"); ordinal = 0;
          for (const sink of telemetry) {
            select(tracking, ordinal++);
            await runStep(tracking, "telemetry.flush", sink.name, sink.flush);
            advance(tracking);
          }
          beginPhase(tracking, "app.afterStop", "app"); ordinal = 0;
          for (const app of apps) {
            select(tracking, ordinal++);
            if (app.lifecycle?.afterStop !== undefined) await runStep(tracking, "app.afterStop", app.id, app.lifecycle.afterStop);
            advance(tracking);
          }
          state = "stopped";
          tracking.phase = "events-projection"; tracking.subject = "runtime"; tracking.boundary = "projection";
          tracking.effect = "cleanup-completed-result-not-returned"; delete tracking.ordinal;
          return { ok: true, value: [...events] };
        } catch (error) {
          state = "failed";
          return platformRuntimeFailure("PLATFORM_RUNTIME_LIFECYCLE_FAILED", "Runtime shutdown lifecycle failed.", { state: "stopping" }, error,
            runtimeBoundaryEvidence(input, tracking, error));
        }
      },
    };
  } catch (error) {
    runtimeBoundaryEvidence(input, { operation: "construct-lifecycle", phase: construction, subject: "runtime", boundary: "selection", effect: "boundary-outcome-unknown" }, error);
    throw error;
  }
}
const defaultPlatformRuntimeDateTime = "2026-07-10T00:00:00.000Z";
