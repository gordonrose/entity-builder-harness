#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.script.operational-realization-typescript-observer
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: deployment.realization
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Observe actual locked TypeScript resolution and emissions in a parent-owned disposable isolated snapshot.
//   portability: {class: reusable, targets: [entity-builder]}
//   effects: [writes-files]
//   used_by:
//   - id: deploy.script.operational-realization-gate
//     path: scripts/04.deploy/operational-realization-gate/script.py

import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";

// This observer does not create a sandbox or authenticate an arbitrary receipt.
// Its parent verifies the toolchain, freezes inputs, enforces OS isolation and
// binds its locally produced observation to the corresponding execution.
const NODE_VERSION = "22.23.3";
const TYPESCRIPT_VERSION = "5.9.3";
const MAX_FILES = 10000;
const MAX_ROWS = 40000;
const MAX_FILE_BYTES = 16 * 1024 * 1024;
const MAX_TOTAL_BYTES = 128 * 1024 * 1024;
const MAX_DIAGNOSTICS = 2000;
const PRIVATE = new Set([".git", ".aws", ".ssh", ".codex", ".agents", ".npmrc", ".pypirc", ".env", "credentials", "credential", "secrets", "secret"]);

class ObserverFailure extends Error {
  constructor(code) { super(code); this.code = code; }
}
function fail(code) { throw new ObserverFailure(code); }
function hash(bytes) { return "sha256:" + createHash("sha256").update(bytes).digest("hex"); }
function canonical(value) {
  const ordered = (item) => Array.isArray(item) ? item.map(ordered)
    : item !== null && typeof item === "object"
      ? Object.fromEntries(Object.keys(item).sort().map((key) => [key, ordered(item[key])])) : item;
  return JSON.stringify(ordered(value)).replace(/[\u007f-\uffff]/g, (character) =>
    "\\u" + character.charCodeAt(0).toString(16).padStart(4, "0"));
}
function safeRelative(value) {
  return typeof value === "string" && value.length > 0 && value.length <= 512
    && /^[A-Za-z0-9_@./+-]+$/.test(value)
    && value.split("/").every((part) => part !== "" && part !== "." && part !== ".."
      && !PRIVATE.has(part.toLowerCase()) && !part.toLowerCase().startsWith(".env.")
      && !/\.(?:pem|key|p12|pfx)$/.test(part.toLowerCase()));
}
function argumentsFrom(argv) {
  if (argv.length !== 6) fail("observer-arguments-invalid");
  const options = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    if (!["--root", "--config", "--output"].includes(key) || key in options
        || !argv[index + 1] || argv[index + 1].startsWith("--")) fail("observer-arguments-invalid");
    options[key] = argv[index + 1];
  }
  if (!path.isAbsolute(options["--root"]) || !path.isAbsolute(options["--output"])
      || !safeRelative(options["--config"]) || !options["--config"].endsWith(".json")) fail("observer-arguments-invalid");
  const root = path.resolve(options["--root"]);
  const output = path.resolve(options["--output"]);
  if (fs.realpathSync(root) !== root || !fs.statSync(root).isDirectory()) fail("observer-root-unsafe");
  if (fs.realpathSync(path.dirname(output)) !== path.dirname(output)
      || output === root || output.startsWith(root + path.sep)) fail("observer-receipt-path-unsafe");
  if (fs.existsSync(output)) fail("observer-receipt-exists");
  return { root, configuration: options["--config"], output };
}

