# m2-cloudcost t4 — optimization-signals spike (implementation notes)

Exploratory, non-gating. Built, offline-proven and live-read in one session; **not pushed**.
These notes carry what does not survive in the code: decisions taken, divergences adjudicated,
and what the next ticket needs to know.

---

## What the isolation invariant actually cost

§t4 has exactly one hard gate — absent the optimization file, the report is byte-identical to
the core report — and the cheapest way to satisfy it turned out to be structural rather than
careful. Three separate places:

1. **Not a `SECTIONS` member, and not an `OPTIONAL_FIELDS` one either.** A4's lesson gave the
   first half (a `SECTIONS` member absent costs a rendering note and exit 1, so every DO run
   would fail forever). The second half is new: `OPTIONAL_FIELDS` reads the *report payload*,
   and this input is a different file. It is a separate context key set from a separate
   argument.
2. **The template guard is on the outside.** One `{%- if optimization %}` around the whole
   block, with A4's whitespace-control idiom, so the absent case emits zero bytes rather than a
   stripped-but-present blank line.
3. **The orchestrator step is numbered 2b, not 3.** Renumbering would have rewritten the text
   of every later step, and the unset prompt could then no longer be compared to t3's
   byte-for-byte. The number is ugly; the comparison is the point.

**Mutation-proven, not asserted.** Removing the template's outer guard turns **six** tests red
— both new isolation tests and all three *pre-existing* byte-identity tests. Run once against
the broken state, watched fail, restored.

**The trap t3 recorded, avoided here:** `source_file` is in the render context, so every
byte-identity measurement holds the input path constant. t3's first attempt at this same
measurement compared renders from two different filenames and reported a spurious mismatch.

**Measured, both halves.** The equality is asserted three ways (flag absent / `None` / `{}`)
*and* the failable half — the same payload with the file renders a different page — so the
equality cannot be satisfied by a section that never renders at all.

---

## Divergences adjudicated (and the doc changed to match)

Per the m3-docbuilder rule: a divergence is closed by changing code *or* the doc, never left as
a silent mismatch. All three landed in `m2-milestone.md` §t4 in a doc-first commit, before any
code.

**1. The file is an envelope, not a bare list.** §t4 said "a loose list of `{service, …}`".
Taken literally the file's root would be a JSON array — and `denied[]`/`warnings[]` would then
have nowhere to live, so a refused API would be indistinguishable from an empty result by
reading the artifact. `signals[]` keeps the §t4 element shape unchanged; the envelope around it
is the one every other cloudcost artifact already uses.

**2. `monthly_cost_estimate` needed a stated rule, not a judgement call.** §t4 said "only where
honestly available … never invented", which does not by itself say whether a hardcoded rate
counts as invented. Ratified: a static list-price table **with a mandatory per-figure
`rate_basis{rate,unit,source,as_of}`** — a figure without its basis IS the fabricated case —
plus omit-and-warn on every dimension lacking a constant.

**3. §t4's Touches under-named the test surface.** It listed the two test modules and the
fixtures but not `conftest.py`/`aws_wire.py`, which is where the offline seam lives. §t4's own
Done-check demands an end-to-end offline CLI proof, and that proof is unreachable without them.
Same shape as t3's F3 (the doc named a `capability_matrix.exs` that does not exist): the
done-check governs over the Touches sketch. Recorded in the doc rather than left for the
reviewer to re-adjudicate.

---

## `aws_wire` read the wrong protocol, and only one service noticed

`aws_wire.encode` dispatched on `ServiceModel.protocol` — the protocol a service *advertises*.
The protocol botocore actually **serializes and parses with** is `resolved_protocol`, the first
entry of `metadata["protocols"]` this botocore supports.

For nine of the ten services they agree. CloudWatch advertises `smithy-rpc-v2-cbor` and
resolves to `json`. Encoding to the advertised protocol produces a body the real parser never
asked for: driving the cbor parser over the json body raises `MemoryError`. So the new
CloudWatch round-trip is red without the fix — the switch is load-bearing, not tidying.

**How it was gated.** This is the one behavioural change to shared scaffolding, so it landed
**alone**, first: the full 244-test suite was captured per-test node-id before and after the
one-word switch and the two lists are byte-identical. Everything after it is additive. Worth
knowing because the same hazard is latent for any future service — read what botocore resolved,
never a table typed out by hand.

---

## Three places an absent fact could have been read as a zero

The recurring shape, and the one this ticket spent the most care on:

