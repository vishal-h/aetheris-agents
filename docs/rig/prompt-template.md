# Claude Code Prompt Template — Rig

Prompts that work consistently follow this structure.
Use this when generating implementation prompts in claude.ai
before pasting into a Claude Code session.

---

## Template

```
Read {spec_file} and implement.

Files to create:
- {path} — {one-line description}

Files to modify:
- {path} — {what changes and why}

Constraints:
- {critical invariant 1}
- {critical invariant 2}
- {the thing most likely to go wrong}

When done: {build verification}. Paste the diff.
```

---

## Build verification strings

**Frontend only:**
```
bun run build exits 0, zero TypeScript errors. Paste the diff.
```

**Rust + frontend:**
```
cargo build exits 0 zero warnings, bun run build exits 0 zero
TypeScript errors. Paste the diff.
```

**Python only:**
```
python3 -m pytest {test_path} -v exits 0. Paste the diff.
```

**Elixir only:**
```
mix test exits 0. Paste the diff.
```

---

## What goes in Constraints

The constraints section is the most important part. It captures
the hard-won knowledge that prevents the most common mistakes.
Use it for:

**Tauri / Rust:**
- Invoke key casing: all invoke() arg keys must be camelCase
  (runId not run_id). Error form: "missing required key runId"
- Plugin permissions: new plugins need entries in
  src-tauri/capabilities/default.json or calls silently do nothing
- State parameters: adding State<'_, T> to a command is safe —
  Tauri resolves by type, frontend call unchanged

**React / Frontend:**
- No form tags — onClick/onChange only
- No TypeScript any
- Filter before group — apply filters to flat list before groupRuns()
- sessionStorage collapse state — useSessionRecord(key, defaultValue)
- localStorage MRU — lazy-init in useState initialiser, not useEffect
- Polling self-terminates — phase must be in useEffect deps array

**Elixir:**
- ORCHESTRATOR_REQUEST via env var, not CLI args
- RunHelpers.ensure_started() before any start_run call
- System.put_env/restore for context injection — snapshot, inject,
  run, restore. Safe because steps are sequential.

**Python / Drive:**
- Shared Drive API calls need supportsAllDrives=True,
  includeItemsFromAllDrives=True, corpora="allDrives"
- Upload scope must be drive not drive.file for server-side automation
- Always call sys.exit() explicitly to close HTTP connections

---

## Prompt length guide

| Task size | Prompt length | Notes |
|-----------|--------------|-------|
| 1-file fix | 5-8 lines | Just constraints + build check |
| New feature | 15-25 lines | Full template |
| Multi-file feature | 25-40 lines | Split into Run 1 / Run 2 if touching different repos |
| New milestone | Two prompts | One per repo (aetheris-agents/, rig/) |

---

## Examples of good constraints

**Too vague:**
> Make sure it works correctly

**Good:**
> orchestrate_start takes config_state: State<'_, AgentConfigState>
> as second parameter — Tauri resolves state by type, frontend
> invoke call unchanged

**Too vague:**
> Handle errors properly

**Good:**
> resolve_period_folder fails with sys.exit(1) and a clear message
> if the period folder does not exist — never creates on the
> download path

---

## Reviewing diffs

After Claude Code pastes a diff, check:
1. All acceptance criteria from the spec are met
2. No unexpected files modified
3. Build verification ran and passed
4. Constraints were followed (scan diff for known anti-patterns)
5. Confirm wiring files (mod.rs, lib.rs, index.ts, registry.ts)
   even if not shown in the diff — ask explicitly if unsure

Paste the diff here for review before pushing.
