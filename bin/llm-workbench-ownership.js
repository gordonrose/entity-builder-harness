#!/usr/bin/env node
'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const WORKBENCH_DIR = '.llm-workbench';
const LOCK_PATH = path.join(WORKBENCH_DIR, 'lock.json');
const MANIFEST_PATH = path.join(WORKBENCH_DIR, 'manifest.json');
const TSV_MANIFEST_PATH = path.join(WORKBENCH_DIR, 'install-manifest.tsv');
const BLOCK_START = '<!-- llm-workbench:start -->';
const BLOCK_END = '<!-- llm-workbench:end -->';

function packageRoot() {
  return path.resolve(__dirname, '..');
}

function packageVersion(root = packageRoot()) {
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
  return manifest.version;
}

function normalizeRelativePath(relativePath) {
  return relativePath.split(path.sep).join('/');
}

function sha256Text(text) {
  return crypto.createHash('sha256').update(text).digest('hex');
}

function sha256File(filePath) {
  return sha256Text(fs.readFileSync(filePath));
}

function readJson(filePath, fallback = null) {
  if (!fs.existsSync(filePath)) {
    return fallback;
  }
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJson(filePath, value) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

function managedBlockText() {
  return `
${BLOCK_START}
## llm-workbench

Follow \`.agentic/00.chat/workflows/chat-start.md\` at the start of each chat.
Use \`commitLogs/<session>/README.md\` as the first source of truth for chat
lifecycle, branch, worktree, context-packet references, commits, and metrics.

<!-- deterministic-check: allow reason="prompt routing may be manual or repo-specific; no universal script can decide whether a context router exists" -->
Do not assign the whole chat a durable layer, mode, or workflow. When a prompt
needs layer, mode, workflow, corpus, or rule context, use the current user
request, this repo's assistant instructions, and any repo-provided context
router if one exists.

Default mode after governed chat-start bootstrap is read-only until the user
explicitly grants write permission for task files.
${BLOCK_END}
`;
}

function findManagedBlock(contents) {
  const start = contents.indexOf(BLOCK_START);
  if (start === -1) {
    return null;
  }
  const end = contents.indexOf(BLOCK_END, start);
  if (end === -1) {
    return null;
  }
  const endExclusive = end + BLOCK_END.length;
  return {
    start,
    end: endExclusive,
    text: contents.slice(start, endExclusive),
  };
}

function replaceManagedBlock(contents, replacement) {
  const block = findManagedBlock(contents);
  if (!block) {
    throw new Error('managed llm-workbench block not found');
  }
  return `${contents.slice(0, block.start)}${replacement.trim()}${contents.slice(block.end)}`;
}

function listFiles(root, relativeDir, options = {}) {
  const dir = path.join(root, relativeDir);
  if (!fs.existsSync(dir)) {
    return [];
  }
  const results = [];

  function walk(current) {
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const absolutePath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        walk(absolutePath);
        continue;
      }
      if (!entry.isFile()) {
        continue;
      }
      const relativePath = normalizeRelativePath(path.relative(root, absolutePath));
      if (options.exclude && options.exclude(relativePath)) {
        continue;
      }
      results.push(relativePath);
    }
  }

  walk(dir);
  return results.sort();
}

function installFileList(root = packageRoot()) {
  const selected = [
    'AGENTS.md',
    'CLAUDE.md',
    '.github/copilot-instructions.md',
    '.cursor/rules/llm-workbench.mdc',
    'LLM_WORKBENCH.md',
  ];

  const trees = [
    ...listFiles(root, 'bin'),
    ...listFiles(root, '.agentic/00.chat'),
    ...listFiles(root, '.agentic/shared'),
    ...listFiles(root, 'scripts/00.chat', {
      exclude: (relativePath) => relativePath.startsWith('scripts/00.chat/upstream/'),
    }),
  ];

  const harnessScripts = [
    'scripts/01.harness/run-governed-script.sh',
    'scripts/01.harness/check-deterministic-process-drift.sh',
    'scripts/01.harness/check-governed-script-command-drift.sh',
    'scripts/01.harness/artifact-metadata/check-headers/script.sh',
    'scripts/01.harness/artifact-metadata/check-headers/smoke-test.sh',
  ];

  return [...new Set([...selected, ...trees, ...harnessScripts])]
    .filter((relativePath) => fs.existsSync(path.join(root, relativePath)))
    .sort();
}

