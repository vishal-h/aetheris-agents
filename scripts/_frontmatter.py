"""Minimal YAML-frontmatter reader shared by `gen_index.py` and `drift_check.py`.

Deliberately stdlib-only: `drift_check.py` runs inside the harness sprint and the
export pre-flight, and neither may grow a third-party import for the sake of a header
block. The subset accepted is the subset the research tree's frontmatter uses —
`key: value` scalars (plain, "double-quoted" with backslash escapes, 'single-quoted'),
one level of nested map by two-space indentation, and block lists of scalars. Anything
outside that subset is a parse error, reported rather than guessed at: the generator
refuses on it, and the drift arm fails on it. `tests/test_gen_index.py` cross-checks the
reader against PyYAML on the committed research tree when PyYAML is importable, so the
subset cannot silently diverge from what a real YAML reader would return.

The document shape:

    ---
    type: brief
    title: "Research brief: ..."
    description: One line, feeds the index.
    generated:
      by: research-session
      at: 2026-06-24
    ---
    # Heading

A file that does not START with the `---` fence has no frontmatter. That is a distinct
answer from a fence that fails to parse, and both are distinct from a fence that parses
but lacks a required field; callers get all three apart.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

FENCE = "---"

Scalar = str
Value = "Scalar | dict[str, Scalar] | list[Scalar]"


class FrontmatterError(ValueError):
    """The fence was present and its content could not be read as frontmatter."""


@dataclass(frozen=True)
class Document:
    frontmatter: dict | None   # None when the file carries no opening fence
    body: str                  # everything after the closing fence (or the whole file)


_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s+(.*))?$")
_NESTED_KEY_RE = re.compile(r"^  ([A-Za-z_][A-Za-z0-9_-]*):(?:\s+(.*))?$")
_LIST_ITEM_RE = re.compile(r"^  - (.*)$")


def _unquote(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        inner = raw[1:-1]
        out: list[str] = []
        i = 0
        while i < len(inner):
            ch = inner[i]
            if ch == "\\" and i + 1 < len(inner):
                nxt = inner[i + 1]
                out.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, nxt))
                i += 2
            else:
                out.append(ch)
                i += 1
        return "".join(out)
    if len(raw) >= 2 and raw[0] == "'" and raw[-1] == "'":
        return raw[1:-1].replace("''", "'")
    if raw.startswith(("'", '"')):
        raise FrontmatterError(f"unterminated quoted scalar: {raw!r}")
    # A plain scalar may not begin with YAML flow/indicator characters this reader does
    # not implement; say so rather than returning a string a YAML reader would not.
    if raw[:1] in ("[", "{", "&", "*", "!", "|", ">", "%", "@", "`"):
        raise FrontmatterError(f"unsupported scalar form (quote it): {raw!r}")
    return raw


def parse_frontmatter_block(lines: list[str]) -> dict:
    """Parse the lines BETWEEN the fences. Raises FrontmatterError on anything unread."""
    data: dict = {}
    current_key: str | None = None
    current_container: dict | list | None = None
    for n, line in enumerate(lines, start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _KEY_RE.match(line)
        if m:
            key, raw = m.group(1), m.group(2)
            if key in data:
                raise FrontmatterError(f"line {n}: duplicate key {key!r}")
            if raw is None or raw.strip() == "":
                # Container opener: the following indented lines decide map vs list.
                data[key] = None
                current_key, current_container = key, None
            else:
                data[key] = _unquote(raw)
                current_key, current_container = None, None
            continue
        m = _NESTED_KEY_RE.match(line)
        if m and current_key is not None:
            if current_container is None:
                current_container = {}
                data[current_key] = current_container
            if not isinstance(current_container, dict):
                raise FrontmatterError(f"line {n}: map entry inside a list under {current_key!r}")
            sub, raw = m.group(1), m.group(2)
            if raw is None or raw.strip() == "":
                raise FrontmatterError(f"line {n}: nesting deeper than one level under {current_key!r}")
            if sub in current_container:
                raise FrontmatterError(f"line {n}: duplicate key {current_key}.{sub}")
            current_container[sub] = _unquote(raw)
            continue
        m = _LIST_ITEM_RE.match(line)
        if m and current_key is not None:
            if current_container is None:
                current_container = []
                data[current_key] = current_container
            if not isinstance(current_container, list):
                raise FrontmatterError(f"line {n}: list item inside a map under {current_key!r}")
            current_container.append(_unquote(m.group(1)))
            continue
        raise FrontmatterError(f"line {n}: unreadable frontmatter line: {line!r}")
    for key, value in data.items():
        if value is None:
            raise FrontmatterError(f"key {key!r} opens a container that has no entries")
    return data


def read_document(text: str) -> Document:
    """Split a markdown file into frontmatter and body.

    - no opening fence on line 1 → `Document(None, text)`
    - opening fence with no closing fence, or unparseable content → FrontmatterError
    """
    lines = text.split("\n")
    if not lines or lines[0].rstrip("\r") != FENCE:
        return Document(None, text)
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r") == FENCE:
            data = parse_frontmatter_block(lines[1:i])
            return Document(data, "\n".join(lines[i + 1:]))
    raise FrontmatterError("opening fence without a closing fence")


def first_heading(body: str) -> str | None:
    """The first `# ` H1 line's text, or None when the body has no H1."""
    for line in body.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return None
