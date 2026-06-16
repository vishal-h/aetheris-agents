# m-eduloka-discovery — kickoff note (claude-ui → claude-code)

> Handoff artifact, not a contract. Orients the milestone; points at canonical
> sources rather than restating them (methodology §1.2). Committed at
> `docs/milestones/` per §3; the milestone doc itself lives at
> `eduloka/milestone.md` (use-case convention).

## Canonical doc

`eduloka/milestone.md` is the source of truth. Generate the GitHub milestone +
issues from it (one issue per ticket, body verbatim + doc path & commit SHA
backlink, §8) before starting t1. Tickets run t1→t8 in order; t1–t5 are
pure-Python and independently testable.

## Standing decisions (from the human/arbiter)

1. **Spike as reference, not adopt-as-is.** A design spike exists (see map
   below). Reimplement each ticket against the contract — `edux_record.py` and
   `eduloka/scripts/README.md` define the intended shape; the spike shows one
   correct realization and the offline-test approach. Do not copy files
   verbatim; rebuild, and improve freely where the contract is silent. If you
   diverge from the spike, that's fine — note it (and why) in the
   implementation notes.
2. **Fetch ticket is split** (t1 core+cse+exa, t2 serp) under the §6 sizing
   rule. Human may collapse back to one ticket; until then, treat as two.

## Spike → ticket map (reference material)

| Ticket | Spike files (reference) |
|---|---|
| t1 | `fetch_base.py`, `fetch_cse.py`, `fetch_exa.py`, `fetch.py`, `test_fetch.py` (cse/exa cases), `conftest.py` |
| t2 | `fetch_serper.py`, `fetch_dataforseo.py`, `test_fetch.py` (serp cases) |
| t3 | `edux_record.py`, `mappers.py`, `map.py`, `test_map.py` |
| t4 | `enrichers.py`, `enrich.py`, `test_enrich.py` |
| t5 | — (no spike; build from `ct-edux` `lib/gws/cse.ex` + `edux_record.to_gws_cse()`) |
| t6 | `list_terms.py`, `data/terms.txt`, `test_list_terms.py` (orchestrator `.exs` is greenfield) |
| t7 | `fetch.py` (partition mode is new) |
| t8 | — (docs/manifest/drift only) |

The `sample.*.jsonl` files from the spike are demonstrations, not fixtures.
Real fixtures get committed under `tests/fixtures/` in t3/t4 per those tickets.

## Spike gotchas worth knowing up front (detail in README §"Caveats")

- CSE is a **GET** (others POST) — hence the `http_get_json` helper in
  `fetch_base`. It is also the only provider returning real
  `pagemap.cse_image`/`metatags`, so its mapper populates `image`/`metatags`
  for real; the other three are best-effort.
- DataForSEO and Exa have no result offset → over-fetch and slice; CSE and
  Serper paginate natively. Exa ignores `country`.
- `data/terms.txt` is **committed config** — keep it out of the `.gitignore`
  layer-dir excludes (`data/raw|edux|gold`, `output/`).
- The spike was written to current provider API shapes but **not live-tested**
  (build sandbox reaches only package registries). Verify endpoints/field names
  against each provider's docs as part of t1/t2; the raw→edux mapping is
  isolated per provider in `mappers.py` to make corrections a one-spot edit.

## Mechanics (methodology — referenced, not restated)

Per §5: at each session start read the `aetheris-agents/CLAUDE.md` learning
sections + the ticket's contract refs; implement; **run the done-check and put
its actual output in the review packet** (a packet without check output is
returned unreviewed, §5). Write implementation notes to
`eduloka/docs/tN-implementation-notes.md`. Review files arrive at
`docs/reviews/m-eduloka-discovery-tN-review.md`; respond with the per-finding
disposition table (§5).

## First action

Confirm the milestone doc is committed, generate the issues, then start t1.
