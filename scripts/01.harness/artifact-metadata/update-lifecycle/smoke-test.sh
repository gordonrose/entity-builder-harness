#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.artifact-metadata.update-lifecycle-smoke-test
#   version: 1
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 01.harness
#   domain: metadata
#   disciplines:
#     - agentic
#   kind: script
#   purpose: Verify lifecycle reporting and bounded updates in disposable Git repositories.
#   portability:
#     class: required
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#     - stages-files
#     - commits
#   used_by:
#     - id: harness.script.artifact-metadata.update-lifecycle
#       path: scripts/01.harness/artifact-metadata/update-lifecycle/script.sh

repo_root="$(git rev-parse --show-toplevel)"
python3 - "$repo_root/scripts/01.harness/artifact-metadata/update-lifecycle/script.sh" <<'PY'
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

UPDATER = Path(sys.argv[1]).resolve()
TODAY = dt.datetime.now(dt.timezone.utc).date().isoformat()

HEADER = """<!-- agentic-artifact:
schema: agentic-artifact/v2
id: {id}
version: 7
status: {status}
layer: 01.harness
domain: metadata
disciplines:
- agentic
kind: guide
purpose: Exercise lifecycle updates.
portability:
  class: source-only
  targets: []
used_by:
- id: test.lifecycle.updater
-->
# Example

Body remains byte-for-byte.
"""


def run(cmd, cwd, **kwargs):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)


def git(repo, *args, **kwargs):
    result = run(["git", *args], repo, **kwargs)
    assert result.returncode == 0, result.stderr.decode()
    return result.stdout


