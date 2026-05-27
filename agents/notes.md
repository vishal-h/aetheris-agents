Two files, clean separation:

**`capability_matrix.exs`** — 5-agent orb, all parallel, each reads one use case directory (≤10 files) and writes `docs/.sections/{use_case}.md`. Max 15 steps each, well within context limits.

**`capability_matrix_assemble.exs`** — solo run after the orb completes. Reads 5 small section files, detects overlaps, writes `docs/capability-matrix.md`. Reads only markdown files so context stays tiny.

**To run:**

```bash
# Step 1 — parallel section generation
mix aetheris run ../aetheris-agents/agents/capability_matrix.exs

# Wait for orb to complete, then:
mix aetheris list --limit 1   # confirm orb status: done

# Step 2 — assemble
mix aetheris run ../aetheris-agents/agents/capability_matrix_assemble.exs

# Check output
cat ../aetheris-agents/docs/capability-matrix.md
```

One thing to confirm before running: `docs/.sections/` directory needs to exist in the repo. Either create it with a `.gitkeep` or let the first `write_file` create the parent directory — `write_file` in Aetheris calls `create_dir_all` for parent directories so it should work without pre-creating the folder.
