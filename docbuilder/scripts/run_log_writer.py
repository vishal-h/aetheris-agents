"""Append a docbuilder run to the run log (m3 context-builder foundation).

Called by the orchestrator at the end of PHASE D (after rename). Writes one entry
per run — `{tenant, doc_type, variant, run_id, timestamp, context, outputs}` — to a
JSON-array log file (`data/run_log.json` by default, gitignored). The m3 context
builder reads this log to offer "same as last month".

Idempotent on re-run: an entry with the same `run_id` is replaced, not duplicated.

Exit codes: 0 on success; 1 if `--context` is invalid JSON or the existing log file
is unreadable/not a JSON array (we must not silently overwrite run history). A
missing/malformed `--renamed` file degrades to `outputs: []` (logging is a best-effort
side effect and must not fail the pipeline).
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

# The loader raises `run_record.RunRecordError`, which subclasses `ValueError` — so
# `main`'s existing `except (json.JSONDecodeError, ValueError)` still catches it and this
# module's exit codes are unchanged.
from run_record import load_json_array, write_json_array  # noqa: E402


def _read_outputs(renamed_path):
    """Return the renamed output paths from a rename_output.py result file.

    Degrades to [] (with a stderr warning) if the file is absent or malformed."""
    if not renamed_path:
        return []
    p = Path(renamed_path)
    if not p.exists():
        print(
            json.dumps({"status": "warning",
                        "warning": f"renamed file '{renamed_path}' not found; outputs=[]"}),
            file=sys.stderr,
        )
        return []
    try:
        data = json.loads(p.read_text())
        return [e["renamed"] for e in data if isinstance(e, dict) and "renamed" in e]
    except (json.JSONDecodeError, TypeError) as e:
        print(
            json.dumps({"status": "warning",
                        "warning": f"could not parse renamed file '{renamed_path}': {e}; outputs=[]"}),
            file=sys.stderr,
        )
        return []


def _load_log(log_path):
    """Load the existing run log as a list. Missing/empty → []. A malformed or
    non-array existing log raises (hard error at the CLI) so run history is never
    silently overwritten.

    Since ds t2 this delegates to `scripts/run_record.load_json_array`, which is the same
    loader the per-step run record uses — one definition of "malformed" for both history
    files rather than two that can drift. `resolve_last_run.py` imports this function, so
    the two docbuilder scripts still share one loader exactly as before."""
    return load_json_array(log_path)


def append_run(log, entry):
    """Append entry to log, replacing any existing entry with the same run_id
    (idempotent re-runs). Returns the new list."""
    run_id = entry.get("run_id")
    if run_id:
        log = [e for e in log if e.get("run_id") != run_id]
    return log + [entry]


def build_entry(tenant, doc_type, variant, run_id, context, outputs, timestamp=None):
    return {
        "tenant": tenant,
        "doc_type": doc_type,
        "variant": variant,
        "run_id": run_id,
        "timestamp": timestamp or datetime.now().astimezone().isoformat(timespec="seconds"),
        "context": context,
        "outputs": outputs,
    }


def main():
    parser = argparse.ArgumentParser(description="Append a docbuilder run to the run log.")
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--doc-type", required=True)
    parser.add_argument("--variant", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--context", required=True,
                        help="inline JSON of the run's DOCBUILDER_CONTEXT")
    parser.add_argument("--renamed", default=None,
                        help="rename_output.py result JSON file (source of the outputs list)")
    parser.add_argument("--log-file", default="data/run_log.json")
    args = parser.parse_args()

    try:
        context = json.loads(args.context)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "error": f"invalid --context JSON: {e}"}),
              file=sys.stderr)
        sys.exit(1)

    outputs = _read_outputs(args.renamed)

    try:
        log = _load_log(args.log_file)
    except (json.JSONDecodeError, ValueError) as e:
        print(json.dumps({"status": "error", "error": f"existing run log unreadable: {e}"}),
              file=sys.stderr)
        sys.exit(1)

    entry = build_entry(args.tenant, args.doc_type, args.variant,
                        args.run_id, context, outputs)
    log = append_run(log, entry)

    # Atomic: temp file then replace. Until ds t2 this was a whole-file `write_text`, so a
    # kill mid-write truncated the entire run history rather than losing one entry.
    out = write_json_array(args.log_file, log)
    print(str(out))


if __name__ == "__main__":
    main()
