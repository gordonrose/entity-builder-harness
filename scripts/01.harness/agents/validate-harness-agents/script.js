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
  {
    fileName: 'cfo-token-efficiency.md',
    displayName: 'CFO Token Efficiency',
    agentId: 'harness.agents.cfo-token-efficiency',
    rubricFile: 'cfo-token-efficiency.yml',
  },
  {
    fileName: 'senior-prompt-engineer.md',
    displayName: 'Senior Prompt Engineer',
    agentId: 'harness.agents.senior-prompt-engineer',
    rubricFile: 'senior-prompt-engineer.yml',
  },
  {
    fileName: 'senior-backend-architect.md',
    displayName: 'Senior Back-End Architect',
    agentId: 'harness.agents.senior-backend-architect',
    rubricFile: 'senior-backend-architect.yml',
  },
  {
    fileName: 'senior-sre-engineer.md',
    displayName: 'Senior SRE Engineer',
    agentId: 'harness.agents.senior-sre-engineer',
    rubricFile: 'senior-sre-engineer.yml',
  },
  {
    fileName: 'secops-engineer.md',
    displayName: 'SecOps Engineer',
    agentId: 'harness.agents.secops-engineer',
    rubricFile: 'secops-engineer.yml',
  },
  {
    fileName: 'ux-ui-engineer.md',
    displayName: 'UX/UI Engineer',
    agentId: 'harness.agents.ux-ui-engineer',
    rubricFile: 'ux-ui-engineer.yml',
  },
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

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function nonEmptyString(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

function meaningfulString(value) {
  if (!nonEmptyString(value)) {
    return false;
  }
  const trimmed = value.trim();
  return trimmed.length >= 20 && !/^(ok|good|bad|todo|tbd|none|n\/a)$/i.test(trimmed);
}

function requireNonEmptyString(errors, label, value) {
  if (!meaningfulString(value)) {
    errors.push(`${label} must be a meaningful string`);
  }
}

function requireStringArray(errors, label, value, minLength = 1) {
  if (!Array.isArray(value) || value.length < minLength) {
    errors.push(`${label} must contain at least ${minLength} item(s)`);
    return;
  }
  value.forEach((item, index) => {
    if (!nonEmptyString(item)) {
      errors.push(`${label}[${index}] must be a non-empty string`);
    }
  });
}

function parseJsonCompatibleRubric(relativePath) {
  const content = read(relativePath);
  const start = content.indexOf('{');
  const end = content.lastIndexOf('}');
  if (start === -1 || end === -1 || end < start) {
    failures.push(`${relativePath} missing JSON-compatible rubric body`);
    return null;
  }

  try {
    return {
      content,
      data: JSON.parse(content.slice(start, end + 1)),
    };
  } catch (error) {
    failures.push(`${relativePath} is not parseable JSON-compatible YAML: ${error.message}`);
    return null;
  }
}

function validateRubricData(rubric, label, agent) {
  const errors = [];
  if (!isPlainObject(rubric)) {
    return [`${label} must be an object`];
  }

  if (rubric.schema !== 'harness/agent-rubric/v1') {
    errors.push(`${label}.schema must equal harness/agent-rubric/v1`);
  }
  if (rubric.agent_id !== agent.agentId) {
    errors.push(`${label}.agent_id must equal ${agent.agentId}`);
  }
  if (!Number.isInteger(rubric.version) || rubric.version < 1) {
    errors.push(`${label}.version must be a positive integer`);
  }
  if (!Number.isInteger(rubric.minimum_dimensions) || rubric.minimum_dimensions < 3) {
    errors.push(`${label}.minimum_dimensions must be at least 3`);
  }

  const policyKeys = ['pass', 'pass_with_notes', 'block', 'delegate', 'not_applicable'];
  if (!isPlainObject(rubric.decision_policy)) {
    errors.push(`${label}.decision_policy must be an object`);
  } else {
    for (const key of policyKeys) {
      requireNonEmptyString(errors, `${label}.decision_policy.${key}`, rubric.decision_policy[key]);
    }
  }

  requireStringArray(errors, `${label}.professional_standard_refs`, rubric.professional_standard_refs, 3);

  if (!isPlainObject(rubric.evidence_model)) {
    errors.push(`${label}.evidence_model must be an object`);
  } else {
    requireStringArray(errors, `${label}.evidence_model.required_sources`, rubric.evidence_model.required_sources, 3);
    requireStringArray(errors, `${label}.evidence_model.confidence_fields`, rubric.evidence_model.confidence_fields, 3);
    if (typeof rubric.evidence_model.minimum_sample_size_for_trend !== 'number') {
      errors.push(`${label}.evidence_model.minimum_sample_size_for_trend must be numeric`);
    }
  }

  if (!isPlainObject(rubric.delegation_model) || Object.keys(rubric.delegation_model).length < 2) {
    errors.push(`${label}.delegation_model must contain at least 2 delegation routes`);
  } else {
    let knownAgentTargets = 0;
    for (const [route, target] of Object.entries(rubric.delegation_model)) {
      if (!nonEmptyString(route) || !meaningfulString(target)) {
        errors.push(`${label}.delegation_model.${route} must describe a meaningful delegation route`);
      }
      if (String(target).startsWith('harness.agents.')) {
        if (!agents.some((candidate) => candidate.agentId === target)) {
          errors.push(`${label}.delegation_model.${route} targets unknown agent id ${target}`);
        } else {
          knownAgentTargets += 1;
        }
      }
    }
    if (knownAgentTargets < 2) {
      errors.push(`${label}.delegation_model must target at least 2 known agents`);
    }
  }

  requireStringArray(errors, `${label}.negative_fixtures`, rubric.negative_fixtures, 3);

  if (!Array.isArray(rubric.dimensions)) {
    errors.push(`${label}.dimensions must be an array`);
    return errors;
  }
  if (rubric.dimensions.length < rubric.minimum_dimensions) {
    errors.push(`${label}.dimensions has ${rubric.dimensions.length} items, below minimum ${rubric.minimum_dimensions}`);
  }

  const dimensionIds = new Set();
  rubric.dimensions.forEach((dimension, index) => {
    const dimensionLabel = `${label}.dimensions[${index}]`;
    if (!isPlainObject(dimension)) {
      errors.push(`${dimensionLabel} must be an object`);
      return;
    }
    if (!/^[a-z][a-z0-9_]*$/.test(dimension.id || '')) {
      errors.push(`${dimensionLabel}.id must be snake_case`);
    } else if (dimensionIds.has(dimension.id)) {
      errors.push(`${dimensionLabel}.id duplicates ${dimension.id}`);
    } else {
      dimensionIds.add(dimension.id);
    }
    if (!nonEmptyString(dimension.name)) {
      errors.push(`${dimensionLabel}.name must be a non-empty string`);
    }
    if (dimension.required !== true) {
      errors.push(`${dimensionLabel}.required must be true`);
    }
    if (typeof dimension.weight !== 'number' || dimension.weight <= 0) {
      errors.push(`${dimensionLabel}.weight must be a positive number`);
    }
    requireStringArray(errors, `${dimensionLabel}.evidence_required`, dimension.evidence_required, 3);
    requireStringArray(errors, `${dimensionLabel}.blocking_conditions`, dimension.blocking_conditions, 1);
    requireStringArray(errors, `${dimensionLabel}.delegation_triggers`, dimension.delegation_triggers, 1);
    requireStringArray(errors, `${dimensionLabel}.professional_standard_refs`, dimension.professional_standard_refs, 1);

    const scoreValues = [];
    for (let score = 0; score <= 5; score += 1) {
      const key = `score_${score}`;
      requireNonEmptyString(errors, `${dimensionLabel}.${key}`, dimension[key]);
      if (nonEmptyString(dimension[key])) {
        scoreValues.push(dimension[key].trim());
      }
    }
    if (new Set(scoreValues).size !== scoreValues.length) {
      errors.push(`${dimensionLabel} score anchors must be distinct`);
    }
  });

  return errors;
}

function validateAgentFiles() {
  const readme = read('.agentic/01.harness/agents/README.md');
  const useCases = read('.agentic/01.harness/agents/use-cases.md');

  for (const { fileName, displayName, agentId, rubricFile } of agents) {
    const relativePath = `.agentic/01.harness/agents/${fileName}`;
    const content = read(relativePath);

    requireText(relativePath, content, `id: ${agentId}`);
    requireText(relativePath, content, `# ${displayName}`);
    requireText('agents README', readme, `](${fileName})`);
    requireText(relativePath, content, `Scoring source: \`rubrics/${rubricFile}\`.`);

    for (const section of requiredSections) {
      requireText(relativePath, content, `## ${section}`);
    }

    requireRegex(relativePath, content, /decision|Decision/);
    requireRegex(relativePath, content, /Score|score/);
    requireText('use cases', useCases, displayName);
  }
}

function validateRubrics() {
  const readme = read('.agentic/01.harness/agents/rubrics/README.md');

  for (const agent of agents) {
    const relativePath = `.agentic/01.harness/agents/rubrics/${agent.rubricFile}`;
    requireText('rubrics README', readme, `\`${agent.rubricFile}\``);

    const parsed = parseJsonCompatibleRubric(relativePath);
    if (!parsed) {
      continue;
    }

    requireText(relativePath, parsed.content, `id: harness.agents.rubrics.${agent.rubricFile.replace(/\.yml$/, '')}`);
    requireText(relativePath, parsed.content, `path: .agentic/01.harness/agents/${agent.fileName}`);

    const errors = validateRubricData(parsed.data, relativePath, agent);
    failures.push(...errors);
  }

  const invalidRubric = {
    schema: 'harness/agent-rubric/v1',
    agent_id: agents[0].agentId,
    version: 1,
    minimum_dimensions: 1,
    decision_policy: {
      pass: 'ok',
      pass_with_notes: 'ok',
      block: 'bad',
      delegate: 'todo',
      not_applicable: 'n/a',
    },
    professional_standard_refs: ['generic'],
    evidence_model: {
      required_sources: ['file'],
      minimum_sample_size_for_trend: 0,
      confidence_fields: ['confidence'],
    },
    delegation_model: {
      generic: agents[0].agentId,
    },
    negative_fixtures: ['bad'],
    dimensions: [
      {
        id: 'example',
        name: 'ok',
        required: true,
        weight: 1,
        evidence_required: ['file'],
        score_5: 'good',
        score_4: 'good',
        score_3: 'ok',
        score_2: 'bad',
        score_1: 'bad',
        score_0: 'bad',
        blocking_conditions: [],
        delegation_triggers: [],
        professional_standard_refs: [],
      },
    ],
  };
  const negativeErrors = validateRubricData(invalidRubric, 'negative rubric fixture', agents[0]);
  if (negativeErrors.length === 0) {
    failures.push('semantic rubric validator accepted the shallow negative rubric fixture');
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
    'scores:',
    'dimension:',
    'score:',
    'evidence:',
    'needed_decision: pass | pass_with_notes | block | delegate | not_applicable',
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
validateRubrics();
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
