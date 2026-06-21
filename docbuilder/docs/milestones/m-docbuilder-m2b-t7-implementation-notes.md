# Implementation notes — m-docbuilder-m2b t7

Ticket: LLM selection + full orchestrator (PHASE 0 + A–F) + sprint + runbook.

---

## What shipped

- `docbuilder_orchestrator.exs` — full m2b pipeline: PHASE 0 (template selection),
  A (fetch), B (compute), C (render), D (rename), conditional E (upload) / F (email),
  G (report). `tools: ["run_command"]`, `max_steps: 40`.
- `../aetheris/scripts/sprint.sh` — docbuilder case is now context-driven, prints the
  PHASE E/F enable/skip status, and verifies the **renamed** outputs.
- `runbook.md` — m2b env vars (`DOCBUILDER_CONTEXT` primary; `DRIVE_DOCBUILDER_ID`,
  `GOOGLE_SERVICE_ACCOUNT_FILE`, `DOCBUILDER_REVIEW_EMAIL`, `SMTP_*`), the phase list,
  updated run commands + expected output.

**Verified (dev, no Drive/SMTP):** sprint run `docbuilder-orch-W6tNPQ`, status `done` —
PHASE 0–D ran, outputs renamed to `acme_corp_proposal_2026-06-20.{xlsx,docx,pdf}`, E/F
skipped with a notice. **Scratch artifacts: 0.** Full suite 202 passed, 3 skipped.

---

## Decisions

**Eval-time resolution; LLM selection is genuine but confirmatory** (per the agreed
plan). At eval time the orchestrator reads the catalogue + context to resolve
`{doc_type, version}` (context `doc_type` for Option A, else the catalogue's first), then
pre-bakes PHASE A–F against that resolution. PHASE 0 still runs `list_templates.py` and
has the LLM emit `{doc_type, variant, rationale}` — for the single-variant demo this
resolves to `proposal/v1` and the LLM's choice confirms it. Multi-variant runtime
selection (where downstream must wait for the choice) is a documented future concern.

**Template fields resolved from the committed FLAT template at eval time.** The bundle
isn't fetched until runtime (and in Drive mode isn't local at all), so `data_sources` /
`output_formats` / `narrative` are read from `data/templates/{tenant}/{prefix}.json`
(always committed, mirrors the bundle). The render/compute commands point at the BUNDLE
dir (`fetch_template`'s output: Drive cache, or the committed nested bundle in dev). Base
files are detected via the flat base file as a proxy.

**`data_sources` paths stripped of `docbuilder/` at eval time** (t2 review F3, Option a) —
the same strip the m2a orchestrator did; no on-disk bundle rewrite.

**Conditional PHASE E/F (graceful degradation).** At eval time the orchestrator includes
PHASE E only if `DRIVE_DOCBUILDER_ID` is set and PHASE F only if `DOCBUILDER_REVIEW_EMAIL`
is set; otherwise each is emitted as a "(skipped: … not set)" line. The pipeline runs
fully in production and cleanly in dev (no creds) — verifying PHASE 0–D. No t5/t6 script
changes.

**PHASE E renamed paths pre-computed in Elixir.** `rename_output.py` produces
`{slug}_{doc_type}_{date}.{ext}`; those names are deterministic from the context, so the
orchestrator replicates `slugify` / `safe_segment` / `doc_type_base` at eval time to
pre-bake `upload_output.py --files <renamed paths>` — no runtime dependency on
`renamed.json` for the upload args.

**PHASE F is the one runtime dependency.** Drive URLs only exist after PHASE E (runtime
file IDs), so PHASE F instructs the LLM to pass the contents of `output/uploaded.json` as
`--drive-links`. This is the single place the LLM hands a file's content to a command;
it's bounded and mitigated (`email_send_review --drive-links` degrades to `(none)`), and
PHASE F only runs when a review alias is set (skipped + unverified in dev). A future
`email_send_review --drive-links-file` would make it fully pre-baked (deferred).

---

## Two sprint.sh bugs found while wiring (fixed)

1. **`${VAR:-{...}}` brace default appended a stray `}`.** The m2a-style
   `DOCBUILDER_CONTEXT="${DOCBUILDER_CONTEXT:-{\"…\"}}"` default mis-parses the nested JSON
   braces: when the var is already set to a value ending in `}`, bash appended an extra `}`
   (len 107), so the eval got invalid JSON (`Jason.DecodeError` at the trailing brace).
   Replaced with an `if [[ -z … ]]; then DOCBUILDER_CONTEXT='{…}'` single-quoted literal.
2. **`set -u` (nounset) on the delivery-status checks.** `[[ -n "${DRIVE_DOCBUILDER_ID}" ]]`
   tripped nounset when the var was unset → added `:-` defaults.

## Forward notes (t8)

- Capability matrix: the orchestrator's tools are now just `run_command`; include the new
  m2b scripts (`fetch_template`, `rename_output`, `upload_output`, `email_send_review`) and
  `_drive.py` (shared helper). `capability_matrix_docbuilder.exs` `max_steps` may need
  another bump (script count grew again).
- `requirements.txt`: add `google-api-python-client`.
- Reconcile `GOOGLE_SERVICE_ACCOUNT_FILE` vs `GOOGLE_SERVICE_ACCOUNT` (t2 review F2).
- CLAUDE.md candidate (t3 review F3): "remove `write_file` from an orchestrator's tools
  once every phase uses `--output FILE`."
- README m2b → done; milestone summary; note the conditional-delivery + LLM-confirmatory-
  selection patterns and the PHASE F runtime-dependency / `--drive-links-file` follow-up.
