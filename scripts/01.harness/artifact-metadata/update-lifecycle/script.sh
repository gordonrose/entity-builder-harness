#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.script.artifact-metadata.update-lifecycle
#   version: 3
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-26"
#   layer: 01.harness
#   domain: metadata
#   disciplines:
#     - agentic
#   kind: script
#   purpose: Report or apply bounded artifact lifecycle metadata updates without staging or committing.
#   portability:
#     class: required
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   effects:
#     - read-only
#     - writes-files
#   used_by:
#     - id: harness.standard.artifact-metadata
#       path: .agentic/01.harness/artifact-metadata/standard.md

python3 - "${BASH_SOURCE[0]}" "$@" <<'PY'
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(sys.argv[1]).resolve().parents[1]))
try:
    from header_discovery import (
        HeaderError, header_span, is_excluded, parse_header_text, recover_legacy_baseline,
    )
except ImportError as exc:
    raise SystemExit(f"ERROR: artifact metadata discovery support is required: {exc}")


class PlanError(Exception):
    pass


def git(*args, check=True):
    return subprocess.run(
        ["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check
    )


ROOT = Path(git("rev-parse", "--show-toplevel").stdout.decode().strip()).resolve()
CHECKER = Path(sys.argv[1]).resolve().parents[1] / "check-headers" / "script.sh"
TODAY = dt.datetime.now(dt.timezone.utc).date().isoformat()
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)*$")
DATE_KEYS = ("created_on", "updated_on", "deprecated_on", "superseded_on")


def iso_date(value, key):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise PlanError(f"{key} must be a quoted YYYY-MM-DD string")
    try:
        dt.date.fromisoformat(value)
    except ValueError as exc:
        raise PlanError(f"{key} is not a valid calendar date: {value}") from exc
    if value > TODAY:
        raise PlanError(f"{key} is in the future: {value}")
    return value


def explicit_path(raw):
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    # Never follow a symlink, including one of the parent directories.
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise PlanError(f"symlink paths are not supported: {raw}")
    path = path.resolve()
    if not path.is_relative_to(ROOT) or ".git" in path.relative_to(ROOT).parts:
        raise PlanError(f"path must be a repository file outside .git: {raw}")
    if is_excluded(path.relative_to(ROOT).as_posix()):
        raise PlanError(f"bootstrap output scaffolds are excluded from lifecycle updates: {raw}")
    if not path.is_file():
        raise PlanError(f"file does not exist: {raw}")
    return path


def changed_paths():
    """Return current task candidates without staging or following deletions."""
    changed = set(git("diff", "--name-only", "-z", "--diff-filter=ACMR", "HEAD").stdout.decode().split("\0"))
    changed.update(git("ls-files", "--others", "--exclude-standard", "-z").stdout.decode().split("\0"))
    return sorted(path for path in changed if path)


