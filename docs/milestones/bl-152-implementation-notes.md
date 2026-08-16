# BL-152 — the repo-root `pytest` invocation cannot collect (implementation notes)

`2026-08-16, at agents 6ffcd76 / aetheris d19f4b6 (both HEADs at the start of the ticket; both
clean, and the harness HEAD is unchanged at the end). Every count, path and command below is
measured at that pair unless it names another. pytest 9.0.3, Python 3.12.13 (mise). Absolute
paths are normalised to ~ throughout.`

Standalone row; no milestone. Notes filed at `docs/milestones/` per the convention for repo-wide
(non-use-case) BL rows — nearest recent examples `docs/milestones/bl-068-implementation-notes.md`
and, for shape, `docs/milestones/export-mechanism-implementation-notes.md` (the commit
immediately before this one).

**Two mid-ticket corrections from the arbiter are folded in**, and both changed the deliverable:
(1) every run that can reach live subprocess work runs under an explicit wall-clock cap, and a
cap-kill is a complete result rather than a check still owed; (2) boxy-pipeline's work is paused
pending its client, which is a *business* fact and must not be expressed through the mechanical
`integration` marker — so there is a second marker, `dormant`, and the gate reports the two
exclusion counts separately.

---

## 1. What the row got right, and the pointers that were wrong at HEAD

The row was established at agents `0303597`. Re-established here at `6ffcd76`.

**Right, and reproduced verbatim.** `python3 -m pytest -q` from the repo root aborts during
collection with exactly the two errors the row quotes —
`boxy-pipeline/tests/test_pipeline.py` (`No module named 'main'`) and
`provenance/mcp/corpus-search/tests/test_server.py` (`No module named 'tests.test_server'`) —
`Interrupted: 2 errors during collection`, exit 2, 4.02s. Right too: no `pytest.ini`,
`setup.cfg` or `pyproject.toml` anywhere in the tree (verified by `find`), so rootdir and
`sys.path` were inferred per invocation. Right too, and centrally: *the two named modules are the
visible edge, not the extent* — §3.

**Wrong pointer 1 — the scope-combination counts have moved.** The row records
`cloudcost/tests/ → 440` and `tests/ → 136`. At HEAD they are **465** and **164**. The
*conclusion* those numbers support is unchanged: `cloudcost/tests/ tests/` together still gives
`164 collected, 8 errors, Interrupted`, and the row's "8 errors" is exact.

**Wrong pointer 2 — "Both modules import and their tests run when pytest is invoked against
their own scope."** False for boxy-pipeline at HEAD, in the sense that matters. Scoped to its own
directory *from the repo root* — `python3 -m pytest boxy-pipeline/tests` — it still fails:
`196 tests collected, 1 error`, `Interrupted`. It collects only when the working directory is
`boxy-pipeline/` (`cd boxy-pipeline && python3 -m pytest tests/` → 208). That is not a detail: it
is the mechanism. `python3 -m pytest` (as opposed to `pytest`) puts the *current working
directory* on `sys.path` — that is `python -m`, not pytest — and `boxy-pipeline/main.py` was
reachable by nothing else.

**Pointer 3 — "blocks inside a live subprocess" — is CONFIRMED, and I got it wrong once before
confirming it.** My first reading was that nothing blocks: the run I had at that point was
`-m "not integration"`, whose three heaviest tests are 88s, 87s and 23s of in-process
`pdfplumber` work, and I generalised from it to the whole tree. That was an inference from a run
that never executed the test in question, and the wrong version of this paragraph was written
into this file before it was caught. Running the excluded set for real (§7) put the row's claim
back:
`boxy-pipeline/tests/test_pipeline.py::test_plan_path_produces_same_output_as_drawings_path`
spawns `plan_extractor.py` against the two sample PDFs by `subprocess.run` — the row's exact
words — and progress stalls there. The row is right on the symptom, right on the file, and right
on the two PDFs.

---

## 2. Baseline (S0b) — every test-bearing directory, before and after

Twelve directories carry pytest tests. Enumerated by searching *all* `.py` files matching
pytest's default `python_files` patterns, not by trusting the row's list; the tracked set and the
on-disk set are identical (no untracked test files).

