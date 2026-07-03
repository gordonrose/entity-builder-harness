#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: chat.script.export.create-worktree-bundle
//   version: 1
//   status: active
//   layer: 00.chat
//   domain: export
//   disciplines:
//     - agentic
//   kind: script
//   purpose: Create portable review bundles from chat-owned worktrees.
//   portability:
//     class: required
//     targets:
//       - llm-workbench
//   used_by:
//     - id: chat.script.export.worktree
//       path: scripts/00.chat/export/worktree/script.sh
//     - id: chat.script.export.worktree-diff
//       path: scripts/00.chat/export/worktree-diff/script.sh
//     - id: chat.script.export.smoke-test
//       path: scripts/00.chat/export/smoke-test.sh
//   effects:
//     - writes-files

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const MONTHS = new Map([
  ['01', 'jan'],
  ['02', 'feb'],
  ['03', 'mar'],
  ['04', 'apr'],
  ['05', 'may'],
  ['06', 'jun'],
  ['07', 'jul'],
  ['08', 'aug'],
  ['09', 'sep'],
  ['10', 'oct'],
  ['11', 'nov'],
  ['12', 'dec'],
]);

function usage(exitCode = 0) {
  const stream = exitCode === 0 ? process.stdout : process.stderr;
  stream.write(`Usage:
  create-worktree-bundle.js --mode worktree [--output <zip>|--output-dir <dir>] [worktree-path|session-log]
  create-worktree-bundle.js --mode worktree-diff [--base <ref>] [--output <zip>|--output-dir <dir>] [worktree-path|session-log]

Creates a portable review bundle from a chat worktree.
`);
  process.exit(exitCode);
}

function fail(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

function runGit(cwd, args, options = {}) {
  const result = spawnSync('git', ['-C', cwd, ...args], {
    encoding: options.buffer ? undefined : 'utf8',
    stdout: 'pipe',
    stderr: 'pipe',
  });
  if (result.status !== 0) {
    const stderr = Buffer.isBuffer(result.stderr)
      ? result.stderr.toString('utf8')
      : result.stderr;
    fail(`git ${args.join(' ')} failed in ${cwd}: ${stderr.trim()}`);
  }
  return result.stdout;
}

function gitText(cwd, args) {
  return String(runGit(cwd, args)).trim();
}

function gitBuffer(cwd, args) {
  return runGit(cwd, args, { buffer: true });
}

function parseArgs(argv) {
  const parsed = {
    mode: '',
    base: 'main',
    output: '',
    outputDir: '',
    target: '',
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    switch (arg) {
      case '--mode':
        parsed.mode = argv[index + 1] || '';
        index += 1;
        break;
      case '--base':
        parsed.base = argv[index + 1] || '';
        index += 1;
        break;
      case '--output':
        parsed.output = argv[index + 1] || '';
        index += 1;
        break;
      case '--output-dir':
        parsed.outputDir = argv[index + 1] || '';
        index += 1;
        break;
      case '-h':
      case '--help':
        usage(0);
        break;
      default:
        if (arg.startsWith('-')) {
          console.error(`ERROR: unknown argument: ${arg}`);
          usage(2);
        }
        if (parsed.target) {
          console.error('ERROR: target specified more than once.');
          usage(2);
        }
        parsed.target = arg;
        break;
    }
  }

  if (!['worktree', 'worktree-diff'].includes(parsed.mode)) {
    console.error('ERROR: --mode must be worktree or worktree-diff.');
    usage(2);
  }
  if (parsed.output && parsed.outputDir) {
    console.error('ERROR: choose only one of --output or --output-dir.');
    usage(2);
  }
  if (parsed.mode === 'worktree-diff' && !parsed.base) {
    console.error('ERROR: --base requires a value.');
    usage(2);
  }

  return parsed;
}

function findRepoRoot(start) {
  const result = spawnSync('git', ['-C', start, 'rev-parse', '--show-toplevel'], {
    encoding: 'utf8',
    stdout: 'pipe',
    stderr: 'pipe',
  });
  if (result.status !== 0) {
    fail(`not inside a Git worktree: ${start}`);
  }
  return result.stdout.trim();
}

function sessionIdFromBranch(branch) {
  return branch.startsWith('chat/') ? branch.slice('chat/'.length) : '';
}

function monthName(month) {
  return MONTHS.get(month) || '';
}

function metadataValue(logFile, key) {
  if (!fs.existsSync(logFile)) {
    return '';
  }
  const text = fs.readFileSync(logFile, 'utf8');
  const match = text.match(/<!-- agentic-session([\s\S]*?)-->/);
  if (!match) {
    return '';
  }
  const line = match[1]
    .split(/\r?\n/)
    .find((candidate) => candidate.startsWith(`${key}: `));
  return line ? line.slice(key.length + 2).trim() : '';
}

function groupedLogPath(repoRoot, sessionId) {
  const year = sessionId.slice(0, 4);
  const month = sessionId.slice(5, 7);
  const day = sessionId.slice(8, 10);
  const monthSlug = monthName(month);
  if (!year || !monthSlug || !day) {
    return '';
  }
  return path.join(repoRoot, 'commitLogs', year, monthSlug, day, sessionId, 'README.md');
}

function flatLogPath(repoRoot, sessionId) {
  return path.join(repoRoot, 'commitLogs', sessionId, 'README.md');
}

function findSessionLog(repoRoot, sessionId) {
  const grouped = groupedLogPath(repoRoot, sessionId);
  if (grouped && fs.existsSync(grouped)) {
    return grouped;
  }

  const flat = flatLogPath(repoRoot, sessionId);
  if (fs.existsSync(flat)) {
    return flat;
  }

  const groupedParent = grouped ? path.dirname(path.dirname(grouped)) : '';
  if (groupedParent && fs.existsSync(groupedParent)) {
    const branch = `chat/${sessionId}`;
    const candidates = [];
    for (const entry of fs.readdirSync(groupedParent, { withFileTypes: true })) {
      if (!entry.isDirectory()) {
        continue;
      }
      const readme = path.join(groupedParent, entry.name, 'README.md');
      if (
        fs.existsSync(readme) &&
        (metadataValue(readme, 'id') === sessionId ||
          metadataValue(readme, 'branch') === branch)
      ) {
        candidates.push(readme);
      }
    }
    if (candidates.length === 1) {
      return candidates[0];
    }
  }

  return grouped || flat;
}

function resolveTarget(target) {
  if (target) {
    const candidate = path.resolve(target);
    if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
      const worktree = metadataValue(candidate, 'worktree');
      if (!worktree) {
        fail(`session log is missing worktree metadata: ${candidate}`);
      }
      return {
        worktree: path.resolve(worktree),
        sessionLog: candidate,
      };
    }
    return {
      worktree: candidate,
      sessionLog: '',
    };
  }

  const currentRoot = findRepoRoot(process.cwd());
  const branch = gitText(currentRoot, ['branch', '--show-current']);
  const sessionId = sessionIdFromBranch(branch);
  if (!sessionId) {
    fail(`current branch is not a chat branch: ${branch}. Pass a chat worktree path or session log path.`);
  }

  const logFile = findSessionLog(currentRoot, sessionId);
  if (!fs.existsSync(logFile)) {
    fail(`missing chat log: ${path.relative(currentRoot, logFile)}`);
  }

  const worktree = metadataValue(logFile, 'worktree');
  if (!worktree) {
    fail(`session log is missing worktree metadata: ${path.relative(currentRoot, logFile)}`);
  }

  return {
    worktree: path.resolve(worktree),
    sessionLog: logFile,
  };
}

