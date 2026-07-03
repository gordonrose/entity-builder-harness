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

const agentById = new Map(agents.map((agent) => [agent.agentId, agent]));
const allowedDecisions = new Set(['pass', 'pass_with_notes', 'block', 'delegate', 'not_applicable']);
const allowedConfidence = new Set(['low', 'medium', 'high']);

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
const cliOptions = parseArgs(process.argv.slice(2));
const cfoOutputPath = cliOptions.cfoOutputPath;

function parseArgs(argv) {
  const options = {
    cfoOutputPath: '',
    scorecardDirs: [],
    scorecardPaths: [],
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--cfo-output') {
      index += 1;
      options.cfoOutputPath = argv[index] || '';
    } else if (arg === '--scorecard') {
      index += 1;
      options.scorecardPaths.push(argv[index] || '');
    } else if (arg === '--scorecard-dir') {
      index += 1;
      options.scorecardDirs.push(argv[index] || '');
    } else if (arg === '--help' || arg === '-h') {
      console.log('Usage: script.sh [--scorecard <path>] [--scorecard-dir <path>]');
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

function parseJsonCompatibleFile(relativePath, expectedDescription) {
  const content = read(relativePath);
  const parsed = parseJsonCompatibleContent(content, relativePath, expectedDescription);
  return parsed ? { content, data: parsed } : null;
}

function resolveInputPath(inputPath) {
  return path.isAbsolute(inputPath) ? inputPath : path.join(repoRoot, inputPath);
}

function labelForPath(inputPath) {
  const resolved = resolveInputPath(inputPath);
  const relative = path.relative(repoRoot, resolved);
  return relative.startsWith('..') ? resolved : relative;
}

function parseJsonCompatiblePath(inputPath, expectedDescription) {
  const resolved = resolveInputPath(inputPath);
  const label = labelForPath(inputPath);
  if (!fs.existsSync(resolved)) {
    failures.push(`missing file: ${label}`);
    return null;
  }
  const content = fs.readFileSync(resolved, 'utf8');
  const parsed = parseJsonCompatibleContent(content, label, expectedDescription);
  return parsed ? { content, data: parsed, path: resolved, label } : null;
}

function parseJsonCompatibleContent(content, label, expectedDescription) {
  const start = content.indexOf('{');
  const end = content.lastIndexOf('}');
  if (start === -1 || end === -1 || end < start) {
    failures.push(`${label} missing JSON-compatible ${expectedDescription} body`);
    return null;
  }

  try {
    return JSON.parse(content.slice(start, end + 1));
  } catch (error) {
    failures.push(`${label} is not parseable JSON-compatible YAML: ${error.message}`);
    return null;
  }
}

function tryParseJsonCompatibleContent(content) {
  const start = content.indexOf('{');
  const end = content.lastIndexOf('}');
  if (start === -1 || end === -1 || end < start) {
    return null;
  }
  try {
    return JSON.parse(content.slice(start, end + 1));
  } catch (_error) {
    return null;
  }
}

function parseWorkflowJsonBlock(relativePath, markerName, expectedSchema) {
  const content = read(relativePath);
  const pattern = new RegExp(`<!-- ${markerName}:start -->\\s*\\\`\\\`\\\`json\\s*([\\s\\S]*?)\\s*\\\`\\\`\\\`\\s*<!-- ${markerName}:end -->`);
  const match = content.match(pattern);
  if (!match) {
    failures.push(`${relativePath} missing ${markerName} JSON block`);
    return null;
  }
  try {
    const data = JSON.parse(match[1]);
    if (data.schema !== expectedSchema) {
      failures.push(`${relativePath} ${markerName}.schema must equal ${expectedSchema}`);
    }
    return data;
  } catch (error) {
    failures.push(`${relativePath} ${markerName} JSON block is invalid: ${error.message}`);
    return null;
  }
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

function forbidText(label, content, needle) {
  if (content.includes(needle)) {
    failures.push(`${label} must not include stale text: ${needle}`);
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

const genericAnchorTerms = new Set([
  'acceptable', 'adequate', 'advice', 'agent', 'analysis', 'anchor',
  'available', 'case', 'clear', 'complete', 'context', 'decision',
  'detail', 'dimension', 'evidence', 'exists', 'explicit', 'field',
  'follow', 'generic', 'good', 'issue', 'material', 'minor', 'missing',
  'notes', 'present', 'professional', 'provided', 'review', 'reviewer',
  'risk', 'score', 'strong', 'surface', 'system', 'task', 'usable',
  'weak', 'without',
]);

const nonRepoEvidenceKinds = new Set([
  'command-output',
  'context-packet',
  'external',
  'external-url',
  'fixture-path',
  'inline',
  'packet',
  'url',
]);

const requiredQualityGateBlocks = [
  'critical_blocker_present is true',
  'any required score is below 3',
  'decision is delegate and delegated review is missing',
];

function tokenizeWords(value) {
  const tokens = String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9_]+/g, ' ')
    .split(/\s+/)
    .filter((token) => token.length >= 4);
  return [...new Set(tokens.flatMap((token) => {
    if (token.endsWith('ies') && token.length > 5) {
      return [token, `${token.slice(0, -3)}y`];
    }
    if (token.endsWith('s') && token.length > 4) {
      return [token, token.slice(0, -1)];
    }
    return [token];
  }))];
}

function dimensionLexicon(dimension) {
  const values = [
    dimension.id,
    dimension.name,
    ...(Array.isArray(dimension.evidence_required) ? dimension.evidence_required : []),
    ...(Array.isArray(dimension.blocking_conditions) ? dimension.blocking_conditions : []),
    ...(Array.isArray(dimension.delegation_triggers) ? dimension.delegation_triggers : []),
    ...(Array.isArray(dimension.professional_standard_refs) ? dimension.professional_standard_refs : []),
  ];
  const tokens = tokenizeWords(values.join(' ')).filter((token) => !genericAnchorTerms.has(token));
  return new Set(tokens);
}

function repoEvidencePathExists(evidencePath) {
  const trimmed = String(evidencePath || '').trim().replace(/:\d+(?::\d+)?$/, '');
  if (!trimmed) {
    return false;
  }
  if (/^(https?:\/\/|s3:\/\/|arn:|packet:|context-packet:|command:|inline:)/i.test(trimmed)) {
    return true;
  }
  if (path.isAbsolute(trimmed)) {
    const relative = path.relative(repoRoot, trimmed);
    return relative && !relative.startsWith('..') && !path.isAbsolute(relative) && fs.existsSync(trimmed);
  }
  return fs.existsSync(path.join(repoRoot, trimmed));
}

function validateScoreEvidenceSpecificity(errors, label, dimension, evidence) {
  if (!dimension || !nonEmptyString(evidence)) {
    return;
  }
  const lexicon = dimensionLexicon(dimension);
  const evidenceTokens = new Set(tokenizeWords(evidence).filter((token) => !genericAnchorTerms.has(token)));
  const matches = [...lexicon].filter((token) => evidenceTokens.has(token));
  if (matches.length === 0) {
    errors.push(`${label}.evidence must reference rubric-specific evidence, blocker, delegation, or professional-standard terms for ${dimension.id}`);
  }
}

function validateScoreAnchorSpecificity(errors, label, dimension, key) {
  const anchor = dimension[key];
  if (!nonEmptyString(anchor)) {
    return;
  }
  const anchorTokens = new Set(tokenizeWords(anchor));
  const lexicon = dimensionLexicon(dimension);
  const matches = [...lexicon].filter((token) => anchorTokens.has(token));
  if (matches.length === 0) {
    errors.push(`${label}.${key} must include dimension-specific evidence, risk, or control terms`);
  }
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
  return parseJsonCompatibleFile(relativePath, 'rubric');
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
        validateScoreAnchorSpecificity(errors, dimensionLabel, dimension, key);
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

function fixtureText(fixture) {
  return [
    fixture.title,
    fixture.task_text,
    ...(Array.isArray(fixture.changed_paths) ? fixture.changed_paths : []),
  ].join(' ').toLowerCase();
}

function hasAny(text, patterns) {
  return patterns.some((pattern) => pattern.test(text));
}

function validateRoutingConfig(routingConfig, label) {
  const errors = [];
  if (!isPlainObject(routingConfig)) {
    return [`${label} must be an object`];
  }
  if (!Number.isInteger(routingConfig.version) || routingConfig.version < 1) {
    errors.push(`${label}.version must be a positive integer`);
  }
  if (!Array.isArray(routingConfig.routes) || routingConfig.routes.length !== agents.length) {
    errors.push(`${label}.routes must contain exactly one route per agent`);
    return errors;
  }
  const seenAgents = new Set();
  routingConfig.routes.forEach((route, index) => {
    const routeLabel = `${label}.routes[${index}]`;
    if (!isPlainObject(route)) {
      errors.push(`${routeLabel} must be an object`);
      return;
    }
    if (!agentById.has(route.agent_id)) {
      errors.push(`${routeLabel}.agent_id is unknown: ${route.agent_id}`);
    } else if (seenAgents.has(route.agent_id)) {
      errors.push(`${routeLabel}.agent_id duplicates ${route.agent_id}`);
    } else {
      seenAgents.add(route.agent_id);
    }
    requireNonEmptyString(errors, `${routeLabel}.reason`, route.reason);
    requireStringArray(errors, `${routeLabel}.match_patterns`, route.match_patterns, 3);
    if (Array.isArray(route.match_patterns)) {
      route.match_patterns.forEach((pattern, patternIndex) => {
        try {
          RegExp(pattern, 'i');
        } catch (error) {
          errors.push(`${routeLabel}.match_patterns[${patternIndex}] is invalid regex: ${error.message}`);
        }
      });
    }
  });
  for (const agent of agents) {
    if (!seenAgents.has(agent.agentId)) {
      errors.push(`${label}.routes missing ${agent.agentId}`);
    }
  }
  return errors;
}

function selectedAgentsForFixture(fixture, routingConfig) {
  const text = fixtureText(fixture);
  const selected = new Set();
  for (const route of routingConfig?.routes || []) {
    const patterns = Array.isArray(route.match_patterns) ? route.match_patterns : [];
    if (patterns.some((pattern) => RegExp(pattern, 'i').test(text))) {
      selected.add(route.agent_id);
    }
  }

  return [...selected].sort();
}

function sorted(values) {
  return [...values].sort();
}

function sameStringSet(left, right) {
  const a = sorted(left);
  const b = sorted(right);
  return a.length === b.length && a.every((value, index) => value === b[index]);
}

function validateMinimumScores(errors, label, value) {
  if (!isPlainObject(value)) {
    errors.push(`${label} must be an object`);
    return;
  }
  if (value.required_dimension_min !== 4) {
    errors.push(`${label}.required_dimension_min must be 4`);
  }
  if (value.block_below !== 3) {
    errors.push(`${label}.block_below must be 3`);
  }
}

function boardRouteByFixtureId(boardRouting, fixtureId) {
  return (boardRouting?.boards || []).find((board) => board.fixture_id === fixtureId) || null;
}

function validateBoardRoutingConfig(boardRouting, label) {
  const errors = [];
  if (!isPlainObject(boardRouting)) {
    return [`${label} must be an object`];
  }
  if (!Number.isInteger(boardRouting.version) || boardRouting.version < 1) {
    errors.push(`${label}.version must be a positive integer`);
  }
  if (!Array.isArray(boardRouting.boards) || boardRouting.boards.length < 4) {
    errors.push(`${label}.boards must contain at least 4 board routes`);
    return errors;
  }
  const ids = new Set();
  boardRouting.boards.forEach((board, index) => {
    const boardLabel = `${label}.boards[${index}]`;
    if (!isPlainObject(board)) {
      errors.push(`${boardLabel} must be an object`);
      return;
    }
    if (!nonEmptyString(board.fixture_id)) {
      errors.push(`${boardLabel}.fixture_id must be a non-empty string`);
    } else if (ids.has(board.fixture_id)) {
      errors.push(`${boardLabel}.fixture_id duplicates ${board.fixture_id}`);
    } else {
      ids.add(board.fixture_id);
    }
    requireNonEmptyString(errors, `${boardLabel}.title`, board.title);
    requireNonEmptyString(errors, `${boardLabel}.reason`, board.reason);
    requireStringArray(errors, `${boardLabel}.agents`, board.agents, 2);
    if (Array.isArray(board.agents)) {
      board.agents.forEach((agentId) => {
        if (!agentById.has(agentId)) {
          errors.push(`${boardLabel}.agents contains unknown agent id ${agentId}`);
        }
      });
    }
  });
  return errors;
}

function selectedAgentsFromComposition(fixture, boardComposition) {
  const text = fixtureText(fixture);
  const selected = new Set();
  for (const rule of boardComposition?.rules || []) {
    const patterns = Array.isArray(rule.when_any) ? rule.when_any : [];
    if (patterns.some((pattern) => RegExp(pattern, 'i').test(text))) {
      selected.add(rule.agent_id);
    }
  }
  return [...selected].sort();
}

function validateBoardCompositionConfig(boardComposition, label) {
  const errors = [];
  if (!isPlainObject(boardComposition)) {
    return [`${label} must be an object`];
  }
  if (!Number.isInteger(boardComposition.version) || boardComposition.version < 1) {
    errors.push(`${label}.version must be a positive integer`);
  }
  if (!Array.isArray(boardComposition.rules) || boardComposition.rules.length !== agents.length) {
    errors.push(`${label}.rules must contain exactly one composition rule per agent`);
    return errors;
  }
  const ids = new Set();
  const seenAgents = new Set();
  boardComposition.rules.forEach((rule, index) => {
    const ruleLabel = `${label}.rules[${index}]`;
    if (!isPlainObject(rule)) {
      errors.push(`${ruleLabel} must be an object`);
      return;
    }
    if (!nonEmptyString(rule.id)) {
      errors.push(`${ruleLabel}.id must be a non-empty string`);
    } else if (ids.has(rule.id)) {
      errors.push(`${ruleLabel}.id duplicates ${rule.id}`);
    } else {
      ids.add(rule.id);
    }
    if (!agentById.has(rule.agent_id)) {
      errors.push(`${ruleLabel}.agent_id is unknown: ${rule.agent_id}`);
    } else if (seenAgents.has(rule.agent_id)) {
      errors.push(`${ruleLabel}.agent_id duplicates ${rule.agent_id}`);
    } else {
      seenAgents.add(rule.agent_id);
    }
    requireStringArray(errors, `${ruleLabel}.when_any`, rule.when_any, 2);
    if (Array.isArray(rule.when_any)) {
      rule.when_any.forEach((pattern, patternIndex) => {
        try {
          RegExp(pattern, 'i');
        } catch (error) {
          errors.push(`${ruleLabel}.when_any[${patternIndex}] is invalid regex: ${error.message}`);
        }
      });
    }
    requireNonEmptyString(errors, `${ruleLabel}.blocking_scope`, rule.blocking_scope);
  });
  for (const agent of agents) {
    if (!seenAgents.has(agent.agentId)) {
      errors.push(`${label}.rules missing ${agent.agentId}`);
    }
  }
  return errors;
}

function validateUseCaseFixture(fixture, index, useCases, routingConfig, boardRouting, boardComposition) {
  const errors = [];
  const label = `use-case fixture[${index}]`;
  const knownAgentIds = new Set(agents.map((agent) => agent.agentId));

  if (!isPlainObject(fixture)) {
    return [`${label} must be an object`];
  }
  if (!/^[a-z]+[a-z0-9_.-]*$/.test(fixture.id || '')) {
    errors.push(`${label}.id must be stable dotted/kebab case`);
  }
  if (!nonEmptyString(fixture.title)) {
    errors.push(`${label}.title must be a non-empty string`);
  } else if (!useCases.includes(`### ${fixture.title}`) && !useCases.includes(`#### ${fixture.title}`)) {
    errors.push(`${label}.title must match a prose use-case heading`);
  }
  if (!['single_agent', 'multi_agent'].includes(fixture.type)) {
    errors.push(`${label}.type must be single_agent or multi_agent`);
  }
  requireNonEmptyString(errors, `${label}.task_text`, fixture.task_text);
  requireStringArray(errors, `${label}.changed_paths`, fixture.changed_paths, 1);
  requireStringArray(errors, `${label}.expected_agents`, fixture.expected_agents, 1);
  requireStringArray(errors, `${label}.highest_standard`, fixture.highest_standard, 3);
  requireStringArray(errors, `${label}.required_evidence`, fixture.required_evidence, 3);
  requireStringArray(errors, `${label}.failure_modes`, fixture.failure_modes, 1);
  requireStringArray(errors, `${label}.expected_blockers`, fixture.expected_blockers, 0);
  validateMinimumScores(errors, `${label}.minimum_scores`, fixture.minimum_scores);
  requireStringArray(errors, `${label}.required_delegation`, fixture.required_delegation, 0);
  requireStringArray(errors, `${label}.forbidden_delegation`, fixture.forbidden_delegation, 0);
  if (!allowedDecisions.has(fixture.expected_board_decision)) {
    errors.push(`${label}.expected_board_decision must be a valid decision`);
  }

  if (Array.isArray(fixture.expected_agents)) {
    for (const agentId of fixture.expected_agents) {
      if (!knownAgentIds.has(agentId)) {
        errors.push(`${label}.expected_agents contains unknown agent id ${agentId}`);
      }
    }
    if (fixture.type === 'single_agent' && fixture.expected_agents.length !== 1) {
      errors.push(`${label} single_agent fixture must expect exactly 1 agent`);
    }
    if (fixture.type === 'multi_agent' && fixture.expected_agents.length < 2) {
      errors.push(`${label} multi_agent fixture must expect at least 2 agents`);
    }

    const selectedAgents = selectedAgentsForFixture(fixture, routingConfig);
    if (!sameStringSet(selectedAgents, fixture.expected_agents)) {
      errors.push(`${label} routed to [${selectedAgents.join(', ')}], expected [${sorted(fixture.expected_agents).join(', ')}]`);
    }

    if (fixture.type === 'single_agent' && fixture.expected_board_decision !== 'not_applicable') {
      errors.push(`${label} single_agent fixture must set expected_board_decision to not_applicable`);
    }
    if (fixture.type === 'multi_agent') {
      if (fixture.expected_board_decision === 'not_applicable') {
        errors.push(`${label} multi_agent fixture must name a board decision`);
      }
      const composedAgents = selectedAgentsFromComposition(fixture, boardComposition);
      if (!sameStringSet(composedAgents, fixture.expected_agents)) {
        errors.push(`${label} board composition selects [${composedAgents.join(', ')}], expected [${sorted(fixture.expected_agents).join(', ')}]`);
      }
      const boardRoute = boardRouteByFixtureId(boardRouting, fixture.id);
      if (!boardRoute) {
        errors.push(`${label} missing matching board route in run-review-board workflow`);
      } else {
        if (boardRoute.title !== fixture.title) {
          errors.push(`${label} board title mismatch: ${boardRoute.title}`);
        }
        if (!sameStringSet(boardRoute.agents, fixture.expected_agents)) {
          errors.push(`${label} board agents [${sorted(boardRoute.agents || []).join(', ')}] do not match expected [${sorted(fixture.expected_agents).join(', ')}]`);
        }
      }
    }
  }

  return errors;
}

function validateUseCaseFixtures() {
  const relativePath = 'scripts/01.harness/agents/validate-harness-agents/fixtures/use-case-fixtures.yml';
  const parsed = parseJsonCompatibleFile(relativePath, 'use-case fixture');
  const useCases = read('.agentic/01.harness/agents/use-cases.md');
  const validatorReadme = read('scripts/01.harness/agents/validate-harness-agents/README.md');
  const routingConfig = parseWorkflowJsonBlock(
    '.agentic/01.harness/workflows/run-agent-review.md',
    'review-agent-routing',
    'harness/review-agent-routing/v1',
  );
  const boardRouting = parseWorkflowJsonBlock(
    '.agentic/01.harness/workflows/run-review-board.md',
    'review-board-routing',
    'harness/review-board-routing/v1',
  );
  const boardComposition = parseWorkflowJsonBlock(
    '.agentic/01.harness/workflows/run-review-board.md',
    'review-board-composition',
    'harness/review-board-composition/v1',
  );
  if (routingConfig) {
    failures.push(...validateRoutingConfig(routingConfig, 'run-agent-review routing'));
  }
  if (boardRouting) {
    failures.push(...validateBoardRoutingConfig(boardRouting, 'run-review-board routing'));
  }
  if (boardComposition) {
    failures.push(...validateBoardCompositionConfig(boardComposition, 'run-review-board composition'));
  }
  requireText('validator README', validatorReadme, 'fixtures/use-case-fixtures.yml');
  requireText('validator README', validatorReadme, 'fixtures/scorecard-fixtures.yml');
  requireText('validator README', validatorReadme, 'fixtures/negative-review-fixtures.yml');
  requireText('validator README', validatorReadme, '--scorecard');
  requireText('validator README', validatorReadme, '--scorecard-dir');
  requireText('use cases', useCases, 'fixtures/use-case-fixtures.yml');
  if (!parsed) {
    return;
  }

  const data = parsed.data;
  if (data.schema !== 'harness/review-agent-use-case-fixtures/v1') {
    failures.push(`${relativePath}.schema must equal harness/review-agent-use-case-fixtures/v1`);
  }
  if (!Number.isInteger(data.version) || data.version < 1) {
    failures.push(`${relativePath}.version must be a positive integer`);
  }
  if (!isPlainObject(data.quality_gate_defaults)) {
    failures.push(`${relativePath}.quality_gate_defaults must be an object`);
  } else {
    if (data.quality_gate_defaults.minimum_required_dimension_score !== 4) {
      failures.push(`${relativePath}.quality_gate_defaults.minimum_required_dimension_score must be 4`);
    }
    if (data.quality_gate_defaults.block_below_required_dimension_score !== 3) {
      failures.push(`${relativePath}.quality_gate_defaults.block_below_required_dimension_score must be 3`);
    }
    if (data.quality_gate_defaults.critical_blocker_policy !== 'critical_findings_block_even_when_average_is_passing') {
      failures.push(`${relativePath}.quality_gate_defaults.critical_blocker_policy must block critical findings`);
    }
    if (data.quality_gate_defaults.review_authority !== 'review_only_unless_workflow_grants_write') {
      failures.push(`${relativePath}.quality_gate_defaults.review_authority must keep review and implementation authority separate`);
    }
  }

  if (!Array.isArray(data.fixtures) || data.fixtures.length < 10) {
    failures.push(`${relativePath}.fixtures must contain at least 10 use cases`);
    return;
  }

  let singleCount = 0;
  let multiCount = 0;
  const ids = new Set();
  for (let index = 0; index < data.fixtures.length; index += 1) {
    const fixture = data.fixtures[index];
    if (isPlainObject(fixture)) {
      if (ids.has(fixture.id)) {
        failures.push(`use-case fixture[${index}].id duplicates ${fixture.id}`);
      } else {
        ids.add(fixture.id);
      }
      if (fixture.type === 'single_agent') {
        singleCount += 1;
      }
      if (fixture.type === 'multi_agent') {
        multiCount += 1;
      }
    }
    failures.push(...validateUseCaseFixture(fixture, index, useCases, routingConfig, boardRouting, boardComposition));
  }
  if (singleCount < 6) {
    failures.push(`${relativePath} must include at least one single-agent fixture per agent`);
  }
  if (multiCount < 4) {
    failures.push(`${relativePath} must include at least 4 multi-agent fixtures`);
  }

  const negativeFixture = {
    id: 'negative.bad_routing',
    title: 'Public Endpoint Exposure',
    type: 'single_agent',
    task_text: 'A public endpoint exposure changes auth and OWASP-relevant controls.',
    changed_paths: ['src/server/public-api.ts'],
    expected_agents: ['harness.agents.cfo-token-efficiency'],
    highest_standard: ['one', 'two', 'three'],
    required_evidence: ['one', 'two', 'three'],
    failure_modes: ['bad route'],
    expected_blockers: [],
    minimum_scores: {
      required_dimension_min: 4,
      block_below: 3,
    },
    required_delegation: [],
    forbidden_delegation: [],
    expected_board_decision: 'not_applicable',
  };
  const negativeErrors = validateUseCaseFixture(negativeFixture, 999, useCases, routingConfig, boardRouting, boardComposition);
  if (negativeErrors.length === 0) {
    failures.push('use-case fixture validator accepted the bad-routing negative fixture');
  }
}

const rubricCache = new Map();

function rubricDataForAgent(agentId) {
  if (rubricCache.has(agentId)) {
    return rubricCache.get(agentId);
  }
  const agent = agentById.get(agentId);
  if (!agent) {
    rubricCache.set(agentId, null);
    return null;
  }
  const parsed = parseJsonCompatibleRubric(`.agentic/01.harness/agents/rubrics/${agent.rubricFile}`);
  const data = parsed?.data || null;
  rubricCache.set(agentId, data);
  return data;
}

function arrayLength(value) {
  return Array.isArray(value) ? value.length : 0;
}

function validateEvidenceSources(errors, label, evidence) {
  if (!isPlainObject(evidence)) {
    errors.push(`${label}.evidence must be an object`);
    return;
  }
  if (!Array.isArray(evidence.sources) || evidence.sources.length === 0) {
    errors.push(`${label}.evidence.sources must contain at least one source`);
  } else {
    evidence.sources.forEach((source, index) => {
      const sourceLabel = `${label}.evidence.sources[${index}]`;
      if (!isPlainObject(source)) {
        errors.push(`${sourceLabel} must be an object`);
        return;
      }
      requireNonEmptyString(errors, `${sourceLabel}.path`, source.path);
      if (!nonEmptyString(source.kind)) {
        errors.push(`${sourceLabel}.kind must be a non-empty string`);
      } else if (!nonRepoEvidenceKinds.has(String(source.kind).toLowerCase()) && !repoEvidencePathExists(source.path)) {
        errors.push(`${sourceLabel}.path must exist in the repository for repo-local evidence kind ${source.kind}`);
      }
      requireNonEmptyString(errors, `${sourceLabel}.note`, source.note);
    });
  }
  if (!Array.isArray(evidence.gaps)) {
    errors.push(`${label}.evidence.gaps must be an array`);
  }
}

function validateFindings(errors, label, findings) {
  if (!isPlainObject(findings)) {
    errors.push(`${label}.findings must be an object`);
    return;
  }
  for (const severity of ['critical', 'high', 'medium', 'low']) {
    requireStringArray(errors, `${label}.findings.${severity}`, findings[severity], 0);
  }
}

function validateQualityGate(errors, label, qualityGate) {
  if (!isPlainObject(qualityGate)) {
    errors.push(`${label}.quality_gate must be an object`);
    return;
  }
  requireStringArray(errors, `${label}.quality_gate.blocks_when`, qualityGate.blocks_when, 3);
  const blocksWhen = Array.isArray(qualityGate.blocks_when) ? qualityGate.blocks_when : [];
  for (const requiredBlock of requiredQualityGateBlocks) {
    if (!blocksWhen.includes(requiredBlock)) {
      errors.push(`${label}.quality_gate.blocks_when must include ${requiredBlock}`);
    }
  }
}

function validateDelegationRequests(errors, label, scorecard) {
  if (!Array.isArray(scorecard.delegation_requests)) {
    errors.push(`${label}.delegation_requests must be an array`);
    return;
  }
  scorecard.delegation_requests.forEach((request, index) => {
    const requestLabel = `${label}.delegation_requests[${index}]`;
    if (!isPlainObject(request)) {
      errors.push(`${requestLabel} must be an object`);
      return;
    }
    if (!agentById.has(request.target_agent_id)) {
      errors.push(`${requestLabel}.target_agent_id must be a known agent id`);
    } else if (request.target_agent_id === scorecard.agent?.id) {
      errors.push(`${requestLabel}.target_agent_id must not self-delegate to the reviewing agent`);
    }
    requireNonEmptyString(errors, `${requestLabel}.blocking_question`, request.blocking_question);
    requireStringArray(errors, `${requestLabel}.evidence_already_reviewed`, request.evidence_already_reviewed, 1);
    if (!allowedDecisions.has(request.needed_decision)) {
      errors.push(`${requestLabel}.needed_decision must be a valid decision`);
    }
  });
}

function roundScore(value) {
  return Math.round(value * 100) / 100;
}

function weightedOverallScore(dimensions, scoreByDimension) {
  let weightedTotal = 0;
  let weightTotal = 0;
  for (const dimension of dimensions) {
    const score = scoreByDimension.get(dimension.id);
    if (typeof score !== 'number') {
      return null;
    }
    weightedTotal += score * dimension.weight;
    weightTotal += dimension.weight;
  }
  return weightTotal === 0 ? null : roundScore(weightedTotal / weightTotal);
}

function validateScorecardData(scorecard, label) {
  const errors = [];
  if (!isPlainObject(scorecard)) {
    return [`${label} must be an object`];
  }
  if (scorecard.schema !== 'harness/agent-scorecard/v1') {
    errors.push(`${label}.schema must equal harness/agent-scorecard/v1`);
  }
  if (!isPlainObject(scorecard.agent)) {
    errors.push(`${label}.agent must be an object`);
  }
  const agentId = scorecard.agent?.id;
  if (!agentById.has(agentId)) {
    errors.push(`${label}.agent.id must be a known harness review agent`);
  }
  if (!isPlainObject(scorecard.review)) {
    errors.push(`${label}.review must be an object`);
  }
  const decision = scorecard.review?.decision;
  if (!allowedDecisions.has(decision)) {
    errors.push(`${label}.review.decision must be a valid decision`);
  }
  if (!['review', 'planning', 'research', 'implementation'].includes(scorecard.review?.mode)) {
    errors.push(`${label}.review.mode must be review, planning, research, or implementation`);
  }
  requireNonEmptyString(errors, `${label}.review.task`, scorecard.review?.task);
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$|^YYYY-MM-DDTHH:MM:SSZ$/.test(scorecard.review?.reviewed_at_utc || '')) {
    errors.push(`${label}.review.reviewed_at_utc must be an ISO UTC timestamp or template placeholder`);
  }
  if (!allowedConfidence.has(scorecard.review?.confidence)) {
    errors.push(`${label}.review.confidence must be low, medium, or high`);
  }
  if (typeof scorecard.review?.critical_blocker_present !== 'boolean') {
    errors.push(`${label}.review.critical_blocker_present must be boolean`);
  }
  if (typeof scorecard.review?.overall_score !== 'number' || scorecard.review.overall_score < 0 || scorecard.review.overall_score > 5) {
    errors.push(`${label}.review.overall_score must be a number from 0 to 5`);
  }

  validateEvidenceSources(errors, label, scorecard.evidence);
  validateFindings(errors, label, scorecard.findings);
  validateDelegationRequests(errors, label, scorecard);
  requireStringArray(errors, `${label}.required_follow_up`, scorecard.required_follow_up, 0);
  validateQualityGate(errors, label, scorecard.quality_gate);

  const rubric = rubricDataForAgent(agentId);
  const knownDimensions = new Map((rubric?.dimensions || []).map((dimension) => [dimension.id, dimension]));
  const requiredDimensions = (rubric?.dimensions || []).filter((dimension) => dimension.required);
  if (!Array.isArray(scorecard.scores) || scorecard.scores.length === 0) {
    errors.push(`${label}.scores must contain rubric dimension scores`);
  }
  const scoreByDimension = new Map();
  if (Array.isArray(scorecard.scores)) {
    scorecard.scores.forEach((scoreEntry, index) => {
      const scoreLabel = `${label}.scores[${index}]`;
      if (!isPlainObject(scoreEntry)) {
        errors.push(`${scoreLabel} must be an object`);
        return;
      }
      if (!knownDimensions.has(scoreEntry.dimension)) {
        errors.push(`${scoreLabel}.dimension must be a known required rubric dimension`);
      } else if (scoreByDimension.has(scoreEntry.dimension)) {
        errors.push(`${scoreLabel}.dimension duplicates ${scoreEntry.dimension}`);
      } else {
        scoreByDimension.set(scoreEntry.dimension, scoreEntry.score);
      }
      if (!Number.isInteger(scoreEntry.score) || scoreEntry.score < 0 || scoreEntry.score > 5) {
        errors.push(`${scoreLabel}.score must be an integer from 0 to 5`);
      }
      requireNonEmptyString(errors, `${scoreLabel}.evidence`, scoreEntry.evidence);
      requireNonEmptyString(errors, `${scoreLabel}.notes`, scoreEntry.notes);
      validateScoreEvidenceSpecificity(errors, scoreLabel, knownDimensions.get(scoreEntry.dimension), scoreEntry.evidence);
    });
  }
  for (const dimension of requiredDimensions) {
    if (!scoreByDimension.has(dimension.id)) {
      errors.push(`${label}.scores missing required dimension ${dimension.id}`);
    }
  }

  const requiredScores = requiredDimensions
    .map((dimension) => ({ dimension: dimension.id, score: scoreByDimension.get(dimension.id) }))
    .filter((entry) => typeof entry.score === 'number');
  const weightedOverall = weightedOverallScore(rubric?.dimensions || [], scoreByDimension);
  if (weightedOverall !== null && typeof scorecard.review?.overall_score === 'number') {
    const delta = Math.abs(scorecard.review.overall_score - weightedOverall);
    if (delta > 0.05) {
      errors.push(`${label}.review.overall_score must match weighted rubric score ${weightedOverall}`);
    }
  }
  const belowThree = requiredScores.filter((entry) => entry.score < 3);
  const belowFour = requiredScores.filter((entry) => entry.score < 4);
  const criticalFindings = arrayLength(scorecard.findings?.critical);
  const criticalBlockerPresent = scorecard.review?.critical_blocker_present === true || criticalFindings > 0;

  if (criticalFindings > 0 && scorecard.review?.critical_blocker_present !== true) {
    errors.push(`${label}.review.critical_blocker_present must be true when critical findings exist`);
  }
  if (criticalBlockerPresent && decision !== 'block') {
    errors.push(`${label}.review.decision must be block when a critical blocker is present`);
  }
  if (belowThree.length > 0 && decision !== 'block') {
    errors.push(`${label}.review.decision must be block when required scores are below 3`);
  }
  if (decision === 'pass' && belowFour.length > 0) {
    errors.push(`${label}.review.decision pass requires all required scores to be at least 4`);
  }
  if (decision === 'delegate' && arrayLength(scorecard.delegation_requests) === 0) {
    errors.push(`${label}.review.decision delegate requires at least one delegation request`);
  }
  if (decision === 'pass' && arrayLength(scorecard.evidence?.gaps) > 0) {
    errors.push(`${label}.review.decision pass cannot have unresolved evidence gaps`);
  }
  if (decision === 'pass' && arrayLength(scorecard.findings?.high) > 0) {
    errors.push(`${label}.review.decision pass cannot have high findings`);
  }
  if (decision === 'block' && arrayLength(scorecard.required_follow_up) === 0) {
    errors.push(`${label}.review.decision block requires required_follow_up`);
  }

  return errors;
}

function cloneData(value) {
  return JSON.parse(JSON.stringify(value));
}

function expectScorecardInvalid(label, scorecard, expectedErrorText) {
  const errors = validateScorecardData(scorecard, label);
  if (errors.length === 0) {
    failures.push(`${label} expected invalid scorecard but validator accepted it`);
    return;
  }
  if (!errors.some((error) => error.includes(expectedErrorText))) {
    failures.push(`${label} expected an error containing ${expectedErrorText}, got: ${errors.join('; ')}`);
  }
}

function validateScorecardSemanticNegativeMutations(baseScorecard) {
  const missingQualityGate = cloneData(baseScorecard);
  delete missingQualityGate.quality_gate;
  expectScorecardInvalid('scorecard semantic negative missing_quality_gate', missingQualityGate, 'quality_gate');

  const fakeRepoEvidence = cloneData(baseScorecard);
  fakeRepoEvidence.evidence.sources[0].path = 'docs/fake-review-evidence/does-not-exist.md';
  fakeRepoEvidence.evidence.sources[0].kind = 'file';
  expectScorecardInvalid('scorecard semantic negative fake_repo_evidence_path', fakeRepoEvidence, 'path must exist');

  const genericEvidence = cloneData(baseScorecard);
  genericEvidence.scores = genericEvidence.scores.map((score) => ({
    ...score,
    evidence: 'This is sufficiently detailed and acceptable for review.',
  }));
  expectScorecardInvalid('scorecard semantic negative generic_score_evidence', genericEvidence, 'rubric-specific evidence');

  const blockWithoutFollowUp = cloneData(baseScorecard);
  blockWithoutFollowUp.review.decision = 'block';
  blockWithoutFollowUp.review.critical_blocker_present = true;
  blockWithoutFollowUp.findings.critical = ['Critical blocker is present and must not pass silently.'];
  blockWithoutFollowUp.required_follow_up = [];
  expectScorecardInvalid('scorecard semantic negative block_without_follow_up', blockWithoutFollowUp, 'block requires required_follow_up');

  const passWithHighFinding = cloneData(baseScorecard);
  passWithHighFinding.findings.high = ['High-severity issue remains unresolved.'];
  expectScorecardInvalid('scorecard semantic negative pass_with_high_finding', passWithHighFinding, 'pass cannot have high findings');

  const selfDelegation = cloneData(baseScorecard);
  selfDelegation.review.decision = 'delegate';
  selfDelegation.evidence.gaps = ['The reviewing agent cannot answer its own delegated question.'];
  selfDelegation.delegation_requests = [
    {
      target_agent_id: selfDelegation.agent.id,
      blocking_question: 'Can the reviewing agent approve its own unresolved concern?',
      evidence_already_reviewed: [selfDelegation.evidence.sources[0].path],
      needed_decision: 'pass_with_notes',
    },
  ];
  selfDelegation.required_follow_up = ['Route the unresolved question to a different responsible agent.'];
  expectScorecardInvalid('scorecard semantic negative self_delegation', selfDelegation, 'must not self-delegate');
}

function validateScorecardFixtures() {
  const relativePath = 'scripts/01.harness/agents/validate-harness-agents/fixtures/scorecard-fixtures.yml';
  const parsed = parseJsonCompatibleFile(relativePath, 'scorecard fixture');
  if (!parsed) {
    return;
  }
  const data = parsed.data;
  if (data.schema !== 'harness/review-agent-scorecard-fixtures/v1') {
    failures.push(`${relativePath}.schema must equal harness/review-agent-scorecard-fixtures/v1`);
  }
  if (!Number.isInteger(data.version) || data.version < 1) {
    failures.push(`${relativePath}.version must be a positive integer`);
  }
  if (!Array.isArray(data.fixtures) || data.fixtures.length < 5) {
    failures.push(`${relativePath}.fixtures must contain pass, block, delegate, and contradictory negative fixtures`);
    return;
  }
  data.fixtures.forEach((fixture, index) => {
    const label = `scorecard fixture[${index}]`;
    if (!isPlainObject(fixture)) {
      failures.push(`${label} must be an object`);
      return;
    }
    if (!nonEmptyString(fixture.id)) {
      failures.push(`${label}.id must be a non-empty string`);
    }
    if (typeof fixture.expected_valid !== 'boolean') {
      failures.push(`${label}.expected_valid must be boolean`);
    }
    const errors = validateScorecardData(fixture.scorecard, label);
    if (fixture.expected_valid && errors.length > 0) {
      failures.push(...errors);
    }
    if (fixture.expected_valid === false) {
      if (errors.length === 0) {
        failures.push(`${label} expected invalid scorecard but validator accepted it`);
      } else if (nonEmptyString(fixture.expected_error_contains) && !errors.some((error) => error.includes(fixture.expected_error_contains))) {
        failures.push(`${label} expected an error containing ${fixture.expected_error_contains}, got: ${errors.join('; ')}`);
      }
    }
  });

  const validPassFixture = data.fixtures.find((fixture) => fixture?.id === 'scorecard.valid_pass');
  if (validPassFixture?.scorecard) {
    validateScorecardSemanticNegativeMutations(validPassFixture.scorecard);
  } else {
    failures.push(`${relativePath} missing scorecard.valid_pass fixture for semantic negative mutations`);
  }

  if (tryParseJsonCompatibleContent('# invalid scorecard\nschema: harness/agent-scorecard/v1\nreview:\n  decision: [pass') !== null) {
    failures.push('scorecard parser accepted malformed YAML without a JSON-compatible body');
  }
}

function walkScorecardFiles(dir) {
  if (!fs.existsSync(dir)) {
    return [];
  }
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const entryPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      return walkScorecardFiles(entryPath);
    }
    if (entry.isFile() && /\.(ya?ml|json|md)$/.test(entry.name)) {
      return [entryPath];
    }
    return [];
  });
}

