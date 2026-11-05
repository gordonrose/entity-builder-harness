#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.artifact-metadata.update-lifecycle-smoke-test
#   version: 3
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-31"
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
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

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


def update_changed(repo, *flags, succeeds=True):
    result = run(["bash", str(UPDATER), "--changed", *flags], repo)
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
    duplicate_report=update(repo,['.agentic/original.md','.agentic/original.md'],'--apply',succeeds=False)
    assert duplicate_report['errors'][0]['code']=='lifecycle-path-duplicate' and duplicate_report['errors'][0]['ordinal']==2
    assert source.read_bytes()==migrated

    # Task preparation discovers changed lifecycle artifacts without touching
    # ordinary source, and a second unchanged preparation is a true no-op.
    source.write_bytes(source.read_bytes() + b"Prepared task body change.\r\n")
    ordinary = repo / "src/ordinary.ts"; ordinary.parent.mkdir()
    ordinary.write_text("export const ordinary = true;\n")
    prepared = update_changed(repo, "--apply")
    assert prepared["selection"] == "changed-artifacts"
    assert [item["path"] for item in prepared["plans"]] == [".agentic/original.md"], prepared
    # The header was already refreshed today; discovering a further same-day
    # body edit must not rewrite it simply to manufacture another update.
    assert not prepared["plans"][0]["changed"]
    assert prepared["skipped"] == [{"path": "src/ordinary.ts", "reason": "not-a-v2-or-v3-artifact"}]
    prepared_bytes = source.read_bytes(); prepared_mtime = source.stat().st_mtime_ns
    repeated = update_changed(repo, "--apply")
    assert not repeated["plans"][0]["changed"]
    assert source.read_bytes() == prepared_bytes and source.stat().st_mtime_ns == prepared_mtime
    assert ordinary.read_text() == "export const ordinary = true;\n"

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
        b"  - id: test.artifact.replacement", b"  - id: private.reference.canary"
    )
    source.write_bytes(mismatched)
    rejected = update(repo, [".agentic/renamed.md"], "--apply", succeeds=False)
    assert source.read_bytes() == mismatched
    assert rejected['errors'][0]['code']=='lifecycle-replacement-id-mismatch'
    assert rejected['errors'][0]['stage']=='references' and rejected['errors'][0]['ordinal']==1
    assert rejected['plans'][0]['before']['superseded_by'] is None
    assert rejected['plans'][0]['after']['superseded_by'] is None
    assert 'private.reference.canary' not in json.dumps(rejected)
    # Repairing an ignored old reference retains original write/admission,
    # while the unvalidated before-value never becomes diagnostic evidence.
    repaired=update(repo,['.agentic/renamed.md'],'--replacement','.agentic/replacement.md','--apply')
    assert repaired['applied'] and repaired['plans'][0]['before']['superseded_by'] is None
    expected_refs=[{'id':'test.artifact.replacement','path':'.agentic/replacement.md'}]
    assert repaired['plans'][0]['after']['superseded_by']==expected_refs
    assert 'private.reference.canary' not in json.dumps(repaired)
    valid_superseded=source.read_bytes()
    rejected_path=valid_superseded.replace(b'path: ".agentic/replacement.md"',b'path: ".agentic/private-reference-path-canary.md"')
    source.write_bytes(rejected_path)
    rejected=update(repo,['.agentic/renamed.md'],'--apply',succeeds=False)
    assert source.read_bytes()==rejected_path and 'private-reference-path-canary' not in json.dumps(rejected)
    assert rejected['plans'][0]['before']['superseded_by'] is None and rejected['plans'][0]['after']['superseded_by'] is None
    source.write_bytes(valid_superseded)
    unchanged=update(repo,['.agentic/renamed.md'])
    assert unchanged['plans'][0]['before']['superseded_by']==unchanged['plans'][0]['after']['superseded_by']==expected_refs

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

    # Existing file-level declarations are updatable outside the old path and
    # extension filters. Their preambles and executable bodies remain exact.
    for name, prefix, preamble, body_text, identity in (
        ("application/component.ts", "//", "", "export const value = 1;\n", "typescript"),
        ("tools/inspect.py", "#", '#!/usr/bin/env python3\n"""Module description."""\n\n', "print('body')\n", "python"),
        ("containers/Dockerfile", "#", "# syntax=docker/dockerfile:1.7\n\n", "FROM scratch\n", "docker"),
        ("custom/metadata.anything", "#", "", "ordinary body\n", "arbitrary"),
        ("infra/provider/foundation.yml", "#", "", "Resources: {}\n", "infra"),
    ):
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        fields = HEADER.format(id="test.discovery." + identity, status="active").split("-->\n", 1)[0].splitlines()[1:]
        original = preamble + prefix + " agentic-artifact:\n" + "".join(prefix + "   " + line + "\n" for line in fields) + "\n" + body_text
        target.write_text(original)
        report = update(repo, [name])
        assert report["plans"][0]["changed"] and target.read_text() == original
        update(repo, [name], "--apply")
        migrated = target.read_text()
        assert migrated.startswith(preamble + prefix + " agentic-artifact:\n")
        assert migrated.endswith("\n" + body_text)
        assert prefix + '   created_on: "' + TODAY + '"' in migrated
        assert prefix + "   version: 7\n" in migrated
        assert not update(repo, [name], "--apply")["plans"][0]["changed"]

    for name, content in (
        ("examples/fenced.md", "# Example\n\n```md\n" + HEADER.format(id="test.embedded.fence", status="active") + "```\n"),
        ("examples/heredoc.sh", "cat <<'EOF'\n" + original_comment + "EOF\n"),
        ("examples/docstring.py", '#!/usr/bin/env python3\n"""\n' + original_comment + '"""\nprint(1)\n'),
        ("docs/00.chat/bootstrap/llm-workbench-template/root/scripts/install.sh.template", original_comment),
    ):
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        before = target.read_bytes()
        update(repo, [name], "--apply", succeeds=False)
        assert target.read_bytes() == before, "embedded examples and output scaffolds must never be edited"

    duplicate = artifact(repo, ".agentic/duplicate.md", "test.artifact.duplicate")
    duplicate.write_text(duplicate.read_text().replace("version: 7", "version: 7\nversion: private-yaml-canary"))
    duplicate_report=update(repo, [".agentic/duplicate.md"], "--apply", succeeds=False)
    assert 'private-yaml-canary' not in json.dumps(duplicate_report)
    alias = repo / ".agentic/alias.md"
    alias.symlink_to(replacement)
    update(repo, [".agentic/alias.md"], "--apply", succeeds=False)
    outside_report=update(repo, [str(Path(temporary) / "private-path-canary.md")], "--apply", succeeds=False)
    assert 'private-path-canary' not in json.dumps(outside_report)

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


