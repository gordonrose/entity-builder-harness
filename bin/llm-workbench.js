#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const PACKAGE_ROOT = path.resolve(__dirname, '..');
const INSTALL_SCRIPT = path.join(PACKAGE_ROOT, 'scripts', 'install.sh');
const OWNERSHIP_SCRIPT = path.join(PACKAGE_ROOT, 'bin', 'llm-workbench-ownership.js');

const INSTALLED_MANIFEST = path.join('.llm-workbench', 'install-manifest.tsv');
const INSTALLED_JSON_MANIFEST = path.join('.llm-workbench', 'manifest.json');
const DISPATCHER_SCRIPT = path.join('scripts', '00.chat', 'command', 'dispatcher', 'script.sh');
const NEW_COMMAND_SCRIPT = path.join('scripts', '00.chat', 'command', 'new', 'script.sh');
const START_NEW_CHAT_SCRIPT = path.join('scripts', '00.chat', 'startup', 'start-new-chat', 'script.sh');
const START_CHAT_SESSION_SCRIPT = path.join('scripts', '00.chat', 'startup', 'start-chat-session', 'script.sh');
const CHECK_WRITE_LOCATION_SCRIPT = path.join('scripts', '00.chat', 'worktree', 'check-write-location', 'script.sh');
const CHECK_COMMIT_PREREQUISITES_SCRIPT = path.join('scripts', '00.chat', 'session-log', 'check-commit-prerequisites', 'script.sh');
const PREPARE_COMMIT_SCRIPT = path.join('scripts', '00.chat', 'session-log', 'prepare-chat-session-before-commit', 'script.sh');
const RECORD_CHAT_COMMIT_SCRIPT = path.join('scripts', '00.chat', 'session-log', 'record-chat-commit', 'script.sh');
const CHECKPOINT_CHAT_SESSION_LOG_SCRIPT = path.join('scripts', '00.chat', 'session-log', 'checkpoint-chat-session-log', 'script.sh');
const VERIFY_MERGE_READY_SCRIPT = path.join('scripts', '00.chat', 'local-merge', 'verify-chat-ready-to-merge-local-main', 'script.sh');
const LIST_ACTIVE_CHAT_BRANCHES_SCRIPT = path.join('scripts', '00.chat', 'local-merge', 'list-active-chat-branches', 'script.sh');

function printHelp(stream = process.stdout) {
  stream.write(`llm-wb

Usage:
  llm-wb <command> [options]

Commands:
  init [--target <repo>] [--dry-run|--apply] [--init-commit]
      Install the workbench harness into a Git repo. Defaults to the current repo.

  adopt [--target <repo>] [--dry-run|--apply]
      Adopt existing workbench files and write ownership state. Defaults to dry-run.

  update [--target <repo>] [--dry-run|--apply]
      Update manifest-owned workbench files. Defaults to dry-run.

  list
      List available installed chat commands from the current Git repo.

  new [--json] "prompt"
      Start a new governed chat session using the installed chat:new flow.

  sessions list [--base <branch>]
      List active chat sessions/branches using the current Git repo.

  commit -m "message" [--summary <text>] [--adr-impact <text>]
      Safely commit current chat work, record it, and checkpoint session evidence.

  merge-main [--base <branch>] [chat-branch]
      Verify and locally merge a completed chat branch into local main.

  help
      Show this help.

Examples:
  llm-wb init --dry-run
  llm-wb init --target /path/to/repo
  llm-wb adopt --dry-run
  llm-wb update --dry-run
  llm-wb new "implement the checkout flow"
  llm-wb sessions list
  llm-wb commit -m "Implement checkout flow"
  llm-wb merge-main
  llm-wb list
`);
}

function printSessionsHelp(stream = process.stdout) {
  stream.write(`llm-wb sessions

Usage:
  llm-wb sessions list [--base <branch>]

Commands:
  list
      List active chat sessions/branches using the existing local-merge report.
`);
}

function fail(message, exitCode = 1, showHelp = false) {
  console.error(`ERROR: ${message}`);
  if (showHelp) {
    console.error('');
    printHelp(process.stderr);
  }
  process.exit(exitCode);
}

function relativeMissing(paths) {
  return paths.map((filePath) => `  ${filePath}`).join('\n');
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || process.cwd(),
    env: options.env || process.env,
    stdio: 'inherit',
  });

  if (result.error) {
    fail(`failed to run ${command}: ${result.error.message}`);
  }

  if (result.signal) {
    fail(`${command} exited after signal ${result.signal}`);
  }

  process.exit(result.status === null ? 1 : result.status);
}

