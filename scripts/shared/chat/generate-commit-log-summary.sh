#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Generate on-demand aggregate summaries from chat session logs.
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/workflows/chat-reporting.md
#     - scripts/chat/generate-commit-log-summary.sh
#   effects: read-only, writes-files

usage() {
  cat <<'EOF'
Usage:
  generate-commit-log-summary.sh [--print|--output <path>]

Prints an aggregate summary from individual chat session logs.
Use --output to write the summary to an explicit on-demand artifact path.
Do not write commitLogs/README.md.
EOF
}

OUTPUT_PATH=""
MODE="print"

while [ $# -gt 0 ]; do
  case "$1" in
    --print)
      MODE="print"
      shift
      ;;
    --output)
      if [ $# -lt 2 ]; then
        usage >&2
        exit 2
      fi
      MODE="output"
      OUTPUT_PATH="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
done

if [ "$OUTPUT_PATH" = "commitLogs/README.md" ]; then
  echo "ERROR: commitLogs/README.md is not maintained as an aggregate artifact." >&2
  echo "Write on-demand summaries somewhere else, such as /tmp/chat-summary.md." >&2
  exit 1
fi

node - "$MODE" "$OUTPUT_PATH" <<'NODE'
const fs = require('fs');
const path = require('path');

const mode = process.argv[2];
const outputPath = process.argv[3];
const root = 'commitLogs';
const retiredOutputPath = path.join(root, 'README.md');

function walk(dir) {
  if (!fs.existsSync(dir)) {
    return [];
  }

  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const entryPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      return walk(entryPath);
    }
    if (entry.isFile() && entry.name === 'README.md' && entryPath !== retiredOutputPath) {
      return [entryPath];
    }
    return [];
  });
}

function metadata(content) {
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

function parseDurationSeconds(value) {
  const match = String(value || '').match(/(\d+)s\b/);
  return match ? Number(match[1]) : null;
}

function parseTokenCount(value) {
  const match = String(value || '').match(/^(\d+)\b/);
  return match ? Number(match[1]) : null;
}

function parseUsdCost(value) {
  const match = String(value || '').match(/^USD\s+(\d+(?:\.\d+)?)\b/);
  return match ? Number(match[1]) : null;
}

function mean(values) {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function standardDeviation(values, average) {
  const variance = values.reduce((sum, value) => {
    return sum + ((value - average) ** 2);
  }, 0) / values.length;
  return Math.sqrt(variance);
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

function metricStats(values) {
  const valid = values.filter((value) => Number.isFinite(value));
  if (valid.length === 0) {
    return {
      validCount: 0,
      includedCount: 0,
      outlierCount: 0,
      total: null,
      min: null,
      max: null,
      average: null,
      q1: null,
      median: null,
      q3: null,
    };
  }

  const average = mean(valid);
  const sd = standardDeviation(valid, average);
  const included = sd === 0
    ? valid
    : valid.filter((value) => Math.abs(value - average) <= 3 * sd);
  const sorted = [...included].sort((a, b) => a - b);

  return {
    validCount: valid.length,
    includedCount: included.length,
    outlierCount: valid.length - included.length,
    total: included.reduce((sum, value) => sum + value, 0),
    min: sorted[0],
    max: sorted[sorted.length - 1],
    average: mean(included),
    q1: quantile(sorted, 0.25),
    median: quantile(sorted, 0.5),
    q3: quantile(sorted, 0.75),
  };
}

function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return 'n/a';
  }
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}

function formatUsd(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return 'n/a';
  }
  if (value > 0 && value < 1) {
    return `USD ${value.toFixed(4)}`;
  }
  return `USD ${value.toFixed(2)}`;
}

function formatDuration(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return 'n/a';
  }

  const rounded = Math.round(value);
  const days = Math.floor(rounded / 86400);
  const hours = Math.floor((rounded % 86400) / 3600);
  const minutes = Math.floor((rounded % 3600) / 60);
  const seconds = rounded % 60;

  return `${rounded}s (${String(days).padStart(2, '0')}:` +
    `${String(hours).padStart(2, '0')}:` +
    `${String(minutes).padStart(2, '0')}:` +
    `${String(seconds).padStart(2, '0')})`;
}

function metricTable(stats, formatter) {
  return [
    '| Metric | Value |',
    '| --- | ---: |',
    `| Valid chats | ${stats.validCount} |`,
    `| Included chats | ${stats.includedCount} |`,
    `| Outliers excluded | ${stats.outlierCount} |`,
    `| Total | ${formatter(stats.total)} |`,
    `| Min | ${formatter(stats.min)} |`,
    `| Max | ${formatter(stats.max)} |`,
    `| Average | ${formatter(stats.average)} |`,
    `| Q1 | ${formatter(stats.q1)} |`,
    `| Median | ${formatter(stats.median)} |`,
    `| Q3 | ${formatter(stats.q3)} |`,
  ].join('\n');
}

const logs = walk(root).sort();
const records = logs.map((filePath) => {
  const content = fs.readFileSync(filePath, 'utf8');
  const data = metadata(content);
  return {
    filePath,
    id: data.id || path.basename(path.dirname(filePath)),
    durationSeconds: parseDurationSeconds(data.chat_duration),
    tokens: parseTokenCount(data.estimated_chat_tokens),
    cost: parseUsdCost(data.estimated_chat_cost),
  };
});

const durationStats = metricStats(records.map((record) => record.durationSeconds));
const tokenStats = metricStats(records.map((record) => record.tokens));
const costStats = metricStats(records.map((record) => record.cost));

const lines = [
  '# Commit Log Summary',
  '',
  `Total chats: ${records.length}`,
  '',
  'Outliers are values more than 3 standard deviations from the mean for each metric.',
  '',
  '## Chat Duration',
  '',
  metricTable(durationStats, formatDuration),
  '',
  '## Estimated Chat Tokens',
  '',
  metricTable(tokenStats, formatNumber),
  '',
  '## Estimated Chat Cost',
  '',
  metricTable(costStats, formatUsd),
  '',
];

const output = lines.join('\n');

if (mode === 'print') {
  process.stdout.write(output);
  process.exit(0);
}

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, output);
console.log(`Wrote ${outputPath}`);
NODE
