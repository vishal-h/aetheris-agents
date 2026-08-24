# uc-inbox — Inbound Messaging as Agent Trigger (design brief)

**Status:** parked — design decided, not scheduled. Pick up after current milestones.
**Type:** design brief. Not a milestone doc; see §9 for what must be answered before one is drafted.
**Date:** 2026-08-05 (rev 2 — generalised from email-only to channel adapters)

---

## 1. Framing

Every existing agent is triggered by cron, a Drive poll, or a human at Rig. There is
no way for anyone who is not sitting at Rig to start a run.

An inbound message is the cheapest intake channel that exists: no UI to build, no
account provisioning for the sender, attachments included, works from a phone.
**The deliverable is a trigger surface, not an archive.**

The failure mode to avoid: building "messages land in a folder plus a table in Rig."
That is a worse Gmail. Value appears only when an inbound message starts a pipeline.

**First milestone framing (one-person allowlist):** this is a remote control for your
own harness — kick off any Aetheris pipeline from your phone, with attachments, no VPN,
no Rig. Not a client intake channel. That comes later, on a different adapter, and
changes the threat model (§8).

---

## 2. Architecture — one use case, pluggable channels

Telegram and email are **not** separate use cases. The spine is channel-agnostic:

```
  [channel adapter]  →  snapshot  →  route  →  authorise  →  parse params
                                                                   ↓
                          reply  ←  dispatch to pipeline  ←  validate
                            ↑
                    [channel adapter]
```

Only two boxes are channel-specific: **fetch** and **reply**. Everything between them
operates on the normalised snapshot and knows nothing about the transport.

Building `uc-telegram` beside `uc-inbox` would duplicate six decisions and drift within
a milestone. The `provider` column in the original schema sketch was the right instinct
— it generalises to `channel`.

### Adapter contract

A channel adapter is two scripts:

| Script | Responsibility |
|---|---|
| `fetch_<channel>.py` | Poll or receive; write raw payload + normalised `messages` / `attachments` rows to the snapshot; **never** interpret content. |
| `reply_<channel>.py` | Given `(message_id, text \| status)`, deliver the echo on the originating channel. |

Precedent for the shape: `cloudcost/scripts/fetch_do.py` and `fetch_aws.py` — read-only
adapters emitting normalised JSON artifacts, with all downstream stages pure.

### Channel comparison

| | Telegram | Email |
|---|---|---|
| Identity | `from.id` — integer issued by Telegram, unforgeable | `From:` header — forgeable; needs DMARC to mean anything |
| Auth setup | Bot token in env | OAuth refresh token or domain-wide delegation (admin decision) |
| Transport | Long-poll `getUpdates`, no public endpoint | Gmail API poll on `historyId` |
| Intent selector | `/command` (BotFather registry → client autocomplete) | Plus-address tag `ai+invoice@` |
| Confirm affordance | Inline keyboard button — one tap | Reply `yes` — thread round-trip |
| Progress | Edit message in place → live event log on phone | One reply at the end; structurally cannot stream |
| Attachment ceiling | **20 MB** (bot API `getFile`) | ~25 MB, and Drive links beyond |
| Audit / business record | None | Yes — a record clients accept |
| Data residency | Transits Telegram's servers | Own Workspace tenancy |

**Telegram is the operator channel. Email is the client channel.** Different jobs, same
spine.

---

## 3. Adapter 1 — Telegram (build first)

Chosen first because it is cheaper to stand up *and* better at the job the first
milestone actually is (one-person remote control):

- **No auth blocker.** Bot token in env. This deletes open question #1 from rev 1
  rather than answering it — no Workspace admin decision on the critical path.
- **Identity is unforgeable**, so the entire DMARC apparatus (§8) is unnecessary here.
  The allowlist is a set of integers.
- **The confirm loop stops being clunky.** The echo *is* the UI (§7); on Telegram the
  destructive-pipeline confirm is an inline button, one tap.
- **Streaming progress.** Runs take minutes. `editMessageText` on a status message
  gives Rig's event log on a phone. Email cannot do this at all.
- **Commands have affordances.** BotFather's command registry provides autocomplete
  with descriptions on the client. This *partly reverses* the anti-grammar argument in
  §6 — the objection was that strict syntax is a UI with no affordances; here it has
  them, so a `/command` grammar is appropriate on this channel and a subject-line
  grammar still is not on email.

### Telegram-specific hazards

- **`getUpdates` is a consuming read.** Once the offset advances, the update is gone
  from Telegram's servers permanently. Write the raw update to disk **before**
  advancing the offset. This is not a replay nicety — it is data-loss prevention, and
  it is the single most important implementation rule on this adapter.
- **Offset durability.** The offset watermark must survive a crash; persist it in the
  store next to the snapshot, not in process memory.
- **Bot token is a bearer credential.** Leak = full control of the bot. The allowlist
  bounds blast radius but does not remove it.
- **20 MB file ceiling** rules Telegram out for provenance and constrains docbuilder.

---

## 4. Adapter 2 — Email