function instructionFiles(root = packageRoot()) {
  return [
    'AGENTS.md',
    'CLAUDE.md',
    '.github/copilot-instructions.md',
    '.cursor/rules/llm-workbench.mdc',
    'LLM_WORKBENCH.md',
  ].filter((relativePath) => fs.existsSync(path.join(root, relativePath)));
}

function packageScripts(root = packageRoot()) {
  const manifest = readJson(path.join(root, 'package.json'), {});
  const scripts = manifest.scripts || {};
  return Object.fromEntries(Object.entries(scripts).filter(([name]) => {
    return name === 'chat' || name.startsWith('chat:');
  }));
}

function currentUtc() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
}

function makeLock(root = packageRoot()) {
  return {
    schema_version: 1,
    package: 'llm-wb',
    version: packageVersion(root),
    source: 'npm',
    updated_at_utc: currentUtc(),
  };
}

function emptyManifest(root = packageRoot()) {
  return {
    schema_version: 1,
    package: 'llm-wb',
    version: packageVersion(root),
    managed_files: [],
    managed_blocks: [],
    managed_package_scripts: [],
  };
}

function sortedManifest(manifest) {
  return {
    ...manifest,
    managed_files: [...(manifest.managed_files || [])].sort((a, b) => a.path.localeCompare(b.path)),
    managed_blocks: [...(manifest.managed_blocks || [])].sort((a, b) => a.path.localeCompare(b.path)),
    managed_package_scripts: [...(manifest.managed_package_scripts || [])].sort((a, b) => a.name.localeCompare(b.name)),
  };
}

function buildTargetManifest(root, targetRepo, actions = []) {
  const manifest = emptyManifest(root);
  const instructionSet = new Set(instructionFiles(root));
  const scripts = packageScripts(root);

  for (const action of actions) {
    if (action.kind === 'package-script') {
      continue;
    }
    const relativePath = action.path;
    const sourcePath = path.join(root, relativePath);
    const targetPath = path.join(targetRepo, relativePath);

    if (action.kind === 'managed-file' && fs.existsSync(targetPath)) {
      manifest.managed_files.push({
        path: relativePath,
        sha256: sha256File(targetPath),
      });
    }

    if (action.kind === 'managed-block' && fs.existsSync(targetPath)) {
      const block = findManagedBlock(fs.readFileSync(targetPath, 'utf8'));
      if (block) {
        manifest.managed_blocks.push({
          path: relativePath,
          block: 'llm-workbench',
          sha256: sha256Text(block.text),
        });
      }
    }

    if (action.kind === 'auto') {
      if (!fs.existsSync(targetPath)) {
        continue;
      }
      if (instructionSet.has(relativePath) && !sameFile(sourcePath, targetPath)) {
        const block = findManagedBlock(fs.readFileSync(targetPath, 'utf8'));
        if (block) {
          manifest.managed_blocks.push({
            path: relativePath,
            block: 'llm-workbench',
            sha256: sha256Text(block.text),
          });
        }
      } else {
        manifest.managed_files.push({
          path: relativePath,
          sha256: sha256File(targetPath),
        });
      }
    }
  }

  for (const [name, value] of Object.entries(scripts)) {
    const packagePath = path.join(targetRepo, 'package.json');
    if (!fs.existsSync(packagePath)) {
      continue;
    }
    const targetPackage = readJson(packagePath, {});
    if (targetPackage.scripts && targetPackage.scripts[name] === value) {
      manifest.managed_package_scripts.push({
        name,
        value,
        sha256: sha256Text(value),
      });
    }
  }

  return sortedManifest(manifest);
}