# A historical malformed v2 header can be repaired and migrated before its first
# commit. Repeating the helper must remain a no-op without weakening v3 history.
with tempfile.TemporaryDirectory(prefix="artifact-legacy-repair-") as temporary:
    repo = Path(temporary)
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Lifecycle legacy repair test")
    git(repo, "config", "user.email", "lifecycle-test@example.invalid")
    source = artifact(repo, "platform/adapters/README.md", "test.artifact.legacy-repair")
    fixed = source.read_text().replace(
        "- id: test.lifecycle.updater\n", "- id: test.lifecycle.updater\n  path: platform/adapters/README.md\n"
    )
    malformed = fixed.replace("  path: platform/", "    path: platform/")
    source.write_text(malformed)
    commit(repo, "Historical malformed v2 metadata")
    source.write_text(fixed)
    update(repo, ["platform/adapters/README.md"], "--apply")
    migrated = source.read_bytes()
    mtime = source.stat().st_mtime_ns
    assert migrated.split(b"-->", 1)[1] == fixed.encode().split(b"-->", 1)[1]
    assert not update(repo, ["platform/adapters/README.md"])["plans"][0]["changed"]
    assert not update(repo, ["platform/adapters/README.md"], "--apply")["plans"][0]["changed"]
    assert source.read_bytes() == migrated and source.stat().st_mtime_ns == mtime
    git(repo, "add", "platform/adapters/README.md")
    validation = run(["bash", str(UPDATER.parents[1] / "check-headers/script.sh"), "--staged"], repo)
    assert validation.returncode == 0, validation.stdout.decode() + validation.stderr.decode()
    git(repo, "commit", "-qm", "Repair and migrate legacy metadata")

    for name, historical in (
        ("malformed-v3", malformed.replace("schema: agentic-artifact/v2", 'schema: agentic-artifact/v3\ncreated_on: "2025-01-03"\nupdated_on: "2025-01-03"')),
        ("duplicate-schema", malformed.replace("schema: agentic-artifact/v2", "schema: agentic-artifact/v3\nschema: agentic-artifact/v2")),
        ("unknown-schema", malformed.replace("schema: agentic-artifact/v2", "schema: agentic-artifact/v99")),
    ):
        path = repo / "platform" / (name + ".md")
        path.write_text(historical.replace("test.artifact.legacy-repair", "test.artifact." + name))
        git(repo, "add", str(path.relative_to(repo)))
        git(repo, "commit", "-qm", "Historical invalid metadata fixture")
        current = migrated.replace(b"test.artifact.legacy-repair", ("test.artifact." + name).encode())
        path.write_bytes(current)
        update(repo, [str(path.relative_to(repo))], "--apply", succeeds=False)
        assert path.read_bytes() == current, "ambiguous or malformed v3 history must fail closed"

