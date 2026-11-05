#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.test.artifact-metadata.backfill-diagnostics
#   version: 1
#   status: active
#   created_on: "2026-10-31"
#   updated_on: "2026-10-31"
#   layer: 01.harness
#   domain: metadata
#   disciplines: [agentic, security]
#   kind: script
#   purpose: Prove actual backfill diagnostics and partial effects using isolated files and closed child fakes, never real Git mutations.
#   portability: {class: required, targets: [llm-workbench, entity-builder, design-system-builder]}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: harness.script.artifact-metadata.generate-index-smoke-test
#     path: scripts/01.harness/artifact-metadata/generate-index/smoke-test.sh

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

SCRIPT = Path(__file__).with_name("script.sh").resolve()
CANARY = "PRIVATE_BACKFILL_DIAGNOSTIC_CANARY"
README = ".agentic/01.harness/README.md"
MANIFEST = ".agentic/01.harness/manifest.yml"
ORDER = ["header-check", "artifact-index", "git-stage", "session-prepare", "git-commit",
         "commit-identity", "record-session", "record-status", "checkpoint-session"]
CASES = 0


def write(root, relative, text):
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def prepare(root):
    (root / "temporary").mkdir()
    write(root, README, "<!-- agentic-artifact:\nschema: agentic-artifact/v1\npurpose: Fixture guide.\n-->\n# Fixture\n")
    write(root, MANIFEST, "# agentic-artifact:\n#   schema: agentic-artifact/v1\n#   purpose: Fixture configuration.\n\nvalue: true\n")
    write(root, "AGENTS.md", "# Fixture owner\n")
    # The closed fake rejects every unrecognized Git argv; it never calls Git.
    git = write(root, "bin/git", """#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
if args and args[0] == 'add': stage = 'git-stage'
elif args and args[0] == 'commit': stage = 'git-commit'
elif args == ['rev-parse', '--short', 'HEAD']: stage = 'commit-identity'
elif args == ['status', '--short', '--untracked-files=no']: stage = 'record-status'
else: raise SystemExit(91)
with Path(os.environ['BACKFILL_FIXTURE_EVENTS']).open('a') as log: log.write(json.dumps([stage, args]) + '\\n')
if os.environ.get('BACKFILL_FAIL_STAGE') == stage:
    print('PRIVATE_BACKFILL_DIAGNOSTIC_CANARY')
    print('PRIVATE_BACKFILL_DIAGNOSTIC_CANARY', file=sys.stderr)
    raise SystemExit(17)
if stage == 'git-commit': print('fixture commit returned')
elif stage == 'commit-identity': print('abc1234')
elif stage == 'record-status' and os.environ.get('BACKFILL_FIXTURE_DIRTY', 'yes') == 'yes': print(' M tracked-session.md')
""")
    git.chmod(0o755)
    write(root, "child.py", """import json, os, sys
from pathlib import Path
stage = sys.argv[1]
with Path(os.environ['BACKFILL_FIXTURE_EVENTS']).open('a') as log: log.write(json.dumps([stage, sys.argv[2:]]) + '\\n')
if os.environ.get('BACKFILL_FAIL_STAGE') == stage:
    print('PRIVATE_BACKFILL_DIAGNOSTIC_CANARY')
    print('PRIVATE_BACKFILL_DIAGNOSTIC_CANARY', file=sys.stderr)
    raise SystemExit(17)
if stage == 'artifact-index': print(os.environ.get('BACKFILL_INDEX_DATA', '{"summary":{"artifacts":2,"legacy_artifacts":0,"skipped":0,"duplicate_ids":0}}'))
else: print(stage + ' returned')
""")
    for relative, stage in [
        ("scripts/01.harness/artifact-metadata/check-headers/script.sh", "header-check"),
        ("scripts/01.harness/artifact-metadata/generate-index/script.sh", "artifact-index"),
        ("scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh", "session-prepare"),
        ("scripts/00.chat/session-log/record-chat-commit/script.sh", "record-session"),
        ("scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh", "checkpoint-session"),
    ]:
        write(root, relative, '#!/usr/bin/env bash\nexec python3 "$BACKFILL_FIXTURE_ROOT/child.py" ' + stage + ' "$@"\n')
    # Only three actual native boundaries need injection to distinguish no write,
    # completed earlier writes, and an attempted current write that may be partial.
    write(root, "injection/sitecustomize.py", """import os
from pathlib import Path
mode = os.environ.get('BACKFILL_NATIVE_INJECTION')
if mode:
    original_read, original_write = Path.read_text, Path.write_text
    reads = {}
    def read(self, *args, **kwargs):
        key = self.as_posix()
        reads[key] = reads.get(key, 0) + 1
        if mode == 'later-payload' and key == '.agentic/01.harness/manifest.yml' and reads[key] == 2:
            raise OSError('PRIVATE_BACKFILL_DIAGNOSTIC_CANARY')
        return original_read(self, *args, **kwargs)
    def write(self, text, *args, **kwargs):
        if mode == 'partial-write' and self.as_posix() == '.agentic/01.harness/manifest.yml':
            original_write(self, 'partial current write', *args, **kwargs)
            raise OSError('PRIVATE_BACKFILL_DIAGNOSTIC_CANARY')
        return original_write(self, text, *args, **kwargs)
    Path.read_text, Path.write_text = read, write
    if mode == 'render':
        import yaml
        def dump(*args, **kwargs): raise ValueError('PRIVATE_BACKFILL_DIAGNOSTIC_CANARY')
        yaml.safe_dump = dump
""")