| Absent thing | Read as | Control that would have caught the alternative |
|---|---|---|
| CloudWatch datapoint | **unknown**, never "empty bucket" | `aws_cloudwatch_metrics_cc_unknown` — no datapoints at all, which is also what a brand-new bucket looks like |
| `imagePushedAt` that will not parse | **undated**, never "recent" | a unit test with a broken timestamp, plus its dated twin |
| A refused API | **unknown**, never "nothing found" | `denied[]` is separate from `warnings[]` and from `signals[]`, and renders as "Not checked" |

`GetMetricData` returns a result object for **every** query id whether or not the metric has
data, so "no datapoints" and "zero" arrive in the same shape. That is why emptiness is asserted
only from an observed `0` and never from an absent value.

---

## Things the next ticket should know

**The spike is AWS-only and says so out loud.** `CLOUDCOST_OPTIMIZATION=1` with any other
provider **raises**. Quietly ignoring the flag would return a report with no optimization
section and no reason given — indistinguishable from a spike that ran and found nothing.

**`detect_optimization_signals.py` exits 0 where `fetch_aws.py` would exit 1.** Deliberate, and
the one place the two lanes' error taxonomies differ: in the gating adapter an `AccessDenied` is
a real gap; in a non-gating spike whose IAM actions are explicitly optional it is an expected
environmental state. It is also the repo rule for analysis/reporting scripts. Only a rejected
credential exits 1 — misconfiguration is not a thin result.

**Ages run against `--reference-date`, defaulting to now.** Every test passes it explicitly. A
suite that let these run off the wall clock would begin failing on a date nobody chose.

**Cost figures are confined to the two sanctioned cases.** ECR storage has a published rate
too, and it is deliberately **not** used: rating it would extend the sanctioned set on this
script's own authority. Its byte counts are in the evidence and its dollars stay out.

**The rate table is deliberately partial**, and the live read proved the omit path is not
decorative — see BL-079.

**`poisoned_default_chain` moved to `conftest.py`.** The spike builds its own clients and owes
the same D2 proof, and two copies of that guard are two things to keep true.

---

## Outside the §t4 Touches list

Declared rather than left for the reviewer to find. Two items, both in tests.

**1. `cloudcost/tests/test_fetch_aws.py` — edited, not listed.** Three changes, all forced by
where the existing guards live:

- `test_every_fixture_round_trips_through_botocore` holds the encoder pin **and** the
  completeness guard `on_disk == set(operations)` — every `aws_*.json` fixture must be
  registered or the test goes red. t4 adds thirteen fixtures, so registering them there is not
  optional, and it is what carries the round-trip property onto all four new services.
- The same test built its parser from `model.protocol`; it now uses `aws_wire._protocol`, or
  CloudWatch would be pinned against a parser botocore never runs.
- `test_get_bucket_location_round_trips_through_botocores_own_handler` added beside it, and
  `poisoned_default_chain` moved out to `conftest.py`.

The alternative was a second round-trip test in `test_optimization_signals.py`, which would
have left the completeness guard blind to exactly the fixtures it exists to catch. Zero
pre-existing tests moved, verified per node-id.

**2. Fixtures are named `aws_{service}_{op}.json`, not `optimization_*.json`.** §t4 Touches
says the latter. They are AWS wire recordings consumed by `AWSStub`, and every wire fixture in
this suite is `aws_*` — which is also the prefix the completeness guard globs, so an
`optimization_*` wire fixture would be silently exempt from the round-trip pin. The
`optimization_*` naming would fit a *signals-file* fixture; the render tests build that payload
inline instead (`optimization_payload()`), because `test_render_report.py`'s standing rule is
that payloads come from the real upstream stage or from an explicit in-test constructor, never
from a hand-written file masquerading as a recording.

---

## Live read (best-effort, non-gating) — the BL-072 seed

Ran under the D2 hermetic prefix. The t4 spike policy **is** attached and sufficient: **18
signals across 17 regions, `denied[]` empty** — every granted call went through.

| Signal | Count | Figure |
|---|---|---|
| `secret_unused` | 9 | $3.60/month total |
| `ecr_no_lifecycle_policy` | 3 | — (not a sanctioned case) |
| `ecr_untagged_image_accumulation` | 3 | — |
| `s3_no_lifecycle_policy` | 3 | — (no `ap-south-1` rate; omitted + warned) |
| `s3_incomplete_multipart` | 0 | |
| `s3_empty_bucket` | 0 | |