function observe(options) {
  const result = { schema: "local-typescript-observation/v1", configuration: options.configuration,
    node_version: process.versions.node, typescript_version: null, verdict: "failed",
    no_emit: false, emit_skipped: true, inputs: [], resolutions: [], outputs: [], diagnostics: [], findings: [] };
  const inputs = new Map();
  const outputs = new Map();
  const resolutions = new Map();
  const directories = new Map();
  let totalInputBytes = 0;
  let totalOutputBytes = 0;
  let visitedEntries = 0;
  let ts;
  const enforce = (action) => (...args) => {
    try { return action(...args); }
    catch (error) {
      // TypeScript converts some host failures into diagnostics. Retain the
      // independent boundary failure even if the compiler catches the throw.
      if (error instanceof ObserverFailure && !result.findings.some((row) => row.code === error.code)) {
        result.findings.push({ code: error.code });
      }
      throw error;
    }
  };
  const contained = (absolute) => absolute === options.root || absolute.startsWith(options.root + path.sep);
  function absoluteName(value) { return path.resolve(options.root, value); }
  function relativeName(value) {
    const absolute = absoluteName(value);
    if (!contained(absolute)) fail("observer-input-path-unsafe");
    const relative = path.relative(options.root, absolute).split(path.sep).join("/");
    if (relative && !safeRelative(relative)) fail("observer-input-path-unsafe");
    return relative;
  }
  function inspect(value, allowMissing = true) {
    const absolute = absoluteName(value);
    relativeName(absolute);
    let real;
    try { real = fs.realpathSync(absolute); }
    catch (error) {
      if (allowMissing && ["ENOENT", "ENOTDIR"].includes(error.code)) return undefined;
      throw error;
    }
    if (!contained(real)) fail("observer-input-link-unsafe");
    relativeName(real);
    const info = fs.statSync(real);
    if (!info.isFile() && !info.isDirectory()) fail("observer-input-kind-unsupported");
    return { absolute, real, info };
  }
  function permittedExistenceProbe(value) {
    const absolute = absoluteName(value);
    if (!contained(absolute)) return false;
    const relative = path.relative(options.root, absolute).split(path.sep).join("/");
    // With baseUrl, Node10 probes filenames such as node:crypto.ts before
    // resolving ambient built-in declarations. Unsupported candidate names
    // are absent without touching the filesystem. Explicit input reads and
    // selected configuration/source paths retain their hard rejection.
    return relative === "" || safeRelative(relative);
  }
  function fileExists(value) {
    if (!permittedExistenceProbe(value)) return false;
    return inspect(value)?.info.isFile() ?? false;
  }
  function directoryExists(value) {
    if (!permittedExistenceProbe(value)) return false;
    return inspect(value)?.info.isDirectory() ?? false;
  }
  function readBytes(value) {
    const item = inspect(value);
    if (!item) return undefined;
    if (!item.info.isFile()) fail("observer-input-kind-unsupported");
    const relative = relativeName(item.real);
    if (relative === ".cache" || relative.startsWith(".cache/")) fail("observer-prior-output-input");
    if (item.info.size > MAX_FILE_BYTES) fail("observer-limit-exceeded");
    const fd = fs.openSync(item.real, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
    let raw;
    try {
      const before = fs.fstatSync(fd);
      if (!before.isFile() || before.size > MAX_FILE_BYTES) fail("observer-input-kind-unsupported");
      raw = fs.readFileSync(fd);
      const after = fs.fstatSync(fd);
      if (raw.length > MAX_FILE_BYTES) fail("observer-limit-exceeded");
      if (before.dev !== after.dev || before.ino !== after.ino || before.size !== after.size
          || before.mtimeMs !== after.mtimeMs || before.ctimeMs !== after.ctimeMs) fail("observer-input-changed");
    } finally { fs.closeSync(fd); }
    const row = { kind: relative.startsWith("node_modules/") ? "dependency" : "repository",
      path: relative, digest: hash(raw), bytes: raw.length };
    if (inputs.has(relative)) {
      if (inputs.get(relative).digest !== row.digest) fail("observer-input-changed");
    } else {
      totalInputBytes += raw.length;
      if (inputs.size >= MAX_FILES || totalInputBytes > MAX_TOTAL_BYTES) fail("observer-limit-exceeded");
      inputs.set(relative, row);
    }
    return raw;
  }
  function readFile(value) {
    if (!contained(absoluteName(value))) return undefined;
    const raw = readBytes(value);
    if (!raw) return undefined;
    // Match TypeScript System.readFile's BOM-aware decoding.
    if (raw.length >= 2 && raw[0] === 0xfe && raw[1] === 0xff) {
      const littleEndian = Buffer.from(raw.subarray(2));
      if (littleEndian.length % 2) fail("observer-input-encoding-unsupported");
      littleEndian.swap16();
      return littleEndian.toString("utf16le");
    }
    if (raw.length >= 2 && raw[0] === 0xff && raw[1] === 0xfe) return raw.subarray(2).toString("utf16le");
    return raw.subarray(raw.length >= 3 && raw[0] === 0xef && raw[1] === 0xbb && raw[2] === 0xbf ? 3 : 0).toString("utf8");
  }
  function realpath(value) {
    if (!contained(absoluteName(value))) return absoluteName(value);
    return inspect(value)?.real ?? absoluteName(value);
  }
  function entries(value) {
    const item = inspect(value);
    if (!item || !item.info.isDirectory()) return { files: [], directories: [] };
    if (directories.has(item.real)) return directories.get(item.real);
    const names = fs.readdirSync(item.real).sort();
    visitedEntries += names.length;
    if (visitedEntries > MAX_ROWS) fail("observer-limit-exceeded");
    const answer = { files: [], directories: [] };
    for (const name of names) {
      if (!safeRelative(name)) fail("observer-input-path-unsafe");
      const child = inspect(path.join(item.real, name));
      if (!child) fail("observer-input-changed");
      answer[child.info.isDirectory() ? "directories" : "files"].push(name);
    }
    directories.set(item.real, answer);
    return answer;
  }
  function outputName(value) {
    const absolute = absoluteName(value);
    if (!contained(absolute)) fail("observer-output-path-unsafe");
    const relative = relativeName(absolute);
    if (!relative.startsWith(".cache/") || inputs.has(relative)) fail("observer-output-path-unsafe");
    let ancestor = options.root;
    for (const part of relative.split("/")) {
      ancestor = path.join(ancestor, part);
      try { if (fs.lstatSync(ancestor).isSymbolicLink()) fail("observer-output-link-unsafe"); }
      catch (error) { if (error.code !== "ENOENT") throw error; }
    }
    return { absolute, relative };
  }
  function writeFile(value, data, bom) {
    const target = outputName(value);
    if (outputs.has(target.relative) || fs.existsSync(target.absolute)) fail("observer-output-exists");
    const raw = Buffer.from((bom ? "\ufeff" : "") + data, "utf8");
    totalOutputBytes += raw.length;
    if (raw.length > MAX_FILE_BYTES || totalOutputBytes > MAX_TOTAL_BYTES || outputs.size >= MAX_FILES) fail("observer-limit-exceeded");
    fs.mkdirSync(path.dirname(target.absolute), { recursive: true });
    fs.writeFileSync(target.absolute, raw, { flag: "wx", mode: 0o600 });
    outputs.set(target.relative, { path: target.relative, digest: hash(raw), bytes: raw.length });
  }
  function recordDiagnostics(phase, values) {
    for (const diagnostic of values) {
      let relative = null;
      let line = null;
      let column = null;
      if (diagnostic.file) {
        relative = relativeName(diagnostic.file.fileName);
        if (diagnostic.start !== undefined) {
          const position = diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start);
          line = position.line + 1;
          column = position.character + 1;
        }
      }
      const category = ["warning", "error", "suggestion", "message"][diagnostic.category];
      if (!category || !Number.isInteger(diagnostic.code)) fail("observer-diagnostic-invalid");
      const row = { phase, category, code: diagnostic.code, path: relative, line, column };
      if (!result.diagnostics.some((prior) => canonical(prior) === canonical(row))) result.diagnostics.push(row);
      if (result.diagnostics.length > MAX_DIAGNOSTICS) fail("observer-limit-exceeded");
    }
  }
  try {
    if (process.versions.node !== NODE_VERSION) fail("observer-node-version-unsupported");
    const compilerPath = path.join(options.root, "node_modules/typescript/lib/typescript.js");
    const packagePath = path.join(options.root, "node_modules/typescript/package.json");
    const compilerBytes = readBytes(compilerPath);
    const packageBytes = readBytes(packagePath);
    if (!compilerBytes || !packageBytes) fail("observer-typescript-unavailable");
    const packageDocument = JSON.parse(packageBytes.toString("utf8"));
    if (packageDocument.version !== TYPESCRIPT_VERSION) fail("observer-typescript-version-unsupported");
    ts = createRequire(import.meta.url)(compilerPath);
    result.typescript_version = ts.version;
    if (ts.version !== TYPESCRIPT_VERSION) fail("observer-typescript-version-unsupported");
    const system = { ...ts.sys, args: [], newLine: "\n", useCaseSensitiveFileNames: true,
      getCurrentDirectory: () => options.root, getExecutingFilePath: () => compilerPath,
      getEnvironmentVariable: () => "", write: () => {}, readFile: enforce(readFile), fileExists: enforce(fileExists),
      directoryExists: enforce(directoryExists), realpath: enforce(realpath),
      getDirectories: enforce((value) => entries(value).directories),
      readDirectory: enforce((value, extensions, excludes, includes, depth) => ts.matchFiles(
        value, extensions, excludes, includes, true, options.root, depth, entries, realpath)),
      writeFile: enforce(writeFile), createDirectory: enforce((value) => {
        outputName(path.join(value, "directory-check"));
        fs.mkdirSync(absoluteName(value), { recursive: true });
      }),
    };
    const configurationPath = path.join(options.root, options.configuration);
    const configuration = ts.readConfigFile(configurationPath, system.readFile);
    if (configuration.error) recordDiagnostics("config", [configuration.error]);
    else {
      const parsed = ts.parseJsonConfigFileContent(configuration.config, system,
        path.dirname(configurationPath), undefined, configurationPath);
      recordDiagnostics("config", parsed.errors);
      result.no_emit = parsed.options.noEmit === true;
      for (const key of ["outDir", "declarationDir"]) {
        if (parsed.options[key]) outputName(path.join(parsed.options[key], "output-check"));
      }
      for (const key of ["outFile", "tsBuildInfoFile"]) {
        if (parsed.options[key]) outputName(parsed.options[key]);
      }
      // These execution features require separate contracts; do not approximate.
      if (parsed.projectReferences?.length || parsed.options.plugins?.length || parsed.options.watch) fail("observer-project-feature-unsupported");
      for (const name of parsed.fileNames) relativeName(name);
      if (!result.diagnostics.some((row) => row.category === "error")) {
        const host = ts.createIncrementalCompilerHost(parsed.options, system);
        const moduleCache = ts.createModuleResolutionCache(options.root, (name) => name, parsed.options);
        host.resolveModuleNameLiterals = (literals, from, redirected, compilerOptions, containingSourceFile) => literals.map((literal) => {
          const mode = ts.getModeForUsageLocation(containingSourceFile, literal, compilerOptions);
          const resolved = ts.resolveModuleName(literal.text, from, compilerOptions, host, moduleCache, redirected, mode);
          const row = { from: relativeName(from), specifier_digest: hash(Buffer.from(literal.text, "utf8")),
            mode: mode === ts.ModuleKind.ESNext ? "import" : mode === ts.ModuleKind.CommonJS ? "require" : "default",
            resolved_path: resolved.resolvedModule ? relativeName(realpath(resolved.resolvedModule.resolvedFileName)) : null,
            is_external: resolved.resolvedModule?.isExternalLibraryImport === true };
          resolutions.set(canonical(row), row);
          if (resolutions.size > MAX_ROWS) fail("observer-limit-exceeded");
          return resolved;
        });
        const arguments_ = { rootNames: parsed.fileNames, options: parsed.options, host,
          configFileParsingDiagnostics: parsed.errors, projectReferences: parsed.projectReferences };
        const incremental = parsed.options.incremental || parsed.options.composite;
        const compilation = incremental ? ts.createIncrementalProgram(arguments_) : ts.createProgram(arguments_);
        const program = incremental ? compilation.getProgram() : compilation;
        recordDiagnostics("program", ts.getPreEmitDiagnostics(program));
        const emitted = compilation.emit();
        result.emit_skipped = emitted.emitSkipped;
        recordDiagnostics("emit", emitted.diagnostics);
        if (result.no_emit && outputs.size) fail("observer-no-emit-violation");
        // Re-read observed inputs after emission to detect concurrent mutation.
        for (const row of [...inputs.values()]) readBytes(path.join(options.root, row.path));
        if (!result.findings.length && !result.diagnostics.some((row) => row.category === "error")) result.verdict = "passed";
      }
    }
  } catch (error) {
    const code = error instanceof ObserverFailure ? error.code : "observer-execution-failed";
    if (!result.findings.some((row) => row.code === code)) result.findings.push({ code });
    result.verdict = "failed";
  }
  const lexical = (left, right) => left < right ? -1 : left > right ? 1 : 0;
  result.inputs = [...inputs.values()].sort((left, right) => lexical(left.path, right.path));
  result.outputs = [...outputs.values()].sort((left, right) => lexical(left.path, right.path));
  result.resolutions = [...resolutions.values()].sort((left, right) => lexical(canonical(left), canonical(right)));
  result.diagnostics.sort((left, right) => lexical(canonical(left), canonical(right)));
  result.observation_digest = hash(Buffer.from(canonical(result), "utf8"));
  return result;
}

try {
  const options = argumentsFrom(process.argv.slice(2));
  const result = observe(options);
  fs.writeFileSync(options.output, canonical(result) + "\n", { flag: "wx", mode: 0o600 });
  process.stdout.write(JSON.stringify({ schema: "local-typescript-driver-status/v1", verdict: result.verdict }) + "\n");
  process.exitCode = result.verdict === "passed" ? 0 : 1;
} catch (error) {
  process.stdout.write(JSON.stringify({ schema: "local-typescript-driver-status/v1", verdict: "failed",
    code: error instanceof ObserverFailure ? error.code : "observer-startup-failed" }) + "\n");
  process.exitCode = 1;
}