| scope | before | after | delta |
|---|---:|---:|---:|
| `api/gateway/tests` | 69 | 69 | — |
| `api/tenant/tests` | 50 | 50 | — |
| `boxy-pipeline/tests` | **196 + 1 error (Interrupted)** | **208** | **+12** |
| `cloudcost/tests` | 465 | 465 | — |
| `docbuilder/tests` | 373 | 373 | — |
| `drive/tests` | 34 | 34 | — |
| `eduloka/tests` | 91 | 91 | — |
| `email/tests` | 32 | 32 | — |
| `payslip/tests` | 32 | 32 | — |
| `provenance/mcp/corpus-search/tests` | 26 | 26 | — |
| `provenance/tests` | 170 | 170 | — |
| `tests` | 164 | 164 | — |
| **sum** | — | **1714** | |

**The one delta, with its mechanism named.** `boxy-pipeline/tests` gains the 12 tests in
`test_pipeline.py`, which previously could not be imported from the repo root at all. Nothing was
gained or lost anywhere else — the risk the row's *Costs* paragraph flagged (pinning rootdir
changing how every use case's `conftest.py` resolves) did not materialise, because the fix does
not change what any `conftest.py` inserts.

**The whole-tree total equals the sum of the per-scope totals exactly: 1714 = 1714.** No
double-collection, no directory missed.

**And the same holds for the cwd-relative form the runbooks document.** `cd <use_case> &&
python3 -m pytest tests/` collects the identical count for all eight single-level use cases, and
`cd api && … tenant/tests gateway/tests` gives 119, matching 69+50. That is why no runbook,
README or milestone doc needed editing.

---

## 3. The three collision mechanisms

Under pytest's default `prepend` import mode a test module's importable name is derived from its
first ancestor directory *without* an `__init__.py`. This tree produced three distinct collisions
from that one rule, and each was invisible until two scopes were combined.

1. **`conftest` claimed twice.** `tests/conftest.py` and `cloudcost/tests/conftest.py` both
   import as the top-level name `conftest`. `cloudcost/tests/test_*.py` does
   `from conftest import FIXTURES`; whichever was imported first won. This is the row's
   "8 errors" — `ImportError: cannot import name 'FIXTURES' from 'conftest'
   (~/sandbox/elixirws/aetheris-agents/tests/conftest.py)`.

2. **`tests` claimed twice, as a package.** `email/tests/__init__.py` exists while
   `email/__init__.py` deliberately does not (the stdlib-`email` shadow rule — `CLAUDE.md`
   §Python script conventions, `docs/agent-creation-guide.md:307`). So email's tests import as
   the package `tests`, and `provenance/mcp/corpus-search/tests/test_server.py` — which has its
   own `__init__.py` — could no longer resolve `tests.test_server`. Confirmed directly:
   `python3 -m pytest email/tests provenance/mcp/corpus-search/tests` reproduces the error; the
   corpus-search scope alone collects 26 clean.

3. **`main` reachable only from one working directory.** As in §1.

`--import-mode=importlib` fixes 1 and 2 by deriving each module name from its full path, so no
two files can collide. It does not fix 3, which is a `sys.path` gap rather than a naming one.

**Mechanism 1 has a surviving runtime half, and it bit this ticket** — see §10.

---

## 4. What landed (S1)

**`pytest.ini` at the repo root** — new file, the narrowest configuration file that does the job.

*Why not `pyproject.toml`.* This is a polyglot tree: Elixir `.exs` agents, Rust at
`provenance/scanner/Cargo.toml` and `rig/src-tauri/Cargo.toml`, TypeScript at `rig/`. A root
`pyproject.toml` is discovered by pip, PEP-517 build backends, uv/poetry, ruff, black and mypy
*whether or not it configures them* — a file that changes what other tooling believes about the
tree. `pytest.ini` is read by pytest and by nothing else. What I checked before choosing: no
`setup.py`/`setup.cfg`/`tox.ini` anywhere; the two `Cargo.toml` files are cargo-only; nothing in
`rig/package.json`'s `scripts` touches Python; the repo has no CI at all (there is no `.github/`
in this repo, and the harness's `.github/workflows/ci.yml` contains no `pytest`). `setup.cfg`
would also have been pytest-only in practice but carries setuptools semantics it does not need.

