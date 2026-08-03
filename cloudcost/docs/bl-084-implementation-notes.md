# BL-084 — `cloudcost/tools.json` manifest (implementation notes)

Declares cloudcost's seven scripts to Rig's Tools module, and lands the offline manifest
suite the repo did not have. These notes carry what does not survive in the code: the two DoD
lines that could not be delivered as written, the facts BL-085 inherits, and the boundary
between what was proven offline and what is only derivable.

---

## Two DoD amendments, adjudicated before implementation

**1. "`_normalized.py` is not Run-able" — not deliverable by manifest.** `ManifestScript`
(`rig/src-tauri/src/commands/tools.rs:29-46`) has no `runnable` field, and the Run button at
`ToolDetail.tsx:175-186` renders for every script, declared or not, gated only on empty
required args. Omitting the entry is strictly worse than declaring it: the walker synthesises
any undeclared flat `.py` as `undeclared: true` (`tools.rs:560-575`), so it would stay amber
*and* stay runnable.

Replaced by: `_normalized` is declared import-only (`args: []`, `output: "text"`, description
naming it a non-CLI). Run-button suppression is tracked by **BL-088**.

The "running it is a no-op" claim in the description was checked before it shipped, not
asserted: `_normalized.py` contains no `__main__`, no `argparse` and no `def main`, and
`python3 cloudcost/scripts/_normalized.py` exits 0 with no output.

**2. "descriptions match capability-matrix.md" — holds for five of six.**
`docs/capability-matrix.md` §Cloudcost lists six script rows and omits
`detect_optimization_signals.py` entirely (its summary row reads `| cloudcost | 1 | 6 |`
against seven files on disk). `fetch_aws`, `fetch_do`, `detect_orphans`,
`compose_report_data`, `render_report` and `_normalized` reuse the matrix cell verbatim;
`_normalized` appends one sentence. `detect_optimization_signals` is source-derived:

> Exploratory AWS optimization signals over S3, ECR, and Secrets Manager — missing S3 and ECR
> lifecycle policies, incomplete multipart uploads, empty buckets, untagged-image
> accumulation, and unused secrets — emitted as a separate signals/denied/warnings artifact
> that the core report pipeline never reads.

Every clause is from the code, not from the docstring's prose: the six signal-type constants
at `detect_optimization_signals.py:96-101` are `s3_no_lifecycle_policy`,
`s3_incomplete_multipart`, `s3_empty_bucket`, `ecr_no_lifecycle_policy`,
`ecr_untagged_image_accumulation`, `secret_unused`; the envelope carries
`signals`/`denied`/`warnings`/`totals`/`regions_swept` (:809-819); the artifact is
`optimization_signals_{PROVIDER}_{period}.json` (:892-894); "the core pipeline never reads
it" is decision G, and `compose_report_data.py` does not touch the file. The
capability-matrix row is to be amended to match this wording.

---

## Decisions taken while writing the manifest

**`default` pre-fills the input — it is not a placeholder hint.** `ToolDetail.tsx:71-73`
seeds `argValues` from `a.default ?? ''`, and `buildArgs` passes whatever is in the box. A
declared default is therefore a value Rig will actually run with. Three consequences:

- **`--history-dir` deliberately carries `null`, not the script's default.** The script
  defaults to the shared `cloudcost/history`, but the pipeline convention is per-provider
  (`cloudcost_orchestrator.exs:91`, `history_dir = "history/#{provider_slug}"`), and the
  orchestrator's own comment at `:82-88` records why: the shared root makes
  `load_prior_snapshots` glob *every* provider's snapshot and sum them into one `prior_total`
  — a wrong month-on-month headline (BL-076). Pre-filling the hazardous path in a one-click
  UI is not what the field is for. The arg description names the convention and the fallback.
- **Relative path defaults are exact, not approximate.** `tools_run_script`
  (`tools.rs:636-673`) sets `current_dir` to the use-case dir, so `templates/report.html.j2`
  resolves to precisely `render_report.DEFAULT_TEMPLATE`. Declaring the absolute value would
  have baked a machine-specific path into a committed file.
- **Numeric defaults are quoted strings.** `ManifestArg.default` is `Option<String>`; a bare
  `30` is a serde reject, which `tools.rs:526` turns into a silently absent manifest.

**`output: "json"` for all six CLIs**, including `render_report`. `output` selects stdout
rendering, not side effects, and every one of them ends in `print(json.dumps(summary,
indent=2))` (`fetch_aws:1130`, `fetch_do:596`, `detect_orphans:650`,
`detect_optimization_signals:897`, `compose_report_data:906`, `render_report:433`).