**What this seeds for BL-072.** The account's bill is Secrets Manager-dominated — t1 measured
Secrets Manager at $4.14 of a $4.99 total — and **nine secrets have not been read in 90+ days**,
one never at all. At the flat published charge that is $3.60/month, i.e. most of the largest
line on the bill, and it is the single highest-value finding the spike produced. The ECR
repositories carry images pushed **up to 1626 days ago** (~4.5 years) with no lifecycle policy
anywhere. Neither family is orphan-shaped, so neither was ever visible to `detect_orphans` —
which is precisely the gap decision G predicted and t4 exists to measure.

**The one thing the live read could not price:** every bucket is in `ap-south-1`, absent from
the rate table, so all three S3 figures were omitted and warned by name rather than estimated
from another region. The designed behaviour, firing in production. → **BL-079**.

Credentials appeared in neither stream and in no emitted file (checked against the live values,
plus an `AKIA|ASIA`-shaped scan).

---

## Gate results

| Gate | Result |
|---|---|
| `pytest cloudcost/tests/` | **287 passed** (244 baseline + 43 new); zero pre-existing tests moved, diffed per node-id |
| §t4 done-check CLI (`--output-dir /tmp/cc`) | exit 0, schema-shaped file, all six signal types present |
| Isolation invariant | byte-identical absent / `None` / `{}` / unreadable-file; differs with the file; **mutation → 6 red** |
| Orchestrator gate | unset ⇒ prompt byte-identical to t3's for **both** providers (same md5, recovered from `255d04b`); set ⇒ exactly one extra step |
| `drift_check.py --strict` | exit 0 — 8 PASS / 0 FAIL / 4 WARN, all four the exempt `project_knowledge` manifest-staleness class |
| `mix test` (off-territory) | 969 tests, 0 failures |
| `mix format --check-formatted` / `credo --strict` / `dialyzer` / `hex.audit` | clean / no issues / 0 errors / no advisories |
| Live read | 18 signals, 0 denied, exit 0 — **PASS (exploratory)** |

**Known-red carried, named, not re-triaged:** BL-069 (live accounts yield 0 orphans, so
`sprint.sh cloudcost`'s ≥1-orphan assertion fails by design until the planted resource returns)
and BL-077 (`sprint.sh`'s `fail()` sets no exit status, so a green `$?` from the sprint proves
nothing — read the `[OK]`/`[FAIL]` lines). t4 changes neither, and the default-off gate leaves
the existing sprint cases untouched.

**Not done, and why:** no sprint case exercises `CLOUDCOST_OPTIMIZATION=1`. §t4 does not ask for
one, the gate defaults off so the existing cases are unaffected, and a hermetic case would need
live credentials. *Filed as BL-082 at review — the r0 reviewer's N3 correctly observed that
"flagged here, no trigger yet" is exactly what a backlog row is for, and prose in a notes file
executes nothing.*

---

## Review outcome (r0, `docs/reviews/m2-cloudcost-t4-review.md`)

**APPROVE — merge-clean, no code changes requested.** Three non-blocking notes, all deferred with
rows filed in the same round:

| # | Note | Disposition |
|---|---|---|
| N1 | `status: "partial"` fires on intentional figure-omission, not only on a read gap — so on this account every run reads `partial` | deferred → **BL-080** |
| N2 | `s3_no_lifecycle_policy` fires on an empty bucket, which has nothing to expire | deferred → **BL-081** |
| N3 | The gated orchestrator path is proven link-by-link, never as one end-to-end run | deferred → **BL-082** |

No code changed after the approval. Editing emitted behaviour post-APPROVE would mean the merged
artifact is not the one that was reviewed, and all three are tidy-ups or watch-items rather than
defects.

**One place the row does not simply implement the note.** N1 suggests reserving `partial` for
`denied[]` and letting figure-omission ride under `ok`. That is right about the symptom and
under-specified about the fix: `warnings[]` today holds *both* intentional omissions ("no
published Standard rate is held for ap-south-1") and genuinely unknown facts ("no
NumberOfObjects datapoint published, so whether it is empty is unknown"). A two-way collapse
would file the second kind under `ok` — the same absent-read-as-fine failure the
`denied[]`/`warnings[]` split exists to prevent. BL-080 therefore specifies a three-way split
with `status` keying on refused-and-unknown only. Recorded here because the row's shape diverges
from the note's sketch, and the next reader should not have to re-derive why.
