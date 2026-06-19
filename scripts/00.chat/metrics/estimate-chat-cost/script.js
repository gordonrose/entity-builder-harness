#!/usr/bin/env node
// agentic-script:
//   owner: 00.chat
//   purpose: Estimate chat cost metadata from an estimated token count.
//   domain: metrics
//   portability: llm-workbench-required
//   used_by:
//     - scripts/shared/git/record-chat-commit.sh
//     - scripts/shared/git/smoke-test-record-chat-commit-metrics.sh
//   effects: read-only

const fs = require('fs');
const path = require('path');

function usage() {
  console.error(`Usage:
  estimate-chat-cost.js <estimated-token-count> [pricing-profile]

Prints estimated_chat_cost and estimated_chat_cost_basis metadata lines.
`);
}

function unavailable(reason) {
  console.log(`estimated_chat_cost: unavailable; ${reason}`);
  console.log(`estimated_chat_cost_basis: unavailable; ${reason}`);
}

function formatUsd(value) {
  if (value > 0 && value < 1) {
    return value.toFixed(4);
  }
  return value.toFixed(2);
}

function findRepoRoot(start) {
  let current = start;
  while (current !== path.dirname(current)) {
    if (fs.existsSync(path.join(current, '.git'))) {
      return current;
    }
    current = path.dirname(current);
  }
  return start;
}

const tokenValue = process.argv[2];
const requestedProfile = process.argv[3] || process.env.CHAT_COST_PROFILE || '';

if (!tokenValue || tokenValue === '-h' || tokenValue === '--help') {
  usage();
  process.exit(tokenValue ? 0 : 2);
}

if (!/^\d+$/.test(tokenValue)) {
  console.error('ERROR: estimated-token-count must be a non-negative integer.');
  process.exit(1);
}

const tokenCount = Number(tokenValue);
const repoRoot = findRepoRoot(process.cwd());
const pricingPath = process.env.CHAT_COST_PRICING_FILE ||
  path.join(repoRoot, '.agentic/harness/data/openai-chat-pricing.json');

if (!fs.existsSync(pricingPath)) {
  unavailable('pricing snapshot not found');
  process.exit(0);
}

let pricing;
try {
  pricing = JSON.parse(fs.readFileSync(pricingPath, 'utf8'));
} catch (error) {
  console.error(`ERROR: failed to parse pricing snapshot: ${pricingPath}`);
  console.error(error.message);
  process.exit(1);
}

const profileName = requestedProfile || pricing.default_profile;
const profile = pricing.profiles && pricing.profiles[profileName];

if (!profile) {
  unavailable(`pricing profile not found: ${profileName || 'none'}`);
  process.exit(0);
}

const rate = Number(profile.estimate_rate_usd_per_1m_tokens);
if (!Number.isFinite(rate) || rate < 0) {
  console.error(`ERROR: invalid estimate_rate_usd_per_1m_tokens for profile: ${profileName}`);
  process.exit(1);
}

const currency = pricing.currency || 'USD';
const cost = (tokenCount / 1000000) * rate;
const source = pricing.source && pricing.source.url ? pricing.source.url : 'unknown';
const retrieved = pricing.source && pricing.source.retrieved_at_utc
  ? pricing.source.retrieved_at_utc
  : 'unknown';

const basis = [
  `profile=${profileName}`,
  `model=${profile.model}`,
  `tier=${profile.tier}`,
  `context=${profile.context}`,
  `rate=${currency} ${rate}/1M tokens`,
  `assumption=${profile.assumption}`,
  `pricing_snapshot=${retrieved}`,
  `source=${source}`,
].join('; ');

console.log(`estimated_chat_cost: ${currency} ${formatUsd(cost)} estimated from estimated_chat_tokens`);
console.log(`estimated_chat_cost_basis: ${basis}`);