**`compose_report_data`'s three repeatable flags have no manifest analogue.** `--cost`,
`--inventory` and `--orphans` are `action="append"`; the schema has no repeatable arg. Each is
declared single-valued with the constraint stated in its description (repeatable on the CLI,
paired positionally, mutually exclusive with `--input-dir`), and the `example` uses
`--input-dir`, which is the form that covers the multi-provider case from the UI.

**The `_normalized` example was fixed after testing it.** The eduloka precedent form
`python3 -c "from X import Y"` fails from the use-case dir — `scripts/` is not on `sys.path`.
The shipped example is `PYTHONPATH=scripts python3 -c "…"`, which was run and produces the
seven canonical types. The other six examples are illustrative: they name period-stamped
artifacts that only exist after a run.

---

## `env` arrays — and what BL-085 inherits

Six keys, group `cloudcost`, declared on the scripts that actually read them:

| Key | Declared on | Masked |
|---|---|---|
| `CLOUDCOST_AWS_ACCESS_KEY_ID` | `fetch_aws`, `detect_optimization_signals` | no |
| `CLOUDCOST_AWS_SECRET_ACCESS_KEY` | `fetch_aws`, `detect_optimization_signals` | yes |
| `CLOUDCOST_AWS_SESSION_TOKEN` | `fetch_aws`, `detect_optimization_signals` | yes |
| `CLOUDCOST_AWS_REGION` | `fetch_aws`, `detect_optimization_signals` | no |
| `CLOUDCOST_AWS_REGIONS` | `fetch_aws`, `detect_optimization_signals` | no |
| `CLOUDCOST_DO_TOKEN` | `fetch_do` | yes |

`detect_optimization_signals` reads `CLOUDCOST_AWS_REGIONS` directly (:883) and the other four
transitively through `from fetch_aws import load_credentials, …` (:72-86). Declaring them on
both is correct rather than redundant: `env` also drives the per-script "Required config" dots
at `ToolDetail.tsx:83-101`. Inventory-level dedup (`tools.rs:594-604`, first declaration wins)
means Settings sees one row each.

`detect_orphans`, `compose_report_data`, `render_report` and `_normalized` declare no `env` —
they read none.

**Deliberately not declared.** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
`AWS_SESSION_TOKEN`, `AWS_PROFILE`, `DO_TOKEN`, `DIGITALOCEAN_ACCESS_TOKEN` are
`SHADOWING_ENV` — read only to emit a warning, never authenticated with. `CLOUDCOST_PROVIDER`
and `CLOUDCOST_OPTIMIZATION` are read by `cloudcost_orchestrator.exs`, not by any script;
declaring them under a script's `env` would be false. They are BL-085's problem.

**Carry-forward to BL-085 (D2), surfaced not resolved.** The `CLOUDCOST_` prefix isolates
cloudcost from `api/tools.json`, which already declares bare `AWS_ACCESS_KEY_ID` and
`AWS_SECRET_ACCESS_KEY` in group `aws` — so those rows are in Rig's config surface *today*,
and dedup gives them to `api` regardless (directory-sort order puts it first). Separately,
`tools_run_script` injects the **entire** agent-config map as env, unfiltered by the script's
declared `env`. A Rig-launched cloudcost run can therefore carry the D2 poison actively
present, not merely lack the `env -u` belt. One more, found while tracing: `exportConfig()`
(`rig/src/hooks/useAgentConfig.ts:33-41`) iterates `AGENT_CONFIG_DEFS` only, so the six
`CLOUDCOST_*` keys will be editable and persisted but silently omitted from Export.

---

## `tests/test_tools_manifests.py`

The repo had no test that parsed a `tools.json` — not in pytest, not in Rust
(`tools.rs` has zero `#[cfg(test)]`). Four checks parametrised over the sweep, plus a guard on
the sweep itself.

**Swept set (9):** `api`, `boxy-pipeline`, `cloudcost`, `docbuilder`, `drive`, `eduloka`,
`email`, `payslip`, `provenance`. Predicate: a top-level dir, excluding dot-dirs and the
walker's own exclusions `rig`/`docs`/`agents` (`tools.rs:514-518`), that either carries a
manifest or holds ≥1 runnable CLI in `scripts/*.py`. Runnable CLI =
`if __name__ == "__main__":`, so import-only modules do not make a dir qualify.

**Expected-red, `xfail(strict=True)` so the marker must be removed when fixed:**
`boxy-pipeline`, `docbuilder`, `provenance` have no manifest (filed alongside BL-084);
`payslip` on `test_no_undeclared_scripts` only, for BL-087.