Its jobs: pin rootdir to the repo root for every invocation, scoped or not, so a run's behaviour
no longer depends on the directory it was launched from; `addopts = --import-mode=importlib`; and
register the two markers with their full statements, including `dormant`'s condition for return.
`provenance/tests/` has no `pytest_configure`, so without the registration the marks added below
would warn.

Neither exclusion is in `addopts`. Making an exclusion the default is exactly how it stops being
visible, which is the thing the whole gate design is against.

**`boxy-pipeline/tests/conftest.py`** — one `sys.path.insert` for the use-case root, beside the
`scripts/` insert already there. This is the repo's existing idiom (ten of the eleven
`conftest.py` files do the same thing), scoped to boxy-pipeline's collection, and strictly
narrower than a global `pythonpath =` entry in `pytest.ini`, which would have put
`boxy-pipeline/{data,docs,output,scripts,tests}` on `sys.path` for every scope in the repo.

**`email/tests/__init__.py`** — deleted. Empty file, 0 bytes; nothing imports `email.tests` or
uses a relative import anywhere under `email/`, `drive/`, `payslip/` or `provenance/mcp/`
(checked). Its removal is what un-claims the package name `tests`. `drive/` and `payslip/` keep
theirs because they *do* have a use-case-level `__init__.py`, so they resolve as `drive.tests.*`
/ `payslip.tests.*` and collide with nothing. This is not a suppression of either module the row
names — it is the removal of the name collision itself.

**`tests/conftest.py`** — gains the deselection-reporting hooks (§6). Why not a root
`conftest.py`: §10.

No product code changed. No `--ignore`, no `skip`, no `xfail`, no deselect list.

---

## 5. The two markers

Two exclusions with two different reasons and two different re-entry conditions, deliberately
never merged into one mechanism. Both are registered in `pytest.ini`; each has its own command.

### 5a. `integration` — test mechanics

Ten tests gained `@pytest.mark.integration`. The criterion is mechanical: **the test depends on
state outside this repo's tracked tree.** All ten passed before the marker was applied and pass
after; none was marked for being slow, and none for being red.

| test | reason |
|---|---|
| `boxy-pipeline/tests/test_plan_extractor.py::test_deduplication_increments_qty_same_drawing` | reads `boxy-pipeline/data/samples/*.pdf`, gitignored client data (`boxy-pipeline/.gitignore:2`, `data/*`) |
| `…::test_deduplication_separate_records_across_drawings` | same sample PDFs |
| `…::test_vision_codes_filtered_through_token_to_code` | same sample PDFs |
| `provenance/tests/test_search_agent.py::test_agent_evaluates_without_error` | spawns `mix run --eval` with `cwd=../aetheris` — the sibling harness repo |
| `…::test_agent_evaluates_without_mcp_enabled` | same |
| `…::test_agent_raises_without_db_path` | same |
| `provenance/tests/test_zip_archaeologist.py::test_agent_evaluates_without_error` | same |
| `provenance/tests/test_zip_orchestrator.py::test_agent_evaluates_without_error` | same |
| `provenance/tests/test_classification_orchestrator.py::test_agent_evaluates_without_error` | same |
| `provenance/tests/test_migration_agent.py::test_agent_evaluates_without_error` | same |

**Proof that none of the ten was red.** The pre-marker whole-tree run was
`1545 passed, 3 skipped, 7 xfailed`, zero failures. The post-marker run was `1535 passed` with
the same skips and xfails. 1545 − 1535 = 10, exactly the marked set, all moving from *passed* to
*deselected*. Nothing red was hidden by a marker.

**The three boxy tests are a consistency repair, not a new judgement.** Seven tests in
`test_plan_extractor.py` carry the identical `if not SAMPLES_AVAILABLE: pytest.skip(...)` guard;
four were already marked and three were not. boxy-pipeline's own `conftest.py` defines the marker
as *"requires sample data files in `data/samples/`"* and auto-skips marked tests when the samples
are absent, so on a clean checkout all seven skip and on this machine three of them ran. That
machine-dependence *is* the defect: those three were 198 of the pre-exclusion 383 seconds here
and 0 seconds on a checkout without the client PDFs. They are kept marked even though boxy is now
dormant, because the mechanical property is still true and will still be true when boxy resumes.

