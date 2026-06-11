# Prompts

Reusable Claude Code prompts for recurring maintenance tasks in this repo.
Each file is a self-contained prompt — paste it directly into a Claude Code
session (or a Claude.ai project conversation) to execute the task.

Prompts are written to be idempotent: running one twice produces the same
result as running it once. They do not assume any prior conversation context.

---

## Files

| File | Task | Issue |
|------|------|-------|
| `bl-002-refresh-project-knowledge.md` | Assemble the Claude.ai project-knowledge bundle and update the manifest | [#43](https://github.com/vishal-h/aetheris-agents/issues/43) |
| `reality-check.md` | Ground-truth snapshot of Rig current state from source code | — |

---

## Schedule

| Prompt | When to run | Trigger |
|--------|-------------|---------|
| `reality-check.md` | At every milestone boundary | Completing or starting a Rig milestone (p-series) |
| `reality-check.md` | After an extended gap | Returning to the project after ~2 weeks away |
| `bl-002-refresh-project-knowledge.md` | At every milestone end | After `reality-check.md` produces a new current-state doc |
| `bl-002-refresh-project-knowledge.md` | Before any handoff session | Starting a new Claude.ai conversation spanning multiple sessions |
| `bl-002-refresh-project-knowledge.md` | On staleness detection | When the `project_knowledge` drift check emits WARN findings |

---

## Staleness check

Project-knowledge staleness is now covered by the `project_knowledge` check
in `scripts/drift_check.py` (check 8). Run it to detect stale manifest entries:

```bash
# From aetheris-agents/ root
AETHERIS_DB_PATH=~/sandbox/elixirws/aetheris/priv/aetheris.db \
  python3 scripts/drift_check.py

# Or via sprint.sh (from aetheris/)
./scripts/sprint.sh drift_check
```

Any `[WARN] project_knowledge:` line means one or more manifest entries are
stale — run `bl-002-refresh-project-knowledge.md` to refresh.

---

## Adding a new prompt

1. Write the prompt as a self-contained `.md` file in this directory.
2. Add a row to the Files table and (if recurring) the Schedule table above.
3. If the prompt is tied to a backlog issue, note the issue number in the Files table.
4. Commit with message `prompts: add <filename>`.
