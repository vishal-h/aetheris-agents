# Aetheris Agent Patterns

Recurring implementation patterns across use cases. Check here before solving a
problem that likely has a known answer.

---

## Sub-agent data passing: UUID temp file

**Problem.** A sub-agent builds a large JSON payload in context (e.g. a batch of
classification results) and needs to pass it to a Python script. Two naive
approaches both fail:

- **stdin piping** — `bash` is not in the exec server's permitted commands, so
  `bash -c "echo '...' | python3 script.py"` is blocked.
- **Fixed temp path** (`/tmp/batch.json`) — parallel sub-agents clobber each
  other's files.

**Solution.** Write the payload to a UUID-named temp file in one `run_command`,
then pass `--input <path>` in the next:

```
# Step 1 — write payload to a unique temp path
run_command:
  command: "python3"
  args: ["-c", "import json,uuid; data=<your_json_array>; fname='/tmp/out_'+str(uuid.uuid4())+'.json'; open(fname,'w').write(json.dumps(data)); print(fname)"]

# Step 2 — read the file path printed to stdout, then call the script
run_command:
  command: "python3"
  args: ["scripts/your_script.py", "--db", "<db_path>", "--input", "<fname_from_step_1>"]
```

The `uuid.uuid4()` call is pure Python stdlib — no external dependency. Each
parallel sub-agent writes to a distinct path, so there is no race condition
regardless of how many agents run concurrently.

**Where this applies.** Any sub-agent that:
- Collects results across multiple tool calls into an in-context data structure, and
- Needs to persist that data to a script that reads from a file or stdin.

First seen in `provenance/agents/classify_batch.exs` (m2-002 / m2-003), where
each batch sub-agent writes classification results to a UUID temp file before
calling `classify_documents.py --input`.

---

## Taxonomy / context document: read once, hold in context

**Problem.** A sub-agent needs a reference document (taxonomy, ruleset, schema)
to process every item in its batch. Reading the document once per item wastes
tool calls and inflates context proportionally to batch size.

**Solution.** Instruct the agent explicitly in the task_prompt to read the
document in Step 1 — before the item loop — and hold it in context:

```
STEP 1 — Read agents/taxonomy.md using read_file ONCE.
Hold this content in context. Do not read it again per file.

STEP 2 — For each file below, classify using the taxonomy you just read...
```

The word "ONCE" and the explicit prohibition ("Do not read it again") are load-
bearing — without them, models tend to re-read per item.

**Where this applies.** Any agent with a per-item loop that depends on a shared
reference: taxonomy files, prompt templates, schema definitions, lookup tables.

First seen in `provenance/agents/classify_batch.exs` (m2-001 / m2-002).

---

## Orchestrator: DRY_RUN mode

**Problem.** Before committing to a large parallel run (potentially thousands of
sub-agents and millions of tokens), operators need a way to estimate cost and
validate configuration without triggering any LLM work.

**Solution.** Check `DRY_RUN=true` in the `.exs` file at eval time and inject a
mode-specific section into the system prompt:

```elixir
dry_run_section = if System.get_env("DRY_RUN") == "true" do
  """
  ## DRY RUN MODE
  Do NOT spawn any sub-agents.
  1. Run the query to count items.
  2. Calculate: batches = ceil(count / #{batch_size}).
  3. Report count and batch estimate, then stop.
  """
else
  ""
end
```

The DRY_RUN branch runs the count query (one `run_command`) and reports — no
`spawn_agent` or `wait_for_all` calls are made, so no sub-agent LLM calls occur.

**Where this applies.** Any orchestrator that spawns a variable number of
sub-agents based on a corpus query.

First seen in `provenance/agents/classification_orchestrator.exs` (m2-003).