**A hypothesis I had and then killed.** I expected the two `extract_pdfs` tests to be marked for
reaching the network: that call path ends in `_extract_codes_via_vision`, which constructs
`anthropic.Anthropic()` when `ANTHROPIC_API_KEY` is set, and it *is* set in this environment.
Measured, it is not so — the same test takes 79.78s with the key and 80.17s with
`env -u ANTHROPIC_API_KEY`. The vision path does not fire for these inputs. The reason in the
table is the sample-file dependency and nothing else.

**The line, and what is on the other side of it.** A great many tests in this repo do
`subprocess.run([sys.executable, SCRIPT], …)` against the repo's own tracked scripts on hermetic
inputs — that is the documented idiom here (`CLAUDE.md`, *`cwd=USE_CASE_ROOT` in subprocess calls
from tests*), it is fast, and it stays in the gate. Read maximally, "spawns a live subprocess"
would swallow all of it and gut the suite. The seven `mix run --eval` tests are on the excluded
side because the subprocess they spawn is a *build tool in a different repository*: without the
marker the agents gate goes red for reasons that live in `../aetheris`, which is the hazard the
exclusion is for. **This line is mine, not the row's, and it is the packet's question for the
arbiter.**

Everything else with an environment guard was already marked — `wkhtmltopdf`, `pandoc`, `duckdb`,
`DRIVE_DOCBUILDER_ID`, `SMTP_*`, AWS credentials, `CT_RABBITMQ_URL`, `EDUX_DATABASE_URL`. The
`cloudcost` AWS tests are *not* marked and correctly so: they run against an in-process
`ThreadingHTTPServer` bound to `127.0.0.1` (`cloudcost/tests/conftest.py:101`), which never leaves
the machine. The `email` tests are fully `MagicMock`ed.

### 5b. `dormant` — business state

boxy-pipeline's work is paused pending its client. That is not a fact about test mechanics, it
has a different condition for return, and putting it through the `integration` marker would have
made the two indistinguishable to any future reader — which is how an exclusion set becomes
permanent and unexaminable. So: a second marker, named for what it means rather than for the use
case that prompted it.

Applied as `pytestmark = pytest.mark.dormant` at module level in each of boxy-pipeline's seven
test modules, each above a three-line dated comment pointing at `pytest.ini` for the full
statement. 208 tests. `pytest.ini` records the date (2026-08-16), the reason as business state
(*paused pending the client*), and the condition for return in a form a future reader can act on:
*it runs again when boxy-pipeline work resumes — delete the `pytestmark` lines in
`boxy-pipeline/tests/test_*.py`*.

**Dormant tests still collect and still import.** Verified: `-m dormant --collect-only` reports
`208/1714 tests collected`, and the whole-tree total is unchanged at 1714. A use case whose tests
stop collecting is one nobody notices has rotted, which is the defect this row exists to remove;
the deselection happens at run time and never at import.

**Scope.** Dormancy here is a test-apparatus fact and nothing else. Nothing was removed from
`sprint.sh`, from any `tools.json`, from any runbook or capability list, or from any document
describing what this repo contains; no boxy code, fixture or output was moved, deleted or
archived. Module-level `pytestmark` was chosen over a `pytest_collection_modifyitems` hook in
boxy's `conftest.py` precisely because it is visible in each file a reader opens.

---

## 6. The gate (S3b), and how it reports itself

```bash
# from the aetheris-agents/ repo root
python3 -m pytest -q -m "not integration and not dormant"
```

`1384 passed, 3 skipped, 320 deselected, 7 xfailed in 178.56s (0:02:58)`, exit 0, under a 900s
cap it did not approach.

**It reports both exclusion counts separately**, on its own summary line:

```
deselected by reason: integration=112, dormant=208 (total 320)
```

pytest itself prints one merged `320 deselected`; the split comes from `pytest_deselected` +
`pytest_terminal_summary` hooks in `tests/conftest.py`. Attribution is disjoint — `dormant` wins
when an item carries both, because a dormant use case's tests are not gating regardless of their
mechanics — so the two counts plus `other` always sum to pytest's own total. 112 + 208 = 320. ✓

**2m58s is tolerable at a ticket boundary.** It is under the harness's own `mix test`, and
`cloudcost/tests/` alone accounts for 153s of it.

