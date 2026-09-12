# m14 T7 — the Rig candidate view

Ticket: harness `docs/aetheris/milestones/m14-skills-auto-extraction.md` §4 T7,
read at harness `3de3908`. Agents-only; the harness commit of this round is
`ecdef3b` (T4 housekeeping, item 3a) and carries none of this.

These notes live in the agents repo rather than beside their m14 siblings in the
harness because the round's harness commit was scoped to 3(a) alone. Nothing in
the harness points here; that is a gap a later m14 round may want to close.

## Decisions

**`disposition` is derived in Rust, not stored and not re-derived in the view.**
The predicate is the curator's own `active/1` — `superseded_by IS NULL AND
status != 'retired'` (harness `lib/aetheris/skill/curator.ex`). Deriving it once,
in `skills_catalog_load`, is what makes "a superseded row cannot render as
current" checkable in one place rather than asserted across a component tree.
Supersession is checked before retirement. A row that is both cannot arise from
today's curator — only active rows are evictable, and similarity runs against
active rows only — so the ordering is defensive, and it prefers the answer an
operator can act on. `status` travels beside `disposition`, so the combination is
still legible.

**The default filter is Active, not All.** An undifferentiated list is the one
outcome the ticket forbids. Three counted tabs plus a per-card reason line was
chosen over a single list with a status column: the counts make the other two
visible without showing them, and the reason line ("Superseded by … — read the
successor, not this row") means a non-active card is unmistakable even in the All
view, which is where a status column would be easiest to miss.

**A malformed JSON column is reported, not defaulted.** `parse_errors` names the
columns that failed to decode. An empty `tool_sequence` and an unparseable one
render identically otherwise — the Silent-wrong-answer class, in the one field an
operator would use to judge whether a candidate describes a real pattern.

**Rows are collected as a `Result`, not `filter_map(|r| r.ok())`.** A row that
fails to decode is a fact about the table; dropping it silently shows a short
catalogue that looks complete. `usage.rs` has the older shape at two sites — see
Owed below.

**`SkillRow` is described in §4 prose, not a second ```rust fence.** A fence would
put its 18 fields under `command_fields` and raise the documented-struct count by
two rather than one. The count is not the reason: 44 of the 56 structs in
`commands/*.rs` are undocumented today, every nested row struct among them
(`MatrixUseCase`, `ModelUsageRow`, `UseCaseUsageRow`, …), so fence-documenting
this one would make it the single exception. The gap is real and is filed as a
class — see Owed.

## Deviations

None from the ticket text. Two additions to it, both named in the round's prompt
as the view's job rather than as contract: the disposition derivation above, and
the full-height `prompt_template` render.

## Done-check

`python3 scripts/drift_check.py --strict` exits 0 at the commit these notes land
in (held and unpushed as they are written; the round's packet names the hash):
`tauri_commands` 50 → 51, `routes` 11 → 12, `command_fields` 11 → 12 structs
(56 → 60 fields), `db_schema` INFO 6 → 0. Four `project_knowledge` staleness
WARNs, strict-exempt, predicted as a set before the run and observed unchanged.

The view renders seeded rows: a four-row fixture (2 active, 1 superseded, 1
retired) in a copy of the real `aetheris.db`, read through the real binary under
Xvfb. Screenshots are in the round's packet; they are not committed.

## Owed

Two backlog rows, not yet filed because R38 holds a row until the commit it
cites is pushed, and this one is held:

1. `command_fields` checks only each command's outermost struct. 44 of 56
   structs in `rig/src-tauri/src/commands/*.rs` are absent from specs.md §4's
   ```rust fences and therefore drift-unchecked, `SkillRow` (18 fields) among
   them.
2. `usage.rs:102` and `:128` drop undecodable DB rows with
   `.filter_map(|r| r.ok())`, so a decode failure shortens an aggregate silently.
   The census is those two sites: the three `.ok()` sites in `tools.rs` are
   `read_dir` entries, one of them in a test helper, which is a weaker case.
