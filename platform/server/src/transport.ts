import { randomUUID } from "node:crypto";
import { createServer as createNodeServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import type { AddressInfo } from "node:net";
import { correlationId, type CorrelationId } from "@kanbien/core/shared";
import { createDiagnosticRecord, diagnosticRelatedRecordLimit, selectDiagnosticEvidence, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { observeServerDiagnostic, platformServerDiagnosticCatalog, serverTransportBoundaryRecord, serverTransportObservationRecord,
  serverTransportRejectionRecord, serverTransportConfigurationDiagnostic, serverTransportRelationshipDiagnostic,
  type serverTransportBoundaryPhases, type serverTransportConfigurationFields } from "./diagnostics";
import type { PlatformServerErrorCode, PlatformServerRequest, PlatformServerResponse } from "./index";

export interface PlatformServerTransportOptions {
  readonly maxRequestBodyBytes?: number;
  readonly maxHeaderBytes?: number;
  readonly maxHeadersCount?: number;
  readonly headersTimeoutMs?: number;
  readonly requestTimeoutMs?: number;
  readonly keepAliveTimeoutMs?: number;
  readonly handlerTimeoutMs?: number;
  readonly shutdownDrainTimeoutMs?: number;
  readonly maxConcurrentRequests?: number;
  readonly maxRequestsPerSocket?: number;
}

export interface PlatformClientAddressResolverInput {
  readonly socketPeerAddress?: string;
  readonly headers: Readonly<Record<string, string | readonly string[]>>;
  readonly onDiagnostic?: (record: DiagnosticRecord) => unknown;
}

export interface PlatformClientAddressResolver {
  resolve(input: PlatformClientAddressResolverInput): string | undefined;
}

export interface ResolvedPlatformServerTransportOptions {
  readonly maxRequestBodyBytes: number;
  readonly maxHeaderBytes: number;
  readonly maxHeadersCount: number;
  readonly headersTimeoutMs: number;
  readonly requestTimeoutMs: number;
  readonly keepAliveTimeoutMs: number;
  readonly handlerTimeoutMs: number;
  readonly shutdownDrainTimeoutMs: number;
  readonly maxConcurrentRequests: number;
  readonly maxRequestsPerSocket: number;
}

export interface PlatformServerTransportFailure {
  readonly method: string;
  readonly path: string;
  readonly headers: Readonly<Record<string, string | readonly string[]>>;
  readonly requestId: CorrelationId;
  readonly status: number;
  readonly code: PlatformServerErrorCode;
  readonly message: string;
  readonly error?: unknown;
  readonly allow?: readonly string[];
  readonly retryAfterMs?: number;
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
}

export type PlatformServerTransportDiagnosticRequest = Pick<PlatformServerTransportFailure, "method" | "path">
  & Partial<Pick<PlatformServerTransportFailure, "headers" | "requestId">>;

export interface PlatformServerTransportAdmission {
  readonly requestId: CorrelationId;
  readonly response?: PlatformServerResponse;
}

export interface PlatformServerListenOptions {
  readonly port?: number;
  readonly host?: string;
}

export interface PlatformServerHandle {
  readonly port: number;
  readonly host?: string;
  close(): Promise<void>;
}

export function resolvePlatformServerTransportOptions(
  options: PlatformServerTransportOptions = {},
): { readonly ok: true; readonly value: ResolvedPlatformServerTransportOptions } | { readonly ok: false; readonly reason: string; readonly diagnosticRecord: DiagnosticRecord } {
  const resolved: ResolvedPlatformServerTransportOptions = {
    maxRequestBodyBytes: options.maxRequestBodyBytes ?? 1_048_576,
    maxHeaderBytes: options.maxHeaderBytes ?? 16_384,
    maxHeadersCount: options.maxHeadersCount ?? 100,
    headersTimeoutMs: options.headersTimeoutMs ?? 10_000,
    requestTimeoutMs: options.requestTimeoutMs ?? 30_000,
    keepAliveTimeoutMs: options.keepAliveTimeoutMs ?? 5_000,
    handlerTimeoutMs: options.handlerTimeoutMs ?? 30_000,
    shutdownDrainTimeoutMs: options.shutdownDrainTimeoutMs ?? 30_000,
    maxConcurrentRequests: options.maxConcurrentRequests ?? 100,
    maxRequestsPerSocket: options.maxRequestsPerSocket ?? 1_000,
  };

  for (const [name, value] of Object.entries(resolved)) {
    const integer = Number.isInteger(value);
    if (!integer || value <= 0) {
      const reason = typeof value !== "number" ? "wrong-type"
        : value !== value || value === Infinity || value === -Infinity ? "not-finite"
        : !integer ? "not-integer" : "not-positive";
      const observed = createDiagnosticRecord(serverTransportConfigurationDiagnostic, {
        field: name as (typeof serverTransportConfigurationFields)[number], reason, phase: "configuration", effect: "rejected",
      });
      if (!observed.ok) throw new TypeError("PLATFORM_SERVER_DIAGNOSTIC_INVALID");
      return { ok: false, reason: `${name} must be a positive integer.`, diagnosticRecord: observed.value };
    }
  }

  if (resolved.headersTimeoutMs > resolved.requestTimeoutMs) {
    const observed = createDiagnosticRecord(serverTransportRelationshipDiagnostic, {
      relationship: "headers-within-request-timeout", rule: "less-than-or-equal", phase: "configuration", effect: "rejected",
    });
    if (!observed.ok) throw new TypeError("PLATFORM_SERVER_DIAGNOSTIC_INVALID");
    return { ok: false, reason: "headersTimeoutMs must not exceed requestTimeoutMs.", diagnosticRecord: observed.value };
  }

  return { ok: true, value: resolved };
}

export async function listenNodePlatformServer(input: {
  readonly handle: (request: PlatformServerRequest) => Promise<PlatformServerResponse>;
  readonly admit: (request: PlatformServerRequest) => Promise<PlatformServerTransportAdmission>;
  readonly failure: (failure: PlatformServerTransportFailure) => PlatformServerResponse;
  readonly onServerError: (error: unknown) => void;
  readonly options: PlatformServerListenOptions;
  readonly transport: ResolvedPlatformServerTransportOptions;
  readonly clientAddressResolver?: PlatformClientAddressResolver;
  readonly onDiagnostic?: (record: DiagnosticRecord, request?: PlatformServerTransportDiagnosticRequest) => unknown;
  readonly onRequestMetadata?: (request: PlatformServerRequest, records: readonly DiagnosticRecord[]) => unknown;
}): Promise<PlatformServerHandle> {
  let accepting = true;
  let inFlight = 0;
  let listeningCompleted = false;
  const controllers = new Set<AbortController>();
  const observe = (record: DiagnosticRecord, request?: PlatformServerTransportDiagnosticRequest): void => {
    observeServerDiagnostic((value) => input.onDiagnostic?.(value, request), record);
  };
  let server: Server;
  try {
    server = createNodeServer({
      headersTimeout: input.transport.headersTimeoutMs,
      keepAliveTimeout: input.transport.keepAliveTimeoutMs,
      maxHeaderSize: input.transport.maxHeaderBytes,
      requestTimeout: input.transport.requestTimeoutMs,
    }, (req, res) => {
      void handleNodeRequest(req, res);
    });
  } catch (error) {
    observe(serverTransportBoundaryRecord("server-construction", "threw", "listener-not-returned"));
    throw error;
  }
  server.maxHeadersCount = input.transport.maxHeadersCount;
  server.maxRequestsPerSocket = input.transport.maxRequestsPerSocket;
  server.on("clientError", (error, socket) => {
    observe(serverTransportBoundaryRecord("client-error", "error-event", "unknown"));
    input.onServerError(error);
    socket.destroy();
  });
  // Preserve the original unbound callback receiver and argument ordering.
  const onServerError = input.onServerError;
  if (typeof onServerError !== "function") {
    // Keep Node's original constructor-time listener validation for untyped callers.
    server.on("error", onServerError);
  } else {
    server.on("error", function (this: Server, error: unknown) {
      observe(serverTransportBoundaryRecord(listeningCompleted ? "server-error" : "listen", "error-event",
        listeningCompleted ? "unknown" : "listener-not-returned"));
      return Reflect.apply(onServerError, this, [error]);
    });
  }

  async function handleNodeRequest(req: IncomingMessage, res: ServerResponse): Promise<void> {
    const controller = new AbortController();
    let metadataForObservation: PlatformServerTransportDiagnosticRequest | undefined;
    controllers.add(controller);
    res.once("close", () => {
      if (!res.writableEnded) {
        controller.abort();
        observe(serverTransportObservationRecord("response-closed-before-end", "response", "abort-requested"), metadataForObservation);
      }
    });

    let request: PlatformServerRequest | undefined;
    let counted = false;
    let handlerOutlivedResponse = false;
    let boundaryPhase: (typeof serverTransportBoundaryPhases)[number] = "metadata";
    const writeResponse = (response: PlatformServerResponse): void => {
      boundaryPhase = "response-headers";
      writeNodeResponse(res, response, (record) => observe(record, metadataForObservation));
    };
    const failureResponse = (failure: PlatformServerTransportFailure): PlatformServerResponse => {
      metadataForObservation ??= failure;
      boundaryPhase = "failure-projection";
      return input.failure(failure);
    };
    const releaseRequestCapacity = (): void => {
      if (counted) {
        inFlight -= 1;
        counted = false;
      }
      controllers.delete(controller);
    };
    try {
      const resolverRecords: DiagnosticRecord[] = [];
      const metadata = requestMetadata(req, controller.signal, input.clientAddressResolver, (record) => {
        if (resolverRecords.length >= diagnosticRelatedRecordLimit) return;
        const selected = selectDiagnosticEvidence(platformServerDiagnosticCatalog.definitions, { diagnosticRecord: record });
        if (selected.diagnosticRecord !== undefined) resolverRecords.push(selected.diagnosticRecord);
      });
      if (!metadata.ok) {
        metadataForObservation = metadata.failure;
        writeResponse(failureResponse(metadata.failure));
        return;
      }
      metadataForObservation = metadata.value;
      if (resolverRecords.length > 0) {
        observeServerDiagnostic(() => input.onRequestMetadata?.(metadata.value, Object.freeze(resolverRecords)), resolverRecords[0]!);
      }

      if (!accepting || inFlight >= input.transport.maxConcurrentRequests) {
        const requestId = metadata.value.requestId ?? platformServerRequestId(undefined);
        writeResponse(failureResponse({
          method: metadata.value.method,
          path: metadata.value.path,
          headers: metadata.value.headers ?? {},
          requestId,
          status: 503,
          code: "PLATFORM_SERVER_SERVICE_UNAVAILABLE",
          message: "The platform server is temporarily unavailable.",
          diagnosticRecord: serverTransportRejectionRecord(!accepting ? "server-closing" : "concurrency-capacity-reached", "admission"),
        }));
        return;
      }

      inFlight += 1;
      counted = true;
      boundaryPhase = "admission";
      const admission = await input.admit(metadata.value);
      if (admission.response !== undefined) {
        writeResponse(admission.response);
        return;
      }

      boundaryPhase = "body-stream";
      const parsed = await readNodeRequestBody(req, metadata.value, admission.requestId, input.transport.maxRequestBodyBytes);
      if (!parsed.ok) {
        writeResponse(failureResponse(parsed.failure));
        return;
      }

      request = parsed.value;
      boundaryPhase = "handler";
      const handler = input.handle(request);
      let handlerDeadlineObserved = false;
      const response = await settleWithin(
        handler,
        input.transport.handlerTimeoutMs,
        () => { handlerDeadlineObserved = true; controller.abort(); },
      );
      if (response === undefined) {
        handlerOutlivedResponse = true;
        void handler.then(
          () => {
            releaseRequestCapacity();
          },
          (error: unknown) => {
            observe(serverTransportBoundaryRecord("late-handler", "threw", "handler-settled"), request);
            input.onServerError(error);
            releaseRequestCapacity();
          },
        );
        writeResponse(failureResponse({
          method: request.method,
          path: request.path,
          headers: request.headers ?? {},
          requestId: request.requestId ?? admission.requestId,
          status: 504,
          code: "PLATFORM_SERVER_REQUEST_TIMEOUT",
          message: "The platform request timed out.",
          diagnosticRecord: serverTransportRejectionRecord(handlerDeadlineObserved ? "handler-deadline-observed" : "handler-result-unavailable", "handler",
            handlerDeadlineObserved ? "handler-still-pending" : "handler-result-not-returned"),
        }));
        return;
      }

      writeResponse(response);
    } catch (error) {
      const requestId = request?.requestId ?? metadataRequestId(req);
      writeResponse(failureResponse({
        method: request?.method ?? req.method ?? "UNKNOWN",
        path: request?.path ?? safePath(req.url),
        headers: request?.headers ?? nodeHeaders(req),
        requestId,
        status: 500,
        code: "PLATFORM_SERVER_HANDLER_FAILED",
        message: "Platform request processing failed.",
        error,
        ...((boundaryPhase as (typeof serverTransportBoundaryPhases)[number]) === "response-headers" ? {} : {
          diagnosticRecord: serverTransportBoundaryRecord(boundaryPhase, "threw", "request-not-returned"),
        }),
      }));
    } finally {
      if (!handlerOutlivedResponse) {
        releaseRequestCapacity();
      }
    }
  }

  await new Promise<void>((resolve, reject) => {
    const onListenError = (error: Error) => {
      server.off("listening", onListen);
      reject(error);
    };
    const onListen = () => {
      server.off("error", onListenError);
      listeningCompleted = true;
      resolve();
    };
    server.once("error", onListenError);
    server.once("listening", onListen);
    try { server.listen(input.options.port ?? 0, input.options.host); }
    catch (error) {
      observe(serverTransportBoundaryRecord("listen", "threw", "listener-not-returned"));
      throw error;
    }
  });

  const address = server.address() as AddressInfo;
  return {
    port: address.port,
    ...(input.options.host === undefined ? {} : { host: input.options.host }),
    close: async () => {
      accepting = false;
      const closed = closeServer(server, observe);
      const drained = await settleWithin(closed, input.transport.shutdownDrainTimeoutMs, () => {
        observe(serverTransportObservationRecord("drain-deadline-observed", "shutdown", "shutdown-still-pending"));
        for (const controller of controllers) {
          controller.abort();
        }
        server.closeAllConnections();
      });
      if (drained === undefined) {
        await closed;
      }
    },
  };
}

function requestMetadata(
  req: IncomingMessage,
  abortSignal: AbortSignal,
  clientAddressResolver?: PlatformClientAddressResolver,
  onDiagnostic?: (record: DiagnosticRecord) => unknown,
): { readonly ok: true; readonly value: PlatformServerRequest } | { readonly ok: false; readonly failure: PlatformServerTransportFailure } {
  const headers = nodeHeaders(req);
  const requestId = metadataRequestId(req);
  const parsedUrl = safeUrl(req.url);
  if (parsedUrl === undefined) {
    return {
      ok: false,
      failure: {
        method: req.method ?? "UNKNOWN",
        path: "/",
        headers,
        requestId,
        status: 400,
        code: "PLATFORM_SERVER_INVALID_REQUEST",
        message: "The request URL is invalid.",
        diagnosticRecord: serverTransportRejectionRecord("url-invalid", "metadata"),
      },
    };
  }

  const method = normalizeMethod(req.method);
  if (method === undefined) {
    return {
      ok: false,
      failure: {
        method: req.method ?? "UNKNOWN",
        path: parsedUrl.pathname,
        headers,
        requestId,
        status: 405,
        code: "PLATFORM_SERVER_METHOD_NOT_ALLOWED",
        message: "The request method is not allowed.",
        diagnosticRecord: serverTransportRejectionRecord("method-unsupported", "metadata"),
      },
    };
  }

  const clientAddress = resolvedClientAddress(clientAddressResolver, req.socket.remoteAddress, headers, onDiagnostic);

  return {
    ok: true,
    value: {
      method,
      path: parsedUrl.pathname,
      headers,
      query: queryFromUrl(parsedUrl),
      ...(clientAddress === undefined ? {} : { clientAddress }),
      requestId,
      abortSignal,
      transportAdmissionApplied: false,
    },
  };
}

function resolvedClientAddress(
  clientAddressResolver: PlatformClientAddressResolver | undefined,
  socketPeerAddress: string | undefined,
  headers: Readonly<Record<string, string | readonly string[]>>,
  onDiagnostic?: (record: DiagnosticRecord) => unknown,
): string | undefined {
  return clientAddressResolver?.resolve({
    headers,
    ...(onDiagnostic === undefined ? {} : { onDiagnostic }),
    ...(socketPeerAddress === undefined ? {} : { socketPeerAddress }),
  }) ?? socketPeerAddress;
}

async function readNodeRequestBody(
  req: IncomingMessage,
  metadata: PlatformServerRequest,
  requestId: CorrelationId,
  maxRequestBodyBytes: number,
): Promise<{ readonly ok: true; readonly value: PlatformServerRequest } | { readonly ok: false; readonly failure: PlatformServerTransportFailure }> {
  const contentLength = firstHeaderValue(metadata.headers ?? {}, "content-length");
  if (contentLength !== undefined && contentLength.length > 0) {
    const declaredLength = Number(contentLength);
    const integer = Number.isInteger(declaredLength);
    if (!integer || declaredLength < 0) {
      return transportFailure(metadata, requestId, 400, "PLATFORM_SERVER_INVALID_REQUEST", "The request content length is invalid.",
        serverTransportRejectionRecord(!integer ? "declared-length-not-integer" : "declared-length-negative", "body"));
    }
    if (declaredLength > maxRequestBodyBytes) {
      return transportFailure(metadata, requestId, 413, "PLATFORM_SERVER_PAYLOAD_TOO_LARGE", "The request payload is too large.",
        serverTransportRejectionRecord("declared-length-over-limit", "body"));
    }
  }

  if (!mayCarryJsonBody(metadata.method)) {
    return { ok: true, value: { ...metadata, requestId, transportAdmissionApplied: true } };
  }

  const chunks: Buffer[] = [];
  let totalBytes = 0;
  for await (const chunk of req) {
    const buffer = typeof chunk === "string" ? Buffer.from(chunk) : chunk;
    totalBytes += buffer.length;
    if (totalBytes > maxRequestBodyBytes) {
      return transportFailure(metadata, requestId, 413, "PLATFORM_SERVER_PAYLOAD_TOO_LARGE", "The request payload is too large.",
        serverTransportRejectionRecord("streamed-body-over-limit", "body"));
    }
    chunks.push(buffer);
  }

  if (totalBytes === 0) {
    return { ok: true, value: { ...metadata, requestId, transportAdmissionApplied: true } };
  }

  const contentType = firstHeaderValue(metadata.headers ?? {}, "content-type");
  const normalizedContentType = contentType?.toLowerCase().split(";", 1)[0]?.trim();
  if (normalizedContentType !== "application/json") {
    return transportFailure(metadata, requestId, 415, "PLATFORM_SERVER_UNSUPPORTED_MEDIA_TYPE", "The request content type must be application/json.",
      serverTransportRejectionRecord(contentType === undefined ? "media-type-missing" : normalizedContentType === "" ? "media-type-empty" : "media-type-unsupported", "body"));
  }

  try {
    return {
      ok: true,
      value: {
        ...metadata,
        requestId,
        body: JSON.parse(Buffer.concat(chunks).toString("utf8")),
        transportAdmissionApplied: true,
      },
    };
  } catch (error) {
    return transportFailure(metadata, requestId, 400, "PLATFORM_SERVER_INVALID_REQUEST", "The request body is not valid JSON.",
      serverTransportRejectionRecord("body-decoding-threw", "body"), error);
  }
}

function transportFailure(
  request: PlatformServerRequest,
  requestId: CorrelationId,
  status: number,
  code: PlatformServerErrorCode,
  message: string,
  diagnosticRecord: DiagnosticRecord,
  error?: unknown,
): { readonly ok: false; readonly failure: PlatformServerTransportFailure } {
  return {
    ok: false,
    failure: {
      method: request.method,
      path: request.path,
      headers: request.headers ?? {},
      requestId,
      status,
      code,
      message,
      diagnosticRecord,
      ...(error === undefined ? {} : { error }),
    },
  };
}

function nodeHeaders(req: IncomingMessage): Readonly<Record<string, string | readonly string[]>> {
  return Object.fromEntries(
    Object.entries(req.headers).flatMap(([key, value]) => {
      if (value === undefined) {
        return [];
      }

      return [[key, typeof value === "string" ? value : [...value]]];
    }),
  ) as Readonly<Record<string, string | readonly string[]>>;
}

function safeUrl(value: string | undefined): URL | undefined {
  try {
    return new URL(value ?? "/", "http://platform-server.invalid");
  } catch {
    return undefined;
  }
}

function safePath(value: string | undefined): string {
  return safeUrl(value)?.pathname ?? "/";
}

function queryFromUrl(url: URL): Readonly<Record<string, string | readonly string[]>> {
  const query: Record<string, string | readonly string[]> = {};
  for (const [key, value] of url.searchParams.entries()) {
    const current = query[key];
    if (current === undefined) {
      query[key] = value;
      continue;
    }

    query[key] = typeof current === "string" ? [current, value] : [...current, value];
  }
  return query;
}

function normalizeMethod(method: string | undefined): PlatformServerRequest["method"] | undefined {
  switch (method) {
    case "GET":
    case "POST":
    case "PUT":
    case "PATCH":
    case "DELETE":
    case "OPTIONS":
      return method;
    default:
      return undefined;
  }
}

function mayCarryJsonBody(method: PlatformServerRequest["method"]): boolean {
  return method === "POST" || method === "PUT" || method === "PATCH";
}

function firstHeaderValue(headers: Readonly<Record<string, string | readonly string[]>>, name: string): string | undefined {
  const entry = Object.entries(headers).find(([key]) => key.toLowerCase() === name.toLowerCase());
  const value = entry?.[1];
  return typeof value === "string" ? value : value?.[0];
}

function metadataRequestId(req: IncomingMessage): CorrelationId {
  const supplied = firstHeaderValue(nodeHeaders(req), "x-request-id");
  return platformServerRequestId(supplied);
}

export function platformServerRequestId(value: string | undefined): CorrelationId {
  return value !== undefined && requestIdPattern.test(value)
    ? correlationId(value)
    : correlationId(randomUUID());
}

async function settleWithin<T>(
  promise: Promise<T>,
  timeoutMs: number,
  onTimeout: () => void,
): Promise<T | undefined> {
  let timeout: NodeJS.Timeout | undefined;
  try {
    return await Promise.race([
      promise,
      new Promise<undefined>((resolve) => {
        timeout = setTimeout(() => {
          onTimeout();
          resolve(undefined);
        }, timeoutMs);
      }),
    ]);
  } finally {
    if (timeout !== undefined) {
      clearTimeout(timeout);
    }
  }
}

function writeNodeResponse(res: ServerResponse, platformResponse: PlatformServerResponse,
  observe: (record: DiagnosticRecord) => void): void {
  if (res.writableEnded) {
    observe(serverTransportObservationRecord("response-already-ended", "response", "response-skipped"));
    return;
  }
  if (res.destroyed) {
    observe(serverTransportObservationRecord("response-destroyed", "response", "response-skipped"));
    return;
  }

  let phase: "response-headers" | "response-status" | "response-serialization" | "response-end" = "response-headers";
  try {
    for (const [key, value] of Object.entries(platformResponse.headers)) {
      res.setHeader(key, value);
    }

    phase = "response-status";
    res.statusCode = platformResponse.status;
    phase = "response-end";
    let body: string | undefined;
    // Resolve the original end method before body projection, as before.
    res.end((phase = "response-serialization", body = JSON.stringify(platformResponse.body ?? null), phase = "response-end", body));
  } catch (error) {
    observe(serverTransportBoundaryRecord(phase, "threw", "unknown"));
    throw error;
  }
}

async function closeServer(server: Server, observe: (record: DiagnosticRecord) => void): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    try {
      server.close((error) => {
        if (error === undefined) {
          resolve();
          return;
        }

        observe(serverTransportBoundaryRecord("close-callback", "callback-error", "close-not-confirmed"));
        reject(error);
      });
    } catch (error) {
      observe(serverTransportBoundaryRecord("close-invocation", "threw", "close-not-confirmed"));
      throw error;
    }
  });
}

const requestIdPattern = /^[A-Za-z0-9._-]{8,128}$/;