**Ruling 1 did not fire.** The suite collects and passes. There is no allowlist, xfail sweep or
deselect list in this ticket's output. The 7 xfails are pre-existing and strict (`NO_MANIFEST_YET`,
BL-089). One real red *did* appear mid-ticket and it was mine, not the repo's — §10.

---

## 7. The two excluded sets (S3d), under caps

The arbiter's Part 1 correction governs this section: every run that can reach live subprocess
work runs under an explicit wall-clock cap, and a cap-kill is a complete and valid result.

**`python3 -m pytest -q -m "integration and not dormant"` — RUN.** Cap 900s.
`98 passed, 14 skipped, 1602 deselected in 25.27s`, exit 0. Twenty-five seconds; the 14 skips are
the credential- and binary-guarded tests self-skipping (`CT_RABBITMQ_URL`, `CT_S3_BUCKET`,
`DRIVE_DOCBUILDER_ID`, `SMTP_*`, `EDUX_DATABASE_URL` all unset here). Slowest single test 1.26s.
**This half of the exclusion costs almost nothing and could be folded back into the gate**; it is
kept separate because the marker asserts a property, not a cost.

**`python3 -m pytest -q -m dormant` — DOCUMENTED, NOT RUN**, per the arbiter's Part 2. What is
known about it comes from two capped runs made before the `dormant` marker existed, both killed
deliberately, both reported here as capped results rather than as checks still owed:

| run | cap | outcome |
|---|---|---|
| `python3 -m pytest -q -m integration` (merged set, before the split) | 2700s | **killed deliberately at 52m21s.** 37 of 169 results emitted. Progress had stalled at collection item 36, `boxy-pipeline/tests/test_pipeline.py::test_plan_path_produces_same_output_as_drawings_path` — the test that spawns `plan_extractor.py` against the two sample PDFs. Sampled at 4.1% CPU with no live child process. Note the process did **not** die at its own 2700s `SIGTERM`; I did not investigate why, and it is not this ticket's business. |
| `python3 -m pytest -m integration boxy-pipeline -v` | 2400s | **killed deliberately at 10m17s.** 21 of 57 results emitted, one `FAILED` (below). |

Projected from the observed rate, the boxy set would need roughly four hours. **That is the
finding, not a check I still owe** — and it is now confined behind a marker whose command nothing
runs by default.

**One red inside the dormant set, reported and left red** (Ruling 1):
`boxy-pipeline/tests/test_catalog_resolver_refactor.py::test_real_jsonl_resolve_matches_excel_result`
**FAILED**. Not fixed, not marked, not deselected for failing — it is deselected because
boxy-pipeline is dormant, and it will be red again the day boxy resumes. A **second** failure
appeared in the merged run's progress stream (`ssssssss................F....F......`) at a
position consistent with `test_order_formatter.py`, but the verbose run was cap-killed before
reaching it, so **its identity is unconfirmed and I am not naming it by inference.**

---

## 8. The true whole-suite figure, and what it does not reconcile with (S3e)

**1714 collected** at the root, zero collection errors. The gate accounts for all of it:
1384 passed + 3 skipped + 7 xfailed + 320 deselected = 1714. ✓

It reconciles with **no** previously reported figure in this repo's notes, and it should not.
Every "full suite" number in the record is a *scope* figure. The row singles out m6 t1's
**386 passed**; that figure appears at `cloudcost/docs/m6-t1-implementation-notes.md:303` and in
five m5 notes files, and in every one of them the command printed beside it is
`python3 -m pytest cloudcost/tests/`. So the row's claim — that it is not reproducible from the
root command — is true, but the sharper statement is that **it was never a root-command figure and
was never presented as one**; the mismatch is between the number and the *phrase* "full suite",
not between the number and its own command. That same `cloudcost/tests/` scope collects **465**
today and runs **464 passed, 1 deselected in 153.57s** (m6 added the GitHub provider). Neither
number is adjusted here.

---

## 9. Documents (S4), and the reference sweep

`CLAUDE.md` §Definition of done gains the gate **as a command**, a two-row table distinguishing
the markers, the "a red test is reported red, not marked" clause, the dormant-tests-still-collect
clause, and the capped-run rule. The standing gate-enumeration line gains the Python gate:
following the wiring-list rule the enumeration was *extended* rather than joined by a second
clause, because the clause was already correct and only its instance list was short. §Commands
gains the three commands.