function runChecked(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || process.cwd(),
    env: options.env || process.env,
    stdio: options.stdio || 'inherit',
    encoding: options.encoding,
  });

  if (result.error) {
    fail(`failed to run ${command}: ${result.error.message}`);
  }

  if (result.signal) {
    fail(`${command} exited after signal ${result.signal}`);
  }

  if (result.status !== 0) {
    process.exit(result.status === null ? 1 : result.status);
  }

  return result;
}

function capture(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || process.cwd(),
    env: options.env || process.env,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  if (result.error) {
    fail(`failed to run ${command}: ${result.error.message}`);
  }

  if (result.status !== 0) {
    const detail = (result.stderr || result.stdout || '').trim();
    fail(detail || `${command} exited with status ${result.status}`);
  }

  return result.stdout.trim();
}

function gitRoot(startPath) {
  const result = spawnSync('git', ['-C', startPath, 'rev-parse', '--show-toplevel'], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  if (result.status !== 0) {
    return null;
  }

  return path.resolve(result.stdout.trim());
}

function requireGitRepo(targetPath) {
  const root = gitRoot(targetPath);
  if (!root) {
    fail(`target repo is not a git repo: ${targetPath}`);
  }
  return root;
}

function requirePackageScript(relativePath) {
  const absolutePath = path.join(PACKAGE_ROOT, relativePath);
  if (!fs.existsSync(absolutePath)) {
    fail(`required llm-workbench package script is missing: ${relativePath}`);
  }
  return absolutePath;
}

function requireInstalledWorkbench(repoRoot) {
  if (
    !fs.existsSync(path.join(repoRoot, INSTALLED_MANIFEST))
    && !fs.existsSync(path.join(repoRoot, INSTALLED_JSON_MANIFEST))
  ) {
    fail(`llm-workbench install has not been run in this repo: ${repoRoot}\nRun: llm-wb init`);
  }
}

function requireTargetScripts(repoRoot, relativePaths) {
  const missing = relativePaths.filter((relativePath) => {
    return !fs.existsSync(path.join(repoRoot, relativePath));
  });

  if (missing.length > 0) {
    fail(`required llm-workbench scripts are missing:\n${relativeMissing(missing)}\nRun: llm-wb init --dry-run`);
  }
}

function currentBranch(repoRoot) {
  return capture('git', ['-C', repoRoot, 'branch', '--show-current']);
}

function requireChatBranch(repoRoot) {
  const branch = currentBranch(repoRoot);
  if (!branch.startsWith('chat/')) {
    fail(`current branch is not a chat branch: ${branch || '<detached>'}`);
  }
  return branch;
}

function sessionIdFromBranch(branch) {
  if (!branch.startsWith('chat/')) {
    return null;
  }
  return branch.slice('chat/'.length);
}

function monthName(month) {
  const names = {
    '01': 'jan',
    '02': 'feb',
    '03': 'mar',
    '04': 'apr',
    '05': 'may',
    '06': 'jun',
    '07': 'jul',
    '08': 'aug',
    '09': 'sep',
    '10': 'oct',
    '11': 'nov',
    '12': 'dec',
  };
  return names[month] || null;
}

function metadataValue(contents, key) {
  const block = contents.match(/<!-- agentic-session\n([\s\S]*?)\n-->/);
  if (!block) {
    return '';
  }

  const line = block[1].split('\n').find((candidate) => candidate.startsWith(`${key}: `));
  return line ? line.slice(key.length + 2) : '';
}

function findSessionLog(repoRoot, sessionId, branch) {
  const year = sessionId.slice(0, 4);
  const month = sessionId.slice(5, 7);
  const day = sessionId.slice(8, 10);
  const monthSlug = monthName(month);
  const candidates = [];

  if (year && monthSlug && day) {
    candidates.push(path.join('commitLogs', year, monthSlug, day, sessionId, 'README.md'));
  }
  candidates.push(path.join('commitLogs', sessionId, 'README.md'));

  for (const candidate of candidates) {
    if (fs.existsSync(path.join(repoRoot, candidate))) {
      return candidate;
    }
  }

  if (!year || !monthSlug || !day) {
    fail(`could not derive session log path from branch: ${branch}`);
  }

  const parent = path.join(repoRoot, 'commitLogs', year, monthSlug, day);
  if (fs.existsSync(parent)) {
    for (const entry of fs.readdirSync(parent, { withFileTypes: true })) {
      if (!entry.isDirectory()) {
        continue;
      }

      const relativePath = path.join('commitLogs', year, monthSlug, day, entry.name, 'README.md');
      const absolutePath = path.join(repoRoot, relativePath);
      if (!fs.existsSync(absolutePath)) {
        continue;
      }

      const contents = fs.readFileSync(absolutePath, 'utf8');
      if (metadataValue(contents, 'id') === sessionId || metadataValue(contents, 'branch') === branch) {
        return relativePath;
      }
    }
  }

  fail(`missing chat log for ${branch}`);
}

function primaryWorktree(repoRoot) {
  const output = capture('git', ['-C', repoRoot, 'worktree', 'list', '--porcelain']);
  const first = output.split('\n').find((line) => line.startsWith('worktree '));
  if (!first) {
    fail('could not resolve root integration worktree');
  }
  return path.resolve(first.slice('worktree '.length));
}

function worktreeForBranch(repoRoot, branch) {
  const output = capture('git', ['-C', repoRoot, 'worktree', 'list', '--porcelain']);
  let currentPath = '';

  for (const line of output.split('\n')) {
    if (line.startsWith('worktree ')) {
      currentPath = line.slice('worktree '.length);
    } else if (line === `branch refs/heads/${branch}`) {
      return path.resolve(currentPath);
    }
  }

  return '';
}

function envWithWorktreeRoot(repoRoot) {
  return {
    ...process.env,
    AGENTIC_CHAT_WORKTREE_ROOT: path.dirname(repoRoot),
  };
}

function parseCommitArgs(args) {
  let message = '';
  let summary = '';
  let adrImpact = '';
  let checkpoint = true;
  const positional = [];

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];

    switch (arg) {
      case '-h':
      case '--help':
        printHelp();
        process.exit(0);
        break;
      case '-m':
      case '--message':
        if (index + 1 >= args.length) {
          fail(`${arg} requires a commit message`, 2);
        }
        message = args[index + 1];
        index += 1;
        break;
      case '--summary':
        if (index + 1 >= args.length) {
          fail('--summary requires text', 2);
        }
        summary = args[index + 1];
        index += 1;
        break;
      case '--adr-impact':
        if (index + 1 >= args.length) {
          fail('--adr-impact requires text', 2);
        }
        adrImpact = args[index + 1];
        index += 1;
        break;
      case '--no-checkpoint':
        checkpoint = false;
        break;
      default:
        if (arg.startsWith('-')) {
          fail(`unknown commit option: ${arg}`, 2);
        }
        positional.push(arg);
    }
  }

  if (message && positional.length > 0) {
    fail('commit message was provided twice', 2);
  }

  if (!message) {
    message = positional.join(' ');
  }

  if (!message.trim()) {
    fail('commit requires a message. Use: llm-wb commit -m "message"', 2);
  }

  return {
    message,
    summary: summary || message,
    adrImpact,
    checkpoint,
  };
}

