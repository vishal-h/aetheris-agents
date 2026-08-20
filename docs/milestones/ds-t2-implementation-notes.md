# ds t2 — the run/artifact record — implementation notes

Two commits, agents repo only, not pushed. Baseline agents `f9328aa`, harness `a6464f4`.

- commit 1 — `0e5e0d2` — the module, its tests, the docbuilder generalisation
- commit 2 — the five remaining adopters, the six filings, the doc edits

---

## Criterion 5 — was the GitHub Project consulted?

**Not consulted.** No decision in this ticket was taken by reading the Project. Every
input came from `docs/milestones/ds-milestone.md` §t2, `docs/backlog-2026-06.md` §BL-153,
the two repos' `CLAUDE.md`, and the source. Issue `#78` was read and re-synced, which is an
act taken *to keep the tracker current* rather than a decision *taken from it* — close
criterion 5 distinguishes those two lists explicitly and this ticket contributes to the
second only.

---

## What was ruled, and what changed under it

### A1 — the unit is the step

BL-153's two rulings are inconsistent. Ruling 1 owes that *"an unstamped or mismatched
DIRECTORY is not a run"*; ruling 2 owes that coverage is *"every artifact a run produces,
INCLUDING the history tree written at an earlier step into a directory the guard never
clears"*. A directory stamp cannot express the second: cloudcost's `history/` is a
different directory from `$CLOUDCOST_OUT`, and one run writes into both.

Resolved in the direction ruling 2 points — the record enumerates artifacts and attests the
**step**. Reader's rule, replacing ruling 1's directory form: *an artifact not named in an
attested step record is not that step's output.* Ruling 1's substance survives intact:
`attested_at` is written only after every artifact write for the step has returned, so an
interrupted step is UNSTAMPED rather than stamped-and-partial.

**One design decision the ruling does not settle, taken here and stated.** The entry is
written when the step **opens**, not only when it completes. An interrupted step therefore
leaves a visible unattested entry rather than no entry at all — and "no entry" cannot be
told apart from "the step never ran", which is most of what the record exists to say.
`StepRecord.add()` re-persists on each call for the same reason: accumulating in memory and
writing once at the end would leave every interrupted step with an empty artifact list.
**That was found by a test, not by design** — `test_a_raising_step_leaves_the_entry_unattested_and_reraises`
failed on `assert [] == ['output/first.html']` against the first implementation.

### A2 — the writer is code

Docbuilder's PHASE D2 is the forbidden shape and was verified so at HEAD: D2 invokes
`run_log_writer.py` at PHASE D (`docbuilder_orchestrator.exs` §PHASE D step D2) and PHASE E
writes `output/uploaded.json` afterwards whenever `DRIVE_DOCBUILDER_ID` is set.

Fixed by making the artifact-writing scripts record their own steps —
`rename_output.py` (`STEP = "rename_output"`) and `upload_output.py`
(`STEP = "upload_output"`). **D2 was NOT moved to a later prompt phase**; that would
relocate the defect. It stays where it is because `run_log.json` feeds
`resolve_last_run.py`'s "same as last month", which is a different file with a different
consumer. The placement defect is filed under BL-151 rather than left as prose.

### A3 — run-level completion is out of scope

Not built, not stubbed, not pretended to. Filed as **BL-167**. The argument is in the row;
the short form is that under an LLM orchestrator every step is prompt-invoked, and two of
six producers have no last-writer position at all (eduloka's N concurrent sub-agents joined
only at `wait_for_all`; boxy-pipeline, where no program knows a run occurred).

---

## Corrections to earlier claims

Per the rule adopted after t1b, corrections to an earlier packet's claims go in the
committed notes, not only in the packet. Stage 1's packet is in a session scratchpad this
session cannot open, so these are corrections to the **claims as they reached t2's prompt**,
each re-derived at HEAD rather than inherited.