def run(label, args=("--batch", "1"), *, status=0, finding=None, changes=None, environment=None, verify=None):
    global CASES
    with tempfile.TemporaryDirectory(prefix="backfill-diagnostics-") as temporary:
        root = Path(temporary)
        prepare(root)
        if changes:
            changes(root)
        env = {**os.environ, "PATH": str(root / "bin") + os.pathsep + os.environ.get("PATH", ""),
               "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(root / "injection"),
               "TMPDIR": str(root / "temporary"),
               "BACKFILL_FIXTURE_ROOT": str(root), "BACKFILL_FIXTURE_EVENTS": str(root / "events.jsonl"),
               "BACKFILL_FAIL_STAGE": "", "BACKFILL_NATIVE_INJECTION": ""}
        env.update(environment or {})
        result = subprocess.run(["bash", str(SCRIPT), *args], cwd=root, env=env,
                                capture_output=True, text=True, timeout=20)
        assert result.returncode == status, label + ": original exit disposition"
        assert CANARY not in result.stdout + result.stderr, label + ": no rejected/native/child content"
        assert "Traceback" not in result.stderr, label + ": no native traceback"
        if finding:
            assert finding in result.stderr, label + ": exact fixed owning finding"
        events = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()] if (root / "events.jsonl").exists() else []
        if verify:
            verify(root, result, events)
        CASES += 1


def successful(root, result, events):
    assert [event[0] for event in events] == ORDER, "original validation/Git/record/checkpoint order"
    assert events[0][1] == ["--paths", README, MANIFEST]
    assert events[1][1] == ["--paths", README, MANIFEST, "--strict"]
    assert events[2][1] == ["add", "--", README, MANIFEST]
    assert events[4][1] == ["commit", "-m", "Backfill governance root metadata headers"]
    assert events[6][1] == ["abc1234", "Backfill governance root metadata headers",
                            "Backfilled artifact metadata v2 headers for harness/shared governance root artifacts.", "No ADR impact."]
    assert "Completed batch " in result.stdout and result.stdout.endswith(" at abc1234.\n")
    assert "yaml parse ok: 1 files\n" in result.stdout
    assert all("schema: agentic-artifact/v2" in (root / relative).read_text() for relative in (README, MANIFEST))


def unavailable_count(_root, result, _events):
    assert "artifacts=unavailable" in result.stdout


def zero_equality(root, result, events):
    successful(root, result, events)
    assert "artifacts=None legacy=False skipped=0.0 duplicates=0" in result.stdout


def ordered(expected):
    def check(_root, _result, events):
        assert [event[0] for event in events] == expected, "actual child call order"
    return check


run("complete original command", verify=successful)
run("original int grammar", ("--batch", " +01 "), verify=successful)
run("original zero equality", environment={"BACKFILL_INDEX_DATA": json.dumps({"summary": {
    "artifacts": None, "legacy_artifacts": False, "skipped": 0.0, "duplicate_ids": 0}})}, verify=zero_equality)
run("untrusted count projection", environment={"BACKFILL_INDEX_DATA": json.dumps({"summary": {
    "artifacts": CANARY, "legacy_artifacts": 0, "skipped": 0, "duplicate_ids": 0}})},
    verify=unavailable_count)