function commandCommit(args) {
  const { message, summary, adrImpact, checkpoint } = parseCommitArgs(args);
  const repoRoot = requireGitRepo(process.cwd());
  requireInstalledWorkbench(repoRoot);
  requireTargetScripts(repoRoot, [
    CHECK_WRITE_LOCATION_SCRIPT,
    CHECK_COMMIT_PREREQUISITES_SCRIPT,
    PREPARE_COMMIT_SCRIPT,
    RECORD_CHAT_COMMIT_SCRIPT,
    CHECKPOINT_CHAT_SESSION_LOG_SCRIPT,
  ]);

  const branch = requireChatBranch(repoRoot);
  const sessionId = sessionIdFromBranch(branch);
  const logFile = findSessionLog(repoRoot, sessionId, branch);
  const commandEnv = envWithWorktreeRoot(repoRoot);

  runChecked('bash', [path.join(repoRoot, CHECK_WRITE_LOCATION_SCRIPT)], { cwd: repoRoot, env: commandEnv });
  runChecked('bash', [path.join(repoRoot, CHECK_COMMIT_PREREQUISITES_SCRIPT)], { cwd: repoRoot, env: commandEnv });

  runChecked('git', ['-C', repoRoot, 'add', '-A'], { cwd: repoRoot, env: commandEnv });
  runChecked('git', ['-C', repoRoot, 'reset', '--', logFile], { cwd: repoRoot, env: commandEnv, stdio: 'ignore' });

  const stagedResult = spawnSync('git', ['-C', repoRoot, 'diff', '--cached', '--quiet'], {
    env: commandEnv,
    stdio: 'ignore',
  });

  if (stagedResult.status === 0) {
    fail(`no task changes to commit after excluding the session log: ${logFile}`);
  }

  runChecked('bash', [path.join(repoRoot, PREPARE_COMMIT_SCRIPT)], { cwd: repoRoot, env: commandEnv });
  runChecked('git', ['-C', repoRoot, 'commit', '-m', message], { cwd: repoRoot, env: commandEnv });

  const commitSha = capture('git', ['-C', repoRoot, 'rev-parse', 'HEAD'], { env: commandEnv });
  const recordArgs = [path.join(repoRoot, RECORD_CHAT_COMMIT_SCRIPT), commitSha, message, summary];
  if (adrImpact) {
    recordArgs.push(adrImpact);
  }
  runChecked('bash', recordArgs, { cwd: repoRoot, env: commandEnv });

  if (checkpoint) {
    runChecked('bash', [
      path.join(repoRoot, CHECKPOINT_CHAT_SESSION_LOG_SCRIPT),
      `chore(session): checkpoint ${commitSha.slice(0, 7)}`,
    ], { cwd: repoRoot, env: commandEnv });
  }

  console.log(`Committed chat task work: ${commitSha}`);
}