`docs/backlog-2026-06.md` BL-152 gains a dated annotation in the row's existing style. **The row
is not marked closed** — the arbiter closes it on the packet.

**Everything else the S0d sweep found is a *scoped* invocation and was left unchanged**, because
`pytest.ini` does not alter what a scoped command collects — proven scope by scope in §2, in both
the root-relative and cwd-relative forms. The full list, with the search commands, is in the
packet. The one worth naming here: the harness's `scripts/sprint.sh` runs
`python3 -m pytest ../aetheris-agents/api/tenant/tests/ ../aetheris-agents/api/gateway/tests/ -q`
from `aetheris/`, which now finds this `pytest.ini` by upward search and pins rootdir to the
agents repo. Verified by running that exact invocation from `aetheris/`: `108 passed, 11 skipped`,
the same 119 collected as before. **The harness needs no change and its HEAD is unchanged at
`d19f4b6`.**

---

## 10. SURPRISES

- **I introduced a real red, and the positive control is what caught it.** My first implementation
  put the deselection-reporting hooks in a new **root `conftest.py`**. pytest imports a rootdir
  conftest under the bare module name `conftest`, and eight cloudcost test modules do a *runtime*
  `from conftest import …`. Two of them broke:
  `ImportError: cannot import name 'CLOUDCOST_ACCESS_KEY' from 'conftest'
  (~/sandbox/elixirws/aetheris-agents/conftest.py)`, in `test_compose_report_data.py:888` and
  `test_detect_orphans.py:898`. This is **§3's mechanism 1 again** — the `conftest` name — in the
  one form `--import-mode=importlib` cannot fix, because the import is executed by test code
  through `sys.path` rather than by pytest's importer. It reproduced only in a whole-tree run:
  `cloudcost/tests` alone was 464 passed, and the two tests alone passed. Fixed by deleting the
  root `conftest.py` and moving the hooks into `tests/conftest.py`, which is collected by every
  whole-tree invocation. Recorded rather than quietly fixed, because for two runs this file
  reported a green gate that was not green.
  **Left standing as a latent fragility, not fixed here:** ten `from conftest import …` lines
  across eight cloudcost modules mean any future root-level `conftest.py` re-breaks them. That is
  a candidate row for the arbiter, not a change this ticket should make.
- **`markers` in `pytest.ini` is a line list, and an indented continuation line registers a whole
  new marker.** My first version wrote each marker's statement across several indented lines,
  which read correctly to a human and registered `@pytest.mark.so`, `@pytest.mark.tests` and
  `@pytest.mark.collecting` to pytest. It produced no warning and did not affect selection — the
  only thing that surfaced it was running `python3 -m pytest --markers` and reading the output.
  Fixed by putting each marker on one line however long, with the long form in the comment block
  above. Worth recording because a registry that silently accepts garbage is a registry that would
  also silently accept a typo'd marker name as valid.
- **The row's "blocks inside a live subprocess" is right, and my first reading of it was wrong.**
  §1, pointer 3. I generalised from a run that never executed the blocking test.
- **`python3 -m pytest` and `pytest` are different commands here.** Every scoped invocation in
  every doc in this repo is written `python3 -m pytest`, and the `-m` is load-bearing: it is what
  put the working directory on `sys.path` and made `boxy-pipeline`'s import work from one
  directory and no other. A repo that had standardised on bare `pytest` would have found this
  defect earlier.
- **The fix's blast radius was smaller than the row's *Costs* paragraph feared.** Pinning rootdir
  did not disturb any `conftest.py`, because the collisions were in *module naming*, not in path
  insertion — and `--import-mode=importlib` takes test-module imports off `sys.path` entirely
  while leaving every `sys.path.insert` in every `conftest.py` doing exactly what it did before.
- **The whole cost of the old root command lived in one dormant use case.** The non-boxy half of
  the integration set runs in 25 seconds; boxy's half does not finish in four hours.

---

## 11. Three checks the arbiter asked for

