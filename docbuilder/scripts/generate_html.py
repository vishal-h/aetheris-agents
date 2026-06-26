"""Render a Jinja2 `.html.j2` template + context dict into an HTML string.

Deterministic, no LLM. The m6 successor to render_template.py (Markdown+regex):
Jinja2 gives conditional sections (`{% if %}`), loops (`{% for %}`), proper
escaping, and native absent-variable handling — an undefined variable renders as
the empty string (`jinja2.Undefined`), so there is no need for the m5
`OPTIONAL_FIELDS` workaround. Use `{{ field | default('') }}` in templates for an
explicit empty default.

Reads:
  --template  path to a .html.j2 file
  --context   inline JSON of variables for substitution (default {})
  --spec      optional path to a doc-spec JSON file; the parsed dict is exposed to
              the template as the variable `spec` (e.g. `{% for s in spec.sheets %}`)
  --output    optional output file; default is stdout

Errors (missing template, template syntax error, bad JSON) print
`{"status":"error","error":"..."}` to stderr and exit 1 (stage-CLI pattern).
"""

import argparse
import json
import sys
from pathlib import Path

import jinja2


def render_html(template_path, context, spec=None):
    """Pure function: render the Jinja2 template at `template_path` with `context`.

    `context` is a dict of template variables. `spec` (if given) is exposed to the
    template as the `spec` variable. Absent variables render as the empty string
    (the default `jinja2.Undefined`), so a template never leaks a literal
    `{{ placeholder }}` into its output.

    Raises jinja2.TemplateNotFound / jinja2.TemplateSyntaxError on template problems.
    """
    template_path = Path(template_path)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_path.parent)),
        undefined=jinja2.Undefined,
        autoescape=jinja2.select_autoescape(["html", "htm", "j2"]),
    )
    template = env.get_template(template_path.name)
    return template.render(**context, spec=spec)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True, help="path to .html.j2 template file")
    parser.add_argument("--context", default="{}", help="inline JSON of template variables")
    parser.add_argument("--spec", default=None, help="optional doc-spec JSON file path")
    parser.add_argument("--output", default=None, help="output file path; default stdout")
    args = parser.parse_args()

    try:
        context = json.loads(args.context)
        spec = None
        if args.spec is not None:
            spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        html = render_html(args.template, context, spec=spec)
    except (jinja2.TemplateNotFound, jinja2.TemplateSyntaxError) as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, OSError) as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

    if args.output:
        Path(args.output).write_text(html, encoding="utf-8")
        print(args.output)
    else:
        sys.stdout.write(html)


if __name__ == "__main__":
    main()