function splitNul(buffer) {
  return buffer
    .toString('utf8')
    .split('\0')
    .filter((value) => value.length > 0);
}

function parseNameStatus(buffer) {
  const parts = splitNul(buffer);
  const entries = [];
  for (let index = 0; index < parts.length;) {
    const status = parts[index];
    index += 1;
    if (!status) {
      continue;
    }
    if (status.startsWith('R') || status.startsWith('C')) {
      const oldPath = parts[index] || '';
      const newPath = parts[index + 1] || '';
      index += 2;
      entries.push({ status, path: newPath, old_path: oldPath });
    } else {
      const filePath = parts[index] || '';
      index += 1;
      entries.push({ status, path: filePath });
    }
  }
  return entries;
}

function normalizeRelativePath(relativePath) {
  const normalized = relativePath.replace(/\\/g, '/');
  if (
    !normalized ||
    normalized.startsWith('/') ||
    normalized.includes('\0') ||
    normalized === '.git' ||
    normalized.startsWith('.git/')
  ) {
    return '';
  }
  const compact = path.posix.normalize(normalized);
  if (compact === '.' || compact.startsWith('../') || compact === '..') {
    return '';
  }
  return compact;
}

function collectFullFiles(repoRoot) {
  const tracked = splitNul(gitBuffer(repoRoot, ['ls-files', '-z']));
  const untracked = splitNul(gitBuffer(repoRoot, ['ls-files', '--others', '--exclude-standard', '-z']));
  const untrackedSet = new Set(untracked.map(normalizeRelativePath).filter(Boolean));
  const files = new Set();

  for (const filePath of [...tracked, ...untracked]) {
    const normalized = normalizeRelativePath(filePath);
    if (normalized) {
      files.add(normalized);
    }
  }

  return {
    files: [...files].sort(),
    statusEntries: [],
    deletedFiles: [],
    untrackedFiles: [...untrackedSet].sort(),
  };
}