Base address `ai@example.com`; intent via plus-addressing: `ai+invoice@`,
`ai+docbuilder@`, `ai+payslip@`.

`[2026-08-24 — the domain in the address above, and the one in §8's DMARC conjunct, are
`example.com`: RFC 2606's documentation placeholder, substituted for the live one. What this
section teaches is the LOCAL PART and the plus-addressing scheme — `ai`, `ai+invoice@`,
`ai+docbuilder@`, `ai+payslip@`, and the case-and-dot normalisation below — and in §8 the
DMARC conjunct. The DOMAIN carries no design information that the placeholder does not. A
brief names a mechanism; a live endpoint is DEPLOYMENT CONFIGURATION, and a brief naming one
is the same category error as a brief hardcoding a token. When uc-inbox is built, the real
address belongs where the rest of that deployment's configuration lives — an env var resolved
at agent-eval time beside the channel credentials, never a literal in a brief, a script or an
agent file. Ruled by the arbiter on that ground, which is independent of the export sweep that
occasioned it: the U2 sweep matched §4's address and has no pattern that could match §8's bare
domain, which a full-file sweep found. `scripts/u2_patterns.txt` and the U2 class are
untouched.]`

**Decision — route on `Delivered-To`, not `To`.** A BCC'd recipient appears in
**neither** `To` nor `Cc`, so routing off `To` silently drops every BCC'd message.
Gmail stamps the delivered sub-address into `Delivered-To`, which survives BCC. Fall
back to `X-Original-To`. Lowercase before lookup — Gmail normalises case and dots, so
`ai+Invoice@` and `ai+invoice@` are the same mailbox and must be the same route.

**Decision — signature stripping is a script concern.** Deterministic and
unit-testable, therefore a script per `agent-creation-guide.md`. Prefer the
`text/plain` part; cut at the first of `-- ` (RFC 3676 separator), `Sent from my…`,
`>`-quoted lines, or `On <date>, X wrote:`. Mailgun's *talon* or *EmailReplyParser*
solve this; build a fixture corpus from your own phone's output.

**Note — the plus tag is a hint, not authorisation.** Plus addresses are trivially
guessable and forgeable. All authority comes from §8.

---

## 5. Routing

**The command / tag is the verb.** Selector → pipeline is a deterministic lookup table
in a script, never an LLM decision. This is the `scripts do, agents decide` line from
`agent-creation-guide.md`.

| Channel | Selector |
|---|---|
| Telegram | `/invoice`, `/docbuilder`, `/payslip` (registered with BotFather) |
| Email | plus tag from `Delivered-To` |

**Decision — unknown selector is `unrouted`, never guessed.** Records a row with status
`unrouted`, surfaced in Rig, and replies with the list of valid commands. The LLM is
never asked to infer which pipeline was meant.

**Caution on scope.** "Receives the message, does due diligence, carries out the task"
invites the LLM to infer intent — the pattern the creation guide warns against. Due
diligence means *validate parameters and confirm*, not *decide what was wanted*.

---

## 6. Message format

**Decision — no free-form grammar on either channel.** The selector already names the
pipeline; a second syntax that re-encodes routing creates two sources of truth that can
disagree.

| Part | Treatment |
|---|---|
| Subject (email) / first line (Telegram) | Free text → the run `label`. Rig's `harness_list_runs` already does `label LIKE ?`, so human-written text becomes searchable run history for free. |
| Parameters | Optional trailer block: leading `key: value` lines, terminated by a blank line or `---` (git-trailer shaped). E.g. `month: 2026-07`, `tenant: acme`. |
| Signature / quoted text | Stripped (email only), not specified. |

**Decision — parameters are validated per pipeline, not globally.** Trailer keys are
parsed by a script and validated against *that pipeline's* schema.
`docbuilder/scripts/validate_fields.py` is the existing pattern — it already exits 1
with a structured error payload on missing or malformed required fields. Parameters do
not generalise across invoice / payslip / docbuilder, so a global parameter grammar
would be inventing a CLI over messaging for pipelines that share no arguments.

---

## 7. The reply is the UI

With no interface, the echo *is* the interface. Every accepted message gets a reply
stating what was parsed, which pipeline, and the `run_id`; every rejected one gets the
specific reason or field. This is what makes loose input safe — the interpretation is
visible before it matters.

For expensive or destructive pipelines, put the rigor here rather than in the syntax:
the echo asks, the operator confirms. **A two-step confirm beats an upfront grammar.**
On Telegram this is an inline keyboard callback; on email, a reply of `yes` matched to
the thread.

On Telegram, extend the same message with live progress via `editMessageText`.

---

## 8. Trust and access

**Allowlist of senders**, starting as one operator.

| Channel | Allowlist key | Notes |
|---|---|---|
| Telegram | `from.id` (integer) | Issued by Telegram, unforgeable. Nothing further required. |
| Email | `From:` **AND** `Authentication-Results` showing spf/dkim/dmarc pass for `example.com` | The From header alone is forgeable — the DMARC conjunct is what makes the allowlist real rather than theatre. |

