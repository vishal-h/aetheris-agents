# t4 — `render_report.py` + `templates/report.html.j2` (custom report, local file) — implementation notes

**Ticket:** m1-cloudcost §t4. **Built:** 2026-07-29.
**Deliverables:** `scripts/render_report.py`, `templates/report.html.j2`,
`tests/test_render_report.py` (30 tests, offline; 1 marked `integration`),
`requirements.txt` (Jinja2).

---

## Decisions

**Purpose-built renderer, not Docbuilder's `generate_html.py` — adjudicated, not assumed.**
§t4 says reuse the Docbuilder path "if it fits the custom layout cleanly". It does not, for a
reason that is structural rather than aesthetic: `generate_html.py` takes its context as
**inline JSON on the command line** (`--context '{…}'`), and this payload is a ~10 KB
`report_data_{period}.json`. Handing it to the orchestrator to re-emit as a CLI argument is
precisely the large-blob round-trip the m2a rule exists to prevent ("give scripts an
`--output FILE`/`--input FILE` flag so the LLM never handles the blob"). `render_report.py`
takes the *path*, and the orchestrator passes a path. Two further points settled it: the
Docbuilder renderer's table enrichment lives in its **caller** (`generate_pdf.py`), so calling
it directly is the exact m6 defect where the DOCX path silently lost its Line Items table; and
a cross-use-case import would couple cloudcost's report to Docbuilder's doc-spec vocabulary,
which it shares none of. Jinja2 — the actual reusable part — is reused.

**Render-only is enforced by construction, then tested by mutation.** The module imports
neither `detect_orphans` nor `compose_report_data`, so there is no code path through which a
stage's arithmetic could re-run here; a test asserts the absence *and* checks its own detector
against positive controls first, so the guard cannot pass by matching nothing. It also imports
neither `datetime` nor `time`: with no clock imported there is no clock, and the "as of" line
is `report_data.as_of`, t3's own derived stamp. The behavioural half is
`test_a_mutated_figure_reaches_the_html`, which sets `grand_total` to a value its own service
lines contradict, a coverage ratio its own counts contradict and a band subtotal its own
candidates contradict — a renderer that re-totalled, re-derived or re-banded anything would
print the *consistent* figure and fail.

**`_normalized.py` is deliberately not imported either, despite the m2b shared-plumbing rule.**
Its `money()` coerces an unusable value to `0.0`. That is correct for arithmetic and wrong for
a report: a report that prints `0.00` where it has nothing is asserting, not reporting — the
silent-wrong-answer shape. `format_amount` renders an absent figure as an em dash instead, and
a test pins both directions (`None → "—"`, `0 → "0.00"`).

**The template applies formatting, never arithmetic — stated because the line matters.** Four
filters: thousands separators + 2dp on an amount, an explicit sign on a change, a payload
*fraction* shown as a percentage (`tag_coverage.coverage = 0.1667 → "16.67 % (0.1667)"`, the
raw payload value kept alongside so nothing is hidden behind the conversion), and `None → "—"`.
`mom_delta.delta_pct` is **not** multiplied — t3 already expressed it in percent, and `null`
there means "no meaningful ratio off a zero base", which renders as an em dash rather than as
`0 %`.

**Three caveats, all driven by payload state, all adjacent to the figure they qualify.**
§t4 Contract refs required the first; the other two are the same defect wearing different
clothes, and were found by rendering the payloads rather than by reasoning about them.

| Condition in the payload | What renders beside the headline |
|---|---|
| `mom_delta.providers_without_prior_snapshot` non-empty | "Not all of this change is organic growth" — names the providers; the worked example renders +74.21 / +46.97 % with DO's real +14.21 and someothercloud's first-time $60 separated in the rows below |
| `mom_delta.providers_only_in_prior` non-empty | the mirror case: a provider present last month and absent this month shows as a decrease |
| `mom_delta.currency` is null while `totals_by_currency` has >1 entry | "This change spans more than one currency" — see §Open items; the cost summary withholds its grand total for this reason but the MoM headline does not |

"Adjacent" is asserted structurally, not by proximity of words: the test locates the caveat
between the headline figure and the section's first `<table>`, i.e. inside the headline block.

**Degrade, don't crash — and `partial` reports *this stage's* problems only.** A section
missing from the payload costs the report that section, a rendering note inside the report and
a `{"status": "partial"}` / exit 1 envelope; the HTML is still written. The payload's own
`warnings[]` and `skipped[]` are **data**, not render failures: t3 already reported them, and
they render into the Data notes section rather than re-reddening a stage that did its job.
Every section body is guarded so an absent key degrades to "no data" rather than to a Jinja
`UndefinedError`, and `main` catches `jinja2.TemplateError` as a backstop so a template fault
becomes the stage-CLI error envelope rather than a traceback across the stdout contract.

**HTML is the primary path and depends on no system binary; PDF is an optional companion.**
§Prerequisites 3 names exactly this trade ("rendering HTML instead avoids that system dep").
The HTML inlines its CSS and fetches nothing — no CDN, stylesheet, font, script or image — so
it opens from disk on any machine, and a test asserts that rather than trusting it. `--pdf`
shells out to `wkhtmltopdf` where it exists; where it does not, the run gets a note and the
PDF, not the report. The PDF test is `@pytest.mark.integration` and skips on an absent binary.

**The template is anchored to the use-case root, not the cwd** (`Path(__file__).parent.parent /
"templates"`), the same rationale as t3's history directory and `__ENV__.file` in agent files:
the orchestrator invokes the script from wherever the harness put it. A test runs the CLI from
an unrelated cwd and asserts the template still resolves.

**Flex `gap` is not used for layout.** The print/PDF renderers built on older WebKit ignore it
and ran the header's metadata values together (`2026-072026-07-27T04:41:53Zdigitalocean`).
Caught by rendering to PDF and *looking*, not by a test — inline-block plus margins degrade
identically everywhere.

---

## Done-check (§t4) — evidence

Real pipeline, not a crafted payload: `detect_orphans.py` → `compose_report_data.py` →
`render_report.py` over the committed t1/t2 fixtures, with `history/2026-06/` seeded so the
MoM path is exercised, and a second run against an empty history for the no-MoM path.

| Path | Written | MoM status |
|---|---|---|
| ordinary monthly report | `cloudcost/output/cloudcost_report_2026-07.html` (19,067 B) | `ok` (+14.21 / +8.99 %) |
| first run, no prior month | `cloudcost/output/first-run/cloudcost_report_2026-07.html` (17,488 B) | `no_prior_month` |

Both `status: "ok"`, `render_warnings: []`. Reviewed visually as PDF renders of the HTML (all
six sections present; the orphan section shows all five candidates with full `evidence[]`,
per-candidate saving, band subtotals and the printed cutoffs; the N=2 render shows the caveat
beside +46.97 %; the multi-currency render shows "No combined total" with per-currency rows).

## Mutation checks (the guards are failable)

| Mutation | Result |
|---|---|
| template: grand total re-summed from `by_service` instead of read from `grand_total` | `test_a_mutated_figure_reaches_the_html` failed |
| template: new-provider caveat removed | `…caveat_adjacent_to_the_delta` failed |
| template: evidence lines replaced with a placeholder | 2 failed |
| renderer: `autoescape` disabled | 2 failed |
| renderer: `import compose_report_data` added | `…imports_no_stage_script_and_reads_no_clock` failed |

Restored: 30 passed; the use case's suite is 156 passed (t1 25, t2 54, t3 47, t4 30).

---

## Open items forwarded

- **`month_on_month` sums across currencies where `service_totals` refuses to.** In the
  multi-currency case t3 withholds `cost_summary.grand_total` and emits a warning — correctly —
  but `mom_delta.current_total` is still `232.21` (172.21 USD + 60.00 EUR) with
  `mom_delta.currency: null`, so the withheld scalar reappears one section down with no unit.
  A t3 change (withhold the cross-currency delta the same way, or emit it per currency); the
  template meanwhile prints the caveat beside it, which is the render-only response and not a
  fix. Unreachable while DO is the only provider.
- **t2's `reported` and `excluded` blocks never reach the report.** `detect_orphans.py` emits
  `reported` (the untagged-in-tagged-account rule, reported-only by §t2 design, each entry
  carrying its own `evidence[]`) and `excluded` (`keep=true` resources); `compose_report_data`'s
  `orphan_section` carries `candidates` only, so `report_data` has no key for either and the
  report cannot show them. The reported-only rule therefore exists in the pipeline and is
  invisible in its output. A t3 change — the renderer will not invent a section the payload
  does not carry. Visible today: the tagged-account fixture reports 2 such resources.
- **Nothing here is delivered.** Local file only (m1 scope). Email/Drive delivery stays on the
  milestone's carried-forward list.
- **t5 wires this as the fourth `run_command` step**:
  `python3 scripts/render_report.py output/report_data_{period}.json --output-dir output`,
  positional payload path, `--output-dir` cwd-relative like t1/t2. The sprint's report-file
  check should look for `output/cloudcost_report_{period}.html`. `--pdf` is not for the
  orchestrator: it adds a system-binary dependency to a step that must not have one.
- **t1/t2/t3's open items stand**, including the live account still carrying no genuine orphan
  (§Prerequisites 2) that t5's "≥1 real orphan" done-when needs planted.