function sameFile(left, right) {
  if (!fs.existsSync(left) || !fs.existsSync(right)) {
    return false;
  }
  return sha256File(left) === sha256File(right);
}

function readInstallActions(fileActionsPath, packageOutputPath) {
  const actions = [];
  const lines = fs.existsSync(fileActionsPath)
    ? fs.readFileSync(fileActionsPath, 'utf8').split(/\r?\n/).filter(Boolean)
    : [];

  for (const line of lines) {
    const [action, , relativePath] = line.split('\t');
    if (!relativePath) {
      continue;
    }
    if (action === 'CREATE' || action === 'CREATE_PACKAGE') {
      actions.push({ kind: 'managed-file', path: relativePath });
    }
    if (action === 'SAME') {
      actions.push({ kind: 'auto', path: relativePath });
    }
    if (action === 'PATCH_BLOCK' || action === 'SAME_BLOCK') {
      actions.push({ kind: 'managed-block', path: relativePath });
    }
  }

  if (fs.existsSync(packageOutputPath)) {
    const packageLines = fs.readFileSync(packageOutputPath, 'utf8').split(/\r?\n/).filter(Boolean);
    for (const line of packageLines) {
      if (line.startsWith('PACKAGE_SAME_SCRIPT ') || line.startsWith('PACKAGE_ADD_SCRIPT ')) {
        actions.push({ kind: 'package-script', name: line.split(' ')[1] });
      }
    }
  }

  return actions;
}

function writeInstallState(root, targetRepo, fileActionsPath, packageOutputPath) {
  const actions = readInstallActions(fileActionsPath, packageOutputPath);
  const manifest = buildTargetManifest(root, targetRepo, actions);
  writeJson(path.join(targetRepo, LOCK_PATH), makeLock(root));
  writeJson(path.join(targetRepo, MANIFEST_PATH), manifest);
  return manifest;
}

function readTargetManifest(targetRepo) {
  return readJson(path.join(targetRepo, MANIFEST_PATH), null);
}

function readTargetLock(targetRepo) {
  return readJson(path.join(targetRepo, LOCK_PATH), null);
}

function appendBlock(contents) {
  return `${contents.replace(/\s*$/, '')}\n${managedBlockText()}`;
}

function planAdopt(root, targetRepo) {
  const actions = [];
  const instructionSet = new Set(instructionFiles(root));
  const targetSeen = new Set();

  for (const relativePath of installFileList(root)) {
    targetSeen.add(relativePath);
    const sourcePath = path.join(root, relativePath);
    const targetPath = path.join(targetRepo, relativePath);

    if (!fs.existsSync(targetPath)) {
      if (instructionSet.has(relativePath)) {
        actions.push({ action: 'CREATE', path: relativePath, kind: 'managed-file' });
      } else {
        actions.push({ action: 'CREATE', path: relativePath, kind: 'managed-file' });
      }
      continue;
    }

    if (sameFile(sourcePath, targetPath)) {
      actions.push({ action: 'ADOPT', path: relativePath, kind: 'managed-file' });
      continue;
    }

    if (instructionSet.has(relativePath)) {
      const block = findManagedBlock(fs.readFileSync(targetPath, 'utf8'));
      if (block) {
        if (sha256Text(block.text) === sha256Text(managedBlockText().trim())) {
          actions.push({ action: 'ADOPT_BLOCK', path: relativePath, kind: 'managed-block' });
        } else {
          actions.push({ action: 'DIFF_BLOCK', path: relativePath, kind: 'managed-block', blocking: true });
        }
      } else {
        actions.push({ action: 'PATCH_BLOCK', path: relativePath, kind: 'managed-block' });
      }
      continue;
    }

    actions.push({ action: 'DIFF', path: relativePath, kind: 'managed-file', blocking: true });
  }

  const sourceScripts = packageScripts(root);
  const targetPackagePath = path.join(targetRepo, 'package.json');
  const targetPackage = fs.existsSync(targetPackagePath) ? readJson(targetPackagePath, {}) : {};
  const targetScripts = targetPackage.scripts || {};
  for (const [name, value] of Object.entries(sourceScripts)) {
    if (targetScripts[name] === undefined) {
      actions.push({ action: 'ADD_PACKAGE_SCRIPT', name, value, kind: 'package-script' });
    } else if (targetScripts[name] === value) {
      actions.push({ action: 'ADOPT_PACKAGE_SCRIPT', name, value, kind: 'package-script' });
    } else {
      actions.push({ action: 'DIFF_PACKAGE_SCRIPT', name, value, actual: targetScripts[name], kind: 'package-script', blocking: true });
    }
  }

  for (const relativePath of listFiles(targetRepo, '.')) {
    if (
      relativePath === 'package.json'
      || relativePath.startsWith('.git/')
      || relativePath.startsWith(`${WORKBENCH_DIR}/`)
      || relativePath.startsWith('commitLogs/')
      || relativePath.startsWith('node_modules/')
    ) {
      continue;
    }
    if (!targetSeen.has(relativePath)) {
      actions.push({ action: 'LOCAL_ONLY', path: relativePath, kind: 'local-only' });
    }
  }

  return actions;
}