**payslip was the only pre-existing red.** `drive`, `email` and `eduloka` declare every
runnable CLI they hold; no dangling `file` and no malformed `env` or arg anywhere. Its other
three params are unmarked and green — only completeness is broken.

**Two boundaries stated rather than papered over.**

- *The check is a proxy for amber on a runnable CLI, not for amber.* Rig badges any undeclared
  flat `.py`, so `drive/scripts/__init__.py`, `drive/scripts/drive_utils.py`,
  `email/scripts/__init__.py` and `payslip/scripts/__init__.py` wear amber today and this
  suite does not flag them. For cloudcost the two coincide, because `_normalized.py` is
  declared — cloudcost ends with zero amber.
- *`test_no_undeclared_scripts[api]` passes over an empty set.* api's scripts live in
  `api/tenant/scripts/` and `api/gateway/scripts/`; the walker only globs flat `scripts/*.py`,
  so neither it nor this suite sees them. `test_discovery_sweep_intact` asserts
  `_flat_cli_scripts("api") == []` explicitly so the vacuity is visible instead of reading as
  coverage.

**Mutation-checked before being trusted** — five breakages, each caught by the intended check,
file restored byte-identical after:

| Mutation to `cloudcost/tools.json` | Failed |
|---|---|
| drop `placeholder` from an `env` entry | `test_env_dep_fields_complete[cloudcost]` |
| point a `file` at a nonexistent script | `test_declared_files_exist[cloudcost]` |
| `output: "html"` | `test_manifest_parses[cloudcost]` |
| delete the `fetch_aws` entry | `test_no_undeclared_scripts[cloudcost]` |
| `description: 42` (non-string where Rust expects `String`) | `test_manifest_parses[cloudcost]` |

---

## What is proven offline, and what is not

**Proven:** the suite above (24 passed, 7 xfailed), the five mutations, the six `--help`
captures every arg form was transcribed from, and the `_normalized` example actually running.

**The transcription gap, and how it was closed.** The pytest schema is a *transcription* of
the serde structs at `tools.rs:4-46`; it does not run serde. That gap is the ticket's core
risk rather than a footnote: if the transcription diverges in either direction — a field serde
requires that pytest treats as optional, or `deny_unknown_fields` on any struct — the manifest
passes the whole suite, fails `serde_json::from_str`, and `tools.rs:526` drops it to `None`.
All six cloudcost scripts would go amber with nothing anywhere saying why: precisely the
failure BL-084 exists to prevent, in its invisible form.

Closed offline by a one-shot round-trip against the **real** structs — a temporary
`#[cfg(test)]` module in `tools.rs` deserializing each committed manifest into `ToolsManifest`,
the exact type `tools.rs:526` targets. `cloudcost` parsed to 7 scripts, the dedup walk yielded
the 6 expected `CLOUDCOST_*` keys in declaration order, `detect_orphans`'s positional
deserialized with `flag: None`, and `_normalized`'s absent `env`/`undeclared` took their
`#[serde(default)]` values rather than erroring. The five existing manifests were parsed in the
same run — api 14, drive 2, eduloka 14, email 2, payslip 2 — so none of them is silently
dropped today either. `deny_unknown_fields` appears nowhere in `src-tauri/src/`.

The round-trip was itself mutation-checked before being believed: dropping `label` from one
`env` entry produced ``[serde FAIL] cloudcost: missing field `label` at line 152 column 9`` and
failed the test; restoring made it pass again. The module was **discarded** after running —
`tools.rs` is byte-identical to HEAD — because adding Rust test coverage there is BL-092's
call, not BL-084's. Re-create it from this paragraph if that row wants a seed.

**Still live-only:** that the badge and the config rows *render*. Deserialization is proven;
display is not.

**Live-only.** Both remaining DoD items are derivable from the traced path but observable only
in a running Rig — amber clearing (`tools.rs:560-575` → `ToolTree.tsx:71-73`; offline proxy is
`test_no_undeclared_scripts[cloudcost]`) and the config rows (`tools.rs:594-604` →
`SettingsRoute.tsx:18` → `AgentConfigTab.tsx:~180-186`, where none of `AGENT_CONFIG_DEFS`' 18
keys is `CLOUDCOST_*`, so all six render as dynamic rows under a `cloudcost` header). Manual
check:

```bash
cd rig && AETHERIS_AGENTS_PATH=/home/it/sandbox/elixirws/aetheris-agents cargo tauri dev
# Tools → cloudcost: 7 scripts, no amber, structured arg forms
# Settings → Agent Config → cloudcost: 6 rows, secret + session token masked
```

`Source: BL-084, 2026-08-03.`
