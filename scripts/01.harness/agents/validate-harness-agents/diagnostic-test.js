#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: harness.script.agents.validate-harness-agents.diagnostic-test
//   version: 1
//   status: active
//   created_on: "2026-10-31"
//   updated_on: "2026-10-31"
//   layer: 01.harness
//   domain: governance.agents
//   disciplines:
//     - agentic
//   kind: script
//   purpose: Exercise real harness-agent validation with isolated native-failure canaries and valid alternatives.
//   portability:
//     class: required
//     targets:
//       - llm-workbench
//       - entity-builder
//       - design-system-builder
//   effects:
//     - read-only
//     - writes-files
//   used_by:
//     - id: harness.script.agents.validate-harness-agents
//       path: scripts/01.harness/agents/validate-harness-agents/script.sh

const assert = require('assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const repoRoot = path.resolve(__dirname, '../../../..');
const fixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'harness-agent-diagnostics-'));
const wrapper = path.join(__dirname, 'script.sh');
const canary = 'PRIVATE_HARNESS_NATIVE_CANARY';
const rubric = '.agentic/01.harness/agents/rubrics/cfo-token-efficiency.yml';
const singleWorkflow = '.agentic/01.harness/workflows/run-agent-review.md';
const boardWorkflow = '.agentic/01.harness/workflows/run-review-board.md';
const scorecardExample = '.agentic/01.harness/templates/examples/cfo-token-efficiency-scorecard.yml';
const dependencies = [
  '.agentic/01.harness/agents',
  '.agentic/01.harness/templates/agent-review-report.md',
  '.agentic/01.harness/templates/agent-scorecard.yml',
  '.agentic/01.harness/templates/agent-scorecard.schema.yml',
  '.agentic/01.harness/templates/agent-scorecard.example.yml',
  scorecardExample,
  singleWorkflow,
  boardWorkflow,
  '.agentic/01.harness/workflows/implement-backend-architecture-guideline.md',
  '.agentic/01.harness/standards/agent-contracts.md',
  '.agentic/01.harness/manifest.yml',
  '.agentic/01.harness/README.md',
  'scripts/01.harness/agents/validate-harness-agents/README.md',
  'scripts/01.harness/agents/validate-harness-agents/fixtures',
  'scripts/01.harness/metrics/compare-task-token-consumption/script.sh',
  'scripts/01.harness/metrics/compare-task-token-consumption/script.js',
];
let cases = 0;

function fixturePath(relative) { return path.join(fixtureRoot, relative); }

function run(label, args = [], expected = undefined, injection = undefined) {
  const result = spawnSync('bash', [wrapper, ...args], {
    cwd: fixtureRoot,
    encoding: 'utf8',
    timeout: 30000,
    env: {
      ...process.env,
      PATH: `${fixturePath('bin')}${path.delimiter}${process.env.PATH || ''}`,
      NODE_OPTIONS: injection ? `--require=${fixturePath('inject-native-failure.cjs')}` : '',
      HARNESS_DIAGNOSTIC_INJECTION: injection || '',
      HARNESS_DIAGNOSTIC_FIXTURE_ROOT: fixtureRoot,
    },
  });
  const output = `${result.stdout || ''}${result.stderr || ''}`;
  assert.equal(result.error, undefined, `${label}: command must finish`);
  assert.equal(result.signal, null, `${label}: command must not be signaled`);
  assert.equal(result.status, expected ? 1 : 0, `${label}: original pass/reject disposition`);
  assert.equal(output.includes(canary), false, `${label}: rejected content and native details must not escape`);
  assert.equal(/\bat (?:Object\.|parseJson|validate|Module\.)|SyntaxError:|TypeError:|Error: PRIVATE/.test(output), false,
    `${label}: no native stack or exception text`);
  if (expected) assert.ok(output.includes(expected), `${label}: exact owned finding`);
  else assert.ok(output.includes('Harness review agents valid.'), `${label}: full command completed`);
  if (injection === 'comparison-discovery' || injection === 'comparison-read') {
    assert.equal(output, `ERROR: ${expected}\n`, `${label}: only the fixed comparison concern escapes`);
  }
  cases += 1;
}

function withContent(relative, content, action) {
  const target = fixturePath(relative);
  const original = fs.readFileSync(target, 'utf8');
  fs.writeFileSync(target, content);
  try { action(); } finally { fs.writeFileSync(target, original); }
}

