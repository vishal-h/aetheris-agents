# Ticket: plan_extractor — persist extraction to plan.jsonl

**Depends on:** consolidation patch (`m-boxy-pipeline-1a-consolidation-patch.md`) merged.

**Context.** The extractor currently writes `PlanComponent` JSON to stdout
only — the per-drawing extraction is ephemeral. Once the pipeline runs,
the raw (drawing, code) pairs are lost; only the consolidated order form
survives. This makes it impossible to:
- Re-run resolution with a different catalog without re-extracting
- Inspect what was found per drawing
- Diff two runs to detect drawing changes
- Feed raw per-drawing data into M2 reconciliation

**The fix:** add an optional `--output` flag to `plan_extractor.py` that
writes the extracted `PlanComponent` list to
`data/projects/{name}/plan.jsonl` — one JSON object per line.
Stdout behaviour is unchanged (still emits JSON array for pipe compatibility).

---

## `plan.jsonl` format

One `PlanComponent` dict per line. Written to
`data/projects/{project}/plan.jsonl`.

```jsonl
{"code": "BLB42FHL", "drawing": "El1", "qty": 1, "notes": null}
{"code": "BLB42FHL", "drawing": "El3", "qty": 2, "notes": null}
{"code": "BLB42FHL", "drawing": "El4", "qty": 1, "notes": null}
{"code": "DB30", "drawing": "El1", "qty": 1, "notes": null}
{"code": "DB30", "drawing": "floor_plan", "qty": 1, "notes": null}
```

Each record is a raw `PlanComponent` — unmerged, one per (drawing, code)
pair. This preserves full provenance for reconciliation.

Also write a metadata header as the first line:

```jsonl
{"_meta": true, "project": "joey", "source_drawings": ["Joey-_Kitchen_2D_Plans_V2.pdf", "Joey-_Kitchen_Plan_V2.pdf"], "extracted_at": "2026-06-14T..."}
```

---

## Change

**File:** `scripts/plan_extractor.py`

Add `--output` and `--project` CLI flags to `main()`:

```python
parser.add_argument(
    "--output", type=Path, default=None, metavar="DIR",
    help="If given, write plan.jsonl to DIR/{project}/plan.jsonl",
)
parser.add_argument(
    "--project", default=None, metavar="NAME",
    help="Project name (required when --output is given)",
)
```

After extracting components, if `--output` is given:

```python
def _write_plan_jsonl(
    components: list[PlanComponent],
    pdf_paths: list[Path],
    project: str,
    output_dir: Path,
) -> Path:
    """Write PlanComponent list to {output_dir}/{project}/plan.jsonl."""
    import datetime
    out_dir = output_dir / project
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "plan.jsonl"
    with open(out_path, "w") as f:
        # Metadata header
        meta = {
            "_meta": True,
            "project": project,
            "source_drawings": [p.name for p in pdf_paths],
            "extracted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        f.write(json.dumps(meta) + "\n")
        for c in components:
            f.write(json.dumps(asdict(c)) + "\n")
    return out_path
```

Validation: if `--output` is given but `--project` is not, print error and
exit 1.

---

## Touches

- `scripts/plan_extractor.py` — add `--output`, `--project` flags;
  add `_write_plan_jsonl`
- `tests/test_plan_extractor.py` — add tests for `_write_plan_jsonl`

**Do not generate.**
- Changes to `main.py`, `catalog_resolver.py`, `schema.py`, or any other file
- Any change to existing tests

---

## Done-check

```bash
cd aetheris-agents/boxy-pipeline
pip install -r requirements.txt -q
python3 -m pytest tests/test_plan_extractor.py -v

# Write plan.jsonl
python3 scripts/plan_extractor.py \
  data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
  data/samples/Joey-_Kitchen_Plan_V2.pdf \
  --project joey \
  --output  data/projects/

# Verify
python3 -c "
import json
from pathlib import Path
lines = Path('data/projects/joey/plan.jsonl').read_text().strip().splitlines()
meta = json.loads(lines[0])
assert meta['_meta'] is True
assert meta['project'] == 'joey'
assert len(meta['source_drawings']) == 2
records = [json.loads(l) for l in lines[1:]]
print(f'Metadata: {meta[\"project\"]}, drawings={meta[\"source_drawings\"]}')
print(f'Records: {len(records)} PlanComponents')
codes = {r[\"code\"] for r in records}
print(f'Distinct codes: {len(codes)}')
required = {\"DB30\", \"BLB42FHL\", \"W2739\", \"SB42\", \"USF330\"}
missing = required - codes
assert not missing, f'Required codes missing: {missing}'
# BLB42FHL must have multiple per-drawing records
blb = [r for r in records if r['code'] == 'BLB42FHL']
print(f'BLB42FHL records: {len(blb)} (one per drawing)')
assert len(blb) > 1, 'Expected BLB42FHL on multiple drawings'
# Stdout still works (pipe compatibility)
print('✓ plan.jsonl written with metadata + per-drawing records')
"

# Confirm stdout still emits JSON array (pipe still works)
python3 scripts/plan_extractor.py \
  data/samples/Joey-_Kitchen_2D_Plans_V2.pdf \
  | python3 -c "import json,sys; data=json.load(sys.stdin); print(f'stdout: {len(data)} records as JSON array ✓')"
```

Expected: `plan.jsonl` written with metadata header + per-drawing records,
stdout still emits JSON array unchanged.

---

## Claude-code prompt

> Implement `plan.jsonl` persistence in `scripts/plan_extractor.py` per
> `docs/m-boxy-pipeline-1a-plan-jsonl-ticket.md`.
>
> Add `--output` and `--project` CLI flags to `main()`. Add
> `_write_plan_jsonl()` per §Change. Call it after extraction when
> `--output` is given. Validate that `--project` is provided when
> `--output` is given; exit 1 with a clear error if not.
>
> Stdout behaviour is unchanged — still emits JSON array regardless of
> whether `--output` is given.
>
> Add unit tests for `_write_plan_jsonl` to `tests/test_plan_extractor.py`:
> metadata header correct, per-drawing records present, stdout unaffected.
>
> Do not modify any other file.
>
> Run the done-check from §Done-check and include actual output in your
> review packet.
