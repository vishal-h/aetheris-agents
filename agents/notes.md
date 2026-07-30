Two halves, clean separation:

**`capability_matrix_{uc}.exs`** — one solo agent per use case, each reads that use case's
`agents/` and `scripts/` directories (≤10 files) and writes `docs/.sections/{uc}.md`. Max 15
steps each, well within context limits. Eight are wired into sprint.sh's `capability_matrix`
case; `capability_matrix_eduloka.exs` exists but is not wired (BL-068).

**`scripts/assemble_matrix.py`** — deterministic assembler, runs after the section agents.
Concatenates the sections verbatim in `SECTIONS` order and computes the derived block (Summary
counts, unique-tools line, Overlap Report) by counting the sections' own table rows, then writes
`docs/capability-matrix.md`. This step used to be an LLM agent
(`capability_matrix_assemble.exs`); its arithmetic was wrong on every regen, so BL-067 replaced
it with the script. Do not put an LLM back in the assemble step.

**To run:**

```bash
# Both halves
cd ~/sandbox/elixirws/aetheris
./scripts/sprint.sh capability_matrix

# Or one section, then re-assemble (the usual case — see the runbook)
mix aetheris run ../aetheris-agents/agents/capability_matrix_{uc}.exs
python3 ../aetheris-agents/scripts/assemble_matrix.py
```

`docs/.sections/` is gitignored and holds a `.gitkeep`; the section agents' `write_file` calls
`create_dir_all` for parents, so it also survives a missing directory.
