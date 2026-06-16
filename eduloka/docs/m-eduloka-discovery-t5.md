# t5 — Operational upsert + `gws_cse` enrichment migration

> Ticket extracted from `eduloka/milestone.md`. Canonical source is
> `milestone.md`; this file is a working reference for implementation.

**Depends on.** t3 merged (t4 recommended — gold is the preferred input, but
edux suffices).

**Scope.** After this ticket `upsert_institute.py` writes `to_gws_cse()` rows
into Postgres `gws_cse` (link-keyed upsert, legacy semantics), and one additive,
idempotent migration adds a nullable `enrichment jsonb` column. The live site is
unaffected.

**Contract refs.** `ct-edux` `lib/gws/cse.ex` (`upsert/1` semantics, columns);
`eduloka/scripts/edux_record.py` (`to_gws_cse()` output);
`aetheris-agents/CLAUDE.md` §"Python script conventions".

**Touches.** `eduloka/scripts/upsert_institute.py`;
`eduloka/data/migrations/0001_add_enrichment_jsonb.sql`;
`eduloka/tests/test_upsert.py` (`@pytest.mark.integration`, auto-skip if no DB);
`eduloka/runbook.md` (DB env + migration step).

**Do not generate.** No ORM — plain SQL/`psycopg`. Additive migration only; do
not alter existing columns/indexes. No full `text` in the operational row.

**Runbook update rule.** Introduces DB connection env (`EDUX_DATABASE_URL` or
equivalent) and a migration-apply step. Document both, including applying the
migration against the existing `ct-edux` DB and the zero-migration fallback
(fold enrichment into `metatags`) noted in `edux_record.py`.

**Done-check.**
```bash
python3 -m pytest eduloka/tests/test_upsert.py -q                    # integration skips cleanly without a DB
psql "$EDUX_DATABASE_URL" -f eduloka/data/migrations/0001_add_enrichment_jsonb.sql   # idempotent
```

**Claude-code prompt.**
> Build `upsert_institute.py`: read edux/gold JSONL, project via
> `EduxRecord.to_gws_cse()`, upsert into `gws_cse` keyed on `link` with the same
> insert-or-update semantics as `ct-edux` `lib/gws/cse.ex`. Write the additive
> `enrichment jsonb` migration (`IF NOT EXISTS`). Gate DB tests with
> `@pytest.mark.integration`. Document DB env + migration in `eduloka/runbook.md`
> per the Runbook update rule. Run the done-check; include output.

**Spike reference.** No spike for this ticket — build from `ct-edux`
`lib/gws/cse.ex` upsert semantics + `EduxRecord.to_gws_cse()` output.

**Implementation notes.** → `eduloka/docs/t5-implementation-notes.md` (write
after ticket closes).