function parseMergeMainArgs(args) {
  let base = 'main';
  let branch = '';

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];

    switch (arg) {
      case '-h':
      case '--help':
        printHelp();
        process.exit(0);
        break;
      case '--base':
        if (index + 1 >= args.length) {
          fail('--base requires a branch name', 2);
        }
        base = args[index + 1];
        index += 1;
        break;
      default:
        if (arg.startsWith('-')) {
          fail(`unknown merge-main option: ${arg}`, 2);
        }
        if (branch) {
          fail('merge-main accepts at most one chat branch', 2);
        }
        branch = arg;
    }
  }

  return { base, branch };
}

function parseSessionsListArgs(args) {
  let base = 'main';

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];

    switch (arg) {
      case '-h':
      case '--help':
        printSessionsHelp();
        process.exit(0);
        break;
      case '--base':
        if (index + 1 >= args.length) {
          fail('--base requires a branch name', 2);
        }
        base = args[index + 1];
        index += 1;
        break;
      default:
        if (arg.startsWith('-')) {
          fail(`unknown sessions list option: ${arg}`, 2);
        }
        fail(`unexpected sessions list argument: ${arg}`, 2);
    }
  }

  return { base };
}

function commandSessions(args) {
  const [subcommand, ...subcommandArgs] = args;

  if (!subcommand || subcommand === '-h' || subcommand === '--help' || subcommand === 'help') {
    printSessionsHelp();
    return;
  }

  if (subcommand !== 'list') {
    fail(`unknown sessions command: ${subcommand}`, 2);
  }

  const { base } = parseSessionsListArgs(subcommandArgs);
  const repoRoot = requireGitRepo(process.cwd());
  requireInstalledWorkbench(repoRoot);
  requireTargetScripts(repoRoot, [LIST_ACTIVE_CHAT_BRANCHES_SCRIPT]);

  run('bash', [path.join(repoRoot, LIST_ACTIVE_CHAT_BRANCHES_SCRIPT), base], { cwd: repoRoot });
}

function commandMergeMain(args) {
  const { base, branch: requestedBranch } = parseMergeMainArgs(args);
  const currentRepoRoot = requireGitRepo(process.cwd());
  const current = currentBranch(currentRepoRoot);
  const targetBranch = requestedBranch || (current.startsWith('chat/') ? current : '');

  if (!targetBranch) {
    fail('merge-main needs a chat branch when not run from a chat worktree', 2);
  }

  if (!targetBranch.startsWith('chat/')) {
    fail(`merge-main target is not a chat branch: ${targetBranch}`, 2);
  }

  const rootWorktree = primaryWorktree(currentRepoRoot);
  requireInstalledWorkbench(rootWorktree);
  requireTargetScripts(rootWorktree, [VERIFY_MERGE_READY_SCRIPT]);

  const branchWorktree = worktreeForBranch(rootWorktree, targetBranch);
  const commandEnv = branchWorktree
    ? { ...process.env, AGENTIC_CHAT_WORKTREE_ROOT: path.dirname(branchWorktree) }
    : process.env;

  runChecked('bash', [
    path.join(rootWorktree, VERIFY_MERGE_READY_SCRIPT),
    '--base',
    base,
    targetBranch,
  ], { cwd: rootWorktree, env: commandEnv });

  runChecked('git', ['-C', rootWorktree, 'merge', '--no-ff', '--no-edit', targetBranch], {
    cwd: rootWorktree,
    env: commandEnv,
  });

  console.log(`Merged ${targetBranch} into local ${base}.`);
  console.log('No remote push was performed.');
}

