#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: harness.script.agents.validate-harness-agents.impl
//   version: 1
//   status: active
//   layer: 01.harness
//   domain: governance.agents
//   disciplines:
//     - agentic
//   kind: script
//   purpose: Implement harness review-agent validation checks.
//   portability:
//     class: required
//     targets:
//       - llm-workbench
//       - entity-builder
//       - design-system-builder
//   effects:
//     - read-only
//   used_by:
//     - id: harness.script.agents.validate-harness-agents
//       path: scripts/01.harness/agents/validate-harness-agents/script.sh

const fs = require('fs');
const path = require('path');

const repoRoot = process.cwd();
const agentDir = path.join(repoRoot, '.agentic/01.harness/agents');
const workflowDir = path.join(repoRoot, '.agentic/01.harness/workflows');
const templateDir = path.join(repoRoot, '.agentic/01.harness/templates');
const scriptDir = path.join(repoRoot, 'scripts/01.harness/agents/validate-harness-agents');

const agents = [
  ['cfo-token-efficiency.md', 'CFO Token Efficiency', 'harness.agents.cfo-token-efficiency'],
  ['senior-prompt-engineer.md', 'Senior Prompt Engineer', 'harness.agents.senior-prompt-engineer'],
  ['senior-backend-architect.md', 'Senior Back-End Architect', 'harness.agents.senior-backend-architect'],
  ['senior-sre-engineer.md', 'Senior SRE Engineer', 'harness.agents.senior-sre-engineer'],
  ['secops-engineer.md', 'SecOps Engineer', 'harness.agents.secops-engineer'],
  ['ux-ui-engineer.md', 'UX/UI Engineer', 'harness.agents.ux-ui-engineer'],
];

const requiredSections = [
  'Responsibility',
  'Use When',
  'Inputs',
  'Required First Move',
  'Allowed Actions',
  'Disallowed Actions',
  'Evidence Sources',
  'Review Rubric',
  'Scoring',
  'Required Output',
  'Delegation And Escalation',
  'Stop Conditions',
];

const failures = [];
const cfoOutputPath = parseArgs(process.argv.slice(2)).cfoOutputPath;

function parseArgs(argv) {
  const options = { cfoOutputPath: '' };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--cfo-output') {
      index += 1;
      options.cfoOutputPath = argv[index] || '';
    } else if (arg === '--help' || arg === '-h') {
      console.log('Usage: script.sh');
      process.exit(0);
    } else {
      failures.push(`unknown argument: ${arg}`);
    }
  }
  return options;
}

function read(relativePath) {
  const fullPath = path.join(repoRoot, relativePath);
  if (!fs.existsSync(fullPath)) {
    failures.push(`missing file: ${relativePath}`);
    return '';
  }
  return fs.readFileSync(fullPath, 'utf8');
}

function requireText(label, content, needle) {
  if (!content.includes(needle)) {
    failures.push(`${label} missing text: ${needle}`);
  }
}

function requireRegex(label, content, pattern) {
  if (!pattern.test(content)) {
    failures.push(`${label} missing pattern: ${pattern}`);
  }
}

function validateAgentFiles() {
  const readme = read('.agentic/01.harness/agents/README.md');
  const useCases = read('.agentic/01.harness/agents/use-cases.md');

  for (const [fileName, displayName, agentId] of agents) {
    const relativePath = `.agentic/01.harness/agents/${fileName}`;
    const content = read(relativePath);

    requireText(relativePath, content, `id: ${agentId}`);
    requireText(relativePath, content, `# ${displayName}`);
    requireText('agents README', readme, `](${fileName})`);

    for (const section of requiredSections) {
      requireText(relativePath, content, `## ${section}`);
    }

    requireRegex(relativePath, content, /decision|Decision/);
    requireRegex(relativePath, content, /Score|score/);
    requireText('use cases', useCases, displayName);
  }
}