with tempfile.TemporaryDirectory(prefix="lifecycle-rollover-") as temporary:
    repo = Path(temporary)
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Lifecycle rollover fixture")
    git(repo, "config", "user.email", "rollover@example.invalid")
    source = artifact(repo)
    commit(repo, "Original artifact")
    source.write_bytes(source.read_bytes() + b"Prepared content.\n")
    # Exercise yesterday's preparation with the same source implementation;
    # there is no production clock override or provider operation.
    yesterday = (dt.date.fromisoformat(TODAY) - dt.timedelta(days=1)).isoformat()
    code = UPDATER.read_text().split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    code = code.replace('TODAY = dt.datetime.now(dt.timezone.utc).date().isoformat()', 'TODAY = ' + repr(yesterday))
    result = run([sys.executable, "-c", code, str(UPDATER), "--paths", ".agentic/original.md", "--apply"], repo)
    assert result.returncode == 0, result.stdout.decode() + result.stderr.decode()
    prepared, mtime = source.read_bytes(), source.stat().st_mtime_ns
    private = Path(git(repo, "rev-parse", "--absolute-git-dir").decode().strip()) / "agentic-local-checks/preparation-report.json"
    receipt_mtime = private.stat().st_mtime_ns
    assert ('updated_on: "' + yesterday + '"').encode() in prepared
    for _ in range(2):
        report = update(repo, [".agentic/original.md"], "--apply")
        assert not report["plans"][0]["changed"], report
        assert source.read_bytes() == prepared and source.stat().st_mtime_ns == mtime
        assert private.stat().st_mtime_ns == receipt_mtime, "unchanged preparation must not rewrite its private receipt"
    git(repo, "add", ".agentic/original.md")
    checker = UPDATER.parents[1] / "check-headers/script.sh"
    validation = run(["bash", str(checker), "--staged"], repo)
    assert validation.returncode == 0, validation.stdout.decode() + validation.stderr.decode()
    source.write_bytes(prepared + b"Unprepared later content.\n")
    git(repo, "add", ".agentic/original.md")
    validation = run(["bash", str(checker), "--staged"], repo)
    assert validation.returncode != 0, "a date receipt cannot authorize changed staged bytes"
    update(repo, [".agentic/original.md"], "--apply")
    assert ('updated_on: "' + TODAY + '"').encode() in source.read_bytes()
    assert b'created_on: "2025-01-03"' in source.read_bytes()