function parseInitArgs(args) {
  let target = process.cwd();
  let mode = '--apply';
  let sawMode = false;
  const installArgs = [];

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];

    switch (arg) {
      case '-h':
      case '--help':
        printHelp();
        process.exit(0);
        break;
      case '--target':
        if (index + 1 >= args.length) {
          fail('--target requires a repo path', 2);
        }
        target = args[index + 1];
        index += 1;
        break;
      case '--dry-run':
      case '--apply':
        if (sawMode) {
          fail('choose only one of --dry-run or --apply', 2);
        }
        mode = arg;
        sawMode = true;
        break;
      case '--init-commit':
        installArgs.push(arg);
        break;
      default:
        if (arg.startsWith('-')) {
          fail(`unknown init option: ${arg}`, 2);
        }
        fail(`unexpected init argument: ${arg}`, 2);
    }
  }

  return { target, mode, installArgs };
}

function commandInit(args) {
  const { target, mode, installArgs } = parseInitArgs(args);
  const repoRoot = requireGitRepo(path.resolve(target));
  const installScript = requirePackageScript(path.relative(PACKAGE_ROOT, INSTALL_SCRIPT));

  // The npm package invokes its own bundled installer, while the installer
  // writes into the caller's Git repository.
  run('bash', [installScript, mode, ...installArgs, repoRoot], { cwd: PACKAGE_ROOT });
}

function parseOwnershipArgs(args) {
  let target = process.cwd();
  let mode = '--dry-run';
  let sawMode = false;

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];

    switch (arg) {
      case '-h':
      case '--help':
        printHelp();
        process.exit(0);
        break;
      case '--target':
        if (index + 1 >= args.length) {
          fail('--target requires a repo path', 2);
        }
        target = args[index + 1];
        index += 1;
        break;
      case '--dry-run':
      case '--apply':
        if (sawMode) {
          fail('choose only one of --dry-run or --apply', 2);
        }
        mode = arg;
        sawMode = true;
        break;
      default:
        if (arg.startsWith('-')) {
          fail(`unknown ownership option: ${arg}`, 2);
        }
        fail(`unexpected ownership argument: ${arg}`, 2);
    }
  }

  return { target, mode };
}

function commandOwnership(command, args) {
  const { target, mode } = parseOwnershipArgs(args);
  const repoRoot = requireGitRepo(path.resolve(target));
  const ownershipScript = requirePackageScript(path.relative(PACKAGE_ROOT, OWNERSHIP_SCRIPT));

  run('node', [ownershipScript, command, mode, '--target', repoRoot], { cwd: PACKAGE_ROOT });
}

function commandList(args) {
  if (args.length > 0) {
    fail('list does not accept arguments', 2);
  }

  const repoRoot = requireGitRepo(process.cwd());
  requireInstalledWorkbench(repoRoot);
  requireTargetScripts(repoRoot, [DISPATCHER_SCRIPT]);

  run('bash', [path.join(repoRoot, DISPATCHER_SCRIPT), 'list'], { cwd: repoRoot });
}

function commandNew(args) {
  const repoRoot = requireGitRepo(process.cwd());
  requireInstalledWorkbench(repoRoot);
  requireTargetScripts(repoRoot, [
    DISPATCHER_SCRIPT,
    NEW_COMMAND_SCRIPT,
    START_NEW_CHAT_SCRIPT,
    START_CHAT_SESSION_SCRIPT,
  ]);

  run('bash', [path.join(repoRoot, DISPATCHER_SCRIPT), 'new', ...args], { cwd: repoRoot });
}

function main(argv) {
  const [command, ...args] = argv;

  if (!command || command === '-h' || command === '--help' || command === 'help') {
    printHelp();
    return;
  }

  switch (command) {
    case 'init':
      commandInit(args);
      break;
    case 'adopt':
      commandOwnership('adopt', args);
      break;
    case 'update':
      commandOwnership('update', args);
      break;
    case 'list':
      commandList(args);
      break;
    case 'new':
      commandNew(args);
      break;
    case 'sessions':
      commandSessions(args);
      break;
    case 'commit':
      commandCommit(args);
      break;
    case 'merge-main':
      commandMergeMain(args);
      break;
    default:
      fail(`unknown command: ${command}`, 2, true);
  }
}

main(process.argv.slice(2));
