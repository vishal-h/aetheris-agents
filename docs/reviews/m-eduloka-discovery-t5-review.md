# m-eduloka-discovery — t5 review

> Reviewer: claude-ui. Against `milestone.md §t5` (direct DB sink).

## Round 1 — Verdict: changes requested

**Done-check:** 55/55 with 2 integration tests **skipped** (no DB). The DB upsert and migration apply did not run; packet punted DB verification to reviewer.

| ID | Severity | Finding |
|----|----------|---------|
| B1 | blocking | `metatags` serialized as `::jsonb` scalar; Ecto `{:array, :map}` backs a `jsonb[]` column — type mismatch, every insert fails |
| B2 | blocking | `INSERT` omitted `inserted_at`/`updated_at`; Ecto `timestamps()` → NOT NULL, no DB default → insert fails; `updated_at` not bumped on conflict |
| B3 | blocking | `ON CONFLICT DO UPDATE SET status = EXCLUDED.status` reactivates `status=0` soft-deletes on re-discovery — diverges from legacy which preserved status |

**Root cause:** All three from the same root — upsert written against an assumed schema without verifying `\d gws_cse` or the legacy update semantics. The live-doc carry-forward (verify provider/legacy field shapes) was deferred to here; it was load-bearing.

**B1 fix:** `metatags` sent as `list[Jsonb]`; `_row()` (pure) split from `_adapt()` (psycopg wrapping). SQL receives `list[Jsonb]` → `jsonb[]`; `::jsonb` cast dropped.

**B2 fix:** `inserted_at = now(), updated_at = now()` on INSERT; `updated_at = now()` in `DO UPDATE SET`.

**B3 fix:** `status` removed from `DO UPDATE SET`; `test_status_not_clobbered_on_conflict` proves `status=0` survives re-discovery.

**Schema clone:** `0000_create_gws_cse_clone.sql` created mirroring the Ecto DDL. `\d gws_cse` confirms: `metatags jsonb[]`, `inserted_at`/`updated_at` NOT NULL no default, `enrichment jsonb`.

## Round 2 — Verdict: direct sink cleared to merge

Integration 9/9, **0 skipped** — DB path executed. Carry-forward closed.

**`\d gws_cse` (eduloka_test clone):**
```
metatags    | jsonb[]                        | not null: no
inserted_at | timestamp(0) without time zone | not null: yes (no default)
updated_at  | timestamp(0) without time zone | not null: yes (no default)
enrichment  | jsonb                          | (from 0001 migration)
```

**Scope change:** r3 — t5 renamed "direct sink (A)"; t5b export sink added; companion ct-edux workstream documented. `0001_add_enrichment_jsonb.sql` ownership moves to ct-edux Ecto migrations; eduloka's copy is emergency-only fallback.

**Promotable-learning:** "when a script writes to a table owned by another system, verify the live DDL and that system's write semantics before trusting an inferred schema — raw SQL against an ORM-managed table breaks on array types, NOT NULL timestamps, and update-field semantics."
