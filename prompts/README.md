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

---

## Schedule

| Prompt | When to run | Trigger |
|--------|-------------|---------|
| `bl-002-refresh-project-knowledge.md` | At every milestone end | Completing a Rig milestone (p-series) or agents milestone (m-series) |
| `bl-002-refresh-project-knowledge.md` | Before any handoff session | Starting a new Claude.ai conversation that will span multiple sessions |
| `bl-002-refresh-project-knowledge.md` | On staleness detection | Any session where `docs/project-knowledge-manifest.md` commit hashes differ from `git log -1 --format=%h -- <path>` |

### Staleness check (run at the start of a new session if uncertain)

```bash
BASE=~/sandbox/elixirws/aetheris-agents
HARNESS=~/sandbox/elixirws/aetheris

# Compare each manifest row against current HEAD
while IFS='|' read -r export_name repo_path repo commit rest; do
  repo_path=$(echo "$repo_path" | xargs)
  repo=$(echo "$repo" | xargs)
  commit=$(echo "$commit" | xargs | tr -d '`')
  [ "$repo" = "aetheris-agents" ] && dir="$BASE" || dir="$HARNESS"
  current=$(git -C "$dir" log -1 --format=%h -- "$repo_path" 2>/dev/null)
  [ "$current" != "$commit" ] && echo "STALE  $repo_path ($commit → $current)"
done < <(grep '^\| \`' "$BASE/docs/project-knowledge-manifest.md")
```

If the script prints any `STALE` lines, run `bl-002-refresh-project-knowledge.md`.

---

## Adding a new prompt

1. Write the prompt as a self-contained `.md` file in this directory.
2. Add a row to the Files table and (if recurring) the Schedule table above.
3. If the prompt is tied to a backlog issue, note the issue number in the Files table.
4. Commit with message `prompts: add <filename>`.
