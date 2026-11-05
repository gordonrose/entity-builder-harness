#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.validate-container-boundaries.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-06-30"
#   updated_on: "2026-10-31"
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - agentic
#   - sre
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
#   - writes-files
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
.codex
.agents
.vscode
.idea
.npmrc
.pypirc
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
.codex
.agents
.vscode
.idea
.npmrc
.pypirc
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

mkdir -p "$TMP_ROOT/late-deny/infra/04.deploy/02.rag-rulebook/image"
cat > "$TMP_ROOT/late-deny/infra/04.deploy/02.rag-rulebook/image/Dockerfile" <<'EOF'
FROM node:22
EOF
cat > "$TMP_ROOT/late-deny/infra/04.deploy/02.rag-rulebook/image/README.md" <<'EOF'
# Image
EOF
cat > "$TMP_ROOT/late-deny/infra/04.deploy/02.rag-rulebook/image/Dockerfile.dockerignore" <<'EOF'
*
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
.codex
.agents
.vscode
.idea
.npmrc
.pypirc
!scripts/
!scripts/02.rag-rulebook/
!scripts/02.rag-rulebook/**
EOF

if bash scripts/04.deploy/validate-container-boundaries/script.sh --root "$TMP_ROOT/late-deny" --json \
  > "$TMP_ROOT/late-deny.json"; then
  fail "validator accepted allowlist without late high-risk deny patterns"
fi
grep -q "allowlist can re-include high-risk files" "$TMP_ROOT/late-deny.json" \
  || fail "late-deny report did not mention allowlist re-include risk"

# A declared repo-root context may use its governed shared ignore file.
mkdir -p "$TMP_ROOT/root-fallback/infra/04.deploy/03.product/image/catalog"
cp "$TMP_ROOT/valid/infra/04.deploy/02.rag-rulebook/image/Dockerfile" "$TMP_ROOT/root-fallback/infra/04.deploy/03.product/image/catalog/Dockerfile"
printf '%s\n' '# Image' 'Build context: repository root. Effective ignore: .dockerignore.' > "$TMP_ROOT/root-fallback/infra/04.deploy/03.product/image/catalog/README.md"
cp "$TMP_ROOT/valid/infra/04.deploy/02.rag-rulebook/image/.dockerignore" "$TMP_ROOT/root-fallback/.dockerignore"
bash scripts/04.deploy/validate-container-boundaries/script.sh --root "$TMP_ROOT/root-fallback" --build-context repository-root --json > "$TMP_ROOT/root-fallback.json"
if bash scripts/04.deploy/validate-container-boundaries/script.sh --root "$TMP_ROOT/root-fallback" --build-context image-directory --json > "$TMP_ROOT/root-fallback-wrong-context.json"; then
  fail "validator accepted repository-root ignore for an image-directory context"
fi
grep -q 'missing an effective ignore file' "$TMP_ROOT/root-fallback-wrong-context.json" || fail "wrong-context rejection has wrong reason"
printf '%s\n' '.git' > "$TMP_ROOT/root-fallback/.dockerignore"
if bash scripts/04.deploy/validate-container-boundaries/script.sh --root "$TMP_ROOT/root-fallback" --build-context repository-root --json > "$TMP_ROOT/root-fallback-bad.json"; then
  fail "validator accepted ineffective root fallback coverage"
fi
grep -q 'coverage is too weak' "$TMP_ROOT/root-fallback-bad.json" || fail "root fallback failed for an unintended reason"

# Existing capability images use one bounded image subdirectory.
mkdir -p "$TMP_ROOT/capability/infra/04.deploy/03.product/image/catalog"
cp "$TMP_ROOT/valid/infra/04.deploy/02.rag-rulebook/image/"{Dockerfile,README.md,.dockerignore} "$TMP_ROOT/capability/infra/04.deploy/03.product/image/catalog/"
bash scripts/04.deploy/validate-container-boundaries/script.sh --root "$TMP_ROOT/capability" --json > "$TMP_ROOT/capability.json"
mkdir -p "$TMP_ROOT/capability/infra/04.deploy/03.product/image/catalog/nested"
cp "$TMP_ROOT/valid/infra/04.deploy/02.rag-rulebook/image/Dockerfile" "$TMP_ROOT/capability/infra/04.deploy/03.product/image/catalog/nested/Dockerfile"
if bash scripts/04.deploy/validate-container-boundaries/script.sh --root "$TMP_ROOT/capability" --json > "$TMP_ROOT/capability-bad.json"; then
  fail "validator accepted arbitrary nested image paths"
fi
grep -q "outside the governed infra image boundary" "$TMP_ROOT/capability-bad.json" || fail "nested boundary failure has wrong reason"
python3 - "$TMP_ROOT" "$ROOT" <<'PY'
import json,os,subprocess,sys
from pathlib import Path
temporary,repo=map(Path,sys.argv[1:])
script=repo/'scripts/04.deploy/validate-container-boundaries/script.sh'
ignore=temporary/'valid/infra/04.deploy/02.rag-rulebook/image/.dockerignore'
ignore.write_bytes(b'\xffcredential-canary-value')
result=subprocess.run(['bash',str(script),'--root',str(temporary/'valid'),'--json'],capture_output=True,text=True)
assert result.returncode==1,(result.stdout,result.stderr)
assert 'Ignore file could not be read as UTF-8.' in result.stdout
assert 'credential-canary-value' not in result.stdout+result.stderr and 'Traceback' not in result.stderr
result=subprocess.run(['bash',str(script),'--credential-canary-value'],capture_output=True,text=True)
assert result.returncode==2 and 'DIAGNOSTIC_CODE=CONTAINER_BOUNDARY_ARGUMENTS_INVALID' in result.stderr
assert 'credential-canary-value' not in result.stdout+result.stderr
# A controlled Path.read_text failure proves both actual reads, including a
# failure of the second read after the first succeeds; no chmod/root assumptions.
hooks=temporary/'hooks';hooks.mkdir()
(hooks/'sitecustomize.py').write_text('''import os
from pathlib import Path
original=Path.read_text
visits=0
def read(self,*args,**kwargs):
 global visits
 if self.name=='.dockerignore':
  visits+=1
  if visits==int(os.environ['IGNORE_FAIL_AT']):raise OSError('credential-canary-value')
 return original(self,*args,**kwargs)
Path.read_text=read
''')
ignore.write_text((temporary/'root-context/infra/04.deploy/02.rag-rulebook/image/Dockerfile.dockerignore').read_text())
for ordinal in ('1','2'):
 result=subprocess.run(['bash',str(script),'--root',str(temporary/'valid'),'--json'],env={**os.environ,'PYTHONPATH':str(hooks),'IGNORE_FAIL_AT':ordinal},capture_output=True,text=True)
 assert result.returncode==1,(ordinal,result.stdout,result.stderr)
 assert 'Ignore file could not be read as UTF-8.' in result.stdout and 'credential-canary-value' not in result.stdout+result.stderr
 assert 'Traceback' not in result.stderr
PY
echo "Container boundary validator smoke test passed."