# Native seams execute the actual embedded command, with only its external
# observations controlled. No Git mutation or checker implementation is added.
code=UPDATER.read_text().split("<<'PY'\n",1)[1].rsplit('\nPY',1)[0]
with tempfile.TemporaryDirectory(prefix='lifecycle-diagnostic-boundaries-') as temporary:
    root=Path(temporary);one=root/'one.md';two=root/'two.md'
    original={one:b'one original\n',two:b'two original\n'}
    for path,raw in original.items():path.write_bytes(raw)
    class BrokenStream(io.StringIO):
        def write(self,value):raise OSError('private-emission-canary')
    def load_owner(error=None, clock=False, emission=None, broken_fallback=False):
        owner={'__name__':'lifecycle_diagnostic_fixture'};out=BrokenStream() if emission=='stdout' else io.StringIO();err=BrokenStream() if broken_fallback else io.StringIO()
        class BrokenClock:
            @classmethod
            def now(cls,*args):raise ValueError('private-clock-canary')
        native=patch.object(subprocess,'run',side_effect=error) if error else patch.object(subprocess,'run',return_value=SimpleNamespace(stdout=os.fsencode(root),returncode=0))
        with native,patch.object(sys,'argv',['fixture',str(UPDATER)]),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err), (patch.object(dt,'datetime',BrokenClock) if clock else contextlib.nullcontext()), (patch.object(json,'dumps',side_effect=ValueError('private-serialization-canary')) if emission=='serialization' else contextlib.nullcontext()):
            try:exec(compile(code,str(UPDATER),'exec'),owner)
            except SystemExit as stopped:return owner,stopped.code,out.getvalue(),err.getvalue()
        owner['LocalCache']=None
        return owner,0,out.getvalue(),err.getvalue()
    for error,clock,stage in [(OSError('private-root-canary'),False,'repository'),(UnicodeDecodeError('utf8',b'\xff',0,1,'private-root-canary'),False,'repository'),(None,True,'clock')]:
        owner,status,out,err=load_owner(error,clock)
        assert status==1 and json.loads(out)['errors'][0]['stage']==stage
        assert 'canary' not in out+err
    for clock,emission,broken_fallback in [(False,'serialization',False),(False,'stdout',False),(True,'serialization',False),(False,'stdout',True)]:
        with patch.object(Path,'write_bytes',side_effect=AssertionError('pre-main failure must not write')):
            _,status,out,err=load_owner(None if clock else OSError('private-root-canary'),clock,emission,broken_fallback)
        assert status==1 and out=='' and err==('' if broken_fallback else 'ERROR: lifecycle-reporting-failed\n')
    owner,status,_,_=load_owner();assert status==0
    out=io.StringIO();err=io.StringIO()
    with patch.object(sys,'argv',['fixture',str(UPDATER),'--paths','one.md','--status','private-cli-canary']),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
        try:owner['main']()
        except SystemExit as stopped:assert stopped.code==2
        else:raise AssertionError('invalid CLI choice admitted')
    assert out.getvalue()=='' and err.getvalue()=='ERROR: lifecycle-arguments-invalid\n'
    def prepared(path,args):
        raw=path.read_bytes();identity='test.lifecycle.'+path.stem
        return {'original':raw,'rendered':raw+b'prepared\n','header':SimpleNamespace(data={'id':identity,'status':'active'}),'report':{'path':path.relative_to(root).as_posix(),'before':{'superseded_by':None},'after':{'superseded_by':None}}}
    def invoke(*flags, replacements=None, child=None, child_error=None):
        out=io.StringIO();err=io.StringIO()
        child_call=patch.object(subprocess,'run',side_effect=child_error) if child_error else patch.object(subprocess,'run',return_value=child or SimpleNamespace(returncode=0,stdout='private-checker-canary',stderr='private-checker-canary'))
        with patch.dict(owner,{'prepare':prepared,**(replacements or {})}),patch.object(sys,'argv',['fixture',str(UPDATER),*flags]),child_call as command,contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            status=owner['main']()
        assert 'canary' not in out.getvalue()+err.getvalue()
        return status,json.loads(out.getvalue()),command
    for error,expected in [(owner['PlanError']('date-calendar','updated_on'),'lifecycle-date-calendar'),(OSError('private-native-canary'),'lifecycle-planning-failed'),(ValueError('private-native-canary'),'lifecycle-planning-failed'),(TypeError('private-native-canary'),'lifecycle-planning-failed')]:
        calls=[]
        def rejected(path,args):calls.append(path);raise error
        status,report,command=invoke('--paths','one.md','two.md','--apply',replacements={'prepare':rejected})
        assert status==1 and not report['applied'] and report['errors'][0]['code']==expected
        assert report['errors'][0]['ordinal']==1 and command.call_count==0
        assert len(calls)==(1 if isinstance(error,TypeError) else 2)
        assert all(path.read_bytes()==raw for path,raw in original.items())
    status,report,command=invoke('--changed',replacements={'changed_paths':lambda:(_ for _ in ()).throw(ValueError('private-selection-canary'))})
    assert status==1 and report['errors'][0]['stage']=='selection' and command.call_count==0
    for error in [OSError('private-checker-canary'),UnicodeDecodeError('utf8',b'\xff',0,1,'private-checker-canary'),subprocess.TimeoutExpired(['private-checker-canary'],1)]:
        status,report,command=invoke('--paths','one.md','--apply',child_error=error)
        assert status==1 and report['errors'][0]['code']=='lifecycle-proposed-check-failed' and command.call_count==1
    prepared_paths=[]
    def stopped_prepare(path,args):
        prepared_paths.append(path)
        if path==two:raise TypeError('private-native-canary')
        return prepared(path,args)
    def forbidden_references(*args,**kwargs):raise AssertionError('native planning abort must not trigger later reference reads')
    status,report,command=invoke('--paths','one.md','two.md','--apply',replacements={'prepare':stopped_prepare,'check_references':forbidden_references})
    assert status==1 and prepared_paths==[one,two] and command.call_count==0 and report['errors'][0]['ordinal']==2
    class NoChildTail:
        returncode=17
        @property
        def stdout(self):raise AssertionError('checker output must not be inspected')
        @property
        def stderr(self):raise AssertionError('checker output must not be inspected')
    status,report,command=invoke('--paths','one.md','--apply',child=NoChildTail())
    assert status==1 and report['errors'][0]['code']=='lifecycle-proposed-check-rejected'
    assert command.call_count==1 and command.call_args.args==(['bash',str(owner['CHECKER']),'--proposed'],)
    assert command.call_args.kwargs['input']==json.dumps({'one.md':(original[one]+b'prepared\n').decode()})
    # Traversal retains the original getter order and reads each target once;
    # report projection does not replay it or carry ignored reference fields.
    target=root/'target.md';target.write_text(HEADER.format(id='test.target',status='active'))
    visits=[];actual_read=Path.read_bytes
    class Reference(dict):
        def __getitem__(self,key):visits.append(key);return super().__getitem__(key)
    ref=Reference(id='test.target',path='target.md',ignored='private-reference-canary')
    validated=[];reads=[]
    def read(path):reads.append(path);return actual_read(path)
    with patch.object(Path,'read_bytes',read):owner['check_references']({'id':'test.source','status':'superseded','superseded_by':[ref]}, {}, validated=validated)
    assert visits==['id','id','path','path','path','id'] and reads==[target],(visits,reads)
    report={'plans':[{'before':{'superseded_by':[ref]},'after':{'superseded_by':[ref]}}]}
    owner['project_reference_reports'](report,validated)
    assert report['plans'][0]['before']['superseded_by'] is None and 'private-reference-canary' not in json.dumps(report)
    with patch.object(Path,'read_bytes',read):
        safe=[{'id':'test.target','path':'target.md'}];report={'plans':[{'before':{'superseded_by':safe},'after':{'superseded_by':safe}}]};owner['project_reference_reports'](report,validated)
    assert reads==[target] and report['plans'][0]['after']['superseded_by']==safe
    assert visits==['id','id','path','path','path','id']
    # The full preflight still precedes every write; a changed source prevents
    # all writes, including ones visited before that source's recheck.
    reads=[]
    def changed(path):
        reads.append(path);value=actual_read(path)
        return value+b'concurrent\n' if path==two and reads.count(path)==2 else value
    with patch.object(Path,'read_bytes',changed),patch.object(Path,'write_bytes',side_effect=AssertionError('preflight must finish first')):
        status,report,command=invoke('--paths','one.md','two.md','--apply')
    assert status==1 and report['errors'][0]['code']=='lifecycle-concurrent-change' and reads==[one,two,one,two]
    actual_write=Path.write_bytes;writes=[]
    def partial_write(path,value):
        writes.append(path)
        if path==two:actual_write(path,b'partial\n');raise OSError('private-write-canary')
        return actual_write(path,value)
    with patch.object(Path,'write_bytes',partial_write):status,report,command=invoke('--paths','one.md','two.md','--apply')
    assert status==1 and not report['applied'] and writes==[one,two]
    assert report['errors'][0]['stage']=='write' and report['errors'][0]['completed_returned_writes']==1 and report['errors'][0]['current_write']=='unknown'
    assert one.read_bytes()==original[one]+b'prepared\n' and two.read_bytes()==b'partial\n'
    for path,raw in original.items():path.write_bytes(raw)
    class ReceiptFailure:
        def __init__(self,selected):assert selected==root
        def record_artifacts(self,artifacts):
            assert list(artifacts)==['one.md','two.md']
            raise OSError('private-receipt-canary')
    status,report,command=invoke('--paths','one.md','two.md','--apply',replacements={'LocalCache':ReceiptFailure})
    assert status==1 and not report['applied'] and report['errors'][0]['stage']=='preparation-receipt' and report['errors'][0]['completed_returned_writes']==2
    assert all(path.read_bytes()==raw+b'prepared\n' for path,raw in original.items())
    actual_dumps=json.dumps
    for phase,emission,broken_fallback in [('selection','serialization',False),('selection','stdout',False),('selection','serialization',True),('final','serialization',False),('final','stdout',False),('final','stdout',True)]:
        for path,raw in original.items():path.write_bytes(raw)
        writes.clear();observed=[]
        out=BrokenStream() if emission=='stdout' else io.StringIO();err=BrokenStream() if broken_fallback else io.StringIO()
        def dumps(value,*args,**kwargs):
            if isinstance(value,dict) and 'plans' in value:
                observed.append(value)
                assert kwargs.get('indent')==2
                if emission=='serialization':raise ValueError('private-secondary-canary')
            return actual_dumps(value,*args,**kwargs)
        overrides={'prepare':prepared,'LocalCache':None}
        if phase=='selection':overrides['changed_paths']=lambda:(_ for _ in ()).throw(ValueError('private-selection-canary'))
        args=['--changed','--apply'] if phase=='selection' else ['--paths','one.md','two.md','--apply']
        with patch.dict(owner,overrides),patch.object(sys,'argv',['fixture',str(UPDATER),*args]),patch.object(subprocess,'run',return_value=SimpleNamespace(returncode=0)) as checker,patch.object(json,'dumps',side_effect=dumps),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err),patch.object(Path,'write_bytes',partial_write):
            status=owner['main']()
        assert status==1 and len(observed)==1 and out.getvalue()==''
        assert err.getvalue()==('' if broken_fallback else 'ERROR: lifecycle-reporting-failed\n')
        assert 'canary' not in out.getvalue()+err.getvalue() and 'Traceback' not in out.getvalue()+err.getvalue()
        if phase=='selection':
            assert writes==[] and checker.call_count==0
            assert observed[0]['errors'][0]['stage']=='selection' and not observed[0]['applied']
            assert all(path.read_bytes()==raw for path,raw in original.items())
        else:
            assert writes==[one,two] and checker.call_count==1
            assert observed[0]['errors'][0]['stage']=='write'
            assert observed[0]['errors'][0]['completed_returned_writes']==1 and observed[0]['errors'][0]['current_write']=='unknown'
            assert one.read_bytes()==original[one]+b'prepared\n' and two.read_bytes()==b'partial\n'

print("Lifecycle updater smoke tests passed (including unchanged preparation across UTC rollover and safe failed-stage/effect reporting).")
PY
