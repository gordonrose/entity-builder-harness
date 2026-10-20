# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.library.artifact-metadata.header-discovery
#   version: 1
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 01.harness
#   domain: metadata
#   disciplines:
#     - agentic
#   kind: script
#   purpose: Discover and parse file-level metadata without treating examples as artifact declarations.
#   portability:
#     class: required
#     targets:
#       - llm-workbench
#       - entity-builder
#       - design-system-builder
#   used_by:
#     - id: harness.script.artifact-metadata.check-headers
#     - id: harness.script.artifact-metadata.generate-index
#   effects:
#     - read-only

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any

import yaml


class HeaderError(ValueError):
    """A declared file header cannot be read safely."""


@dataclass(frozen=True)
class HeaderSpan:
    """Zero-based lines covering the marker through the exclusive header end."""

    start: int
    end: int
    style: str
    marker: str
    comment: str


SCAFFOLD_ROOT = "docs/00.chat/bootstrap/llm-workbench-template/root/"
EXCLUDED_PATHS = frozenset(SCAFFOLD_ROOT + name for name in (
    "scripts/install.sh.template",
    "scripts/uninstall.sh.template",
    ".github/workflows/portability.yml.template",
))
_MARKER = re.compile(r"^(<!--|#|//)[ \t]*(agentic-artifact|agentic-script):.*$")
_DOCSTRING = re.compile(r"^(?:[rRuU])?(\"\"\"|''')")
_SHELL_SETUP = re.compile(r"^set\s+(?:(?:-[a-zA-Z]+|\+?[a-zA-Z]+)(?:\s+|$))+$")


def is_excluded(path: str) -> bool:
    return PurePosixPath(path).as_posix() in EXCLUDED_PATHS


def is_legacy_script_path(path: str) -> bool:
    return (path.startswith("scripts/") and path.endswith((".sh", ".js", ".mjs"))) or (
        path.startswith(".agentic/") and path.endswith((".js", ".mjs")))


def is_legacy_markdown_path(path: str) -> bool:
    return path.endswith(".md") and path.startswith((
        ".agentic/", "docs/00.chat/", "docs/01.harness/", "docs/02.rag-rulebook/",
        "docs/03.product/", "docs/04.deploy/", "docs/06.shared/", "docs/aws/",
        "docs/education/", "docs/harness/", "infra/", "scripts/"))


def is_legacy_yaml_path(path: str) -> bool:
    return path.endswith((".yml", ".yaml")) and path.startswith((
        ".agentic/", ".github/workflows/", "docs/01.harness/", "docs/02.rag-rulebook/",
        "docs/03.product/", "docs/04.deploy/", "docs/06.shared/", "docs/aws/",
        "docs/education/", "docs/harness/", "scripts/"))


def requires_header(path: str) -> bool:
    """Keep required-header placement separate from declaration discovery."""
    return not is_excluded(path) and (
        is_legacy_script_path(path) or is_legacy_markdown_path(path) or is_legacy_yaml_path(path))


def _repository_paths(root: Path | str, include_untracked: bool) -> list[str]:
    root = Path(root).resolve()
    actual = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                            check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
    if Path(actual).resolve() != root:
        raise HeaderError(f"artifact discovery requires the exact Git root: {root}")
    command = ["git", "-C", str(root), "ls-files", "--cached", "-z"]
    if include_untracked:
        command += ["--others", "--exclude-standard"]
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE)
    return sorted(set(part.decode("utf-8", "surrogateescape")
                      for part in result.stdout.split(b"\0") if part))


def tracked_paths(root: Path | str) -> list[str]:
    return _repository_paths(root, False)


def repository_paths(root: Path | str) -> list[str]:
    """Tracked files plus unignored new files, including an unborn Git repo."""
    return _repository_paths(root, True)


def strip_comment(line: str) -> str:
    stripped = line.lstrip()
    for prefix in ("//", "#"):
        if stripped.startswith(prefix):
            content = stripped[len(prefix):]
            return content[1:] if content.startswith(" ") else content
    return line


def _marker_start(text: str) -> tuple[list[str], int, str, str] | None:
    # Only leading file material is eligible. A fenced example, patch, heredoc,
    # import, assignment, or ordinary prose ends the preamble immediately.
    lines = text.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        raw = lines[index].rstrip("\r\n")
        if index == 0:
            raw = raw.removeprefix("\ufeff")
        match = _MARKER.fullmatch(raw)
        if match:
            comment = match.group(1)
            marker = match.group(2)
            return lines, index, comment, marker
        if not raw.strip() or raw.startswith("#!"):
            index += 1
            continue
        # Indented code and blockquotes must never count as a file preamble.
        if raw != raw.lstrip():
            return None
        if raw.startswith(("#", "//")) or _SHELL_SETUP.fullmatch(raw):
            index += 1
            continue
        if raw.startswith("<!--"):
            while "-->" not in lines[index]:
                index += 1
                if index == len(lines):
                    return None
            if lines[index].split("-->", 1)[1].strip():
                return None
            index += 1
            continue
        docstring = _DOCSTRING.match(raw)
        if docstring:
            quote = docstring.group(1)
            tail = raw[docstring.end():]
            while quote not in tail:
                index += 1
                if index == len(lines):
                    return None
                tail = lines[index]
            if tail.split(quote, 1)[1].strip():
                return None
            index += 1
            continue
        return None
    return None


