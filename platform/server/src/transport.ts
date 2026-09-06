import { randomUUID } from "node:crypto";
import { createServer as createNodeServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import type { AddressInfo } from "node:net";
import { correlationId, type CorrelationId } from "@kanbien/core/shared";
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
}

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
): { readonly ok: true; readonly value: ResolvedPlatformServerTransportOptions } | { readonly ok: false; readonly reason: string } {
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
    if (!Number.isInteger(value) || value <= 0) {
      return { ok: false, reason: `${name} must be a positive integer.` };
    }
  }

  if (resolved.headersTimeoutMs > resolved.requestTimeoutMs) {
    return { ok: false, reason: "headersTimeoutMs must not exceed requestTimeoutMs." };
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
}): Promise<PlatformServerHandle> {
  let accepting = true;
  let inFlight = 0;
  const controllers = new Set<AbortController>();
  const server = createNodeServer({
    headersTimeout: input.transport.headersTimeoutMs,
    keepAliveTimeout: input.transport.keepAliveTimeoutMs,
    maxHeaderSize: input.transport.maxHeaderBytes,
    requestTimeout: input.transport.requestTimeoutMs,
  }, (req, res) => {
    void handleNodeRequest(req, res);
  });
  server.maxHeadersCount = input.transport.maxHeadersCount;
  server.maxRequestsPerSocket = input.transport.maxRequestsPerSocket;
  server.on("clientError", (error, socket) => {
    input.onServerError(error);
    socket.destroy();
  });
  server.on("error", input.onServerError);

  async function handleNodeRequest(req: IncomingMessage, res: ServerResponse): Promise<void> {
    const controller = new AbortController();
    controllers.add(controller);
    res.once("close", () => {
      if (!res.writableEnded) {
        controller.abort();
      }
    });

    let request: PlatformServerRequest | undefined;
    let counted = false;
    let handlerOutlivedResponse = false;
    const releaseRequestCapacity = (): void => {
      if (counted) {
        inFlight -= 1;
        counted = false;
      }
      controllers.delete(controller);
    };
    try {
      const metadata = requestMetadata(req, controller.signal, input.clientAddressResolver);
      if (!metadata.ok) {
        writeNodeResponse(res, input.failure(metadata.failure));
        return;
      }

      if (!accepting || inFlight >= input.transport.maxConcurrentRequests) {
        const requestId = metadata.value.requestId ?? platformServerRequestId(undefined);
        writeNodeResponse(res, input.failure({
          method: metadata.value.method,
          path: metadata.value.path,
          headers: metadata.value.headers ?? {},
          requestId,
          status: 503,
          code: "PLATFORM_SERVER_SERVICE_UNAVAILABLE",
          message: "The platform server is temporarily unavailable.",
        }));
        return;
      }

      inFlight += 1;
      counted = true;
      const admission = await input.admit(metadata.value);
      if (admission.response !== undefined) {
        writeNodeResponse(res, admission.response);
        return;
      }

      const parsed = await readNodeRequestBody(req, metadata.value, admission.requestId, input.transport.maxRequestBodyBytes);
      if (!parsed.ok) {
        writeNodeResponse(res, input.failure(parsed.failure));
        return;
      }

      request = parsed.value;
      const handler = input.handle(request);
      const response = await settleWithin(
        handler,
        input.transport.handlerTimeoutMs,
        () => controller.abort(),
      );
      if (response === undefined) {
        handlerOutlivedResponse = true;
        void handler.then(
          () => {
            releaseRequestCapacity();
          },
          (error: unknown) => {
            input.onServerError(error);
            releaseRequestCapacity();
          },
        );
        writeNodeResponse(res, input.failure({
          method: request.method,
          path: request.path,
          headers: request.headers ?? {},
          requestId: request.requestId ?? admission.requestId,
          status: 504,
          code: "PLATFORM_SERVER_REQUEST_TIMEOUT",
          message: "The platform request timed out.",
        }));
        return;
      }

      writeNodeResponse(res, response);
    } catch (error) {
      const requestId = request?.requestId ?? metadataRequestId(req);
      writeNodeResponse(res, input.failure({
        method: request?.method ?? req.method ?? "UNKNOWN",
        path: request?.path ?? safePath(req.url),
        headers: request?.headers ?? nodeHeaders(req),
        requestId,
        status: 500,
        code: "PLATFORM_SERVER_HANDLER_FAILED",
        message: "Platform request processing failed.",
        error,
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
      resolve();
    };
    server.once("error", onListenError);
    server.once("listening", onListen);
    server.listen(input.options.port ?? 0, input.options.host);
  });

  const address = server.address() as AddressInfo;
  return {
    port: address.port,
    ...(input.options.host === undefined ? {} : { host: input.options.host }),
    close: async () => {
      accepting = false;
      const closed = closeServer(server);
      const drained = await settleWithin(closed, input.transport.shutdownDrainTimeoutMs, () => {
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
      },
    };
  }

  const clientAddress = resolvedClientAddress(clientAddressResolver, req.socket.remoteAddress, headers);

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
): string | undefined {
  return clientAddressResolver?.resolve({
    headers,
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
    if (!Number.isInteger(declaredLength) || declaredLength < 0) {
      return transportFailure(metadata, requestId, 400, "PLATFORM_SERVER_INVALID_REQUEST", "The request content length is invalid.");
    }
    if (declaredLength > maxRequestBodyBytes) {
      return transportFailure(metadata, requestId, 413, "PLATFORM_SERVER_PAYLOAD_TOO_LARGE", "The request payload is too large.");
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
      return transportFailure(metadata, requestId, 413, "PLATFORM_SERVER_PAYLOAD_TOO_LARGE", "The request payload is too large.");
    }
    chunks.push(buffer);
  }

  if (totalBytes === 0) {
    return { ok: true, value: { ...metadata, requestId, transportAdmissionApplied: true } };
  }

  const contentType = firstHeaderValue(metadata.headers ?? {}, "content-type");
  if (!isJsonContentType(contentType)) {
    return transportFailure(metadata, requestId, 415, "PLATFORM_SERVER_UNSUPPORTED_MEDIA_TYPE", "The request content type must be application/json.");
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
    return transportFailure(metadata, requestId, 400, "PLATFORM_SERVER_INVALID_REQUEST", "The request body is not valid JSON.", error);
  }
}

function transportFailure(
  request: PlatformServerRequest,
  requestId: CorrelationId,
  status: number,
  code: PlatformServerErrorCode,
  message: string,
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

function isJsonContentType(value: string | undefined): boolean {
  return value?.toLowerCase().split(";", 1)[0]?.trim() === "application/json";
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

function writeNodeResponse(res: ServerResponse, platformResponse: PlatformServerResponse): void {
  if (res.writableEnded || res.destroyed) {
    return;
  }

  for (const [key, value] of Object.entries(platformResponse.headers)) {
    res.setHeader(key, value);
  }

  res.statusCode = platformResponse.status;
  res.end(JSON.stringify(platformResponse.body ?? null));
}

async function closeServer(server: Server): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    server.close((error) => {
      if (error === undefined) {
        resolve();
        return;
      }

      reject(error);
    });
  });
}

const requestIdPattern = /^[A-Za-z0-9._-]{8,128}$/;
