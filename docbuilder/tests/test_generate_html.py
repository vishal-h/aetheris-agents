"""Tests for generate_html.py (m6 t1) — the Jinja2 narrative renderer.

Exercises the importable `render_html` directly and the CLI via subprocess.
Skips cleanly if jinja2 is not installed (per the requirements.txt convention).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("jinja2")

from generate_html import render_html

USE_CASE_ROOT = Path(__file__).parent.parent
SCRIPT = USE_CASE_ROOT / "scripts" / "generate_html.py"


def _write(tmp_path, name, body):
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


# --- render_html (importable) ---

def test_present_variable_rendered(tmp_path):
    t = _write(tmp_path, "t.html.j2", "<p>Hello {{ name }}</p>")
    assert render_html(t, {"name": "World"}) == "<p>Hello World</p>"


def test_absent_variable_renders_empty(tmp_path):
    # Undefined variable → empty string, NOT an exception and NOT a raw {{ }}.
    t = _write(tmp_path, "t.html.j2", "<p>Hello {{ missing }}</p>")
    out = render_html(t, {})
    assert out == "<p>Hello </p>"
    assert "{{" not in out


def test_default_filter(tmp_path):
    t = _write(tmp_path, "t.html.j2", "<p>{{ name | default('—') }}</p>")
    assert render_html(t, {}) == "<p>—</p>"
    assert render_html(t, {"name": "X"}) == "<p>X</p>"


def test_if_block_present_and_absent(tmp_path):
    t = _write(tmp_path, "t.html.j2", "A{% if show %}-YES{% endif %}B")
    assert render_html(t, {"show": True}) == "A-YESB"
    assert render_html(t, {}) == "AB"            # undefined → falsy → skipped


def test_for_loop(tmp_path):
    t = _write(tmp_path, "t.html.j2", "{% for i in items %}[{{ i }}]{% endfor %}")
    assert render_html(t, {"items": [1, 2, 3]}) == "[1][2][3]"


def test_spec_available_in_template(tmp_path):
    t = _write(tmp_path, "t.html.j2", "{% for s in spec.sheets %}{{ s }};{% endfor %}")
    assert render_html(t, {}, spec={"sheets": ["a", "b"]}) == "a;b;"


def test_autoescape_html(tmp_path):
    # HTML autoescaping is on — a value with markup is escaped, not injected.
    t = _write(tmp_path, "t.html.j2", "<p>{{ v }}</p>")
    out = render_html(t, {"v": "<b>x</b>"})
    assert "&lt;b&gt;" in out
    assert "<b>x</b>" not in out


def test_missing_template_raises(tmp_path):
    import jinja2
    with pytest.raises(jinja2.TemplateNotFound):
        render_html(tmp_path / "does_not_exist.html.j2", {})


def test_syntax_error_raises(tmp_path):
    import jinja2
    t = _write(tmp_path, "bad.html.j2", "{% if %}")   # malformed
    with pytest.raises(jinja2.TemplateSyntaxError):
        render_html(t, {})


# --- CLI ---

def _run(args, **kw):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, cwd=str(USE_CASE_ROOT), **kw
    )


def test_cli_stdout(tmp_path):
    t = _write(tmp_path, "t.html.j2", '<p>Hello {{ name | default("") }}</p>')
    r = _run(["--template", str(t), "--context", '{"name":"World"}'])
    assert r.returncode == 0, r.stderr
    assert r.stdout == "<p>Hello World</p>"


def test_cli_absent_var_empty(tmp_path):
    t = _write(tmp_path, "t.html.j2", '<p>Hello {{ name | default("") }}</p>')
    r = _run(["--template", str(t), "--context", "{}"])
    assert r.returncode == 0, r.stderr
    assert r.stdout == "<p>Hello </p>"


def test_cli_output_file(tmp_path):
    t = _write(tmp_path, "t.html.j2", "<p>{{ x }}</p>")
    out = tmp_path / "out.html"
    r = _run(["--template", str(t), "--context", '{"x":"Y"}', "--output", str(out)])
    assert r.returncode == 0, r.stderr
    assert out.read_text() == "<p>Y</p>"
    assert r.stdout.strip() == str(out)          # prints the path, not the HTML


def test_cli_spec_file(tmp_path):
    t = _write(tmp_path, "t.html.j2", "{{ spec.title }}")
    spec = _write(tmp_path, "spec.json", '{"title":"Quarterly"}')
    r = _run(["--template", str(t), "--spec", str(spec)])
    assert r.returncode == 0, r.stderr
    assert r.stdout == "Quarterly"


def test_cli_missing_template_exit1(tmp_path):
    r = _run(["--template", str(tmp_path / "nope.html.j2")])
    assert r.returncode == 1
    assert "error" in r.stderr


def test_cli_bad_context_json_exit1(tmp_path):
    t = _write(tmp_path, "t.html.j2", "<p>{{ x }}</p>")
    r = _run(["--template", str(t), "--context", "{not json"])
    assert r.returncode == 1
    assert "error" in r.stderr
