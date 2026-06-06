# rig/p4-tools: Manifest spec

## Context

This issue defines the `tools.json` manifest format and writes the initial
manifests for all existing use cases. No code changes — pure JSON files and
documentation.

The manifest is the contract between use-case authors and the Rig inventory
walker. Writing it well pays off every time a new agent author asks "what
can I call from here?"

All files for this phase live in:
```
aetheris-agents/docs/rig/milestones/p4-tools/
```

---

## `tools.json` schema

Place at `{use_case}/tools.json` in `aetheris-agents/`.

```json
{
  "manifest_version": "1",
  "use_case": "payslip",
  "description": "One sentence about what this use case does",
  "scripts": [
    {
      "name": "script_name",
      "file": "scripts/script_name.py",
      "description": "What this script does (one sentence)",
      "args": [
        {
          "name": "arg_name",
          "flag": "--arg-name",
          "type": "string | file | directory | integer | float | boolean",
          "required": true,
          "default": null,
          "description": "What this arg controls"
        }
      ],
      "output": "json | text | files",
      "example": "python3 scripts/script_name.py --arg-name value"
    }
  ]
}
```

### Field reference

**Top-level**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `manifest_version` | `"1"` | Yes | Integer string. Walker skips unknown versions with a warning. |
| `use_case` | string | Yes | Must match the directory name. |
| `description` | string | Yes | One sentence shown in the left-panel group header tooltip. |
| `scripts` | array | Yes | May be empty `[]` if no scripts yet. |

**Per script**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | Snake_case. Used as the tree label and as the run job key. |
| `file` | string | Yes | Relative to use-case root. Always `scripts/*.py` for flat layouts; `tenant/scripts/*.py` etc. for nested layouts. |
| `description` | string | Yes | Shown in the right panel header. |
| `args` | array | Yes | May be `[]` for scripts that take no args. |
| `output` | `"json"` \| `"text"` \| `"files"` | Yes | `json` → pretty-print output. `text` → raw. `files` → show file list. |
| `example` | string | Yes | Shown verbatim below the arg form. Copied to clipboard on click. |

**Per arg**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | Snake_case. Used as the form field label. |
| `flag` | string | No | CLI flag e.g. `"--output-dir"`. Omit for positional args. |
| `type` | string | Yes | Controls the form widget: `file` → path input, `boolean` → checkbox, others → text input. |
| `required` | boolean | Yes | Required fields show `*` in the form. Run button disabled until all required fields have values. |
| `default` | string \| null | Yes | Shown as placeholder in the form field. `null` = no default. |
| `description` | string | Yes | Shown as field hint below the input. |

### Positional args (no `flag`)

Some scripts take positional args rather than flags
(e.g. `payslip_compute.py data/sample_payroll.csv`). For these, omit
`flag` entirely. The runner concatenates positional args in declaration
order, before any flagged args.

```json
{
  "name": "csv_path",
  "type": "file",
  "required": true,
  "default": "data/sample_payroll.csv",
  "description": "Path to payroll CSV"
}
```

### `output` types

| Value | Runner behaviour | UI behaviour |
|-------|-----------------|--------------|
| `"json"` | Captures stdout, attempts `JSON.parse` | Pretty-prints with syntax highlight |
| `"text"` | Captures stdout verbatim | Renders in monospace pre block |
| `"files"` | Captures stdout (expected to be a file list or JSON array of paths) | Renders as file list |

If a `json` script's stdout is not valid JSON, the runner falls back to
raw text display.

---

## Manifests to write

### `payslip/tools.json`

Scripts in `payslip/scripts/`:
- `payslip_compute.py` — takes a positional CSV path, outputs JSON salary data
- `generate_employee_payslips.py` — takes an employee ID, generates PDF payslips

```json
{
  "manifest_version": "1",
  "use_case": "payslip",
  "description": "Compute net salaries and generate employee payslip PDFs",
  "scripts": [
    {
      "name": "payslip_compute",
      "file": "scripts/payslip_compute.py",
      "description": "Compute net salary for all employees from a payroll CSV",
      "args": [
        {
          "name": "csv_path",
          "type": "file",
          "required": true,
          "default": "data/sample_payroll.csv",
          "description": "Path to payroll CSV"
        }
      ],
      "output": "json",
      "example": "python3 scripts/payslip_compute.py data/sample_payroll.csv"
    },
    {
      "name": "generate_employee_payslips",
      "file": "scripts/generate_employee_payslips.py",
      "description": "Generate PDF payslips for a single employee",
      "args": [
        {
          "name": "employee_id",
          "type": "string",
          "required": true,
          "default": null,
          "description": "Employee ID (e.g. BTL_999)"
        },
        {
          "name": "output_dir",
          "flag": "--output-dir",
          "type": "directory",
          "required": false,
          "default": "output",
          "description": "Directory to write payslip PDFs into"
        }
      ],
      "output": "files",
      "example": "python3 scripts/generate_employee_payslips.py BTL_999"
    }
  ]
}
```

### `drive/tools.json`

```json
{
  "manifest_version": "1",
  "use_case": "drive",
  "description": "Google Drive file scanning and inventory tools",
  "scripts": []
}
```

> Fill in scripts once drive scripts are confirmed. Placeholder `[]` is
> valid — the use case appears in the tree with an empty scripts list.

### `email/tools.json`

```json
{
  "manifest_version": "1",
  "use_case": "email",
  "description": "Email composition and dispatch tools",
  "scripts": []
}
```

### `api/tools.json`

```json
{
  "manifest_version": "1",
  "use_case": "api",
  "description": "TAP protocol — tenant API gateway and command tools",
  "scripts": []
}
```

> The `api/` use case has scripts in `api/tenant/scripts/` and
> `api/gateway/scripts/` rather than a flat `scripts/` directory. The
> manifest walker uses `file` paths relative to the use-case root, so
> entries like `"file": "tenant/scripts/foo.py"` are valid. Add them
> once the TAP scripts are stable.

---

## Walker behaviour for undeclared scripts

If a `.py` file exists in `{use_case}/scripts/` but has no entry in
`tools.json`, the walker synthesises a minimal entry:

```json
{
  "name": "undeclared_script",
  "file": "scripts/undeclared_script.py",
  "description": "(not declared in tools.json)",
  "args": [],
  "output": "text",
  "example": "python3 scripts/undeclared_script.py",
  "undeclared": true
}
```

The UI renders these with an amber `!` badge in the tree and a banner in
the detail panel: *"This script is not declared in tools.json. Add an
entry to enable arg forms and output formatting."*

The Run button is still present for undeclared scripts — the runner
accepts a raw args string (a single text input) instead of a structured
form.

---

## Acceptance criteria

- [ ] `payslip/tools.json` written and valid against the schema above
- [ ] `drive/tools.json`, `email/tools.json`, `api/tools.json` written
      (may have empty `scripts: []`)
- [ ] Schema documented in this file is the authoritative reference —
      `p4-002-rust-backend.md` deserialises exactly these shapes
- [ ] Walker behaviour for undeclared scripts documented above

## Files to create

- `aetheris-agents/payslip/tools.json`
- `aetheris-agents/drive/tools.json`
- `aetheris-agents/email/tools.json`
- `aetheris-agents/api/tools.json`