**1. The producer set does not follow from `docs/use-cases.md`.** The prompt instructs
*"Derive the set from `docs/use-cases.md`, NOT from an `output/` directory sweep."* The
registry has **ten** rows and carries no producer column — its membership criterion is
`D/tests/conftest.py` + `D/scripts/`, which is about separately-testable code. The registry
supplies the population; a stated criterion supplies the subset: *a producer writes a
durable local artifact that a later reader inspects to establish what a run produced.*
`api/gateway` and `api/tenant` write no local files (0 hits for `open(…'w'`/`write_text`/
`write_bytes` over both `scripts/`); `drive` and `email` write only *inbound* fetches
(`drive_download.py:82`, `email_download_template.py:60`). The six carried are correct; the
derivation as stated is not, and a reader following it literally gets ten. Both halves are
now asserted in `tests/test_run_record_adoption.py::test_the_producer_set_partitions_the_registry`.

**2. There are 31 `docbuilder-orch-*` run directories, not fifteen.** `ls -d
priv/runs/docbuilder-orch-* | wc -l` → 31. The "one entry in `run_log.json`" half of the
claim is correct (1 entry, `run_id` `docbuilder-orch-iDGIIQ`), as are the gitignore and the
three truncating sprint legs (`sprint.sh:2235`, `:2317`, `:2553`).

**3. `run_log_writer.py`'s stated posture is narrower than "never fail a producer".** Its
docstring scopes best-effort to one input — *"A missing/malformed `--renamed` file degrades
to `outputs: []`"* — and states the other half two lines above: *"1 if `--context` is invalid
JSON or the existing log file is unreadable"*. Both are preserved; see §Failure posture.

**4. cloudcost's two history layouts are one code layout under two roots.** `persist_history`
(`compose_report_data.py:989`) has a single shape; the divergence is `--history-dir`, which
the orchestrator sets per-provider (`cloudcost_orchestrator.exs:141`) and which defaults to
the shared root (`:111`). The observable facts carried in the prompt — two files, same
provider and period, ~6h apart, one unreadable by `load_prior_snapshots` — all hold, with
md5s in the BL-151 filing.

**5. eduloka's raw path has two branches and the orchestrator uses the non-partitioned
one.** `_make_output_path` (`fetch.py:31,33`) returns
`{base}/provider={p}/dt={YYYY-MM-DD}/{slug}.jsonl` under `--partition` and `{base}/{provider}.jsonl`
otherwise. The orchestrator passes `--output-dir data/raw/<SLUG>` and no `--partition`, so the
live shape is `data/raw/<slug>/{provider}.jsonl` — the carried claim, correct for the live
path, but not the only branch in the file.

**6. R3's stated reason is wrong; its conclusion holds.** `--pdf` occurs in
`cloudcost/tools.json:582` and `render_report.py` (3×) and in no cloudcost `.exs` and not in
`sprint.sh`. Amended on BL-153.

**7. R4's generalisation is false.** docbuilder threads a run id into argv and has since
before both rulings (`docbuilder_orchestrator.exs:146`, `:231`, `:351`). Amended on BL-153;
ruling 2's conclusion stands on a better premise than its own citation.

**8. The `aetheris_run_id` count of five is confirmed**, re-derived rather than carried:
`init_db.py:31,47,60,74` and `migrations.rs:39`. Filed as **BL-168**, which also names four
mirroring doc lines in `docs/provenance/specs.md` that a code-only fix would strand.

---

## The record

**Where.** `<use_case>/data/run-records.json`. Under `data/`, never `output/`: payslip's
`output/runs.log` (`generate_employee_payslips.py:181`, default `output_dir="output"`) sits
inside the tree `../aetheris/scripts/sprint.sh:1006` `rm -rf`s, so it dies with the
artifacts it attests. `docbuilder/data/run_log.json` is the placement precedent. Gitignored
in all six, with the lock file — asserted by
`test_run_record_adoption.py::test_every_producer_gitignores_its_record`.