def lifecycle_candidate(path):
    """Only v2/v3 artifact headers belong to automatic lifecycle maintenance.

    Legacy and headerless source can be part of a verification task but must not
    be rewritten merely because a task-preparation command saw it. A malformed
    leading artifact declaration remains a candidate so the normal planner can
    report it instead of silently skipping it.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise PlanError(f"artifact must be UTF-8 text: {exc}") from exc
    try:
        span = header_span(text)
        if span is None or span.marker != "agentic-artifact":
            return False
        parsed = parse_header_text(text).get("agentic-artifact", {})
        return not isinstance(parsed, dict) or parsed.get("schema") in ("agentic-artifact/v2", "agentic-artifact/v3")
    except HeaderError:
        return "agentic-artifact:" in text[:8192]


class Header:
    """Edit only named metadata lines; retain all unrelated file bytes."""

    def __init__(self, raw):
        try:
            self.lines = raw.decode("utf-8").splitlines(keepends=True)
        except UnicodeError as exc:
            raise PlanError("artifact must be UTF-8 text") from exc
        self.newline = "\r\n" if any(s.endswith("\r\n") for s in self.lines) else "\n"
        try:
            text = raw.decode("utf-8")
            span = header_span(text)
            parsed = parse_header_text(text)
        except HeaderError as exc:
            raise PlanError(str(exc)) from exc
        if span is None or span.marker != "agentic-artifact":
            raise PlanError("requires an existing file-level agentic-artifact/v2 or v3 header")
        self.start = span.start
        self.markdown = span.style == "html"
        self.comment = span.comment
        # Editing offsets exclude the HTML close but include all metadata lines.
        self.end = span.end - 1 if self.markdown else span.end
        block = self.lines[self.start + 1:self.end]
        if self.markdown:
            schema_line = next((line for line in block if re.match(r"^\s*schema:", line)), "")
            self.prefix = schema_line[:schema_line.index("schema:")] if schema_line else ""
        else:
            schema_line = next(
                (line for line in block if re.match(r"^\s*" + re.escape(self.comment) + r"\s+schema:", line)), ""
            )
            self.prefix = schema_line[:schema_line.index("schema:")] if schema_line else self.comment + "   "
        self.data = parsed["agentic-artifact"]
        if self.data.get("schema") not in ("agentic-artifact/v2", "agentic-artifact/v3"):
            raise PlanError("only v2 and v3 headers can be updated")
        if not isinstance(self.data.get("id"), str) or not ID_RE.fullmatch(self.data["id"]):
            raise PlanError("artifact requires a valid stable ID")
        if self.data.get("status") not in ("draft", "active", "deprecated", "superseded", "retired"):
            raise PlanError("artifact requires a valid status")
        if self.data["schema"] == "agentic-artifact/v2" and self.data["status"] == "superseded":
            raise PlanError("status: superseded requires an existing v3 header")

    def set_field(self, key, value):
        # Preserve comments on unchanged fields. Lifecycle fields deliberately
        # use double-quoted dates in all newly written metadata.
        if self.data.get(key) == value:
            return
        field_re = re.compile(re.escape(self.prefix) + re.escape(key) + r":")
        index = next(
            (i for i in range(self.start + 1, self.end) if field_re.match(self.lines[i])),
            None,
        )
        if key == "superseded_by":
            replacement = [self.prefix + "superseded_by:" + self.newline]
            for ref in value:
                replacement.extend([
                    self.prefix + "  - id: " + ref["id"] + self.newline,
                    self.prefix + "    path: " + json.dumps(ref["path"]) + self.newline,
                ])
        else:
            rendered = json.dumps(value) if key in DATE_KEYS else str(value)
            replacement = [self.prefix + key + ": " + rendered + self.newline]
        if index is None:
            anchor = {
                "created_on": "status",
                "updated_on": "created_on",
                "deprecated_on": "updated_on",
                "superseded_on": "deprecated_on" if "deprecated_on" in self.data else "updated_on",
                "superseded_by": "superseded_on",
            }.get(key, "status")
            anchor_re = re.compile(re.escape(self.prefix) + re.escape(anchor) + r":")
            index = next(
                (i + 1 for i in range(self.start + 1, self.end) if anchor_re.match(self.lines[i])),
                self.end,
            )
            end = index
        else:
            end = index + 1
            if key == "superseded_by":
                # YAML supports both indented and indentless sequence entries.
                top_field = re.compile(re.escape(self.prefix) + r"[a-zA-Z_][a-zA-Z_0-9-]*:")
                while end < self.end and not top_field.match(self.lines[end]):
                    end += 1
        self.lines[index:end] = replacement
        self.end += len(replacement) - (end - index)
        self.data[key] = value

    def notice(self, path, references):
        if not self.markdown:
            return
        title = next(
            (i for i in range(self.end + 1, len(self.lines)) if self.lines[i].startswith("# ")),
            None,
        )
        if title is None:
            raise PlanError("superseded Markdown artifact requires an H1 title for the visible notice")
        links = []
        for ref in references:
            relative = os.path.relpath(ROOT / ref["path"], path.parent)
            links.append(f'[{ref["id"]}]({quote(relative, safe="/.-_")})')
        notice = "> Superseded by " + ", ".join(links) + "." + self.newline
        cursor = title + 1
        while cursor < len(self.lines) and not self.lines[cursor].strip():
            cursor += 1
        if cursor < len(self.lines) and self.lines[cursor].startswith("> Superseded by "):
            self.lines[cursor] = notice
        else:
            self.lines[title + 1:title + 1] = [self.newline, notice, self.newline]

    def render(self):
        return "".join(self.lines).encode("utf-8")


def utc_commit_date(value):
    return dt.datetime.fromisoformat(value).astimezone(dt.timezone.utc).date().isoformat()


def head_baseline(path, own_id):
    """Find an existing artifact at this path or its unambiguous rename source."""
    relative = path.relative_to(ROOT).as_posix()
    direct = git("show", f"HEAD:{relative}", check=False)
    if direct.returncode == 0:
        return relative, direct.stdout
    changes = git(
        "diff", "--name-status", "-z", "--find-renames", "--diff-filter=RD", "HEAD", check=False
    )
    fields = iter(changes.stdout.decode().split("\0")[:-1])
    deleted = set()
    detected_sources = set()
    for status in fields:
        source = next(fields)
        if status.startswith("R"):
            target = next(fields)
            if target == relative:
                detected_sources.add(source)
        else:
            deleted.add(source)
    candidates = {}
    for source in sorted(deleted | detected_sources):
        previous = git("show", f"HEAD:{source}", check=False)
        if previous.returncode != 0:
            continue
        try:
            source_id = Header(previous.stdout).data["id"]
        except PlanError:
            if source in detected_sources:
                raise PlanError("cannot establish metadata identity for the detected rename source")
            continue
        if source_id == own_id:
            candidates[source] = previous.stdout
        elif source in detected_sources:
            raise PlanError("artifact ID differs from the detected HEAD rename source")
    if len(candidates) > 1:
        raise PlanError("multiple deleted HEAD artifacts share this ID; rename baseline is ambiguous")
    if candidates:
        return next(iter(candidates.items()))
    return None, None


def evidence(path):
    relative = path.relative_to(ROOT).as_posix()
    last = git("log", "-1", "--format=%H%x00%cI", "--", relative).stdout.decode().strip()
    result = {"last_committed_on": None, "last_commit": None}
    if last:
        commit, timestamp = last.split("\0")
        result.update(last_committed_on=utc_commit_date(timestamp), last_commit=commit)
    shallow = git("rev-parse", "--is-shallow-repository").stdout.strip() == b"true"
    first = git(
        "log", "--follow", "--diff-filter=A", "--format=%H%x00%cI", "--", relative
    ).stdout.decode().splitlines()
    if len(first) > 1 and not shallow:
        result.update(
            basis="unknown",
            reason="Multiple addition events indicate ambiguous deletion/recreation history.",
        )
    elif first and not shallow:
        commit, timestamp = first[-1].split("\0")
        result.update(
            basis="git-first-added", created_on=utc_commit_date(timestamp), commit=commit,
            meaning="Repository introduction in available Git history; not a claim of original authorship.",
        )
        addition_paths = [
            value for value in git(
                "log", "--follow", "--diff-filter=A", "--format=", "--name-only", "-z", "--", relative
            ).stdout.decode().split("\0") if value
        ]
        if len(addition_paths) != 1:
            result.update(basis="unknown", reason="Could not identify an unambiguous original added path.")
        else:
            added = git("show", f"{commit}:{addition_paths[0]}", check=False)
            if added.returncode == 0:
                try:
                    old_id = Header(added.stdout).data["id"]
                    if old_id != Header(path.read_bytes()).data["id"]:
                        result.update(
                            basis="unknown",
                            reason="The first-added artifact ID differs from the current ID.",
                        )
                except PlanError:
                    # Older versions may predate metadata; the Git date is
                    # still explicitly only repository-introduction evidence.
                    pass
    elif not first and not last and not shallow:
        # Uncommitted renames, including unstaged moves and heavily edited
        # staged moves, must not silently become newly created artifacts.
        own_id = Header(path.read_bytes()).data["id"]
        source, previous = head_baseline(path, own_id)
        if previous is None:
            result.update(basis="new-artifact", created_on=TODAY)
        else:
            result.update(
                basis="unknown", reason="No reliable addition event; possible uncommitted rename.",
                head_source=source,
            )
    else:
        result.update(
            basis="unknown",
            reason="Shallow history." if shallow else "No reliable first-addition commit in available history.",
        )
    return result


def validate_dates(data):
    for key in DATE_KEYS:
        if key in data:
            iso_date(data[key], key)
    if not all(key in data for key in ("created_on", "updated_on")):
        raise PlanError("v3 requires created_on and updated_on")
    if data["created_on"] > data["updated_on"]:
        raise PlanError("created_on must be on or before updated_on")
    for key in ("deprecated_on", "superseded_on"):
        if key in data and not data["created_on"] <= data[key] <= data["updated_on"]:
            raise PlanError(f"{key} must fall between created_on and updated_on")
    if data["status"] == "deprecated" and "deprecated_on" not in data:
        raise PlanError("existing deprecation requires --deprecated-on with a confirmed historical date")
    if data["status"] == "superseded" and "superseded_on" not in data:
        raise PlanError("existing supersession requires --superseded-on with a confirmed historical date")
    if "deprecated_on" in data and "superseded_on" in data:
        if data["deprecated_on"] > data["superseded_on"]:
            raise PlanError("deprecated_on must be on or before superseded_on")
    if ("superseded_on" in data) != ("superseded_by" in data):
        raise PlanError("superseded_on and superseded_by must be present together")
    if data["status"] not in ("superseded", "retired") and ("superseded_on" in data or "superseded_by" in data):
        raise PlanError("supersession metadata requires status: superseded or retired")
    if data["status"] in ("draft", "active") and "deprecated_on" in data:
        raise PlanError("active/draft artifacts cannot retain a deprecation date")


def replacement_refs(raw_paths, own_id):
    result = []
    seen = set()
    for raw in raw_paths:
        path = explicit_path(raw)
        header = Header(path.read_bytes())
        ref = {"id": header.data["id"], "path": path.relative_to(ROOT).as_posix()}
        if ref["id"] == own_id:
            raise PlanError("superseded_by cannot refer to the same artifact ID")
        if ref["id"] in seen:
            raise PlanError(f"duplicate replacement ID: {ref['id']}")
        seen.add(ref["id"])
        result.append(ref)
    return result


def check_references(data, plans, trail=()):
    own_id = data["id"]
    if own_id in trail:
        raise PlanError("supersession cycle: " + " -> ".join((*trail, own_id)))
    references = data.get("superseded_by", [])
    if data["status"] == "superseded" and not references:
        raise PlanError("superseded artifacts require at least one --replacement")
    if not isinstance(references, list):
        raise PlanError("superseded_by must be an array")
    seen = set()
    for ref in references:
        if not isinstance(ref, dict) or not isinstance(ref.get("path"), str) or not isinstance(ref.get("id"), str):
            raise PlanError("replacement references require an ID and repository path")
        if ref["id"] in seen:
            raise PlanError(f"duplicate replacement ID: {ref['id']}")
        seen.add(ref["id"])
        if Path(ref["path"]).is_absolute() or ".." in Path(ref["path"]).parts:
            raise PlanError("replacement paths must be repository-relative without parent traversal")
        path = explicit_path(ref["path"])
        target = plans.get(path)
        target_data = target["header"].data if target else Header(path.read_bytes()).data
        if target_data["id"] != ref["id"]:
            raise PlanError(f"replacement ID does not match {ref['path']}")
        check_references(target_data, plans, (*trail, own_id))


def prepare(path, args):
    raw = path.read_bytes()
    header = Header(raw)
    original = dict(header.data)
    # Fail before planning writes or serializing a report. In particular,
    # PyYAML decodes unquoted dates as date objects, not the v3 string type.
    for key in DATE_KEYS:
        if key in original:
            iso_date(original[key], key)
    history = evidence(path)
    if "created_on" in original:
        created = iso_date(original["created_on"], "created_on")
        if args.created_on and args.created_on != created:
            raise PlanError("--created-on cannot overwrite an existing creation date")
        provenance = {"basis": "existing-header", "created_on": created, "history": history}
    elif args.created_on:
        created = iso_date(args.created_on, "--created-on")
        provenance = {"basis": "explicit-date", "created_on": created, "history": history}
    elif history["basis"] != "unknown":
        created = history["created_on"]
        provenance = history
    else:
        raise PlanError(history["reason"] + " Supply --created-on only with confirmed creation evidence.")
    header.set_field("schema", "agentic-artifact/v3")
    header.set_field("created_on", created)
    if args.status:
        if original["status"] in ("superseded", "retired") and args.status != original["status"]:
            raise PlanError("this bounded updater does not reactivate superseded or retired artifacts")
        header.set_field("status", args.status)
        event = args.status + "_on"
        if original["status"] != args.status:
            header.set_field(event, TODAY)
    for key in ("deprecated_on", "superseded_on"):
        value = getattr(args, key)
        if value:
            iso_date(value, "--" + key.replace("_", "-"))
            if args.status and original["status"] != args.status and key == args.status + "_on" and value != TODAY:
                raise PlanError("a new lifecycle transition must use today's UTC date")
            if key in original and original[key] != value:
                raise PlanError(f"cannot overwrite an existing {key} event")
            header.set_field(key, value)
    if args.replacement:
        if header.data["status"] != "superseded":
            raise PlanError("--replacement requires status: superseded")
        header.set_field("superseded_by", replacement_refs(args.replacement, header.data["id"]))
    if header.data["status"] == "superseded":
        references = header.data.get("superseded_by", [])
        if not references:
            raise PlanError("superseded artifacts require at least one --replacement")
        if not isinstance(references, list) or any(
            not isinstance(ref, dict) or not isinstance(ref.get("id"), str) or not isinstance(ref.get("path"), str)
            for ref in references
        ):
            raise PlanError("replacement references require an ID and repository path")
        header.notice(path, references)
    relative = path.relative_to(ROOT).as_posix()
    baseline_path, baseline = head_baseline(path, original["id"])
    if baseline is not None and original["schema"] == "agentic-artifact/v3":
        try:
            old_data = Header(baseline).data
        except PlanError:
            # A repaired legacy header may still be malformed in HEAD until
            # this migration is committed. Recover only an unambiguous v2
            # identity; never waive historical v3 creation-date protection.
            old_data = recover_legacy_baseline(baseline.decode("utf-8")).get("agentic-artifact")
            if old_data is None:
                raise
        if old_data["schema"] == "agentic-artifact/v3":
            if old_data.get("created_on") != created:
                raise PlanError("created_on differs from HEAD; creation dates are immutable after migration")
    # Ignore changes to the update-date line when deciding whether content
    # differs from HEAD. Reading an unchanged old artifact must be a no-op.
    def strip_updated(value):
        try:
            parsed = Header(value)
        except PlanError:
            return value
        line_re = re.compile(re.escape(parsed.prefix) + r"updated_on:")
        return "".join(
            line for index, line in enumerate(parsed.lines)
            if not (parsed.start < index < parsed.end and line_re.match(line))
        ).encode("utf-8")
    content_changed = (
        baseline is not None and strip_updated(raw) != strip_updated(baseline)
    ) or (baseline is None and history["basis"] == "new-artifact")
    if header.render() != raw or content_changed or "updated_on" not in header.data:
        header.set_field("updated_on", TODAY)
    validate_dates(header.data)
    rendered = header.render()
    return {
        "path": path,
        "original": raw,
        "rendered": rendered,
        "header": header,
        "report": {
            "path": relative,
            "id": header.data["id"],
            "changed": rendered != raw,
            "content_differs_from_head": content_changed,
            "head_baseline_path": baseline_path,
            "creation_evidence": provenance,
            "last_committed_on": history["last_committed_on"],
            "before": {key: original.get(key) for key in ("schema", "status", *DATE_KEYS, "superseded_by")},
            "after": {key: header.data.get(key) for key in ("schema", "status", *DATE_KEYS, "superseded_by")},
            "sha256_before": hashlib.sha256(raw).hexdigest(),
            "sha256_after": hashlib.sha256(rendered).hexdigest(),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Report lifecycle changes for explicit paths; --apply writes only a fully valid plan. Never stages or commits."
    )
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--paths", nargs="+", help="repository-relative explicit paths")
    selection.add_argument("--changed", action="store_true", help="prepare all changed v2/v3 artifact headers without staging")
    parser.add_argument("--skip-non-artifacts", action="store_true", help="ignore headerless and legacy paths in an explicit task path set")
    parser.add_argument("--apply", action="store_true", help="apply the complete validated plan")
    parser.add_argument("--created-on", help="explicitly confirmed creation date when automatic Git evidence is insufficient")
    parser.add_argument("--status", choices=("deprecated", "superseded"), help="explicit lifecycle transition")
    parser.add_argument("--replacement", action="append", default=[], help="replacement artifact path (repeatable)")
    parser.add_argument("--deprecated-on", help="confirmed historical deprecation date")
    parser.add_argument("--superseded-on", help="confirmed historical supersession date")
    args = parser.parse_args(sys.argv[2:])
    if args.changed and (args.status or args.replacement or args.deprecated_on or args.superseded_on or args.created_on):
        parser.error("--changed only refreshes existing lifecycle metadata; use --paths for explicit transitions or dates")
    raw_paths = changed_paths() if args.changed else args.paths
    skip_non_artifacts = args.changed or args.skip_non_artifacts
    report = {"mode": "apply" if args.apply else "report", "selection": "changed-artifacts" if args.changed else "explicit-paths", "today_utc": TODAY, "plans": [], "skipped": [], "errors": [], "applied": False}
    plans = {}
    for raw_path in raw_paths:
        try:
            path = explicit_path(raw_path)
            if path in plans:
                raise PlanError("duplicate explicit path")
            if skip_non_artifacts and not lifecycle_candidate(path):
                report["skipped"].append({"path": path.relative_to(ROOT).as_posix(), "reason": "not-a-v2-or-v3-artifact"})
                continue
            plan = prepare(path, args)
            plans[path] = plan
            report["plans"].append(plan["report"])
        except (PlanError, OSError, ValueError) as exc:
            report["errors"].append({"path": raw_path, "error": str(exc)})
    for path, plan in plans.items():
        try:
            check_references(plan["header"].data, plans)
        except (PlanError, OSError, ValueError) as exc:
            report["errors"].append({"path": path.relative_to(ROOT).as_posix(), "error": str(exc)})
    if plans and not report["errors"]:
        proposed = {
            path.relative_to(ROOT).as_posix(): plan["rendered"].decode("utf-8")
            for path, plan in plans.items()
        }
        validation = subprocess.run(
            ["bash", str(CHECKER), "--proposed"],
            input=json.dumps(proposed), text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if validation.returncode:
            report["errors"].append({
                "path": "<batch>",
                "error": "Proposed header validation failed: " + validation.stdout + validation.stderr,
            })
    if args.apply and not report["errors"]:
        # Recheck every source immediately before any mutation. Invalid plans
        # or detected concurrent edits cause no writes; this is not a
        # transactional guarantee against later filesystem I/O failures.
        for path, plan in plans.items():
            try:
                if explicit_path(str(path)).read_bytes() != plan["original"]:
                    raise PlanError("file changed during planning; rerun the report")
            except (PlanError, OSError) as exc:
                report["errors"].append({"path": path.relative_to(ROOT).as_posix(), "error": str(exc)})
        if not report["errors"]:
            for path, plan in plans.items():
                if plan["rendered"] != plan["original"]:
                    path.write_bytes(plan["rendered"])
            report["applied"] = True
    print(json.dumps(report, indent=2))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
PY
