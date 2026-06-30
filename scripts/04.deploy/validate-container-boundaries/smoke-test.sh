#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.validate-container-boundaries.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - agentic
#   - sre
#   - security
#   kind: script
#   purpose: Smoke test the read-only container boundary validator.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#     - entity-builder
#     - design-system-builder
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.script.validate-container-boundaries
#     path: scripts/04.deploy/validate-container-boundaries/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

mkdir -p "$TMP_ROOT/valid/infra/04.deploy/02.rag-rulebook/image"
cat > "$TMP_ROOT/valid/infra/04.deploy/02.rag-rulebook/image/Dockerfile" <<'EOF'
FROM node:22-bookworm-slim
EOF
cat > "$TMP_ROOT/valid/infra/04.deploy/02.rag-rulebook/image/README.md" <<'EOF'
# Image
EOF
cat > "$TMP_ROOT/valid/infra/04.deploy/02.rag-rulebook/image/.dockerignore" <<'EOF'
.git
.cache
commitLogs
.env
*.env
secrets
credentials
.aws
*.pem
*.key
id_rsa
*.log
logs
tmp
temp
*.tmp
node_modules
.venv
vendor
__pycache__
.cache/02.rag-rulebook
runtime-cache
local-runtime
EOF

bash scripts/04.deploy/validate-container-boundaries/script.sh --root "$TMP_ROOT/valid" --json \
  > "$TMP_ROOT/valid.json"
python3 - "$TMP_ROOT/valid.json" <<'PY'
import json
import sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
assert data["ok"] is True
assert data["counts"]["dockerfiles"] == 1
assert data["counts"]["errors"] == 0
PY

mkdir -p "$TMP_ROOT/bad/apps/api"
cat > "$TMP_ROOT/bad/apps/api/Dockerfile" <<'EOF'
FROM node:22
EOF

if bash scripts/04.deploy/validate-container-boundaries/script.sh --root "$TMP_ROOT/bad" --json \
  > "$TMP_ROOT/bad.json"; then
  fail "validator accepted Dockerfile outside infra image boundary"
fi
grep -q "outside the governed infra image boundary" "$TMP_ROOT/bad.json" \
  || fail "bad report did not explain boundary violation"

mkdir -p "$TMP_ROOT/missing/infra/04.deploy/02.rag-rulebook/image"
cat > "$TMP_ROOT/missing/infra/04.deploy/02.rag-rulebook/image/Dockerfile" <<'EOF'
FROM node:22
EOF

if bash scripts/04.deploy/validate-container-boundaries/script.sh --root "$TMP_ROOT/missing" --json \
  > "$TMP_ROOT/missing.json"; then
  fail "validator accepted Dockerfile missing README and .dockerignore"
fi
grep -q "missing sibling README" "$TMP_ROOT/missing.json" \
  || fail "missing report did not mention README"
grep -q "missing an effective ignore file" "$TMP_ROOT/missing.json" \
  || fail "missing report did not mention effective ignore file"

if bash scripts/04.deploy/validate-container-boundaries/script.sh --root "$TMP_ROOT/absent" --json \
  > "$TMP_ROOT/absent.json"; then
  fail "validator accepted missing root"
fi
grep -q "Validation root does not exist" "$TMP_ROOT/absent.json" \
  || fail "absent-root report did not mention missing root"

mkdir -p "$TMP_ROOT/weak/infra/04.deploy/02.rag-rulebook/image"
cat > "$TMP_ROOT/weak/infra/04.deploy/02.rag-rulebook/image/Dockerfile" <<'EOF'
FROM node:22
EOF
cat > "$TMP_ROOT/weak/infra/04.deploy/02.rag-rulebook/image/README.md" <<'EOF'
# Image
EOF
cat > "$TMP_ROOT/weak/infra/04.deploy/02.rag-rulebook/image/.dockerignore" <<'EOF'
.git
.cache
EOF

if bash scripts/04.deploy/validate-container-boundaries/script.sh --root "$TMP_ROOT/weak" --json \
  > "$TMP_ROOT/weak.json"; then
  fail "validator accepted weak .dockerignore coverage"
fi
grep -q "coverage is too weak" "$TMP_ROOT/weak.json" \
  || fail "weak report did not mention weak coverage"
grep -q "credentials and secrets" "$TMP_ROOT/weak.json" \
  || fail "weak report did not mention missing secret coverage"

mkdir -p "$TMP_ROOT/root-context/infra/04.deploy/02.rag-rulebook/image"
cat > "$TMP_ROOT/root-context/infra/04.deploy/02.rag-rulebook/image/Dockerfile" <<'EOF'
FROM node:22
EOF
cat > "$TMP_ROOT/root-context/infra/04.deploy/02.rag-rulebook/image/README.md" <<'EOF'
# Image
EOF
cat > "$TMP_ROOT/root-context/infra/04.deploy/02.rag-rulebook/image/Dockerfile.dockerignore" <<'EOF'
.git
.cache
commitLogs
.env
*.env
secrets
credentials
.aws
*.pem
*.key
id_rsa
*.log
logs
tmp
temp
*.tmp
node_modules
.venv
vendor
__pycache__
.cache/02.rag-rulebook
runtime-cache
local-runtime
EOF
cat > "$TMP_ROOT/root-context/.dockerignore" <<'EOF'
.git
EOF

if bash scripts/04.deploy/validate-container-boundaries/script.sh --root "$TMP_ROOT/root-context" --json \
  > "$TMP_ROOT/root-context.json"; then
  fail "validator accepted weak repo-root .dockerignore coverage"
fi
grep -q ".dockerignore coverage is too weak" "$TMP_ROOT/root-context.json" \
  || fail "root-context report did not mention weak repo-root ignore coverage"

echo "Container boundary validator smoke test passed."