**Module location.** Repo-root `scripts/run_record.py`, following `scripts/_manifest.py` —
the in-repo precedent for a shared module with several consumers (imported by
`repin_manifest.py`, `assemble_export_bundle.py` and two root test files). The alternative
shapes were rejected on the repo's own conventions: no use case may import another's
`scripts/`, so a module owned by one producer and imported by five inverts the dependency;
and six copies drift by construction. Use-case scripts reach it with a two-line bootstrap,
necessary because they run with the use-case root as cwd, putting `<use_case>/scripts` on
`sys.path` and not the repo root's.

**Failure posture, both halves.** Recording is best-effort at the point of write and never
fails a producer; a malformed existing record file is never silently overwritten. These only
look opposed: in best-effort mode a malformed file makes the write **skip** with a loud
stderr warning, so history survives and the producer does not fail. `strict=True` raises.

**Which call site is which.** *All six producers' adoptions are best-effort* — recording is a
side effect of their real work. *The strict path is offered and currently taken by no
producer*; it exists for a call site whose only job is the recording, which is what
`run_log_writer.py` is, and `run_log_writer.py` keeps its own pre-existing hard-fail via
`main()`'s `except (json.JSONDecodeError, ValueError)` → exit 1 rather than by passing
`strict=True`. That is why `RunRecordError` subclasses `ValueError`: both CLIs' existing
except clauses and exit codes are unchanged by the generalisation.

**Concurrency, which the ruling does not mention and eduloka forces.** `os.replace` makes
the *write* atomic and does nothing for the read-modify-write around it. eduloka spawns one
sub-agent per term, joined only at `wait_for_all`, so concurrent writers would silently drop
each other's entries — a record that under-reports exactly when the most work happened.
`_exclusive()` holds an `fcntl.flock` on a sidecar `.lock` file (sidecar because the record's
inode is replaced on every write). `test_concurrent_writers_do_not_lose_entries` spawns 12
processes; with the lock disabled it failed in 2 of 3 samples, which is what a race looks
like.

**The test seam is an env var, not a flag**, and deliberately: `AETHERIS_RUN_RECORD_ROOT`,
read in exactly one function. An optional flag whose default differs from what the
orchestrator passes is precisely what produced cloudcost's two history roots.

---

## C3 — the live consumer did not break

`resolve_last_run.py` is **byte-unchanged**: sha256
`57de65f41d1aacc6dfb7505b7e7a634ac895b916abb4ed93bee82be29453364a` at `f9328aa` and at
commit 1.

`docbuilder/tests/test_resolve_last_run_characterisation.py` was written **first**, run at
`f9328aa` with both scripts unmodified (15 passed), and re-run unchanged after the
generalisation. It pins the contract by behaviour, not implementation: exact `==` on
`tenant`/`doc_type`; `context.client_name` folded and substring-matching either direction;
`timestamp` lexicographic max with array-order tie-break; the whole `context` dict carried
forward; `run_id` never selecting.

**The lexicographic sort is pinned as a defect on purpose.**
`test_lexicographic_sort_is_the_pinned_defect` asserts today's inverted behaviour and its
failure message says to retire the test and close BL-151's entry when the fix lands. Pinning
it is what keeps this ticket honest — a refactor of the writer must not quietly change the
reader's selection.

**One pre-existing test was changed**, and the reasoning is recorded because "update the
test" can hide a weakened gate. `test_run_log_writer.test_load_malformed_raises` asserted
`json.JSONDecodeError`, an incidental consequence of `json.loads` being inline. It now
asserts the invariant the exit-1 contract actually rests on — that the raise is caught by
`main()`'s `except (json.JSONDecodeError, ValueError)` — which is asserted explicitly rather
than implied. Strictly more is checked than before. `test_load_non_array_raises` is untouched
and still passes.

---

## The six producers

