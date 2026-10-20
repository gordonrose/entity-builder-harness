#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.artifact-metadata.check-headers-smoke-test
#   version: 3
#   status: active
#   created_on: "2026-06-24"
#   updated_on: "2026-10-20"
#   layer: 01.harness
#   domain: metadata
#   disciplines:
#     - agentic
#   kind: script
#   purpose: Test lifecycle validation and staged-content maintenance with isolated repository fixtures.
#   portability:
#     class: required
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - writes-files
#   used_by:
#     - id: harness.script.artifact-metadata.check-headers
#       path: scripts/01.harness/artifact-metadata/check-headers/script.sh

repo_root="$(git rev-parse --show-toplevel)"
checker="$repo_root/scripts/01.harness/artifact-metadata/check-headers/script.sh"

bash "$checker" --paths \
  .agentic/00.chat/workflows/chat-start.md \
  .agentic/shared/standards/upstream-repo-bootstrap.md \
  docs/00.chat/README.md \
  scripts/00.chat/startup/start-chat-session/script.sh \
  scripts/01.harness/artifact-metadata/check-headers/script.sh \
  scripts/01.harness/artifact-metadata/check-headers/smoke-test.sh

python3 - "$checker" <<'PY'
import copy
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

CHECKER = str(Path(sys.argv[1]).resolve())
TODAY = dt.datetime.now(dt.timezone.utc).date()
YESTERDAY = (TODAY - dt.timedelta(days=1)).isoformat()
TODAY = TODAY.isoformat()
COUNT = 0
ENV = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
ENV.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)


def payload(**overrides):
    value = {
        "schema": "agentic-artifact/v3", "id": "test.source", "version": 1,
        "status": "active", "created_on": "2024-01-01", "updated_on": TODAY,
        "layer": "01.harness", "domain": "metadata", "disciplines": ["agentic"],
        "kind": "guide", "purpose": "Exercise lifecycle validation.",
        "portability": {"class": "required", "targets": []},
        "used_by": [{"id": "test.harness"}],
    }
    value.update(overrides)
    return value


def text(value, body="Original content.\n", style="markdown"):
    header = yaml.safe_dump(value, sort_keys=False).rstrip()
    if style == "markdown":
        return "<!-- agentic-artifact:\n" + header + "\n-->\n\n" + body
    prefix = "//" if style == "javascript" else "#"
    preamble = "#!/usr/bin/env bash\n" if style == "shell" else ""
    return preamble + prefix + " agentic-artifact:\n" + "\n".join(prefix + "   " + line for line in header.splitlines()) + "\n\n" + body


def write(root, path, value, body="Original content.\n", style="markdown"):
    destination = root / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text(value, body, style) if isinstance(value, dict) else value)


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], env=ENV, check=True, text=True, capture_output=True).stdout


def check(root, *args, error=None, proposed=None):
    global COUNT
    index = root / ".git/index"
    before = index.read_bytes() if index.exists() else None
    result = subprocess.run(["bash", CHECKER, *args], cwd=root, env=ENV, text=True,
                            input=json.dumps(proposed) if proposed is not None else None,
                            capture_output=True)
    output = result.stdout + result.stderr
    after = index.read_bytes() if index.exists() else None
    assert before == after, "Checker mutated Git index"
    assert "Traceback" not in output, output
    if error is None:
        assert result.returncode == 0, output
    else:
        assert result.returncode != 0 and error in output, (error, output)
    COUNT += 1
    return output


def reset(root):
    git(root, "reset", "--hard", "HEAD")
    git(root, "clean", "-fd")