def has_declared_header(text: str) -> bool:
    """Recognize malformed declarations too, so validation cannot skip them."""
    return _marker_start(text) is not None


def header_span(text: str) -> HeaderSpan | None:
    located = _marker_start(text)
    if located is None:
        return None
    lines, start, comment, marker = located
    end = start + 1
    if comment == "<!--":
        while end < len(lines):
            if "-->" in lines[end]:
                if lines[end].strip() != "-->":
                    raise HeaderError("metadata closing marker must occupy its own line")
                return HeaderSpan(start, end + 1, "html", marker, comment)
            end += 1
        raise HeaderError("unterminated metadata header")
    while end < len(lines) and lines[end].lstrip().startswith(comment):
        end += 1
    return HeaderSpan(start, end, "line", marker, comment)


class _UniqueLoader(yaml.SafeLoader):
    pass


def _unique_mapping(loader: _UniqueLoader, node: yaml.MappingNode, deep: bool = False) -> dict:
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            if key in result:
                raise HeaderError(f"duplicate metadata key: {key}")
            result[key] = loader.construct_object(value_node, deep=deep)
        except TypeError as exc:
            raise HeaderError("metadata mapping keys must be scalar values") from exc
    return result


_UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def parse_header_text(text: str) -> dict[str, Any]:
    span = header_span(text)
    if span is None:
        return {}
    if "\0" in text:
        raise HeaderError("declared metadata must not contain NUL bytes")
    lines = text.splitlines()
    first = lines[span.start].removeprefix("\ufeff")
    if span.style == "html":
        marker_line = first.removeprefix("<!--").strip()
        body = ["  " + line for line in lines[span.start + 1:span.end - 1]]
    else:
        marker_line = strip_comment(first)
        body = [strip_comment(line) for line in lines[span.start + 1:span.end]]
    try:
        parsed = yaml.load("\n".join([marker_line, *body]), Loader=_UniqueLoader)
    except yaml.YAMLError as exc:
        raise HeaderError(f"invalid metadata YAML: {exc}") from exc
    if not isinstance(parsed, dict) or set(parsed) != {span.marker} or not isinstance(parsed[span.marker], dict):
        raise HeaderError("invalid metadata header shape")
    return parsed

def recover_legacy_baseline(text: str) -> dict[str, Any]:
    """Recover only unambiguous v2 identity from malformed historical YAML.

    This is for HEAD comparison after strict parsing failed. Never use it to
    validate current or proposed content, or to waive v3 lifecycle history.
    """
    if "\0" in text:
        return {}
    try:
        span = header_span(text)
    except HeaderError:
        return {}
    if span is None or span.marker != "agentic-artifact":
        return {}
    lines = text.splitlines()[span.start + 1:span.end - (span.style == "html")]
    if span.style == "line":
        lines = [strip_comment(line) for line in lines]
    identity_lines: dict[str, list[str]] = {key: [] for key in ("schema", "id", "status")}
    key_pattern = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_-]*|'(?:[^']|'')*'|\"(?:[^\"\\]|\\.)*\")\s*:")
    for line in lines:
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        # Complex, tagged, anchored, or split keys are deliberately outside
        # this narrow recovery path: they could conceal a second schema.
        if stripped.startswith(("?", ":", "!", "&", "*", "{", "[")):
            return {}
        match = key_pattern.match(stripped)
        if match:
            key_text = match.group(0).rsplit(":", 1)[0].rstrip()
            try:
                decoded_key = yaml.safe_load(key_text)
            except yaml.YAMLError:
                return {}
            if isinstance(decoded_key, str) and decoded_key in identity_lines:
                identity_lines[decoded_key].append(line)
        elif stripped.startswith(("'", '\"')):
            return {}
    recovered: dict[str, str] = {}
    indent = None
    for key in ("schema", "id", "status"):
        candidates = identity_lines[key]
        if len(candidates) != 1:
            return {}
        line = candidates[0]
        leading = len(line) - len(line.lstrip())
        if indent is not None and leading != indent:
            return {}
        indent = leading
        try:
            field = yaml.safe_load(line.strip())
        except yaml.YAMLError:
            return {}
        if not isinstance(field, dict) or set(field) != {key} or not isinstance(field[key], str):
            return {}
        recovered[key] = field[key]
    if (recovered["schema"] != "agentic-artifact/v2"
            or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)*", recovered["id"])
            or recovered["status"] not in {"draft", "active", "deprecated", "retired"}):
        return {}
    # The identity fields must be at the block's top level, never nested under
    # another key whose apparent v2 value could conceal an actual v3 schema.
    substantive = [line for line in lines if line.strip() and not line.lstrip().startswith("#")]
    if any(len(line) - len(line.lstrip()) < indent for line in substantive):
        return {}
    return {"agentic-artifact": recovered}
