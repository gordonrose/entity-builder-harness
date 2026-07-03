#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: harness.script.metrics.compare-task-token-consumption.impl
//   version: 1
//   status: active
//   layer: 01.harness
//   domain: governance.agents
//   disciplines:
//     - agentic
//   kind: script
//   purpose: Implement task-similarity token statistics for CFO review.
//   portability:
//     class: required
//     targets:
//       - llm-workbench
//       - entity-builder
//       - design-system-builder
//   effects:
//     - read-only
//   used_by:
//     - id: harness.script.metrics.compare-task-token-consumption
//       path: scripts/01.harness/metrics/compare-task-token-consumption/script.sh

const fs = require('fs');
const path = require('path');

const STOP_WORDS = new Set([
  'a', 'an', 'and', 'are', 'as', 'be', 'by', 'can', 'for', 'from', 'how',
  'i', 'in', 'is', 'it', 'my', 'of', 'on', 'or', 'our', 'please', 'that',
  'the', 'this', 'to', 'we', 'with', 'would', 'you',
]);

function usage(exitCode) {
  const stream = exitCode === 0 ? process.stdout : process.stderr;
  stream.write(`Usage:
  script.sh --task-query <text> [--current-tokens <count>] [--commit-log-root <path>] [--min-score <number>] [--limit <count>] [--workflow <id>] [--changed-path <path>] [--agent <agent-id>] [--pricing-basis <text>]

Emits JSON token-consumption statistics for sessions similar to the task query.
`);
  process.exit(exitCode);
}

function parseArgs(argv) {
  const options = {
    changedPaths: [],
    commitLogRoot: 'commitLogs',
    currentTokens: null,
    limit: 50,
    minScore: 0.12,
    pricingBasis: 'token_only_no_model_pricing_applied',
    requestedAgents: [],
    taskQuery: '',
    workflow: '',
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => {
      index += 1;
      if (index >= argv.length || argv[index] === '') {
        usage(2);
      }
      return argv[index];
    };

    if (arg === '--help' || arg === '-h') {
      usage(0);
    } else if (arg === '--task-query') {
      options.taskQuery = next();
    } else if (arg === '--current-tokens') {
      options.currentTokens = parseInteger(next(), '--current-tokens');
    } else if (arg === '--workflow') {
      options.workflow = next();
    } else if (arg === '--changed-path') {
      options.changedPaths.push(next());
    } else if (arg === '--agent') {
      options.requestedAgents.push(next());
    } else if (arg === '--pricing-basis') {
      options.pricingBasis = next();
    } else if (arg === '--commit-log-root') {
      options.commitLogRoot = next();
    } else if (arg === '--min-score') {
      options.minScore = parseNumber(next(), '--min-score');
    } else if (arg === '--limit') {
      options.limit = parseInteger(next(), '--limit');
    } else {
      usage(2);
    }
  }

  if (!options.taskQuery.trim()) {
    usage(2);
  }
  if (options.limit < 1) {
    fail('--limit must be greater than zero.');
  }
  if (options.minScore < 0 || options.minScore > 1) {
    fail('--min-score must be between 0 and 1.');
  }

  return options;
}

function parseInteger(value, name) {
  if (!/^\d+$/.test(value)) {
    fail(`${name} must be a non-negative integer.`);
  }
  return Number(value);
}

function parseNumber(value, name) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    fail(`${name} must be a number.`);
  }
  return parsed;
}

function fail(message) {
  console.error(`ERROR: ${message}`);
  process.exit(1);
}

function walkReadmes(dir) {
  if (!fs.existsSync(dir)) {
    return [];
  }

  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const entryPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      return walkReadmes(entryPath);
    }
    if (entry.isFile() && entry.name === 'README.md') {
      return [entryPath];
    }
    return [];
  });
}

function parseMetadata(content) {
  const match = content.match(/<!-- agentic-session\n([\s\S]*?)\n-->/);
  if (!match) {
    return {};
  }

  return Object.fromEntries(
    match[1].split('\n').map((line) => {
      const separator = line.indexOf(':');
      if (separator === -1) {
        return null;
      }
      return [
        line.slice(0, separator).trim(),
        line.slice(separator + 1).trim(),
      ];
    }).filter(Boolean),
  );
}

function parseTokenCount(value) {
  const match = String(value || '').match(/^(\d+)\b/);
  return match ? Number(match[1]) : null;
}

