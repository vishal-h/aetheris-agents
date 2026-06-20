# Docbuilder Runbook

Operational guide for the docbuilder pipeline.

---

## Required env vars

| Variable | Description | Example |
|----------|-------------|---------|
| `DOCBUILDER_TENANT` | Tenant name — selects the template directory under `data/templates/` | `demo` |
| `DOCBUILDER_DOC_TYPE` | Document type — selects the template file | `proposal` |
| `DOCBUILDER_VERSION` | Template version string | `v1` |
| `DOCBUILDER_DATA_PATH` | Path to the input CSV, relative to the docbuilder/ sandbox root | `data/sample_data.csv` |
| `ANTHROPIC_API_KEY` | Anthropic API key for the LLM | _(set in shell)_ |

Optional overrides:

| Variable | Default |
|----------|---------|
| `AETHERIS_MODEL` | `claude-haiku-4-5-20251001` |
| `AETHERIS_PROVIDER` | `anthropic` |

---

## Python dependencies

The renderer scripts need these third-party packages in the mise Python env:

```bash
python3 -m pip install openpyxl python-docx weasyprint markdown
```

- `openpyxl` — `generate_xlsx.py`
- `python-docx` — `generate_docx.py`
- `weasyprint` — `generate_pdf.py`
- `markdown` — `render_template.py` (narrative-mode PDF)

> A pinned `requirements.txt` is added at m2a t10. Until then, tests for a renderer
> whose dependency is missing **skip** (via `pytest.importorskip`) rather than fail —
> so a missing package is silent. Install the list above for a complete run.

---

## How to run

### Via sprint.sh (recommended)

```bash
cd ~/sandbox/elixirws/aetheris

DOCBUILDER_TENANT=demo \
DOCBUILDER_DOC_TYPE=proposal \
DOCBUILDER_VERSION=v1 \
DOCBUILDER_DATA_PATH=data/sample_data.csv \
./scripts/sprint.sh docbuilder
```

### Direct run

```bash
cd ~/sandbox/elixirws/aetheris

DOCBUILDER_TENANT=demo \
DOCBUILDER_DOC_TYPE=proposal \
DOCBUILDER_VERSION=v1 \
DOCBUILDER_DATA_PATH=data/sample_data.csv \
mix aetheris run ../aetheris-agents/docbuilder/agents/docbuilder_orchestrator.exs
```

### Syntax check (no LLM call)

```bash
cd ~/sandbox/elixirws/aetheris

DOCBUILDER_TENANT=demo \
DOCBUILDER_DOC_TYPE=proposal \
DOCBUILDER_VERSION=v1 \
DOCBUILDER_DATA_PATH=data/sample_data.csv \
mix run --eval \
  'Code.eval_file("../aetheris-agents/docbuilder/agents/docbuilder_orchestrator.exs")'
```

---

## Expected output

After a successful run, `docbuilder/output/` will contain:

```
output/pipeline_raw.json      # intermediate — raw fetch output
output/pipeline_spec.json     # intermediate — computed doc spec
output/proposal_v1.xlsx
output/proposal_v1.pdf
```

The formats generated depend on the `output_formats` array in the template. The
`demo/proposal_v1.json` template specifies `["xlsx", "pdf"]`.

---

## Template location convention

Templates live at:
```
data/templates/{DOCBUILDER_TENANT}/{DOCBUILDER_DOC_TYPE}_{DOCBUILDER_VERSION}.json
```

Example: `DOCBUILDER_TENANT=demo`, `DOCBUILDER_DOC_TYPE=proposal`, `DOCBUILDER_VERSION=v1`
→ `data/templates/demo/proposal_v1.json`

---

## Running tests

```bash
cd ~/sandbox/elixirws/aetheris-agents

# All docbuilder tests
python3 -m pytest docbuilder/tests/ -v

# Single script
python3 -m pytest docbuilder/tests/test_compute_doc.py -v
```

---

## Common failure modes

### `DOCBUILDER_TENANT not set` (or similar) on eval

All four `DOCBUILDER_*` vars must be exported before running `mix aetheris run`
or `mix run --eval`. The orchestrator raises immediately if any are absent.

### Output files missing after run

Check `overlay_base_dir` — it must be `nil`. If output files appeared in a
per-run `upper/` directory under `priv/runs/`, `overlay_base_dir` was set
non-nil. The orchestrator explicitly sets `overlay_base_dir: nil`.

### `python3 python3 script.py` in run_command

The LLM duplicated the executable in both `command` and `args`. The system
prompt explicitly warns: "Do not pass 'python3' inside the args array." If
this happens, re-run — the system prompt guard should prevent it.

### Template not found (exit code 1 from compute_doc.py)

Verify the template path:
```bash
ls docbuilder/data/templates/demo/
```
Expected: `proposal_v1.json`. The path is constructed as
`data/templates/{TENANT}/{DOC_TYPE}_{VERSION}.json`.

### Env vars not inherited by workers

The exec server spawns workers at invocation time and they inherit the
environment at that moment. If you exported env vars after starting a
long-lived worker, kill stale workers and re-run:
```bash
pkill -f aetheris_worker
```

### Stale `output/pipeline_raw.json` or `output/pipeline_spec.json`

These files are overwritten on each run. If a partial run left stale
intermediates, delete them before re-running:
```bash
rm -f docbuilder/output/pipeline_raw.json docbuilder/output/pipeline_spec.json
```