function validateUseCases() {
  const useCases = read('.agentic/01.harness/agents/use-cases.md');
  const multiAgentCases = [
    'Hosted RAG Service Deployment',
    'Harness Workflow Capability Build',
    'Product Platform Feature With Public UI',
    'Token Spend Regression In A Secure Workflow',
  ];

  for (const caseName of multiAgentCases) {
    requireText('use cases', useCases, `### ${caseName}`);
  }

  requireText('use cases', useCases, 'Expected agent: CFO Token Efficiency.');
  requireText('use cases', useCases, 'Expected agent: Senior Prompt Engineer.');
  requireText('use cases', useCases, 'Expected agent: Senior Back-End Architect.');
  requireText('use cases', useCases, 'Expected agent: Senior SRE Engineer.');
  requireText('use cases', useCases, 'Expected agent: SecOps Engineer.');
  requireText('use cases', useCases, 'Expected agent: UX/UI Engineer.');
  requireText('use cases', useCases, 'critical findings cannot be hidden by a high average score');
}

function validateTemplates() {
  const report = read('.agentic/01.harness/templates/agent-review-report.md');
  const scorecard = read('.agentic/01.harness/templates/agent-scorecard.yml');

  for (const text of [
    'Critical blocker present',
    'Evidence Reviewed',
    'Delegation Requests',
    'Evidence Gaps',
  ]) {
    requireText('agent-review-report template', report, text);
  }

  for (const text of [
    'schema: harness/agent-scorecard/v1',
    'critical_blocker_present',
    'delegation_requests',
    'quality_gate',
    'any required score is below 3',
  ]) {
    requireText('agent-scorecard template', scorecard, text);
  }
}

function validateWorkflows() {
  const single = read('.agentic/01.harness/workflows/run-agent-review.md');
  const board = read('.agentic/01.harness/workflows/run-review-board.md');

  requireText('run-agent-review workflow', single, 'templates/agent-review-report.md');
  requireText('run-agent-review workflow', single, 'templates/agent-scorecard.yml');
  requireText('run-agent-review workflow', single, 'Select the narrowest responsible agent');
  requireText('run-review-board workflow', board, 'Do not invite every');
  requireText('run-review-board workflow', board, 'Critical findings block the board');
  requireText('run-review-board workflow', board, 'hosted RAG service deployment');
}

function validateCfoFixture() {
  if (!cfoOutputPath) {
    failures.push('missing CFO fixture output path');
    return;
  }
  if (!fs.existsSync(cfoOutputPath)) {
    failures.push(`missing CFO fixture output file: ${cfoOutputPath}`);
    return;
  }
  const output = fs.readFileSync(cfoOutputPath, 'utf8');
  const parsed = JSON.parse(output);

  if (parsed.similar_tasks.count !== 3) {
    failures.push(`CFO fixture expected 3 similar tasks, got ${parsed.similar_tasks.count}`);
  }
  if (parsed.token_statistics.min !== 100) {
    failures.push(`CFO fixture expected min 100, got ${parsed.token_statistics.min}`);
  }
  if (parsed.token_statistics.max !== 300) {
    failures.push(`CFO fixture expected max 300, got ${parsed.token_statistics.max}`);
  }
  if (parsed.token_statistics.median !== 200) {
    failures.push(`CFO fixture expected median 200, got ${parsed.token_statistics.median}`);
  }
  if (parsed.token_statistics.q1 !== 150) {
    failures.push(`CFO fixture expected q1 150, got ${parsed.token_statistics.q1}`);
  }
  if (parsed.token_statistics.q3 !== 250) {
    failures.push(`CFO fixture expected q3 250, got ${parsed.token_statistics.q3}`);
  }
  if (parsed.trend.direction !== 'up') {
    failures.push(`CFO fixture expected upward trend, got ${parsed.trend.direction}`);
  }
  if (!parsed.current_task || parsed.current_task.delta_from_median !== -20) {
    failures.push('CFO fixture expected current task delta from median to equal -20');
  }
}

validateAgentFiles();
validateUseCases();
validateTemplates();
validateWorkflows();
validateCfoFixture();

if (failures.length > 0) {
  for (const failure of failures) {
    console.error(`ERROR: ${failure}`);
  }
  process.exit(1);
}

console.log('Harness review agents valid.');
