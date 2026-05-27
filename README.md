# aetheris-agents

Use-case agent implementations built on the [Aetheris](../aetheris) harness.
Each use case is a self-contained directory with Python scripts, Elixir agent
files, tests, and docs.

No Elixir source lives here — only `.exs` agent scripts that the harness
evaluates. All sprint and agent commands run from `../aetheris/`.

---

## Use cases

| Directory | What it does | Status |
|-----------|-------------|--------|
| [`payslip/`](payslip/) | Generate monthly payslips from payroll CSV; parallel sub-agents per employee | ✅ |
| [`drive/`](drive/) | Download payroll CSV from Google Drive; upload generated PDFs back | ✅ |
| [`email/`](email/) | Email each employee their payslip PDF | ✅ |
| [`api/`](api/) | TAP protocol — agent-to-agent enrollment via ct.stu API | ✅ T1–T4 |

### Payslip pipeline

```
drive (download)  →  payslip (generate)  →  drive (upload)  →  email (deliver)
```

### TAP protocol track

```
TAP v0 design  →  uc-api-agent T1-T4  →  T5 durable state (planned)
```

---

## Getting started

```bash
# Install Python deps (mise-managed Python 3.12)
python3 -m pip install pytest boto3 pika

# Run tests for a use case
python3 -m pytest api/tenant/tests/ api/gateway/tests/ -v

# Run an agent (from the aetheris sibling repo)
cd ../aetheris
mix aetheris run ../aetheris-agents/api/tenant/agents/at1cmd.exs
```

---

## Repository conventions

See [`CLAUDE.md`](CLAUDE.md) for the full reference. Key points:

**Scripts do; agents decide.** Python handles computation, file I/O, and API
calls. Elixir agent files contain only the `RunConfig` or `OrbConfig` struct.

**`__ENV__.file` for sandbox_path.** Always resolve paths relative to the
agent file, not `File.cwd!()`.

**`context_strategy: :full` for short-lived agents.** `:rolling` truncates old
messages and can leave orphaned `tool_use_id` references, causing HTTP 400.
Use `:full` for any agent that runs fewer than ~20 steps.

**Two repos, two commits.** Sprint cases in `../aetheris/scripts/sprint.sh` are
a separate commit from the agent files here. Do not merge without review.

---

## Docs

| Document | Contents |
|----------|---------|
| [`CLAUDE.md`](CLAUDE.md) | Conventions, commands, critical patterns |
| [`docs/agent-creation-guide.md`](docs/agent-creation-guide.md) | How to build a new use case |
| [`docs/uc-api-agent-design.md`](docs/uc-api-agent-design.md) | TAP protocol architecture |
| [`protocol/TAP-v0-design.md`](protocol/TAP-v0-design.md) | TAP v0 spec |
| [`ROADMAP.md`](ROADMAP.md) | What's next |