with tempfile.TemporaryDirectory(prefix="artifact-lifecycle-check-") as temp:
    root = Path(temp)
    git(root, "init", "--quiet")
    git(root, "config", "user.name", "Metadata Fixture")
    git(root, "config", "user.email", "metadata-fixture@example.invalid")
    git(root, "config", "core.hooksPath", os.devnull)
    source, target = ".agentic/source.md", ".agentic/target.md"
    replacement = [{"id": "test.target", "path": target}]
    target_payload = payload(schema="agentic-artifact/v2", id="test.target")
    target_payload.pop("created_on")
    target_payload.pop("updated_on")
    write(root, target, target_payload)

    def case(value, error=None, **options):
        write(root, source, value, **options)
        check(root, "--paths", source, error=error)

    case(payload())
    case(payload(status="draft"))
    case(payload(status="deprecated", deprecated_on="2024-02-01"))
    superseded = payload(status="superseded", superseded_on="2024-03-01", superseded_by=replacement)
    case(superseded)
    case(dict(superseded, deprecated_on="2024-02-01"))
    case(payload(status="retired"))
    case(dict(superseded, status="retired", deprecated_on="2024-02-01"))
    for field in ("created_on", "updated_on"):
        missing = payload()
        missing.pop(field)
        case(missing, "missing " + field)
    case(text(payload()).replace("'2024-01-01'", "2024-01-01"), "quoted YYYY-MM-DD")
    case(payload(created_on="2024-02-30"), "real calendar date")
    case(payload(updated_on="2024-1-2"), "quoted YYYY-MM-DD")
    case(payload(created_on=None), "missing created_on")
    case(payload(updated_on=(dt.date.fromisoformat(TODAY) + dt.timedelta(days=1)).isoformat()), "in the future")
    case(payload(created_on="2024-04-01", updated_on="2024-03-01"), "created_on must not follow")
    case(payload(status="deprecated"), "requires deprecated_on")
    case(payload(deprecated_on="2024-02-01"), "deprecated_on is only allowed")
    case(payload(status="deprecated", deprecated_on="2023-12-31"), "between created_on and updated_on")
    case(payload(status="deprecated", deprecated_on=TODAY, updated_on=YESTERDAY), "between created_on and updated_on")
    case(payload(status="superseded"), "requires superseded_on and superseded_by")
    case(payload(status="superseded", superseded_on="2024-03-01"), "provided together")
    case(payload(status="superseded", superseded_by=replacement), "provided together")
    case(dict(superseded, deprecated_on="2024-04-01"), "deprecated_on must not follow")
    case(dict(superseded, status="active"), "supersession metadata is only allowed")
    for refs in ([], None, "bad"):
        case(dict(superseded, superseded_by=refs), "non-empty list")
    case(dict(superseded, superseded_by=["bad"]), "entries must be objects")
    case(dict(superseded, superseded_by=[{"id": "test.target"}]), "repository-relative path")
    case(dict(superseded, superseded_by=[{"id": "test.target", "path": ".agentic/missing.md"}]), "missing or non-regular")
    case(dict(superseded, superseded_by=[{"id": "test.target", "path": ".agentic"}]), "missing or non-regular")
    for outside in ("../outside.md", str(root / target), "./" + target, ".agentic/../target.md"):
        case(dict(superseded, superseded_by=[{"id": "test.target", "path": outside}]), "stay inside the repository")
    case(dict(superseded, superseded_by=[{"id": "test.wrong", "path": target}]), "id/path mismatch")
    case(dict(superseded, superseded_by=[{"id": "test.source", "path": target}]), "must not reference itself")
    case(dict(superseded, superseded_by=[{"id": "test.target", "path": source}]), "must not reference itself")
    case(dict(superseded, superseded_by=replacement * 2), "duplicate superseded_by")
    write(root, target, payload(id="test.target", status="superseded", superseded_on=TODAY,
                                superseded_by=[{"id": "test.source", "path": source}]))
    case(superseded, "supersession cycle")
    write(root, target, target_payload)
    case(payload(schema="agentic-artifact/v99"), "unsupported artifact metadata schema")
    case(payload(schema=None), "unsupported artifact metadata schema")
    case(payload(schema="agentic-artifact/v2", status="superseded"), "invalid status")
    v2 = payload(schema="agentic-artifact/v2", status="retired")
    v2.pop("created_on")
    v2.pop("updated_on")
    case(v2)
    legacy = {"owner": "harness", "kind": "guide", "purpose": "Legacy.", "domain": "metadata",
              "portability": "internal", "used_by": []}
    case(legacy)
    case(dict(legacy, schema="agentic-artifact/v1"))
    case("# Missing header\n", "missing agentic-artifact")
    case("<!-- agentic-artifact:\nschema: agentic-artifact/v3\n", "unterminated")
    for path, style, kind in (("scripts/test.sh", "shell", "script"), ("scripts/test.mjs", "javascript", "script"),
                              (".agentic/test.yml", "yaml", "config")):
        value = payload(id="test." + style, kind=kind)
        if kind == "script":
            value["effects"] = ["read-only"]
        write(root, path, value, body="", style=style)
        check(root, "--paths", path)
    script_v1 = "# agentic-script:\n" + "\n".join("#   " + line for line in yaml.safe_dump(dict(legacy, effects=["read-only"])).splitlines()) + "\n"
    write(root, "scripts/legacy.sh", script_v1)
    check(root, "--paths", "scripts/legacy.sh")

    # Proposed overlays use complete proposed content, including references to new files.
    check(root, "--proposed", proposed={source: text(superseded), target: text(target_payload)})
    check(root, "--proposed", proposed={source: text(dict(superseded, superseded_by=[{"id": "test.new", "path": ".agentic/new.md"}])),
                                       ".agentic/new.md": text(payload(id="test.new"))})
    check(root, "--proposed", proposed={source: "missing header"}, error="missing agentic-artifact")
    check(root, "--proposed", proposed={source: text(superseded), target: text(payload(id="wrong.target"))}, error="id/path mismatch")
    check(root, "--proposed", proposed={"../outside.md": text(payload())}, error="unsafe proposed")
    check(root, "--proposed", proposed={source: 12}, error="must be a string")
    check(root, "--proposed", proposed={"package.json": "{}"}, error="outside metadata coverage")

    # Establish historical fixtures, including a document without metadata, in this disposable repo only.
    baseline = payload(updated_on=YESTERDAY)
    write(root, source, baseline)
    write(root, ".agentic/headerless.md", "Existing legacy text.\n")
    write(root, ".agentic/legacy.md", legacy)
    historic_deprecated = payload(id="test.past-deprecated", status="deprecated", deprecated_on="2024-02-01", updated_on=YESTERDAY)
    historic_superseded = payload(id="test.past-superseded", status="superseded", superseded_on="2024-03-01", superseded_by=replacement, updated_on=YESTERDAY)
    write(root, ".agentic/past-deprecated.md", historic_deprecated)
    write(root, ".agentic/past-superseded.md", historic_superseded)
    git(root, "add", ".")
    git(root, "commit", "--quiet", "-m", "Create isolated metadata fixtures")

    def staged(value, body="Original content.\n"):
        reset(root)
        write(root, source, value, body)
        git(root, "add", "--", source)

    staged(baseline, "Changed content.\n")
    write(root, source, payload(), "Changed content.\n")
    check(root, "--staged", error="updated_on must be today's UTC date")
    check(root, "--staged-added")  # Historical option keeps A/C/R scope.
    staged(payload(), "Changed content.\n")
    write(root, source, "invalid unstaged working-tree content")
    check(root, "--staged")
    (root / source).unlink()
    check(root, "--staged")
    staged(payload(created_on="2024-01-02"))
    check(root, "--staged", error="created_on is immutable")
    staged(payload(updated_on="2025-01-01"))
    check(root, "--staged")  # Date-only correction does not require today's updated_on.
    staged(v2)
    check(root, "--staged", error="must not be downgraded")
    staged("# Header removed\n")
    check(root, "--staged", error="must not be downgraded")
    staged(payload(status="deprecated", deprecated_on=YESTERDAY))
    check(root, "--staged", error="deprecated_on must be today's UTC date")
    staged(payload(status="deprecated", deprecated_on=TODAY))
    check(root, "--staged")
    staged(dict(superseded, superseded_on=YESTERDAY))
    check(root, "--staged", error="superseded_on must be today's UTC date")
    staged(dict(superseded, superseded_on=TODAY))
    write(root, target, payload(id="unstaged.wrong"))
    check(root, "--staged")
    git(root, "add", "--", target)
    write(root, target, target_payload)
    check(root, "--staged", error="id/path mismatch")
    staged(payload(status="superseded", superseded_on=TODAY,
                   superseded_by=[{"id": "test.new", "path": ".agentic/new.md"}]))
    write(root, ".agentic/new.md", payload(id="test.new"))
    check(root, "--staged", error="missing or non-regular")
    git(root, "add", "--", ".agentic/new.md")
    check(root, "--staged")

    reset(root)
    write(root, ".agentic/headerless.md", "Changed legacy text.\n")
    git(root, "add", "--", ".agentic/headerless.md")
    assert "1 existing headerless" in check(root, "--staged")
    write(root, ".agentic/new-headerless.md", "New ungoverned text.\n")
    git(root, "add", "--", ".agentic/new-headerless.md")
    check(root, "--staged", error="missing agentic-artifact")
    reset(root)
    write(root, target, "Removed v2 header.\n")
    git(root, "add", "--", target)
    check(root, "--staged", error="missing agentic-artifact")
    reset(root)
    write(root, target, payload(id="test.target", updated_on=YESTERDAY))
    git(root, "add", "--", target)
    check(root, "--staged", error="updated_on must be today's UTC date")
    write(root, target, payload(id="test.target"))
    git(root, "add", "--", target)
    check(root, "--staged")
    reset(root)
    write(root, ".agentic/added.md", payload(id="test.added", updated_on=YESTERDAY))
    git(root, "add", "--", ".agentic/added.md")
    check(root, "--staged", error="updated_on must be today's UTC date")

    for historical_path, historic, date_field in (
        (".agentic/past-deprecated.md", historic_deprecated, "deprecated_on"),
        (".agentic/past-superseded.md", historic_superseded, "superseded_on"),
    ):
        reset(root)
        write(root, historical_path, dict(historic, **{date_field: "2024-04-01"}))
        git(root, "add", "--", historical_path)
        check(root, "--staged", error=date_field + " is immutable while retained")
        lost_history = dict(historic, status="retired", updated_on=TODAY)
        lost_history.pop(date_field)
        lost_history.pop("superseded_by", None)
        write(root, historical_path, lost_history)
        git(root, "add", "--", historical_path)
        check(root, "--staged", error=date_field + " must be retained")
        reactivated = dict(historic, status="active", updated_on=TODAY)
        reactivated.pop(date_field)
        reactivated.pop("superseded_by", None)
        write(root, historical_path, reactivated)
        git(root, "add", "--", historical_path)
        check(root, "--staged")
    reset(root)
    write(root, ".agentic/past-deprecated.md", dict(historic_deprecated, status="superseded", updated_on=TODAY, superseded_on=TODAY, superseded_by=replacement))
    git(root, "add", "--", ".agentic/past-deprecated.md")
    check(root, "--staged")

    reset(root)
    renamed = ".agentic/renamed.md"
    git(root, "mv", "--", source, renamed)
    check(root, "--staged")
    write(root, renamed, payload(created_on="2024-01-02"))
    git(root, "add", "--", renamed)
    assert git(root, "diff", "--cached", "--name-status", "--find-renames").startswith("R")
    check(root, "--staged", error="created_on is immutable")
    write(root, renamed, payload(id="test.changed-identity"))
    git(root, "add", "--", renamed)
    check(root, "--staged", error="artifact id must be preserved")
    write(root, renamed, v2)
    git(root, "add", "--", renamed)
    check(root, "--staged", error="must not be downgraded")

    # Changes to a target must validate inbound links from unchanged sources.
    # Historical sources keep old dates unless their own content is changed.
    historic_source = ".agentic/past-superseded.md"
    renamed_target = ".agentic/renamed-target.md"
    reset(root)
    git(root, "mv", "--", target, renamed_target)
    check(root, "--staged", error="superseded_by references missing or non-regular")
    renamed_ref = [{"id": "test.target", "path": renamed_target}]
    write(root, historic_source, dict(historic_superseded, updated_on=TODAY, superseded_by=renamed_ref))
    check(root, "--staged", error="superseded_by references missing or non-regular")
    git(root, "add", "--", historic_source)
    check(root, "--staged")

    reset(root)
    git(root, "rm", "--", target)
    # Restoring only the worktree target must not repair the staged graph.
    write(root, target, target_payload)
    check(root, "--staged", error="superseded_by references missing or non-regular")
    write(root, historic_source, dict(historic_superseded, updated_on=TODAY,
          superseded_by=[{"id": "test.source", "path": source}]))
    git(root, "add", "--", historic_source)
    check(root, "--staged")

    reset(root)
    write(root, target, dict(target_payload, id="test.changed-target"))
    git(root, "add", "--", target)
    check(root, "--staged", error="superseded_by id/path mismatch")
    write(root, historic_source, dict(historic_superseded, updated_on=TODAY,
          superseded_by=[{"id": "test.changed-target", "path": target}]))
    check(root, "--staged", error="superseded_by id/path mismatch")
    git(root, "add", "--", historic_source)
    check(root, "--staged")

    reset(root)
    # A target-only content edit is valid while its historical source is unchanged.
    write(root, target, target_payload, "Target guidance changed.\n")
    git(root, "add", "--", target)
    check(root, "--staged")
    assert yaml.safe_load((root / historic_source).read_text().split("-->", 1)[0].replace("<!-- agentic-artifact:", ""))["updated_on"] == YESTERDAY
    reset(root)
    git(root, "rm", "--", historic_source, target)
    check(root, "--staged")