function validateCliScorecards() {
  const paths = new Set();
  for (const inputPath of cliOptions.scorecardPaths) {
    if (!nonEmptyString(inputPath)) {
      failures.push('--scorecard requires a path');
      continue;
    }
    paths.add(resolveInputPath(inputPath));
  }
  for (const inputDir of cliOptions.scorecardDirs) {
    if (!nonEmptyString(inputDir)) {
      failures.push('--scorecard-dir requires a path');
      continue;
    }
    const resolved = resolveInputPath(inputDir);
    if (!fs.existsSync(resolved) || !fs.statSync(resolved).isDirectory()) {
      failures.push(`missing scorecard directory: ${labelForPath(inputDir)}`);
      continue;
    }
    const files = walkScorecardFiles(resolved);
    if (files.length === 0) {
      failures.push(`scorecard directory contains no scorecard-like files: ${labelForPath(inputDir)}`);
    }
    files.forEach((filePath) => paths.add(filePath));
  }
  for (const scorecardPath of paths) {
    const parsed = parseJsonCompatiblePath(scorecardPath, 'scorecard');
    if (!parsed) {
      continue;
    }
    failures.push(...validateScorecardData(parsed.data, `scorecard ${parsed.label}`));
  }
}

function buildBlockingScorecardFromNegativeFixture(fixture, rubric) {
  const scores = rubric.dimensions.map((dimension) => ({
    dimension: dimension.id,
    score: dimension.id === fixture.expected_blocking_dimension ? 2 : 4,
    evidence: dimension.id === fixture.expected_blocking_dimension
      ? `Blocking fixture evidence covers ${dimension.id} and ${fixture.expected_blocker_terms.join(', ')}.`
      : `Non-blocking fixture evidence covers ${dimension.id} and ${dimension.evidence_required?.[0] || dimension.name}.`,
    notes: dimension.id === fixture.expected_blocking_dimension
      ? 'Below the required blocking threshold.'
      : 'Not the fixture blocker.',
  }));
  const scoreByDimension = new Map(scores.map((score) => [score.dimension, score.score]));
  const overallScore = weightedOverallScore(rubric.dimensions, scoreByDimension) ?? 2;

  return {
    schema: 'harness/agent-scorecard/v1',
    agent: {
      id: fixture.agent_id,
      name: agentById.get(fixture.agent_id)?.displayName || fixture.agent_id,
    },
    review: {
      mode: 'review',
      task: fixture.task_text,
      reviewed_at_utc: '2026-01-01T00:00:00Z',
      decision: fixture.expected_decision,
      confidence: 'high',
      critical_blocker_present: true,
      overall_score: overallScore,
    },
    evidence: {
      sources: fixture.changed_paths.map((changedPath) => ({
        path: changedPath,
        kind: 'fixture-path',
        note: `Negative fixture evidence for ${fixture.rubric_negative_fixture}.`,
      })),
      gaps: [`Unresolved blocker: ${fixture.expected_blocker_terms.join(', ')}.`],
    },
    findings: {
      critical: [`${fixture.rubric_negative_fixture} must block: ${fixture.expected_blocker_terms.join(', ')}.`],
      high: [],
      medium: [],
      low: [],
    },
    scores,
    delegation_requests: [],
    required_follow_up: [`Resolve ${fixture.rubric_negative_fixture} before passing review.`],
    quality_gate: {
      blocks_when: [
        'critical_blocker_present is true',
        'any required score is below 3',
        'decision is delegate and delegated review is missing',
      ],
    },
  };
}