1. **Does the gate write into the tree?** Measured by timestamp across two full gate runs: the
   only files written anywhere in the tree are `.pytest_cache/v/cache/{lastfailed,nodeids}` and
   `**/__pycache__/*.pyc`. Both are ignored — `.gitignore:4` (`.pytest_cache/`) and `.gitignore:2`
   (`__pycache__/`), both patterns unanchored and so matching at any depth. `git status
   --porcelain` after a gate run shows nothing but this ticket's own edits. The
   `boxy-pipeline/output/jsonl_test_order_form.xlsx` written earlier in this session came from a
   boxy test, and it is ignored by `boxy-pipeline/.gitignore:6` (`output/*`, with
   `!output/.gitkeep`); with boxy dormant the gate no longer writes it at all. **No unignored gate
   side effect on the tree.** Reported only — no product behaviour changed.
2. **The new root `.pytest_cache/`.** Already covered: `.gitignore:4` is `.pytest_cache/` with no
   leading slash, so it matches at the root as well as nested. Confirmed by
   `git check-ignore -v .pytest_cache/` → `.gitignore:4:.pytest_cache/`. No `.gitignore` change
   was needed, so it is not in Touches.
3. **The five `provenance/tests/*` files.** Seven added lines total, every one a bare
   `@pytest.mark.integration`; no other edit in any of them.
   `test_search_agent.py` +3 (three tests), `test_zip_archaeologist.py` +1,
   `test_zip_orchestrator.py` +1, `test_classification_orchestrator.py` +1,
   `test_migration_agent.py` +1. **The mechanical property earning each:** the test body calls
   `subprocess.run(["mix", "run", "--eval", …], cwd=<repo>/../aetheris)` — it spawns the sibling
   harness repo's build tool. **None was red before the marker**, proven by the 1545→1535
   arithmetic in §5a; all seven pass today inside `-m "integration and not dormant"`.

---

## 12. UNREAD

- I did not read the bodies of the 1384 gate tests. The claim in §6 is that they pass, measured;
  it is not a claim about what they cover.
- I did not audit the 159 pre-existing `@pytest.mark.integration` marks against the criterion now
  written in `pytest.ini` — I checked the other direction, that every environment-guarded
  *unmarked* test was either marked here or justified. Some existing mark may not meet it.
- I did not identify the second failure in the dormant set (§7), and did not name it by inference.
- I did not investigate why the merged integration run outlived its own `timeout 2700` SIGTERM.
- `provenance/mcp/corpus-search/tests/` has no `conftest.py` and is the only test directory
  without one. It collects and passes; I did not investigate why it differs.

---

## 13. The amendment (2026-08-16, after approval of 2868a3e)

Approved with amendments; `2868a3e` is not rewritten, because a review packet citing its
done-checks had already been issued and amending would leave those citations pointing at a tree
that never existed. Everything below is a second commit on top.

### 13a. The `integration` criterion, restated (A1)

The §8 judgement was upheld, but *"leaves this repository"* described the ten marks without
explaining them. `pytest.ini` now states the property underneath all three cases:

> **The criterion:** the test's outcome depends on state that is not in this repository at the
> commit under test.
>
> **The test to apply:** would this test do its work and pass in a fresh clone of this repo at
> this commit, offline, with no sibling repository present? If it would fail, error, or *silently
> skip* because the thing it needs is not there — it is `integration`. A subprocess against a
> script tracked in this repo is not, however many it spawns.

**A silent skip counts, and that clause is doing real work here** — without it the criterion
would exempt all ten marks, because every one of them guards itself with `pytest.skip` rather than
failing. "Passed here, skipped in a fresh clone" is precisely an outcome that depends on state the
repository does not carry.

**All ten re-checked; none loses its justification, so nothing was re-marked.**

- The three in `boxy-pipeline/tests/test_plan_extractor.py` read
  `boxy-pipeline/data/samples/*.pdf`. `git ls-files boxy-pipeline/data/samples/` is **empty** —
  the PDFs are gitignored client data (`boxy-pipeline/.gitignore:2`, `data/*`), so a fresh clone
  has none of them, `SAMPLES_AVAILABLE` is False, and all three skip (guards at `:150`, `:163`,
  `:431`).
- The seven in `provenance/tests/` call
  `subprocess.run(["mix","run","--eval",…], cwd=<repo>/../aetheris)` and each guards with
  `pytest.skip("aetheris repo not found")` — `test_search_agent.py:20,38,57`,
  `test_zip_archaeologist.py:21`, `test_zip_orchestrator.py:227`,
  `test_migration_agent.py:197`, `test_classification_orchestrator.py:149`. A fresh clone with no
  sibling checkout skips all seven.