function mutateWorkflow(relative, marker, update, action) {
  const original = fs.readFileSync(fixturePath(relative), 'utf8');
  const pattern = new RegExp(`(<!-- ${marker}:start -->\\s*\x60\x60\x60json\\s*)([\\s\\S]*?)(\\s*\x60\x60\x60\\s*<!-- ${marker}:end -->)`);
  assert.ok(pattern.test(original), 'fixture must locate the actual workflow JSON block');
  withContent(relative, original.replace(pattern, (_match, start, body, end) => `${start}${update(body)}${end}`), action);
}

try {
  for (const relative of dependencies) {
    fs.mkdirSync(path.dirname(fixturePath(relative)), { recursive: true });
    fs.cpSync(path.join(repoRoot, relative), fixturePath(relative), { recursive: true });
  }
  fs.mkdirSync(fixturePath('bin'));
  // Only the wrapper's read-only root lookup is replaced; no repository is initialized or changed.
  fs.writeFileSync(fixturePath('bin/git'), '#!/usr/bin/env bash\n[[ "$*" == "rev-parse --show-toplevel" ]] || exit 90\nprintf "%s\\n" "$HARNESS_DIAGNOSTIC_FIXTURE_ROOT"\n', { mode: 0o755 });
  // Native I/O failures are injected at the real command's actual fs calls, without changing its predicates.
  fs.writeFileSync(fixturePath('inject-native-failure.cjs'), `
const fs = require('fs');
const path = require('path');
const root = process.env.HARNESS_DIAGNOSTIC_FIXTURE_ROOT;
const injection = process.env.HARNESS_DIAGNOSTIC_INJECTION;
const index = process.argv.indexOf('--cfo-output');
const cfoPath = index < 0 ? undefined : process.argv[index + 1];
const comparisonIndex = process.argv.indexOf('--commit-log-root');
const comparisonRoot = comparisonIndex < 0 ? undefined : process.argv[comparisonIndex + 1];
const originalRead = fs.readFileSync;
fs.readFileSync = function(file, ...args) {
  if (String(file) === cfoPath) {
    if (injection === 'cfo-read') throw new Error('${canary}');
    if (injection === 'cfo-json') return '{"value":"${canary}",}';
    if (injection === 'cfo-shape') return '{}';
    if (injection === 'cfo-value') {
      const result = JSON.parse(Reflect.apply(originalRead, this, [file, ...args]));
      result.schema = '${canary}';
      return JSON.stringify(result);
    }
  }
  if (injection === 'input-read' && String(file) === path.join(root, '${rubric}')) throw new Error('${canary}');
  if (injection === 'comparison-read' && comparisonRoot && String(file).startsWith(comparisonRoot + path.sep)
      && path.basename(String(file)) === 'README.md') throw new Error('${canary}');
  return Reflect.apply(originalRead, this, [file, ...args]);
};
for (const [method, mode] of [['statSync', 'directory-stat'], ['readdirSync', 'directory-read']]) {
  const original = fs[method];
  fs[method] = function(file, ...args) {
    if (injection === mode && String(file) === path.join(root, 'scorecards')) throw new Error('${canary}');
    if (method === 'readdirSync' && injection === 'comparison-discovery' && String(file) === comparisonRoot) throw new Error('${canary}');
    return Reflect.apply(original, this, [file, ...args]);
  };
}
`);

  run('existing complete internal fixtures');
  run('valid live scorecard', ['--scorecard', scorecardExample]);
  fs.mkdirSync(fixturePath('scorecards'));
  fs.copyFileSync(fixturePath(scorecardExample), fixturePath('scorecards/example.yml'));
  run('valid scorecard directory', ['--scorecard-dir', 'scorecards']);

  withContent(rubric, `# retained JSON-compatible YAML grammar\n{"value":"${canary}",}`, () => {
    run('rubric JSON parse', [], `${rubric} is not parseable JSON-compatible YAML [HARNESS_AGENT_JSON_PARSE_FAILED]`);
  });
  for (const [relative, marker] of [
    [singleWorkflow, 'review-agent-routing'],
    [boardWorkflow, 'review-board-routing'],
    [boardWorkflow, 'review-board-composition'],
  ]) {
    mutateWorkflow(relative, marker, () => `{"value":"${canary}",}`, () => {
      run(`${marker} JSON parse`, [], `${relative} ${marker} JSON block is invalid [HARNESS_AGENT_WORKFLOW_JSON_PARSE_FAILED]`);
    });
  }
  mutateWorkflow(singleWorkflow, 'review-agent-routing', (body) => {
    const data = JSON.parse(body);
    data.routes[0].match_patterns[0] = `${canary}(`;
    return JSON.stringify(data, null, 2);
  }, () => run('route regex compile and later matching', [], 'match_patterns[0] is invalid regex [HARNESS_AGENT_REGEX_COMPILE_FAILED]'));
  mutateWorkflow(boardWorkflow, 'review-board-composition', (body) => {
    const data = JSON.parse(body);
    data.rules[0].when_any[0] = `${canary}(`;
    return JSON.stringify(data, null, 2);
  }, () => run('composition regex compile and later matching', [], 'when_any[0] is invalid regex [HARNESS_AGENT_REGEX_COMPILE_FAILED]'));

  for (const [relative, marker, field, property] of [
    [singleWorkflow, 'review-agent-routing', 'routes', 'match_patterns'],
    [boardWorkflow, 'review-board-composition', 'rules', 'when_any'],
  ]) {
    mutateWorkflow(relative, marker, (body) => {
      const data = JSON.parse(body);
      for (const entry of data[field]) entry[property] = entry[property].map((pattern) => `(?:${pattern})`);
      return JSON.stringify(data, null, 2);
    }, () => run(`${marker} equivalent native regex alternatives`));
  }

  const malformedScorecard = `${canary}.json`;
  fs.writeFileSync(fixturePath(malformedScorecard), `{"value":"${canary}",}`);
  run('CLI JSON parse and path privacy', ['--scorecard', malformedScorecard], 'CLI scorecard input is not parseable JSON-compatible YAML [HARNESS_AGENT_JSON_PARSE_FAILED]');
  run('CLI input read', ['--scorecard', 'scorecards'], 'CLI scorecard input could not be read [HARNESS_AGENT_INPUT_READ_FAILED]');
  run('CLI missing input', ['--scorecard', `missing-${canary}`], 'missing file: CLI scorecard input');
  run('CLI missing directory', ['--scorecard-dir', `missing-${canary}`], 'missing CLI scorecard directory');
  run('CLI unknown argument', [`--${canary}`], 'unknown argument [HARNESS_AGENT_ARGUMENT_UNRECOGNIZED]');
  run('owned static input read', [], `${rubric} could not be read [HARNESS_AGENT_INPUT_READ_FAILED]`, 'input-read');
  run('CLI directory inspection', ['--scorecard-dir', 'scorecards'], 'CLI scorecard directory could not be inspected [HARNESS_AGENT_DIRECTORY_INSPECTION_FAILED]', 'directory-stat');
  run('CLI directory traversal', ['--scorecard-dir', 'scorecards'], 'CLI scorecard directory could not be read [HARNESS_AGENT_DIRECTORY_READ_FAILED]', 'directory-read');
  run('CFO input read', [], 'CFO fixture output could not be read [HARNESS_AGENT_CFO_READ_FAILED]', 'cfo-read');
  run('CFO JSON parse', [], 'CFO fixture output is not parseable JSON [HARNESS_AGENT_CFO_JSON_PARSE_FAILED]', 'cfo-json');
  run('CFO parsed shape', [], 'CFO fixture comparison could not be checked [HARNESS_AGENT_CFO_VALIDATION_FAILED]', 'cfo-shape');
  run('CFO rejected value', [], 'CFO fixture expected schema v3.1 [HARNESS_AGENT_CFO_VALUE_MISMATCH]', 'cfo-value');
  run('comparison session discovery', [], 'Comparison session discovery failed [HARNESS_METRIC_DISCOVERY_FAILED]', 'comparison-discovery');
  run('comparison session input read', [], 'Comparison session input could not be read [HARNESS_METRIC_INPUT_READ_FAILED]', 'comparison-read');
  run('restored complete internal fixtures');
  console.log(`Harness review-agent diagnostic regressions valid (${cases} cases).`);
} finally {
  fs.rmSync(fixtureRoot, { recursive: true, force: true });
}