function validateNegativeReviewFixtures() {
  const relativePath = 'scripts/01.harness/agents/validate-harness-agents/fixtures/negative-review-fixtures.yml';
  const parsed = parseJsonCompatibleFile(relativePath, 'negative review fixture');
  const routingConfig = parseWorkflowJsonBlock(
    '.agentic/01.harness/workflows/run-agent-review.md',
    'review-agent-routing',
    'harness/review-agent-routing/v1',
  );
  if (!parsed) {
    return;
  }
  const data = parsed.data;
  if (data.schema !== 'harness/review-agent-negative-fixtures/v1') {
    failures.push(`${relativePath}.schema must equal harness/review-agent-negative-fixtures/v1`);
  }
  if (!Number.isInteger(data.version) || data.version < 1) {
    failures.push(`${relativePath}.version must be a positive integer`);
  }
  if (!Array.isArray(data.fixtures) || data.fixtures.length < 20) {
    failures.push(`${relativePath}.fixtures must contain executable negative fixtures across all agents`);
    return;
  }

  const fixtureByAgentAndLabel = new Map();
  data.fixtures.forEach((fixture, index) => {
    const label = `negative review fixture[${index}]`;
    if (!isPlainObject(fixture)) {
      failures.push(`${label} must be an object`);
      return;
    }
    if (!nonEmptyString(fixture.id)) {
      failures.push(`${label}.id must be a non-empty string`);
    }
    if (!agentById.has(fixture.agent_id)) {
      failures.push(`${label}.agent_id must be a known agent id`);
      return;
    }
    if (!nonEmptyString(fixture.rubric_negative_fixture)) {
      failures.push(`${label}.rubric_negative_fixture must be a non-empty string`);
    }
    requireNonEmptyString(failures, `${label}.task_text`, fixture.task_text);
    requireStringArray(failures, `${label}.changed_paths`, fixture.changed_paths, 1);
    if (fixture.expected_decision !== 'block') {
      failures.push(`${label}.expected_decision must be block`);
    }
    if (!nonEmptyString(fixture.expected_blocking_dimension)) {
      failures.push(`${label}.expected_blocking_dimension must be a non-empty string`);
    }
    requireStringArray(failures, `${label}.expected_blocker_terms`, fixture.expected_blocker_terms, 2);

    const rubric = rubricDataForAgent(fixture.agent_id);
    if (!rubric) {
      return;
    }
    if (!rubric.negative_fixtures.includes(fixture.rubric_negative_fixture)) {
      failures.push(`${label}.rubric_negative_fixture is not declared in ${fixture.agent_id} rubric`);
    }
    if (!rubric.dimensions.some((dimension) => dimension.id === fixture.expected_blocking_dimension)) {
      failures.push(`${label}.expected_blocking_dimension is not a dimension for ${fixture.agent_id}`);
    }
    const selectedAgents = selectedAgentsForFixture({
      title: fixture.id,
      task_text: fixture.task_text,
      changed_paths: fixture.changed_paths,
    }, routingConfig);
    if (!selectedAgents.includes(fixture.agent_id)) {
      failures.push(`${label} routes to [${selectedAgents.join(', ')}], but must include ${fixture.agent_id}`);
    }

    const key = `${fixture.agent_id}:${fixture.rubric_negative_fixture}`;
    if (fixtureByAgentAndLabel.has(key)) {
      failures.push(`${label} duplicates ${key}`);
    } else {
      fixtureByAgentAndLabel.set(key, fixture);
    }

    const scorecard = buildBlockingScorecardFromNegativeFixture(fixture, rubric);
    const scorecardErrors = validateScorecardData(scorecard, `${label}.synthetic_scorecard`);
    if (scorecardErrors.length > 0) {
      failures.push(...scorecardErrors);
    }
  });

  for (const agent of agents) {
    const rubric = rubricDataForAgent(agent.agentId);
    for (const fixtureName of rubric?.negative_fixtures || []) {
      const key = `${agent.agentId}:${fixtureName}`;
      if (!fixtureByAgentAndLabel.has(key)) {
        failures.push(`${relativePath} missing executable negative fixture for ${key}`);
      }
    }
  }
}