function collectDiffFiles(repoRoot, baseRef) {
  gitText(repoRoot, ['rev-parse', '--verify', `${baseRef}^{commit}`]);

  const diffEntries = parseNameStatus(gitBuffer(repoRoot, ['diff', '--name-status', '-z', baseRef, '--']));
  const untracked = splitNul(gitBuffer(repoRoot, ['ls-files', '--others', '--exclude-standard', '-z']))
    .map(normalizeRelativePath)
    .filter(Boolean);

  const files = new Set();
  const deletedFiles = new Set();
  const statusEntries = [];
  const renamedFiles = [];

  for (const entry of diffEntries) {
    const normalized = normalizeRelativePath(entry.path);
    const oldPath = entry.old_path ? normalizeRelativePath(entry.old_path) : '';
    if (!normalized) {
      continue;
    }
    const record = {
      status: entry.status,
      path: normalized,
    };
    if (oldPath) {
      record.old_path = oldPath;
      renamedFiles.push({ old_path: oldPath, path: normalized, status: entry.status });
    }
    statusEntries.push(record);
    if (entry.status.startsWith('D')) {
      deletedFiles.add(normalized);
    } else {
      files.add(normalized);
    }
  }

  for (const filePath of untracked) {
    files.add(filePath);
    statusEntries.push({ status: '??', path: filePath });
  }

  return {
    files: [...files].sort(),
    statusEntries: statusEntries.sort((left, right) => left.path.localeCompare(right.path)),
    deletedFiles: [...deletedFiles].sort(),
    untrackedFiles: [...new Set(untracked)].sort(),
    renamedFiles,
  };
}

function safeName(value) {
  return value.replace(/[^A-Za-z0-9._-]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '') || 'worktree';
}

function isInside(parent, child) {
  const relative = path.relative(parent, child);
  return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative));
}

function defaultOutputPath(repoRoot, branch, mode, outputDir) {
  const repoSlug = safeName(path.basename(repoRoot));
  const branchSlug = safeName(branch || 'detached');
  const kind = mode === 'worktree-diff' ? 'worktree-diff' : 'worktree';
  const timestamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
  const directory = path.resolve(
    outputDir ||
      process.env.CHAT_EXPORT_OUTPUT_DIR ||
      path.join(os.tmpdir(), 'llm-workbench-exports'),
  );
  return path.join(directory, `${repoSlug}-${branchSlug}-${kind}-${timestamp}.zip`);
}