function tokenize(text) {
  return new Set(String(text || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .split(/\s+/)
    .filter((token) => token.length >= 3 && !STOP_WORDS.has(token)));
}

function jaccard(a, b) {
  if (a.size === 0 || b.size === 0) {
    return 0;
  }
  let intersection = 0;
  for (const token of a) {
    if (b.has(token)) {
      intersection += 1;
    }
  }
  const union = new Set([...a, ...b]).size;
  return union === 0 ? 0 : intersection / union;
}

function quantile(sortedValues, q) {
  if (sortedValues.length === 0) {
    return null;
  }
  if (sortedValues.length === 1) {
    return sortedValues[0];
  }

  const position = (sortedValues.length - 1) * q;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  const weight = position - lower;
  return sortedValues[lower] * (1 - weight) + sortedValues[upper] * weight;
}

function mean(values) {
  if (values.length === 0) {
    return null;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function stats(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return {
    count: sorted.length,
    min: sorted[0] ?? null,
    max: sorted[sorted.length - 1] ?? null,
    mean: mean(sorted),
    median: quantile(sorted, 0.5),
    q1: quantile(sorted, 0.25),
    q3: quantile(sorted, 0.75),
  };
}

function linearSlope(points) {
  if (points.length < 2) {
    return null;
  }

  const xs = points.map((_, index) => index + 1);
  const ys = points.map((point) => point.tokens);
  const xMean = mean(xs);
  const yMean = mean(ys);
  let numerator = 0;
  let denominator = 0;

  for (let index = 0; index < points.length; index += 1) {
    numerator += (xs[index] - xMean) * (ys[index] - yMean);
    denominator += (xs[index] - xMean) ** 2;
  }

  return denominator === 0 ? null : numerator / denominator;
}

function trendDirection(slope) {
  if (slope === null) {
    return 'insufficient_data';
  }
  if (Math.abs(slope) < 1) {
    return 'flat';
  }
  return slope < 0 ? 'down' : 'up';
}

function sessionDate(meta, filePath) {
  const raw = meta.latest_commit_at_utc || meta.raised_at_utc || '';
  const parsed = Date.parse(raw);
  if (!Number.isNaN(parsed)) {
    return new Date(parsed).toISOString();
  }
  const match = filePath.match(/commitLogs\/(\d{4})\/([a-z]{3})\/(\d{2})\//);
  if (!match) {
    return '';
  }
  const months = {
    jan: '01', feb: '02', mar: '03', apr: '04', may: '05', jun: '06',
    jul: '07', aug: '08', sep: '09', oct: '10', nov: '11', dec: '12',
  };
  return `${match[1]}-${months[match[2]] || '01'}-${match[3]}T00:00:00.000Z`;
}

function readSessions(root, queryTokens, minScore) {
  return walkReadmes(root).map((filePath) => {
    const content = fs.readFileSync(filePath, 'utf8');
    const meta = parseMetadata(content);
    const task = meta.task || '';
    const tokens = parseTokenCount(meta.estimated_chat_tokens);
    const score = jaccard(queryTokens, tokenize(task));

    return {
      path: filePath,
      id: meta.id || path.basename(path.dirname(filePath)),
      task,
      tokens,
      score,
      raised_at_utc: meta.raised_at_utc || '',
      estimated_chat_cost: meta.estimated_chat_cost || '',
      estimated_chat_cost_basis: meta.estimated_chat_cost_basis || '',
      sort_date: sessionDate(meta, filePath),
    };
  }).filter((session) => session.tokens !== null && session.score >= minScore);
}

function currentComparison(currentTokens, metricStats) {
  if (currentTokens === null || metricStats.count === 0) {
    return null;
  }
  return {
    tokens: currentTokens,
    delta_from_median: metricStats.median === null ? null : currentTokens - metricStats.median,
    ratio_to_median: metricStats.median ? currentTokens / metricStats.median : null,
    above_q3: metricStats.q3 === null ? null : currentTokens > metricStats.q3,
    below_q1: metricStats.q1 === null ? null : currentTokens < metricStats.q1,
    status: currentTokenStatus(currentTokens, metricStats),
  };
}

function currentTokenStatus(currentTokens, metricStats) {
  if (currentTokens === null || metricStats.count === 0) {
    return 'not_available';
  }
  if (metricStats.q3 !== null && currentTokens > metricStats.q3) {
    return 'above_q3';
  }
  if (metricStats.q1 !== null && currentTokens < metricStats.q1) {
    return 'below_q1';
  }
  return 'within_iqr';
}

function dateRange(sessions) {
  const dates = sessions.map((session) => session.sort_date).filter(Boolean).sort();
  if (dates.length === 0) {
    return {
      first_seen_at_utc: null,
      last_seen_at_utc: null,
      day_span: null,
    };
  }
  const first = dates[0];
  const last = dates[dates.length - 1];
  return {
    first_seen_at_utc: first,
    last_seen_at_utc: last,
    day_span: Math.round((Date.parse(last) - Date.parse(first)) / (1000 * 60 * 60 * 24)),
  };
}

function trendConfidence(sessions, slope) {
  const reasons = [];
  if (sessions.length < 3) {
    reasons.push('fewer than 3 comparable sessions');
    return { level: 'low', reasons };
  }
  if (sessions.some((session) => !session.sort_date)) {
    reasons.push('one or more comparable sessions lack dates');
  }
  if (slope === null) {
    reasons.push('slope unavailable');
    return { level: 'low', reasons };
  }
  if (Math.abs(slope) < 1) {
    reasons.push('trend is effectively flat');
  }
  if (sessions.length >= 5 && reasons.length === 0) {
    reasons.push('at least 5 dated comparable sessions');
    return { level: 'high', reasons };
  }
  reasons.push('minimum comparable sample met');
  return { level: reasons.some((reason) => reason.includes('lack dates')) ? 'low' : 'medium', reasons };
}

function inferredDelegationTargets(options, trend, comparison) {
  const text = [
    options.taskQuery,
    options.workflow,
    ...options.changedPaths,
    ...options.requestedAgents,
  ].join(' ').toLowerCase();
  const targets = new Set();

  if (/\b(workflow|prompt|skill|gate|template|schema|retrieval|context|corpus|rulebook|chat-start|commit-gate)\b/.test(text)) {
    targets.add('harness.agents.senior-prompt-engineer');
  }
  if (/\b(deploy|runtime|aws|ecs|ecr|rds|route53|cloudwatch|service|per-query|per request|cloud)\b/.test(text)) {
    targets.add('harness.agents.senior-sre-engineer');
  }
  if (/\b(secret|security|auth|public|exposure|owasp|iso|credential)\b/.test(text)) {
    targets.add('harness.agents.secops-engineer');
  }
  if (/\b(backend|architecture|platform|entity|feature|capability|dependency)\b/.test(text)) {
    targets.add('harness.agents.senior-backend-architect');
  }
  if (/\b(ux|ui|cli|human|operator|chat|fallback|blocked response|accessibility|wcag)\b/.test(text)) {
    targets.add('harness.agents.ux-ui-engineer');
  }
  if (targets.size === 0 && (trend.direction === 'up' || trend.direction === 'flat' || comparison?.above_q3)) {
    targets.add('harness.agents.senior-prompt-engineer');
  }

  return [...targets].sort();
}

function delegationDecision(options, metricStats, trend, comparison) {
  const reasons = [];
  if (metricStats.count === 0) {
    return {
      required: false,
      decision: 'not_applicable',
      reasons: ['no comparable sessions were found'],
      delegate_to: [],
      blocking_question: '',
    };
  }
  if (metricStats.count < 3) {
    reasons.push('sample size below trend threshold');
  }
  if (metricStats.count >= 3 && trend.direction !== 'down') {
    reasons.push(`trend direction is ${trend.direction}`);
  }
  if (comparison?.above_q3) {
    reasons.push('current task is above historical Q3');
  }

  const required = reasons.some((reason) => !reason.includes('sample size below'));
  const delegateTo = inferredDelegationTargets(options, trend, comparison);
  return {
    required,
    decision: required ? 'delegate' : 'pass_with_notes',
    reasons,
    delegate_to: required ? delegateTo : [],
    blocking_question: required
      ? 'Identify safe token reductions for the suspected cost driver without weakening required evidence, security, reliability, architecture, UX, or workflow flexibility.'
      : '',
  };
}

const options = parseArgs(process.argv.slice(2));
const queryTokens = tokenize(options.taskQuery);
const sessions = readSessions(options.commitLogRoot, queryTokens, options.minScore)
  .sort((a, b) => b.score - a.score || a.sort_date.localeCompare(b.sort_date))
  .slice(0, options.limit)
  .sort((a, b) => a.sort_date.localeCompare(b.sort_date));
const tokenValues = sessions.map((session) => session.tokens);
const metricStats = stats(tokenValues);
const slope = linearSlope(sessions);
const trend = {
  method: 'least_squares_by_chronological_similar_session_index',
  sample_size: sessions.length,
  slope_tokens_per_session: slope,
  direction: trendDirection(slope),
  confidence: trendConfidence(sessions, slope),
};
const currentTask = currentComparison(options.currentTokens, metricStats);

const result = {
  schema: 'harness/cfo-token-comparison/v2',
  query: {
    task_query: options.taskQuery,
    workflow: options.workflow || null,
    changed_paths: options.changedPaths,
    requested_agents: options.requestedAgents,
    commit_log_root: options.commitLogRoot,
    min_score: options.minScore,
    limit: options.limit,
    query_terms: [...queryTokens].sort(),
  },
  similarity_basis: {
    method: 'jaccard_task_terms',
    minimum_score: options.minScore,
    limit: options.limit,
    query_terms: [...queryTokens].sort(),
    note: 'Similarity is lexical and should be treated as a candidate set for CFO review, not proof of identical scope.',
  },
  similar_tasks: {
    count: sessions.length,
    sessions: sessions.map((session) => ({
      id: session.id,
      path: session.path,
      task: session.task,
      estimated_chat_tokens: session.tokens,
      estimated_chat_cost: session.estimated_chat_cost,
      estimated_chat_cost_basis: session.estimated_chat_cost_basis,
      similarity_score: Number(session.score.toFixed(4)),
      raised_at_utc: session.raised_at_utc,
    })),
  },
  date_range: dateRange(sessions),
  token_statistics: metricStats,
  trend,
  pricing_basis: {
    mode: 'token_only',
    source: options.pricingBasis,
    note: 'This script compares token counts and preserves historical cost-basis metadata; it does not apply live model pricing.',
  },
  current_task: currentTask,
  delegation: delegationDecision(options, metricStats, trend, currentTask),
};

process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