function validateTemplates() {
  const report = read('.agentic/01.harness/templates/agent-review-report.md');
  const template = parseJsonCompatibleFile('.agentic/01.harness/templates/agent-scorecard.yml', 'scorecard template');
  const schema = parseJsonCompatibleFile('.agentic/01.harness/templates/agent-scorecard.schema.yml', 'scorecard schema');
  const exampleTemplate = parseJsonCompatibleFile('.agentic/01.harness/templates/agent-scorecard.example.yml', 'scorecard example template');
  const cfoExample = parseJsonCompatibleFile('.agentic/01.harness/templates/examples/cfo-token-efficiency-scorecard.yml', 'CFO scorecard example');

  for (const text of [
    'Critical blocker present',
    'Evidence Reviewed',
    'Delegation Requests',
    'Evidence Gaps',
  ]) {
    requireText('agent-review-report template', report, text);
  }

  if (template) {
    if (template.data.schema !== 'harness/agent-scorecard-template/v1') {
      failures.push('agent-scorecard template schema must equal harness/agent-scorecard-template/v1');
    }
    if (template.data.scorecard_schema !== 'harness/agent-scorecard/v1') {
      failures.push('agent-scorecard template must point to harness/agent-scorecard/v1');
    }
    requireStringArray(failures, 'agent-scorecard template.required_top_level_fields', template.data.required_top_level_fields, 8);
    requireStringArray(failures, 'agent-scorecard template.score_rules', template.data.score_rules, 5);
    requireStringArray(failures, 'agent-scorecard template.examples', template.data.examples, 1);
  }
  if (schema) {
    if (schema.data.schema !== 'harness/agent-scorecard-schema/v1') {
      failures.push('agent-scorecard schema file must equal harness/agent-scorecard-schema/v1');
    }
    if (schema.data.quality_gate?.overall_score_rule !== 'weighted_average_of_selected_agent_rubric_dimensions') {
      failures.push('agent-scorecard schema must require weighted overall score');
    }
  }
  if (exampleTemplate) {
    if (exampleTemplate.data.schema !== 'harness/agent-scorecard-example-template/v1') {
      failures.push('agent-scorecard example template schema must equal harness/agent-scorecard-example-template/v1');
    }
    requireStringArray(failures, 'agent-scorecard example template.instructions', exampleTemplate.data.instructions, 3);
  }
  if (cfoExample) {
    failures.push(...validateScorecardData(cfoExample.data, 'CFO scorecard example'));
    const blocksWhen = cfoExample.data.quality_gate?.blocks_when || [];
    for (const text of [
      'critical_blocker_present is true',
      'any required score is below 3',
      'decision is delegate and delegated review is missing',
    ]) {
      if (!blocksWhen.includes(text)) {
        failures.push(`CFO scorecard example quality_gate.blocks_when missing ${text}`);
      }
    }
  }
}