function planUpdate(root, targetRepo) {
  const manifest = readTargetManifest(targetRepo);
  if (!manifest) {
    throw new Error(`llm-workbench manifest not found: ${MANIFEST_PATH}`);
  }

  const actions = [];
  for (const entry of manifest.managed_files || []) {
    const sourcePath = path.join(root, entry.path);
    const targetPath = path.join(targetRepo, entry.path);
    if (!fs.existsSync(sourcePath)) {
      actions.push({ action: 'SOURCE_MISSING', path: entry.path, blocking: true });
    } else if (!fs.existsSync(targetPath)) {
      actions.push({ action: 'MISSING', path: entry.path, blocking: true });
    } else if (sha256File(targetPath) !== entry.sha256) {
      actions.push({ action: 'CONFLICT', path: entry.path, blocking: true });
    } else if (sha256File(sourcePath) === entry.sha256) {
      actions.push({ action: 'SAME', path: entry.path });
    } else {
      actions.push({ action: 'UPDATE', path: entry.path });
    }
  }

  for (const entry of manifest.managed_blocks || []) {
    const targetPath = path.join(targetRepo, entry.path);
    if (!fs.existsSync(targetPath)) {
      actions.push({ action: 'MISSING_BLOCK', path: entry.path, blocking: true });
      continue;
    }
    const contents = fs.readFileSync(targetPath, 'utf8');
    const block = findManagedBlock(contents);
    if (!block) {
      actions.push({ action: 'MISSING_BLOCK', path: entry.path, blocking: true });
    } else if (sha256Text(block.text) !== entry.sha256) {
      actions.push({ action: 'CONFLICT_BLOCK', path: entry.path, blocking: true });
    } else if (sha256Text(managedBlockText().trim()) === entry.sha256) {
      actions.push({ action: 'SAME_BLOCK', path: entry.path });
    } else {
      actions.push({ action: 'PATCH_BLOCK', path: entry.path });
    }
  }

  const sourceScripts = packageScripts(root);
  const packagePath = path.join(targetRepo, 'package.json');
  const targetPackage = fs.existsSync(packagePath) ? readJson(packagePath, {}) : {};
  const targetScripts = targetPackage.scripts || {};
  for (const entry of manifest.managed_package_scripts || []) {
    const newValue = sourceScripts[entry.name];
    if (newValue === undefined) {
      actions.push({ action: 'SOURCE_SCRIPT_MISSING', name: entry.name, blocking: true });
    } else if (targetScripts[entry.name] === undefined) {
      actions.push({ action: 'MISSING_PACKAGE_SCRIPT', name: entry.name, blocking: true });
    } else if (targetScripts[entry.name] !== entry.value) {
      actions.push({ action: 'CONFLICT_PACKAGE_SCRIPT', name: entry.name, blocking: true });
    } else if (newValue === entry.value) {
      actions.push({ action: 'SAME_PACKAGE_SCRIPT', name: entry.name });
    } else {
      actions.push({ action: 'UPDATE_PACKAGE_SCRIPT', name: entry.name, value: newValue });
    }
  }

  return actions;
}