run("invalid batch integer", ("--batch", CANARY), status=1, finding="stage=batch-input condition=integer-conversion-failed effect=not-started")
run("unsupported batch", ("--batch", "16"), status=1, finding="stage=batch-selection condition=unsupported effect=not-started")
run("disabled batch remains failed", ("--batch", "3"), status=1, finding="stage=batch-selection condition=no-remaining-artifacts effect=not-started")
run("already versioned remains failed", status=1, finding="condition=no-remaining-artifacts",
    changes=lambda root: [(root / relative).write_text((root / relative).read_text().replace("agentic-artifact/v1", "agentic-artifact/v3")) for relative in (README, MANIFEST)])
run("unsupported schema", status=1, finding="stage=header-schema condition=unsupported effect=not-started completed_writes=0",
    changes=lambda root: write(root, README, "<!-- agentic-artifact:\nschema: " + CANARY + "\n-->\n"))
run("header parse", status=1, finding="stage=header-parse condition=native-failure effect=not-started completed_writes=0",
    changes=lambda root: write(root, README, "<!-- agentic-artifact:\nschema: [" + CANARY + "\n-->\n"))
run("native schema projection", status=1, finding="stage=header-schema condition=native-failure",
    changes=lambda root: write(root, README, "<!-- agentic-artifact:\nschema: [" + CANARY + "]\n-->\n"))
run("status native read", ("--status",), status=1, finding="stage=status-read condition=native-failure effect=not-started",
    changes=lambda root: (root / README).write_bytes(b"\xff"))


def partial(root, result, events):
    assert not events and "Backfilled batch" not in result.stdout
    assert "schema: agentic-artifact/v2" in (root / README).read_text()
    assert (root / MANIFEST).read_text() == "partial current write"


run("partial current write", status=1,
    finding="stage=header-write condition=native-failure effect=current-write-unknown completed_writes=1 ordinal=1",
    environment={"BACKFILL_NATIVE_INJECTION": "partial-write"}, verify=partial)
run("later payload after earlier write", status=1,
    finding="stage=header-read condition=native-failure effect=prior-writes-returned completed_writes=1 ordinal=1",
    environment={"BACKFILL_NATIVE_INJECTION": "later-payload"})
run("render before first write", status=1,
    finding="stage=header-render condition=native-failure effect=not-started completed_writes=0 ordinal=0",
    environment={"BACKFILL_NATIVE_INJECTION": "render"})
run("index parse", status=1, finding="stage=index-parse condition=native-failure effect=headers-written",
    environment={"BACKFILL_INDEX_DATA": '{"value":"' + CANARY + '",}'})
run("index projection", status=1, finding="stage=index-projection condition=native-failure effect=headers-written",
    environment={"BACKFILL_INDEX_DATA": '{"summary":null}'})
run("all original zero-comparison rejections", status=1,
    finding="stage=index-comparison condition=zero-comparison-rejected fields=legacy_artifacts,skipped,duplicate_ids effect=headers-written",
    environment={"BACKFILL_INDEX_DATA": json.dumps({"summary": {key: CANARY for key in ("legacy_artifacts", "skipped", "duplicate_ids")}})})
run("post-write YAML parser", status=1, finding="stage=yaml-parse condition=native-failure effect=headers-written ordinal=0",
    changes=lambda root: write(root, MANIFEST, "# agentic-artifact:\n#   schema: agentic-artifact/v1\n\nvalue: [" + CANARY + "\n"))

for stage in ORDER:
    effect = "commit-outcome-unknown" if stage == "git-commit" else "commit-returned" if stage in ORDER[5:] else "staging-outcome-unknown" if stage == "git-stage" else "git-stage-returned" if stage == "session-prepare" else "headers-written"
    run("failed actual child " + stage, status=17, finding=f"stage={stage} condition=child-failed effect={effect} child_status=17",
        environment={"BACKFILL_FAIL_STAGE": stage},
        verify=ordered(ORDER[:ORDER.index(stage) + 1]))

run("record only has no invented commit", ("--record-only", "abc1234", "fixture message", "fixture summary"),
    verify=ordered(ORDER[6:]))
run("clean record skips checkpoint", ("--record-only", "abc1234", "fixture message", "fixture summary"),
    environment={"BACKFILL_FIXTURE_DIRTY": "no"},
    verify=ordered(ORDER[6:8]))
run("record-only failure unknown prior commit", ("--record-only", "abc1234", "fixture message", "fixture summary"), status=17,
    finding="stage=record-session condition=child-failed effect=not-assessed child_status=17", environment={"BACKFILL_FAIL_STAGE": "record-session"})
print(f"Backfill diagnostic fixture passed ({CASES} cases; no real Git commands).")