function validateWorkflows() {
  const single = read('.agentic/01.harness/workflows/run-agent-review.md');
  const board = read('.agentic/01.harness/workflows/run-review-board.md');
  const backendImplementation = read('.agentic/01.harness/workflows/implement-backend-architecture-guideline.md');

  requireText('run-agent-review workflow', single, 'templates/agent-review-report.md');
  requireText('run-agent-review workflow', single, 'templates/agent-scorecard.yml');
  requireText('run-agent-review workflow', single, 'Select the narrowest responsible agent');
  requireText('run-agent-review workflow', single, '<!-- review-agent-routing:start -->');
  requireText('run-agent-review workflow', single, '"schema": "harness/review-agent-routing/v1"');
  requireText('run-review-board workflow', board, 'Do not invite every');
  requireText('run-review-board workflow', board, 'Critical findings block the board');
  requireText('run-review-board workflow', board, '<!-- review-board-routing:start -->');
  requireText('run-review-board workflow', board, '"schema": "harness/review-board-routing/v1"');
  requireText('run-review-board workflow', board, '<!-- review-board-composition:start -->');
  requireText('run-review-board workflow', board, '"schema": "harness/review-board-composition/v1"');
  requireText('run-review-board workflow', board, 'only when that lane can independently block the outcome');
  requireText('run-review-board workflow', board, 'Hosted RAG Service Deployment');
  requireText('backend architecture implementation workflow', backendImplementation, 'Senior Back-End Architect is explicitly invoked');
  requireText('backend architecture implementation workflow', backendImplementation, 'Implementation mode is limited to architecture-guideline artifacts');
  requireText('backend architecture implementation workflow', backendImplementation, 'It may not edit');
  requireText('backend architecture implementation workflow', backendImplementation, 'product or backend runtime code');
}