| use case | instrumented | step name(s) | run id | verified by |
|---|---|---|---|---|
| `docbuilder` | `rename_output.py`, `upload_output.py` | `rename_output`, `upload_output` | agent, threaded | CLI subprocess tests |
| `cloudcost` | `compose_report_data.py`, `render_report.py` | `compose_report_data`, `render_report` | agent, hoisted + threaded | its own 465-test suite drives both stages |
| `payslip` | `generate_employee_payslips.py` | `generate_employee_payslips:{emp_id}` | agent, hoisted + threaded | its suite drives the loop |
| `eduloka` | `fetch.py`, `map.py`, `enrich.py` | `fetch:{slug}`, `map:{slug}`, `enrich:{slug}` | agent, threaded to 3 sub-agent stages | structural — stages need a live search provider |
| `provenance` | `inventory_report.py` | `inventory_report` | `--run-id`, nothing passes it yet | structural — needs a populated DuckDB |
| `boxy-pipeline` | `order_formatter.py` | `order_formatter` | **null** — no route exists | dormant test, run targeted under `-m dormant` |

**cloudcost.** `compose_report_data` records **both** its writes — the report data under
`--output-dir` and the snapshot under `--history-dir` — which is ruling 2's coverage clause
in force. `render_report`'s record spans the HTML and, when asked for, the PDF; an absent PDF
binary is a note rather than a failure, so it does not withhold the attestation.

**payslip.** One entry per **employee**, because that is the unit that can be complete: the
script loops employees and each iteration writes a directory of deliverables, so a
per-invocation entry could not say which employees finished when a run dies mid-loop.
`output/runs.log` is **not deleted** — the overlap is deliberate and stated: the log is a
human-readable append-only trace inside `output/`, the record is a machine-readable
attestation outside it, and the log dies with the sprint's `rm -rf` while the record does
not. Retiring the log is not this ticket's call.

**eduloka.** Step names carry the slug, which reconciles A1 with the prompt's "one record
entry per TERM sub-agent": the attestable unit stays the step, and the term is complete iff
its stages are all attested — strictly more information than one entry per term, and the only
shape that works when N sub-agents write one file concurrently. The sink stage
(`upsert_institute.py`) is **not** instrumented: it writes no file, so it has no artifact to
attest, and `export_institute.py`'s output is already covered as `enrich`'s gold file.

**provenance.** Its DB attestation is **not duplicated**. `scan_runs` already goes
`'running'` (`scan.rs:457`) → `'complete'` (`scan.rs:502`), which is started/attested
semantics for the *scan*. The record covers the *report* step, which is downstream —
`_section_summary` selects `WHERE status = 'complete'`. The two compose; nothing here writes
to `scan_runs`.

**boxy-pipeline.** `run_id: null`, a real value meaning no run reached the script, never a
fabricated substitute. Its adoption test carries `pytestmark = pytest.mark.dormant`, without
which `tests/test_use_case_registry.py`'s marker-equals-registry arm goes red. **What it is
and is not evidence for is stated in the file rather than left to be inferred**: it was run
targeted under `-m dormant` and passed (3 passed), so "written and never executed" would be
false and is not claimed; what is *not* verified is the boxy pipeline itself — no order form
was produced through `write_order_form`, and the full `-m dormant` set has never finished
under either recorded cap (BL-159).

---

## Out of scope, and left alone deliberately

- **No reader that refuses an unattested artifact.** Specified, not built.
- **No `drift_check` arm** over these records, **no `sprint.sh` change**, **no harness change**.
- **The sprint's arm ordering is NOT changed** — BL-153's first ruling stands.
- **`provenance/scripts/inventory_report.py:49`** stamps its report filename with local time
  and no offset marker. Same class as the BL-151 timestamp filing; changing an artifact
  filename convention is not this ticket's scope, so it is **filed, not fixed**, and a
  comment at the site says so. (It was briefly changed during implementation and reverted.)
- **`output/runs.log`** kept, per above.

---

## What a later reader should know

The record is **write-only today**. Nothing reads `run-records.json` — that is deliberate
(the reader is out of scope) but it means the format has never been exercised by a consumer,
and a first reader may well find a field it wants that is not there. The obvious candidates,
noted rather than added: the invoker (orchestrator vs Tools panel vs operator), which is what
BL-153's amended R3 shows actually determines a pipeline's shape and which no script can
currently observe; and a link from a step entry to the run-level completion BL-167 owes.

`run-records.json` is gitignored in all six, so **no record file is committed** and none can
be inspected from a fresh clone. Anyone verifying the format must run a producer.