function crc32(buffer) {
  const table = crc32.table || (crc32.table = buildCrc32Table());
  let crc = 0xffffffff;
  for (const byte of buffer) {
    crc = (crc >>> 8) ^ table[(crc ^ byte) & 0xff];
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function buildCrc32Table() {
  const table = new Uint32Array(256);
  for (let index = 0; index < 256; index += 1) {
    let value = index;
    for (let bit = 0; bit < 8; bit += 1) {
      value = value & 1 ? 0xedb88320 ^ (value >>> 1) : value >>> 1;
    }
    table[index] = value >>> 0;
  }
  return table;
}

function dosDateTime(date) {
  const year = Math.max(date.getFullYear(), 1980);
  const dosTime =
    (date.getHours() << 11) |
    (date.getMinutes() << 5) |
    Math.floor(date.getSeconds() / 2);
  const dosDate =
    ((year - 1980) << 9) |
    ((date.getMonth() + 1) << 5) |
    date.getDate();
  return { dosDate, dosTime };
}

function uint16(value) {
  const buffer = Buffer.alloc(2);
  buffer.writeUInt16LE(value);
  return buffer;
}

function uint32(value) {
  const buffer = Buffer.alloc(4);
  buffer.writeUInt32LE(value >>> 0);
  return buffer;
}

function createZip(entries, outputPath) {
  const fileParts = [];
  const centralParts = [];
  let offset = 0;
  const now = new Date();
  const { dosDate, dosTime } = dosDateTime(now);

  for (const entry of entries) {
    const nameBuffer = Buffer.from(entry.name, 'utf8');
    const data = entry.data;
    const crc = crc32(data);
    const mode = entry.mode || 0o100644;
    if (data.length > 0xffffffff || offset > 0xffffffff) {
      fail('zip64 is not supported for chat worktree exports.');
    }

    const localHeader = Buffer.concat([
      uint32(0x04034b50),
      uint16(20),
      uint16(0x0800),
      uint16(0),
      uint16(dosTime),
      uint16(dosDate),
      uint32(crc),
      uint32(data.length),
      uint32(data.length),
      uint16(nameBuffer.length),
      uint16(0),
      nameBuffer,
    ]);
    fileParts.push(localHeader, data);

    const centralHeader = Buffer.concat([
      uint32(0x02014b50),
      uint16(0x031e),
      uint16(20),
      uint16(0x0800),
      uint16(0),
      uint16(dosTime),
      uint16(dosDate),
      uint32(crc),
      uint32(data.length),
      uint32(data.length),
      uint16(nameBuffer.length),
      uint16(0),
      uint16(0),
      uint16(0),
      uint16(0),
      uint32((mode & 0xffff) << 16),
      uint32(offset),
      nameBuffer,
    ]);
    centralParts.push(centralHeader);
    offset += localHeader.length + data.length;
  }

  const centralDirectory = Buffer.concat(centralParts);
  const endRecord = Buffer.concat([
    uint32(0x06054b50),
    uint16(0),
    uint16(0),
    uint16(entries.length),
    uint16(entries.length),
    uint32(centralDirectory.length),
    uint32(offset),
    uint16(0),
  ]);

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, Buffer.concat([...fileParts, centralDirectory, endRecord]));
}

function fileEntry(repoRoot, relativePath, zipName) {
  const absolute = path.join(repoRoot, relativePath);
  if (!isInside(repoRoot, absolute) || !fs.existsSync(absolute)) {
    return null;
  }
  const stats = fs.lstatSync(absolute);
  if (stats.isSymbolicLink()) {
    return {
      name: zipName,
      data: Buffer.from(fs.readlinkSync(absolute), 'utf8'),
      mode: 0o120777,
    };
  }
  if (!stats.isFile()) {
    return null;
  }
  const permissions = stats.mode & 0o777;
  return {
    name: zipName,
    data: fs.readFileSync(absolute),
    mode: 0o100000 | permissions,
  };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const target = resolveTarget(args.target);
  if (!fs.existsSync(target.worktree) || !fs.statSync(target.worktree).isDirectory()) {
    fail(`chat worktree path does not exist: ${target.worktree}`);
  }

  const repoRoot = findRepoRoot(target.worktree);
  const branch = gitText(repoRoot, ['branch', '--show-current']) || 'detached';
  const headSha = gitText(repoRoot, ['rev-parse', '--verify', 'HEAD']);
  const sessionId = sessionIdFromBranch(branch);
  const sessionLog = target.sessionLog ||
    (sessionId ? findSessionLog(repoRoot, sessionId) : '');
  const sessionLogRelative = sessionLog && fs.existsSync(sessionLog) && isInside(repoRoot, sessionLog)
    ? path.relative(repoRoot, sessionLog).replace(/\\/g, '/')
    : '';
  const outputPath = path.resolve(args.output || defaultOutputPath(repoRoot, branch, args.mode, args.outputDir));
  const outputRelative = isInside(repoRoot, outputPath)
    ? normalizeRelativePath(path.relative(repoRoot, outputPath))
    : '';
  const baseSha = args.mode === 'worktree-diff'
    ? gitText(repoRoot, ['rev-parse', '--verify', `${args.base}^{commit}`])
    : '';

  const collection = args.mode === 'worktree-diff'
    ? collectDiffFiles(repoRoot, args.base)
    : collectFullFiles(repoRoot);
  const files = collection.files.filter((filePath) => filePath && filePath !== outputRelative);
  const prefix = `${safeName(path.basename(repoRoot))}-${safeName(branch)}-${args.mode === 'worktree-diff' ? 'worktree-diff-export' : 'worktree-export'}`;
  const createdAt = new Date().toISOString();

  const manifest = {
    schema: 'llm-workbench/worktree-export/v1',
    kind: args.mode,
    created_at_utc: createdAt,
    repo_name: path.basename(repoRoot),
    branch,
    head_sha: headSha,
    base_ref: args.mode === 'worktree-diff' ? args.base : '',
    base_sha: baseSha,
    session_id: sessionId,
    session_log: sessionLogRelative,
    bundle_prefix: prefix,
    transport: 'zip',
    included_files: files,
    deleted_files: collection.deletedFiles || [],
    renamed_files: collection.renamedFiles || [],
    untracked_files: collection.untrackedFiles || [],
    status_entries: collection.statusEntries || [],
    exclusions: [
      '.git directory',
      'Git ignored files',
      'Files outside the selected worktree',
    ],
  };

  const entries = [
    {
      name: `${prefix}/llm-workbench-export-manifest.json`,
      data: Buffer.from(`${JSON.stringify(manifest, null, 2)}\n`, 'utf8'),
      mode: 0o100644,
    },
  ];

  for (const relativePath of files) {
    const entry = fileEntry(repoRoot, relativePath, `${prefix}/${relativePath}`);
    if (entry) {
      entries.push(entry);
    }
  }

  createZip(entries, outputPath);

  console.log(`Export kind: ${args.mode}`);
  console.log(`Branch: ${branch}`);
  if (args.mode === 'worktree-diff') {
    console.log(`Base ref: ${args.base}`);
  }
  console.log(`Files: ${files.length}`);
  console.log(`Output: ${outputPath}`);
}

main();