The DMARC rule is written down now because it is exactly the check that gets skipped
until the allowlist widens to clients — precisely when forgery starts to matter. For
internal Workspace mail it is free today.

**Decision — gate attachment *persistence*, not just processing.** A rejected sender
gets a `messages` row with status `rejected` and **nothing written to disk**. Otherwise
an unknown sender retains a write primitive onto the filesystem via a public address,
which is the one thing the allowlist exists to prevent.

**Deferred — quarantine tiering.** A public address means attachments are hostile bytes
an agent will later read, and body text becomes prompt content the moment reasoning is
added. With a one-person allowlist this is near-zero risk, so it is deliberately not
built. Build the *hook* — a `trust` / `status` column and the allowlist in config — so
widening is a config edit, not a refactor. Prior art when needed:
`aetheris--jiyi-brief.md` §5 (quarantine pattern for external document content) and its
trust-tier ranking.

---

## 9. Determinism and storage

**Decision — fetch is a script, never the agent.** A message queue is nondeterministic
external state; the harness contract is record / replay / verify. The adapter writes
raw payload plus normalised JSON to disk, and the agent runs on the **snapshot**.
Replay reads the snapshot and never touches Telegram or Gmail.

**Forced by constraint anyway:** `http_call` currently SIGSYSes the worker
(`setsockopt` missing from the seccomp allowlist — backlog BL-025 / BL-042), so all
channel API calls must be Python under `run_command` regardless of design preference.
Revisit only if that row lands.

| Channel | Idempotency key | Extra state |
|---|---|---|
| Telegram | `update_id` | Durable offset watermark (§3) |
| Email | RFC-822 `Message-ID` | `historyId` watermark |

### Store

**Decision — a separate store, not `aetheris.db`.** The harness owns `aetheris.db`;
Rig opens it `SQLITE_OPEN_READ_ONLY`, and the trust boundary in `rig--architecture.md`
says nothing outside the harness writes it. Use a separate `ingest.db`.

| Table | Key columns |
|---|---|
| `messages` | `id` (PK), `channel`, `channel_msg_id` (`update_id` \| `Message-ID` — unique per channel), `sender_key`, `thread_ref`, `selector`, `label`, `body_raw_path`, `received_at`, `status` (`accepted` / `rejected` / `unrouted` / `processed` / `failed`), `run_id` |
| `attachments` | `message_id` (FK), `filename`, `mime`, `size`, `sha256`, `path` |

SHA-256 on attachments mirrors the provenance dedup story.

---

## 10. Open questions — answer before drafting the milestone doc

1. **Store choice.** Rig already carries two connections (`rusqlite` for `aetheris.db`,
   `duckdb-rs` for `corpus.duckdb`). Third SQLite connection, or reuse DuckDB? Small
   increment either way, but it is a design choice, not a coin flip.
2. **Poll trigger.** Harness `scheduled_runs`, or an external supervisor running the
   long-poll loop? Telegram long-polling is a persistent loop, not a cron shape — this
   may not fit `scheduled_runs` at all and is the main structural unknown.
3. **Reply transport for email.** Reuse `email/scripts/email_send.py` (SMTP), or send
   via the Gmail API on the same credential so replies thread correctly? Threading
   argues for the API. *(Telegram has no equivalent question — same bot token.)*
4. **Gmail auth path** *(deferred with adapter 2, no longer blocking)*. Dedicated
   Workspace user with an OAuth refresh token, or service account with domain-wide
   delegation? A service account cannot read a mailbox without DWD, which needs a
   Workspace admin decision. Compare the Drive service-account `storageQuotaExceeded` /
   Shared Drive experience in `agent-creation-guide.md` — same class of surprise.

---

## 11. Structural notes

- **New `inbox/` use case — do not extend `email/`.** Opposite direction, different
  credentials, different tests. `email/` also already carries the Python stdlib
  shadowing workaround (`agent-creation-guide.md` → Python package naming); a fresh
  `inbox/` directory sidesteps it. Confirm with `python3 -c "import inbox"` before
  committing to the name.
- **Rig surfacing** needs a new module plus Tauri commands; Rig currently reads only
  `aetheris.db` and `corpus.duckdb`.
- **Capability matrix** regenerates from the sprint case — no manual edit.

---

## 12. Suggested first milestone shape (not tickets)

Do not build generic ingest first. Build **one channel → one selector → one existing
pipeline, end to end**, and let the schema fall out of a real case rather than a guess.

Channel: Telegram. Pipeline: docbuilder — send a data file, agent generates the doc,
reply carries the output. `validate_fields.py` already exists, which bounds the LLM's
job to "extract fields into the context schema" — testable, not open-ended.

Rough arc: Telegram adapter + snapshot (offset-before-ack) → command table + integer
allowlist → trailer parse → dispatch to docbuilder → reply echo with inline confirm →
Rig panel.

**Email lands as adapter 2 and is the test of the abstraction.** If adding it touches
anything between snapshot and dispatch, the seam was drawn in the wrong place.