function actionBlocksApply(actions) {
  return actions.some((action) => action.blocking);
}

function ensureCleanPlan(actions) {
  if (actionBlocksApply(actions)) {
    throw new Error('plan has conflicts or missing managed material; apply refused');
  }
}

function copyManagedFile(root, targetRepo, relativePath) {
  const sourcePath = path.join(root, relativePath);
  const targetPath = path.join(targetRepo, relativePath);
  fs.mkdirSync(path.dirname(targetPath), { recursive: true });
  fs.copyFileSync(sourcePath, targetPath);
}

function applyAdopt(root, targetRepo, actions) {
  ensureCleanPlan(actions);

  for (const action of actions) {
    if (action.action === 'CREATE') {
      copyManagedFile(root, targetRepo, action.path);
    }
    if (action.action === 'PATCH_BLOCK') {
      const targetPath = path.join(targetRepo, action.path);
      const contents = fs.existsSync(targetPath) ? fs.readFileSync(targetPath, 'utf8') : '';
      fs.mkdirSync(path.dirname(targetPath), { recursive: true });
      fs.writeFileSync(targetPath, appendBlock(contents));
    }
    if (action.action === 'ADD_PACKAGE_SCRIPT') {
      const packagePath = path.join(targetRepo, 'package.json');
      const targetPackage = fs.existsSync(packagePath) ? readJson(packagePath, {}) : {};
      targetPackage.scripts = targetPackage.scripts || {};
      targetPackage.scripts[action.name] = action.value;
      writeJson(packagePath, targetPackage);
    }
  }

  const manifestActions = actions
    .filter((action) => ['CREATE', 'ADOPT', 'PATCH_BLOCK', 'ADOPT_BLOCK'].includes(action.action))
    .map((action) => {
      return {
        kind: action.kind === 'managed-block' ? 'managed-block' : 'managed-file',
        path: action.path,
      };
    });
  const manifest = buildTargetManifest(root, targetRepo, manifestActions);
  writeJson(path.join(targetRepo, LOCK_PATH), makeLock(root));
  writeJson(path.join(targetRepo, MANIFEST_PATH), manifest);
  return manifest;
}

function applyUpdate(root, targetRepo, actions) {
  ensureCleanPlan(actions);

  for (const action of actions) {
    if (action.action === 'UPDATE') {
      copyManagedFile(root, targetRepo, action.path);
    }
    if (action.action === 'PATCH_BLOCK') {
      const targetPath = path.join(targetRepo, action.path);
      const contents = fs.readFileSync(targetPath, 'utf8');
      fs.writeFileSync(targetPath, replaceManagedBlock(contents, managedBlockText()));
    }
    if (action.action === 'UPDATE_PACKAGE_SCRIPT') {
      const packagePath = path.join(targetRepo, 'package.json');
      const targetPackage = readJson(packagePath, {});
      targetPackage.scripts = targetPackage.scripts || {};
      targetPackage.scripts[action.name] = action.value;
      writeJson(packagePath, targetPackage);
    }
  }

  const oldManifest = readTargetManifest(targetRepo);
  const manifestActions = [
    ...(oldManifest.managed_files || []).map((entry) => ({ kind: 'managed-file', path: entry.path })),
    ...(oldManifest.managed_blocks || []).map((entry) => ({ kind: 'managed-block', path: entry.path })),
  ];
  const manifest = buildTargetManifest(root, targetRepo, manifestActions);
  writeJson(path.join(targetRepo, LOCK_PATH), makeLock(root));
  writeJson(path.join(targetRepo, MANIFEST_PATH), manifest);
  return manifest;
}