# A copied checker installation must remain complete and discover declarations
# independently from required-header path rules or the caller's checkout.
with tempfile.TemporaryDirectory(prefix="artifact-discovery-check-") as temp:
    import shutil
    temp = Path(temp)
    installation = temp / "installation/artifact-metadata"
    (installation / "check-headers").mkdir(parents=True)
    shutil.copyfile(CHECKER, installation / "check-headers/script.sh")
    shutil.copyfile(Path(CHECKER).parent.parent / "header_discovery.py", installation / "header_discovery.py")
    CHECKER = str(installation / "check-headers/script.sh")
    root = temp / "repo"
    root.mkdir()
    git(root, "init", "--quiet")
    git(root, "config", "user.name", "Discovery Fixture")
    git(root, "config", "user.email", "discovery@example.invalid")
    git(root, "config", "core.hooksPath", os.devnull)
    current = "src/current.ts"
    historic = payload(id="test.current", updated_on=YESTERDAY)
    declarations = {
        "README.md": text(payload(id="test.readme", updated_on=YESTERDAY)),
        "docs/general/guide.rst": text(payload(id="test.guide", updated_on=YESTERDAY)),
        "infra/templates/cloudformation.yaml": text(payload(id="test.template", updated_on=YESTERDAY), style="shell"),
        current: text(historic, style="javascript"),
        "tools/helper.py": '#!/usr/bin/env python3\n"""A module docstring."""\n\n' + text(payload(id="test.python", updated_on=YESTERDAY), style="shell").split('\n', 1)[1],
        "Dockerfile": '# syntax=docker/dockerfile:1.7\n\n' + text(payload(id="test.docker", updated_on=YESTERDAY), style="shell").split('\n', 1)[1],
        "notes/old.txt": text(payload(id="test.old", status="superseded", updated_on=YESTERDAY,
            superseded_on="2024-02-01", superseded_by=[{"id":"test.current", "path":current}])),
    }
    for path, content in declarations.items():
        write(root, path, content)
    embedded = text(payload(updated_on="9999-01-01"))
    examples = {
        "examples/fenced.md": '```markdown\n' + embedded + '```\n',
        "examples/indented.md": ''.join('    ' + line for line in embedded.splitlines(keepends=True)),
        "examples/quoted.md": ''.join('> ' + line for line in embedded.splitlines(keepends=True)),
        "examples/change.patch": 'diff --git a/README.md b/README.md\n@@ -1,2 +1,2 @@\n' + embedded,
        "examples/string.py": 'value = """\n' + embedded + '"""\n',
        "examples/docstring.py": '"""\n' + embedded + '"""\nprint("done")\n',
        "examples/heredoc.txt": "cat <<'EOF'\n" + embedded + "EOF\n",
        "src/headerless.ts": 'export const ok = true;\n',
        "tools/headerless.py": 'print("ok")\n',
        "infra/headerless.yaml": 'Resources: {}\n',
    }
    for path, content in examples.items():
        write(root, path, content)
    scaffolds = ["scripts/install.sh.template", "scripts/uninstall.sh.template", ".github/workflows/portability.yml.template"]
    for scaffold in scaffolds:
        write(root, "docs/00.chat/bootstrap/llm-workbench-template/root/" + scaffold,
              text(payload(created_on="{{ARTIFACT_CREATED_ON}}"), style="shell"))
    (root / "binary.data").write_bytes(b"\xff\xfe# agentic-artifact:\n")
    (root / "nul.data").write_bytes(b"\0binary data\n# agentic-artifact:\n")
    outside = temp / "outside.txt"
    outside.write_text(embedded)
    (root / "symlink.txt").symlink_to(outside)
    git(root, "add", ".")
    git(root, "commit", "-qm", "Declared artifacts and unrelated files")
    output = check(root, "--all")
    assert "for 7 file(s)" in output, output
    for path in declarations:
        check(root, "--paths", path)
    for path in examples:
        assert "for 0 file(s)" in check(root, "--paths", path)
    assert not list(installation.rglob("__pycache__")), "Read-only checker wrote bytecode"

    # Declarations outside the old path/extension allowlist receive full checks.
    for path, bad, message in (
        (current, text(dict(historic, updated_on="9999-01-01"), style="javascript"), "in the future"),
        (current, '// agentic-artifact:\n//   schema: [broken\n', "invalid metadata YAML"),
        ("README.md", '<!-- agentic-artifact:\nschema: agentic-artifact/v3\n', "unterminated metadata"),
        (current, text(historic, style="javascript").replace('//   id: test.current', '//   id: test.current\n//   id: test.duplicate'), "duplicate metadata key"),
        ("infra/templates/cloudformation.yaml", text(payload(status="deprecated"), style="shell"), "requires deprecated_on"),
    ):
        reset(root)
        write(root, path, bad)
        check(root, "--all", error=message)
    reset(root)
    check(root, "--proposed", proposed={"other/no-extension": text(payload())})
    check(root, "--proposed", proposed={"other/no-extension": "No header.\n"}, error="outside metadata coverage")
    check(root, "--proposed", proposed={"other/no-extension": '<!-- agentic-artifact:\nschema: [bad\n-->\n'}, error="invalid metadata YAML")
    check(root, "--proposed", proposed={"docs/00.chat/bootstrap/llm-workbench-template/root/scripts/install.sh.template": text(payload())}, error="excluded bootstrap scaffold")

    # Raw bootstrap scaffolds stay excluded when their existing placeholders change.
    scaffold = "docs/00.chat/bootstrap/llm-workbench-template/root/scripts/install.sh.template"
    (root / scaffold).write_text((root / scaffold).read_text() + "# Scaffold change.\n")
    git(root, "add", "--", scaffold)
    check(root, "--staged")
    reset(root)
    for invalid_bytes, message in ((b"\xff", "must be UTF-8"), (b"\0", "NUL bytes")):
        (root / current).write_bytes(declarations[current].encode("utf-8") + invalid_bytes)
        check(root, "--all", error=message)
        git(root, "add", "--", current)
        check(root, "--staged", error=message)
        reset(root)
    (root / current).unlink()
    (root / current).symlink_to(outside)
    git(root, "add", "--", current)
    check(root, "--staged", error="regular text repository file")
    reset(root)
    write(root, "new/untracked.custom", payload(updated_on="9999-01-01"))
    check(root, "--all", error="in the future")
    reset(root)

    # Index blobs, not unstaged repairs, determine freshness and header removal.
    write(root, current, historic, "Changed body.\n", style="javascript")
    git(root, "add", "--", current)
    write(root, current, dict(historic, updated_on=TODAY), "Changed body.\n", style="javascript")
    check(root, "--staged", error="updated_on must be today's UTC date")
    git(root, "add", "--", current)
    check(root, "--staged")
    write(root, current, dict(historic, created_on="2024-01-02"), style="javascript")
    check(root, "--staged")
    reset(root)
    write(root, current, "export const removed = true;\n")
    git(root, "add", "--", current)
    write(root, current, historic, style="javascript")
    check(root, "--staged", error="must not be downgraded or removed")

    # Renaming globally declared metadata preserves its identity and creation.
    reset(root)
    original = "tools/helper.py"
    renamed = "other/renamed.custom"
    (root / "other").mkdir()
    git(root, "mv", "--", original, renamed)
    check(root, "--staged")
    (root / renamed).write_text((root / renamed).read_text().replace("'2024-01-01'", "'2024-01-02'"))
    git(root, "add", "--", renamed)
    check(root, "--staged", error="created_on is immutable")
    reset(root)

    # Unchanged global sources still constrain staged target deletion.
    git(root, "rm", "--", current)
    write(root, current, historic, style="javascript")
    check(root, "--staged", error="superseded_by references missing or non-regular")
    reset(root)
    old = payload(id="test.old", status="superseded", updated_on=TODAY, superseded_on="2024-02-01",
                  superseded_by=[{"id":"test.outside", "path":"symlink.txt"}])
    write(root, "notes/old.txt", old)
    git(root, "add", "--", "notes/old.txt")
    check(root, "--staged", error="missing or non-regular")

    # A repaired legacy v2 header may have malformed historical YAML. Its
    # explicit identity is recoverable; ambiguous or v3 history is not waived.
    reset(root)
    legacy_path = "other/malformed-legacy.data"
    legacy_fields = payload(schema="agentic-artifact/v2", id="test.legacy-repair")
    legacy_fields.pop("created_on")
    legacy_fields.pop("updated_on")
    malformed = text(legacy_fields).replace("- id: test.harness", "- id: test.harness\n    path: docs/missing.md")
    write(root, legacy_path, malformed)
    git(root, "add", "--", legacy_path)
    git(root, "commit", "-qm", "Malformed legacy fixture")
    fixed = payload(id="test.legacy-repair")
    write(root, legacy_path, fixed)
    git(root, "add", "--", legacy_path)
    check(root, "--staged")
    write(root, legacy_path, dict(fixed, updated_on=YESTERDAY))
    git(root, "add", "--", legacy_path)
    check(root, "--staged", error="updated_on must be today's UTC date")
    reset(root)
    write(root, legacy_path, malformed.replace("schema: agentic-artifact/v2", "schema: agentic-artifact/v3"))
    git(root, "add", "--", legacy_path)
    git(root, "commit", "-qm", "Malformed v3 history must remain protected")
    write(root, legacy_path, fixed)
    git(root, "add", "--", legacy_path)
    check(root, "--staged", error="invalid metadata YAML")
    reset(root)
    ambiguous = malformed.replace("schema: agentic-artifact/v2", "schema: agentic-artifact/v2\nschema: agentic-artifact/v3")
    write(root, legacy_path, ambiguous)
    git(root, "add", "--", legacy_path)
    git(root, "commit", "-qm", "Ambiguous schema history must remain protected")
    write(root, legacy_path, fixed)
    git(root, "add", "--", legacy_path)
    check(root, "--staged", error="invalid metadata YAML")

    for key, value in (("\"schema\"", "agentic-artifact/v3"), ("'schema'", "agentic-artifact/v3"),
                       ('"sch\\u0065ma"', "agentic-artifact/v3"), ("\"id\"", "test.hidden"), ("'status'", "retired")):
        reset(root)
        ambiguous = malformed.replace("schema: agentic-artifact/v2", "schema: agentic-artifact/v2\n" + key + ": " + value)
        write(root, legacy_path, ambiguous)
        git(root, "add", "--", legacy_path)
        git(root, "commit", "-qm", "Quoted historical identity ambiguity")
        write(root, legacy_path, fixed)
        git(root, "add", "--", legacy_path)
        check(root, "--staged", error="invalid metadata YAML")
    reset(root)
    write(root, legacy_path, malformed + "\0")
    git(root, "add", "--", legacy_path)
    git(root, "commit", "-qm", "NUL historical metadata is not recoverable")
    write(root, legacy_path, fixed)
    git(root, "add", "--", legacy_path)
    check(root, "--staged", error="NUL bytes")

print(f"Artifact metadata header checker smoke test passed ({COUNT} assertions).")
PY