function validateManifestAndBackendMode() {
  const manifest = read('.agentic/01.harness/manifest.yml');
  const readme = read('.agentic/01.harness/README.md');
  const backendAgent = read('.agentic/01.harness/agents/senior-backend-architect.md');
  const agentContract = read('.agentic/01.harness/standards/agent-contracts.md');

  requireText('harness manifest', manifest, 'title: Harness governance operating pack');
  requireText('harness manifest', manifest, 'review_agent_capabilities:');
  requireText('harness manifest', manifest, 'review_agent_fixtures: scripts/01.harness/agents/validate-harness-agents/fixtures');
  requireText('harness manifest', manifest, 'templates/agent-scorecard.schema.yml');
  requireText('harness manifest', manifest, 'templates/agent-scorecard.example.yml');
  requireText('harness manifest', manifest, 'templates/examples/cfo-token-efficiency-scorecard.yml');
  requireText('harness manifest', manifest, 'fixtures/scorecard-fixtures.yml');
  requireText('harness manifest', manifest, 'fixtures/negative-review-fixtures.yml');
  requireText('harness manifest', manifest, 'Create executable harness validators, gates, metrics, or eval runners only when');
  requireText('harness manifest', manifest, 'Implementation-agent mode requires an explicit workflow');
  requireText('harness manifest', manifest, 'Review agents may not edit files during review mode.');
  forbidText('harness manifest', manifest, 'title: Architecture rulebook operating pack');
  forbidText('harness manifest', manifest, 'without building runtime harness code');
  forbidText('harness manifest', manifest, 'Do not build the full agentic harness.');
  forbidText('harness manifest', manifest, 'Do not create eval runners.');

  requireText('harness README', readme, '## Harness Governance Operating Pack');
  requireText('harness README', readme, 'workflows/implement-backend-architecture-guideline.md');
  requireText('harness README', readme, 'deterministic validators are also governed');
  requireText('harness README', readme, 'templates/agent-scorecard.schema.yml');
  requireText('harness README', readme, 'templates/examples/cfo-token-efficiency-scorecard.yml');

  requireText('Senior Back-End Architect agent', backendAgent, '## Implementation Mode');
  requireText('Senior Back-End Architect agent', backendAgent, 'Default mode is review mode.');
  requireText('Senior Back-End Architect agent', backendAgent, 'workflows/implement-backend-architecture-guideline.md');
  requireText('Senior Back-End Architect agent', backendAgent, 'review mode or implementation mode');
  requireText('agent contract standard', agentContract, 'Implementation-agent authority must name the implementation workflow');
  requireText('agent contract standard', agentContract, 'A review-mode decision does not imply write authority.');
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

  if (parsed.schema !== 'harness/cfo-token-comparison/v3.1') {
    failures.push(`CFO fixture expected schema v3.1, got ${parsed.schema}`);
  }
  if (parsed.similar_tasks.count !== 3) {
    failures.push(`CFO fixture expected 3 similar tasks, got ${parsed.similar_tasks.count}`);
  }
  if (parsed.similarity_basis.method !== 'weighted_jaccard_task_workflow_paths_agents') {
    failures.push(`CFO fixture expected weighted similarity, got ${parsed.similarity_basis.method}`);
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
  if (parsed.trend.sample_size !== 3) {
    failures.push(`CFO fixture expected trend sample size 3, got ${parsed.trend.sample_size}`);
  }
  if (parsed.trend.confidence.level !== 'medium') {
    failures.push(`CFO fixture expected medium trend confidence, got ${parsed.trend.confidence.level}`);
  }
  if (!parsed.cost_trend || parsed.cost_trend.direction !== 'up') {
    failures.push(`CFO fixture expected upward cost trend, got ${parsed.cost_trend?.direction}`);
  }
  if (!parsed.cost_trend || parsed.cost_trend.sample_size !== 3) {
    failures.push(`CFO fixture expected cost trend sample size 3, got ${parsed.cost_trend?.sample_size}`);
  }
  if (!parsed.cost_per_query_trend || parsed.cost_per_query_trend.direction !== 'up') {
    failures.push(`CFO fixture expected upward cost-per-query trend, got ${parsed.cost_per_query_trend?.direction}`);
  }
  if (!parsed.cost_per_query_trend || parsed.cost_per_query_trend.sample_size !== 3) {
    failures.push(`CFO fixture expected cost-per-query trend sample size 3, got ${parsed.cost_per_query_trend?.sample_size}`);
  }
  if (parsed.date_range.day_span !== 2) {
    failures.push(`CFO fixture expected date range day_span 2, got ${parsed.date_range.day_span}`);
  }
  if (!parsed.current_task || parsed.current_task.delta_from_median !== -20) {
    failures.push('CFO fixture expected current task delta from median to equal -20');
  }
  if (!parsed.current_task || parsed.current_task.cost_usd !== 0.018) {
    failures.push('CFO fixture expected current task cost_usd to equal 0.018');
  }
  if (!parsed.current_task || parsed.current_task.cost_per_query_usd !== 0.0018) {
    failures.push('CFO fixture expected current task cost_per_query_usd to equal 0.0018');
  }
  if (!parsed.cost_statistics || parsed.cost_statistics.estimated_chat_cost_usd.median !== 0.02) {
    failures.push('CFO fixture expected historical cost median to equal 0.02');
  }
  if (!parsed.cost_statistics || parsed.cost_statistics.estimated_cost_per_query_usd.median !== 0.002) {
    failures.push('CFO fixture expected historical cost-per-query median to equal 0.002');
  }
  if (!parsed.pricing_basis || parsed.pricing_basis.source !== 'fixture token and cost basis') {
    failures.push('CFO fixture expected pricing basis source to be preserved');
  }
  if (!parsed.pricing_basis || parsed.pricing_basis.mode !== 'token_and_cost_when_available') {
    failures.push('CFO fixture expected token_and_cost_when_available pricing mode');
  }
  if (!parsed.pricing_basis || parsed.pricing_basis.historical_cost_samples !== 3) {
    failures.push('CFO fixture expected 3 historical cost samples');
  }
  if (!parsed.similar_tasks.sessions.every((session) => session.cost_basis_fields?.model === 'fixture-model')) {
    failures.push('CFO fixture expected model cost-basis fields on every similar session');
  }
  if (!parsed.delegation || parsed.delegation.required !== true) {
    failures.push('CFO fixture expected delegation to be required for upward token, cost, or cost-per-query trend');
  }
  for (const reason of ['trend direction is up', 'cost trend direction is up', 'cost per query trend direction is up']) {
    if (!parsed.delegation?.reasons?.includes(reason)) {
      failures.push(`CFO fixture expected delegation reason: ${reason}`);
    }
  }
  if (!parsed.delegation.delegate_to.includes('harness.agents.senior-prompt-engineer')) {
    failures.push('CFO fixture expected delegation to Senior Prompt Engineer for workflow token trend');
  }
  if (parsed.delegation.delegate_to.includes('harness.agents.ux-ui-engineer')) {
    failures.push('CFO fixture must not delegate to UX/UI for bare chat workflow text without a human-facing interface signal');
  }
}

validateAgentFiles();
validateRubrics();
validateUseCases();
validateUseCaseFixtures();
validateScorecardFixtures();
validateCliScorecards();
validateNegativeReviewFixtures();
validateTemplates();
validateWorkflows();
validateManifestAndBackendMode();
validateCfoFixture();

if (failures.length > 0) {
  for (const failure of failures) {
    console.error(`ERROR: ${failure}`);
  }
  process.exit(1);
}

console.log('Harness review agents valid.');
