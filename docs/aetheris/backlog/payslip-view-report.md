# Technical brief — Payslip "View report"

**Candidate backlog row:** unnumbered — assign the next free id when filed, not now (timing is
open, and the free id may shift before this is taken up)
**Size:** XS–S · **Priority:** low · **Section:** aetheris-agents (`rig/` verify; possibly
`payslip/scripts/`)
**Relationship:** pure drop-in on BL-073's generic control; no dependency on provider three.
Fires whenever someone is next in the payslip pipeline.

---

## Summary

Payslip runs generate documents (HTML, PDF, CSV) but expose no way to open them from Rig, unlike
cloudcost and docbuilder, which got "View report(s)" at BL-073. The question is whether payslip
should have the same affordance.

**The finding that shapes this: it is verify-not-build.** BL-073's resolver
(`harness_run_artifacts` / `harness_open_artifact`) is deliberately use-case-agnostic — it scrapes
any run's `tool_result` for paths ending in the document-extension set (`.html .htm .pdf .docx
.xlsx .pptx .csv .md .xml`), resolves them against the run's `sandbox_path`, existence-gates them
server-side, and offers the set. Payslip's `generate_employee_payslips.py` emits **HTML, PDF and
CSV** (`capability-matrix.md` §Payslip), all in that set. So a payslip run *should* surface "View
report(s)" with **no Rig change** — provided three conditions hold. Payslip was simply not in
BL-073's live enumeration (which covered cloudcost + docbuilder), so it is untested, not excluded.

The likely outcome of this ticket is therefore a confirmation plus at most a small script-side
adjustment — not a new Rig feature.

## The three conditions that decide whether it already works

1. **Payload shape — the one real unknown.** BL-073 discovers a path only if the generation step
   prints it inside a JSON `stdout` the value-scanner can parse: `payload.output` (JSON string) →
   `stdout` (JSON string) → recursive scan for string values ending in a document extension. This
   is proven for `render_report` (`{file, pdf, …}`) and docbuilder's generators. It is **unverified
   for payslip** — if `generate_employee_payslips.py` prints its output paths as plain text, or does
   not echo them, the scan finds nothing and no control appears. Enumerate a real payslip
   trajectory's `tool_result` the way BL-086 §7 did for the other two. This is the load-bearing
   check.

2. **Existence at view time — payslip's lifecycle differs.** cloudcost and docbuilder *produce and
   keep* their artifact locally. Payslip *generates locally, then uploads to Drive and emails it*
   (pipeline: `drive_download → payslip generate → drive_upload → email_send`; some runs skip
   generation entirely — "payslips already uploaded in drive, do not create again"). If the local
   `payslip/output/{EMPLOYEE_ID}/…` copy is cleaned after upload, the existence gate correctly hides
   the control — the same reason stale June docbuilder runs show nothing. So even a scrapable path
   may resolve to a gone file. Verify whether the local copy persists past the upload step; if it
   usually does not, "View report" for payslip is low-value as-is unless the flow is changed to
   retain the local copy.

3. **Multiplicity — the bulk case.** A single-employee run (e.g. `BTL_099`) produces one document
   in up to three formats — fine, offer-the-set handles it. A run *for all employees* produces
   N employees × 3 formats; the offer-the-set list was not designed for dozens of filenames. Decide
   whether to cap/group the list or scope the control to single-employee runs.

## One softer consideration

Payslips carry salary / PII, unlike a cost report or a generated document. `open::that_detached`
runs on the operator's own machine, so it is not a leak, but opening payroll documents from Rig
should be a conscious accept rather than an unremarked default — worth one line in the runbook if
this lands.

## Decision points (if it becomes a ticket)

- **If shape fails (paths not in scannable JSON):** either give `generate_employee_payslips.py` a
  structured `stdout` emitting its output paths (a payslip-script change, *not* a Rig change, and it
  aligns payslip with the contract `render_report` and docbuilder's generators already follow), or
  accept no control for payslip. Prefer the former — it is the same generic-emit convention, and it
  also benefits any future consumer that reads payslip output paths.
- **If existence is usually false (local cleaned after upload):** the real question is payslip's
  artifact lifecycle, not Rig. Decide whether the payslip flow should retain the local copy (so the
  control has something to open) or whether "View in Drive" is the more honest affordance for a
  use case whose deliverable lives in Drive, not on disk. This is the genuinely different-from-the-
  -others part and where the design judgment sits.
- **Multiplicity:** cap or group the offer-the-set list for bulk runs, or scope to single-employee.

## Verification plan (offline where possible)

- Enumerate a real payslip run's `tool_result` payloads: is each generated path present in a JSON
  `stdout`? (Same method as BL-086 §7 — read on-disk trajectories, no launch.)
- Run BL-073's resolver against a payslip run offline (its live arm already does this for cloudcost /
  docbuilder) and record what it returns: the artifact set, and how many survive the existence gate.
- Check local-copy persistence across the `drive_upload` step.
- Only the rendered control and the actual open are live-only — and per the standing learning, if
  the Done-when names a user-facing action, that click-through is a merge gate, not an owed
  residual.

## Done-when (if filed)

A single-employee payslip run whose local artifact is present shows "View report(s)" opening the
payslip; the bulk-run and cleaned-local cases behave predictably — a grouped/capped list or no
control, never a broken link; **no Rig code change if the generic path already covers it**, else the
single named adjustment (script `stdout` shape, or the lifecycle/"View in Drive" decision) rather
than special-casing payslip in Rig — the whole point of BL-073 being generic is that a use case does
not earn cloudcost-style strings in Rig.

---

`Source: follow-up to BL-073 (generic View report), 2026-08-04.`