def commit(repo, message, date="2025-01-02T23:00:00-03:00"):
    git(repo, "add", ".")
    env = dict(os.environ, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    git(repo, "commit", "-qm", message, env=env)


def update(repo, paths, *flags, succeeds=True):
    result = run(["bash", str(UPDATER), "--paths", *paths, *flags], repo)
    assert result.returncode == (0 if succeeds else 1), result.stderr.decode() + result.stdout.decode()
    return json.loads(result.stdout)


def artifact(repo, name=".agentic/original.md", identity="test.artifact.original", status="active", crlf=False):
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    text = HEADER.format(id=identity, status=status)
    path.write_bytes(text.replace("\n", "\r\n").encode() if crlf else text.encode())
    return path


with tempfile.TemporaryDirectory(prefix="artifact-lifecycle-test-") as temporary:
    repo = Path(temporary) / "repository"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Lifecycle smoke test")
    git(repo, "config", "user.email", "lifecycle-test@example.invalid")
    source = artifact(repo, crlf=True)
    replacement = artifact(repo, ".agentic/replacement.md", "test.artifact.replacement")
    commit(repo, "Initial artifacts")
    original = source.read_bytes()
    mtime = source.stat().st_mtime_ns
    index = git(repo, "write-tree")
    report = update(repo, [".agentic/original.md"])
    plan = report["plans"][0]
    assert plan["changed"] and not report["applied"]
    assert plan["creation_evidence"]["basis"] == "git-first-added"
    assert plan["after"]["created_on"] == "2025-01-03", "committer timestamps must become UTC dates"
    assert plan["last_committed_on"] == "2025-01-03"
    assert source.read_bytes() == original and source.stat().st_mtime_ns == mtime
    assert git(repo, "write-tree") == index, "report must not stage files"

    report = update(repo, [".agentic/original.md"], "--apply")
    migrated = source.read_bytes()
    assert report["applied"]
    assert b'version: 7\r\n' in migrated
    assert b'created_on: "2025-01-03"\r\n' in migrated
    assert b'updated_on: "' + TODAY.encode() + b'"\r\n' in migrated
    assert migrated.split(b"-->", 1)[1] == original.split(b"-->", 1)[1]
    assert b"\n" not in migrated.replace(b"\r\n", b""), "CRLF must be retained"
    assert git(repo, "write-tree") == index, "apply must not stage files"
    mtime = source.stat().st_mtime_ns
    assert not update(repo, [".agentic/original.md"], "--apply")["plans"][0]["changed"]
    assert source.stat().st_mtime_ns == mtime, "repeat apply must not rewrite unchanged files"

    commit(repo, "Migrate lifecycle", TODAY + "T00:00:00+00:00")
    git(repo, "mv", ".agentic/original.md", ".agentic/renamed.md")
    commit(repo, "Rename artifact", TODAY + "T00:00:00+00:00")
    source = repo / ".agentic/renamed.md"
    report = update(repo, [".agentic/renamed.md"], "--apply")
    assert not report["plans"][0]["changed"]
    assert report["plans"][0]["after"]["created_on"] == "2025-01-03"
    assert report["plans"][0]["creation_evidence"]["basis"] == "existing-header"

    # A rename with edits compares against the original HEAD path, even before
    # the rename is committed. It must also enforce creation-date immutability.
    rename_source = artifact(repo, ".agentic/rename-edit.md", "test.artifact.rename-edit")
    rename_source.write_text(rename_source.read_text().replace(
        "schema: agentic-artifact/v2",
        'schema: agentic-artifact/v3\ncreated_on: "2025-01-03"\nupdated_on: "2025-01-03"'
    ))
    git(repo, "add", ".agentic/rename-edit.md")
    git(repo, "commit", "-qm", "Add rename-edit fixture")
    git(repo, "mv", ".agentic/rename-edit.md", ".agentic/renamed-edit.md")
    renamed = repo / ".agentic/renamed-edit.md"
    renamed.write_text(renamed.read_text() + "Edited while moving.\n")
    git(repo, "add", ".agentic/renamed-edit.md")
    report = update(repo, [".agentic/renamed-edit.md"], "--apply")
    assert report["plans"][0]["head_baseline_path"] == ".agentic/rename-edit.md"
    assert report["plans"][0]["after"]["updated_on"] == TODAY
    assert report["plans"][0]["after"]["created_on"] == "2025-01-03"
    immutable_before = renamed.read_bytes()
    renamed.write_bytes(immutable_before.replace(b'created_on: "2025-01-03"', b'created_on: "2025-01-04"'))
    rejected = update(repo, [".agentic/renamed-edit.md"], "--apply", succeeds=False)
    assert "created_on differs from HEAD" in rejected["errors"][0]["error"]
    renamed.write_bytes(immutable_before)
    git(repo, "add", ".agentic/renamed-edit.md")
    git(repo, "commit", "-qm", "Finish staged rename-edit fixture")
    # The same stable-ID baseline works for an unstaged move to an untracked
    # destination; reading an unchanged move remains a no-op.
    unstaged = repo / ".agentic/unstaged-renamed.md"
    renamed.rename(unstaged)
    assert not update(repo, [".agentic/unstaged-renamed.md"])["plans"][0]["changed"]
    unstaged.write_text(unstaged.read_text() + "Edited after an unstaged move.\n")
    report = update(repo, [".agentic/unstaged-renamed.md"], "--apply")
    assert report["plans"][0]["head_baseline_path"] == ".agentic/renamed-edit.md"
    assert report["plans"][0]["content_differs_from_head"]
    unstaged.rename(renamed)

    # A clean valid v3 artifact keeps its older update date on another day.
    old = source.read_bytes().replace(
        b'updated_on: "' + TODAY.encode() + b'"', b'updated_on: "2025-01-03"'
    )
    source.write_bytes(old)
    commit(repo, "Old metadata date fixture", TODAY + "T00:00:00+00:00")
    assert not update(repo, [".agentic/renamed.md"])["plans"][0]["changed"]
    source.write_bytes(old + b'updated_on: "2025-04-01"\r\n')
    commit(repo, "Body example date fixture", TODAY + "T00:00:00+00:00")
    source.write_bytes(source.read_bytes().replace(
        b'updated_on: "2025-04-01"', b'updated_on: "2025-04-02"'
    ))
    assert update(repo, [".agentic/renamed.md"], "--apply")["plans"][0]["after"]["updated_on"] == TODAY
    source.write_bytes(old + b"New body content.\r\n")
    report = update(repo, [".agentic/renamed.md"], "--apply")
    assert report["plans"][0]["after"]["updated_on"] == TODAY
    assert source.read_bytes().endswith(b"New body content.\r\n")

    # Validate the whole batch before any file mutation.
    pending = artifact(repo, ".agentic/pending.md", "test.artifact.pending")
    before = pending.read_bytes()
    bad = repo / ".agentic/broken.md"
    bad.write_text("# Missing metadata\n")
    report = update(repo, [".agentic/pending.md", ".agentic/broken.md", ".agentic/absent.md"], "--apply", succeeds=False)
    assert len(report["errors"]) == 2 and not report["applied"]
    assert pending.read_bytes() == before
    assert report["plans"][0]["creation_evidence"]["basis"] == "new-artifact"
    update(repo, [".agentic/pending.md"], "--apply", "--created-on", "2025-02-30", succeeds=False)
    assert pending.read_bytes() == before
    update(repo, [".agentic/renamed.md"], "--created-on", "2025-01-02", succeeds=False)
    malformed = artifact(repo, ".agentic/unquoted.md", "test.artifact.unquoted")
    malformed.write_text(malformed.read_text().replace(
        "schema: agentic-artifact/v2",
        'schema: agentic-artifact/v3\ncreated_on: "2025-01-03"\nupdated_on: 2025-01-03'
    ))
    malformed_before = malformed.read_bytes()
    update(repo, [".agentic/unquoted.md"], "--apply", succeeds=False)
    assert malformed.read_bytes() == malformed_before
    new_v3 = artifact(repo, ".agentic/new-v3.md", "test.artifact.new-v3")
    new_v3.write_text(new_v3.read_text().replace(
        "schema: agentic-artifact/v2",
        'schema: agentic-artifact/v3\ncreated_on: "2025-01-03"\nupdated_on: "2025-01-03"'
    ))
    report = update(repo, [".agentic/new-v3.md"], "--apply")
    assert report["plans"][0]["after"]["updated_on"] == TODAY
    assert report["plans"][0]["after"]["created_on"] == "2025-01-03"

    # Historical deprecations need explicit event evidence.
    deprecated = artifact(repo, ".agentic/deprecated.md", "test.artifact.deprecated", "deprecated")
    update(repo, [".agentic/deprecated.md"], "--apply", succeeds=False)
    report = update(
        repo, [".agentic/deprecated.md"], "--apply", "--created-on", "2025-01-03",
        "--deprecated-on", "2025-02-01"
    )
    assert report["plans"][0]["after"]["deprecated_on"] == "2025-02-01"
    assert report["plans"][0]["creation_evidence"]["basis"] == "explicit-date"

    # Explicit deprecation and supersession require appropriate metadata.
    report = update(repo, [".agentic/renamed.md"], "--apply", "--status", "deprecated")
    assert report["plans"][0]["after"]["deprecated_on"] == TODAY
    pre_transition = source.read_bytes()
    update(repo, [".agentic/renamed.md"], "--apply", "--status", "superseded", succeeds=False)
    assert source.read_bytes() == pre_transition
    update(repo, [".agentic/renamed.md"], "--status", "superseded", "--replacement", ".agentic/renamed.md", succeeds=False)
    report = update(
        repo, [".agentic/renamed.md"], "--apply", "--status", "superseded",
        "--replacement", ".agentic/replacement.md"
    )
    assert report["plans"][0]["after"]["superseded_on"] == TODAY
    assert b"> Superseded by [test.artifact.replacement](replacement.md)." in source.read_bytes()
    assert not update(repo, [".agentic/renamed.md"], "--apply")["plans"][0]["changed"]
    before_replacement = replacement.read_bytes()
    update(
        repo, [".agentic/replacement.md"], "--apply", "--status", "superseded",
        "--replacement", ".agentic/renamed.md", succeeds=False
    )
    assert replacement.read_bytes() == before_replacement, "cycles must block before writing"
    update(
        repo, [".agentic/replacement.md"], "--apply", "--status", "deprecated",
        "--deprecated-on", "2025-01-03", succeeds=False
    )

    # Replacement IDs must agree with referenced headers.
    mismatched = source.read_bytes().replace(
        b"  - id: test.artifact.replacement", b"  - id: test.artifact.wrong"
    )
    source.write_bytes(mismatched)
    update(repo, [".agentic/renamed.md"], "--apply", succeeds=False)
    assert source.read_bytes() == mismatched

    # YAML/script comment headers retain unrelated bytes and indentation.
    comment = repo / "scripts/comment.sh"
    comment.parent.mkdir(parents=True)
    body = HEADER.format(id="test.artifact.comment", status="active").split("-->", 1)[0]
    body = body.replace("kind: guide", "kind: script\neffects: [read-only]")
    yaml_lines = body.splitlines()[1:]
    original_comment = "#!/usr/bin/env bash\n# agentic-artifact:\n" + "".join(
        "#   " + line + "\n" for line in yaml_lines
    ) + "\nprintf 'body\\n'\n"
    comment.write_text(original_comment)
    update(repo, ["scripts/comment.sh"], "--apply")
    assert '#   created_on: "' + TODAY + '"' in comment.read_text()
    assert comment.read_text().endswith("\nprintf 'body\\n'\n")

    js = repo / ".agentic/comment.mjs"
    js.write_text(original_comment.replace("#!/usr/bin/env bash\n", "").replace("# ", "// ")
                  .replace("test.artifact.comment", "test.artifact.javascript"))
    update(repo, [".agentic/comment.mjs"], "--apply")
    assert '//   created_on: "' + TODAY + '"' in js.read_text()

    indented = artifact(repo, ".agentic/indented.md", "test.artifact.indented")
    lines = indented.read_text().splitlines(keepends=True)
    end = lines.index("-->\n")
    lines[1:end] = ["  " + line for line in lines[1:end]]
    indented.write_text("".join(lines))
    body = indented.read_text().split("-->", 1)[1]
    update(repo, [".agentic/indented.md"], "--apply")
    assert indented.read_text().count("schema:") == 1
    assert '  created_on: "' + TODAY + '"' in indented.read_text()
    assert indented.read_text().split("-->", 1)[1] == body

    duplicate = artifact(repo, ".agentic/duplicate.md", "test.artifact.duplicate")
    duplicate.write_text(duplicate.read_text().replace("version: 7", "version: 7\nversion: 8"))
    update(repo, [".agentic/duplicate.md"], "--apply", succeeds=False)
    alias = repo / ".agentic/alias.md"
    alias.symlink_to(replacement)
    update(repo, [".agentic/alias.md"], "--apply", succeeds=False)
    update(repo, [str(Path(temporary) / "outside.md")], "--apply", succeeds=False)

    # An unstaged v2 move must not silently become a newly created artifact.
    move_source = artifact(repo, ".agentic/move-source.md", "test.artifact.move")
    git(repo, "add", ".agentic/move-source.md")
    git(repo, "commit", "-qm", "Add move fixture")
    moved = repo / ".agentic/moved.md"
    move_source.rename(moved)
    before_move = moved.read_bytes()
    report = update(repo, [".agentic/moved.md"], "--apply", succeeds=False)
    assert "possible uncommitted rename" in report["errors"][0]["error"]
    assert moved.read_bytes() == before_move
    moved.rename(move_source)

    reused = artifact(repo, ".agentic/reused.md", "test.artifact.first")
    git(repo, "add", ".agentic/reused.md")
    git(repo, "commit", "-qm", "First path use")
    git(repo, "rm", ".agentic/reused.md")
    git(repo, "commit", "-qm", "Remove old path use")
    artifact(repo, ".agentic/reused.md", "test.artifact.second")
    git(repo, "add", ".agentic/reused.md")
    git(repo, "commit", "-qm", "Reuse path for different artifact")
    report = update(repo, [".agentic/reused.md"], succeeds=False)
    assert any(reason in report["errors"][0]["error"] for reason in (
        "ambiguous deletion/recreation", "first-added artifact ID differs"
    )), report

    identity = artifact(repo, ".agentic/identity.md", "test.artifact.old-identity")
    git(repo, "add", ".agentic/identity.md")
    git(repo, "commit", "-qm", "Add identity fixture")
    identity.write_text(identity.read_text().replace("old-identity", "new-identity"))
    report = update(repo, [".agentic/identity.md"], succeeds=False)
    assert "first-added artifact ID differs" in report["errors"][0]["error"]
    report = update(repo, [".agentic/identity.md"], "--created-on", "2025-01-03")
    assert report["plans"][0]["creation_evidence"]["basis"] == "explicit-date"

    # Committed renames of v2 files still find the original introduction date.
    git(repo, "mv", ".agentic/replacement.md", ".agentic/replacement-renamed.md")
    # Keep invalid fixtures out of Git; only stage the rename in this fixture.
    git(repo, "commit", "-qm", "Rename v2 artifact")
    report = update(repo, [".agentic/replacement-renamed.md"])
    assert report["plans"][0]["after"]["created_on"] == "2025-01-03"

    # Shallow clones cannot establish reliable creation history.
    shallow = Path(temporary) / "shallow"
    git(Path(temporary), "clone", "--quiet", "--depth=1", repo.as_uri(), str(shallow))
    report = update(shallow, [".agentic/replacement-renamed.md"], "--apply", succeeds=False)
    assert "Shallow history" in report["errors"][0]["error"]
    report = update(shallow, [".agentic/replacement-renamed.md"], "--created-on", "2025-01-03")
    assert report["plans"][0]["creation_evidence"]["basis"] == "explicit-date"

print("Lifecycle updater smoke tests passed.")
PY