The criterion remains structural. A red test still does not become `integration`.

### 13b. `--strict-markers` — KEPT (A2)

Added to `addopts`. Whole-tree collection under it is clean:

```
$ python3 -m pytest -q --collect-only        # with --strict-markers
1714 tests collected in 2.89s
EXIT=0
```

and the gate is unaffected: `1384 passed, 3 skipped, 320 deselected, 7 xfailed in 179.65s`,
exit 0. **Nothing to record as blocked, and no marker was added to make anything pass.**

**What this settles and what it does not.** It proves every mark in the tree is *registered* — the
cheap, syntactic half of the audit declined in §12, and it came back empty. It says nothing about
whether a registered mark belongs on the test carrying it. That semantic audit is **BL-158**.

`python3 -m pytest --markers` now shows exactly the intended registry and no accidental entries:
the two from `pytest.ini`, plus the pre-existing per-conftest `integration` line
(*"requires live repo files and optionally AETHERIS_DB_PATH"*, `tests/conftest.py:8`) and pytest's
own nine builtins. The junk entries recorded in §10 (`@pytest.mark.so`, `.tests`, `.collecting`)
are gone.

### 13c. Rows filed (A3) — packet prose files nothing

Next free numbers verified at HEAD: rows existed through **BL-156**, so:

| row | what it owns |
|---|---|
| **BL-157** | The bare module name `conftest` is a standing trap held open by an absence. Ten runtime `from conftest import …` lines in eight cloudcost modules, which `--import-mode=importlib` does not cover; they work only because no root `conftest.py` exists, and nothing checks that. Carries §10's `ImportError` reproduction verbatim. Owes the choice between a guard test, a call-site change, or something else — **not decided**. |
| **BL-158** | The 159 pre-existing `integration` marks have never been read against the criterion the gate now uses. Figures re-verified rather than carried: **169** marked tests (the grep's 171 includes two docstring mentions), 10 added here, **159 pre-existing**, of which 105 the gate deselects and 54 the dormant set absorbs. Names both directions — an unmarked test that *should* carry the mark is the worse defect, and this ticket found three. |
| **BL-159** | What the dormant set owes when boxy-pipeline resumes: ~4h projected, did not finish under either cap, one named red left red, one failure unidentified and deliberately not inferred. **Cross-referenced both ways** with `pytest.ini`'s condition for return. |

Two seeds appended to **BL-151**: `ROADMAP.md:246`'s command-less claim, now contradicted by a
gate that deselects 320 of 1714; and the merged `-m integration` run outliving its own
`timeout 2700` SIGTERM at 4.1% CPU with no live child, recorded with its guessed cause explicitly
labelled a guess.

**The third seed was investigated and deliberately not filed.** The top-level `email/` directory
versus stdlib `email` is **inert today**, established by running it rather than by reasoning:
with the repo root at `sys.path[0]`, `import email` resolves to
`…/python3.12/lib/python3.12/email/__init__.py`. A directory without `__init__.py` contributes only
a namespace *portion*, which does not stop the path scan, so the stdlib's regular package wins.
`email/` is the only top-level directory in the repo sharing a name with a stdlib module. The
conditional hazard is real — adding `email/__init__.py` would shadow stdlib `email` repo-wide —
but it is already governed by a documented convention (`CLAUDE.md` §Python script conventions;
`docs/agent-creation-guide.md:307`), and a row asserting a defect that does not exist would be a
false entry. The **decision** not to file is recorded in BL-151's existing *"Deliberately not
seeded"* convention, so it is auditable in the tree rather than only in a packet.

### 13d. `CLAUDE.md` touched, beyond the three files the amendment predicted

The amendment's done-check 2 expected `pytest.ini`, `docs/backlog-2026-06.md` and this file.
`CLAUDE.md` is the fourth, and the reason is A1's own logic: its marker table stated the *old*
criterion in its own words. Leaving it would have created two surfaces stating the criterion
differently — the exact defect `CLAUDE.md` itself warns about — so the table row and the paragraph
under it now carry the restated form and name `pytest.ini` as the authority rather than restating
it a second time. No command in that file changed; done-check 6's byte-identity still holds.