function printPlan(title, mode, targetRepo, actions) {
  const lock = readTargetLock(targetRepo);
  console.log(`llm-workbench ${title} ${mode}`);
  console.log('');
  if (lock) {
    console.log(`Current version: ${lock.version}`);
  }
  console.log(`Target version: ${packageVersion()}`);
  console.log(`Target repo: ${targetRepo}`);
  console.log('');
  for (const action of actions) {
    if (action.path) {
      console.log(`${action.action} ${action.path}`);
    } else if (action.name) {
      console.log(`${action.action} ${action.name}`);
    }
  }
  console.log('');
  console.log('Summary:');
  const counts = actions.reduce((accumulator, action) => {
    accumulator[action.action] = (accumulator[action.action] || 0) + 1;
    return accumulator;
  }, {});
  for (const [name, count] of Object.entries(counts).sort()) {
    console.log(`${name.toLowerCase()}: ${count}`);
  }
  console.log(`conflicts: ${actions.filter((action) => action.blocking).length}`);
  console.log(`mode: ${mode}`);
}

function parseCommonArgs(args) {
  let target = process.cwd();
  let mode = 'dry-run';
  let sawMode = false;

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    switch (arg) {
      case '--target':
        if (index + 1 >= args.length) {
          throw new Error('--target requires a repo path');
        }
        target = args[index + 1];
        index += 1;
        break;
      case '--dry-run':
        if (sawMode) {
          throw new Error('choose only one mode');
        }
        mode = 'dry-run';
        sawMode = true;
        break;
      case '--apply':
        if (sawMode) {
          throw new Error('choose only one mode');
        }
        mode = 'apply';
        sawMode = true;
        break;
      default:
        throw new Error(`unknown argument: ${arg}`);
    }
  }

  return {
    targetRepo: path.resolve(target),
    mode,
  };
}

function main(argv) {
  const [command, ...args] = argv;
  try {
    if (command === 'write-install-state') {
      const [root, targetRepo, fileActionsPath, packageOutputPath] = args.map((value) => path.resolve(value));
      const manifest = writeInstallState(root, targetRepo, fileActionsPath, packageOutputPath);
      console.log(`Wrote llm-workbench lock: ${LOCK_PATH}`);
      console.log(`Wrote llm-workbench manifest: ${MANIFEST_PATH}`);
      console.log(`managed_files: ${manifest.managed_files.length}`);
      console.log(`managed_blocks: ${manifest.managed_blocks.length}`);
      console.log(`managed_package_scripts: ${manifest.managed_package_scripts.length}`);
      return;
    }

    if (command === 'adopt') {
      const { targetRepo, mode } = parseCommonArgs(args);
      const actions = planAdopt(packageRoot(), targetRepo);
      printPlan('adopt', mode, targetRepo, actions);
      if (mode === 'apply') {
        applyAdopt(packageRoot(), targetRepo, actions);
        console.log('');
        console.log('Adopt apply completed.');
      } else {
        console.log('');
        console.log('No files changed.');
      }
      return;
    }

    if (command === 'update') {
      const { targetRepo, mode } = parseCommonArgs(args);
      const actions = planUpdate(packageRoot(), targetRepo);
      printPlan('update', mode, targetRepo, actions);
      if (mode === 'apply') {
        applyUpdate(packageRoot(), targetRepo, actions);
        console.log('');
        console.log('Update apply completed.');
      } else {
        console.log('');
        console.log('No files changed.');
      }
      return;
    }

    throw new Error(`unknown ownership command: ${command || '<none>'}`);
  } catch (error) {
    console.error(`ERROR: ${error.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main(process.argv.slice(2));
}

module.exports = {
  LOCK_PATH,
  MANIFEST_PATH,
  TSV_MANIFEST_PATH,
  appendBlock,
  buildTargetManifest,
  findManagedBlock,
  installFileList,
  makeLock,
  managedBlockText,
  packageScripts,
  packageVersion,
  planAdopt,
  planUpdate,
  readTargetLock,
  readTargetManifest,
  sha256File,
  sha256Text,
  writeInstallState,
};
