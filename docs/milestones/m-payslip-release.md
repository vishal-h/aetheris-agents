# m-payslip-release — releasing payslips to employees

**Status:** draft — design input, not yet approved. No tickets generated.
**Drafted:** 2026-09-07 by claude-ui, from the payslip incident session of the same day.
**Repo state all citations were verified against:** `aetheris-agents` `ab64cf2`; harness `../aetheris` `ca11d35`.
**Size:** L. Per repo convention an L row gets its own milestone doc before implementation; this is that doc.

> **Citation currency.** Every `file:line` below was opened at the commit named above. Line citations decay — re-verify at HEAD before reuse. Figures about live Drive state carry the timestamp of the read they rest on.

---

## 1. What exists today

`email/scripts/email_send.py` sends one email per employee, each with that employee's payslip PDF attached — **all to a single address**. The recipient is computed once:

```python
# :45
to_addr = os.getenv("SMTP_TO") or username
# :155
msg["To"] = config["to_address"]
```

Payroll receives the batch at `payroll@bitloka.com`, reviews it, and forwards to employees by hand.

**The per-employee address is already loaded and already discarded.** `payroll.csv` carries an `email` column, `payslip_compute.py` surfaces it, and `email_send.py` reads it at `:228` and renders it into the body at `:241` — so each review email already states its intended recipient in prose while the envelope goes to the shared address. That divergence *is* the current design.

**Consequence for this milestone:** a recipient manifest for humans to read is not needed. The review emails already disclose the mapping, one per employee.

---

## 2. The constraint that shapes everything

**Rig's approval gate cannot serve as a release gate.** `rig/src/hooks/useOrchestrator.ts:96` calls `orchestrate_approve(jobId, approved)` at phase `plan_ready` — *before any step executes*. It approves the plan, not an artifact. By the time payslips exist to review, the run is executing and the gate is spent.

This is not a Rig gap to patch. `mix aetheris run` is single-shot and `ask_human` is deliberately excluded from the tool set; `CLAUDE.md` §Learning — m4-docbuilder already states that interactive-approval designs get re-modelled as stop-and-re-run.

---

## 3. The shape: two runs, not one gate

- **Run A** — today's flow, unchanged: download → generate → upload → review mail to payroll.
- *Human reviews the emails already received.*
- **Run B** — `email/agents/email_release_orchestrator.exs`, sending per-employee from the same `payslip/output/` artifacts.

Rig's existing plan-approval then lands where it is wanted: **Run B's plan card is the release gate**, using an affordance that already exists rather than inventing a mid-run one.

---

## 4. Design decisions

### 4.1 Envelope and body collapse to one value

Run B sets `msg["To"] = variables["employee_email"]`. That is what makes the review email a literal preview of the release email rather than a description of one. It is also the whole substance of the send-side change — the address is already in scope at `:228`.

### 4.2 The send manifest is hashed, and it is the binding

Run A writes a manifest as a byproduct — it has all the data at `:236-246`. Each entry is the triple **`(employee_id, email, sha256)`** per attached file. Run B sends strictly from that manifest and verifies the hash before attaching, refusing on mismatch.

Filename-only binding is insufficient: a payslip regenerated between review and release has the same name and different bytes, and passes.

**Hash at send time, not generate time**, so it covers exactly what was attached.

**What the hash buys and does not buy.** It buys byte-integrity and durable binding. It does *not* buy human mapping-verification — nobody eyeballs a sha256. The employee→email mapping is verified by the body disclosure that already exists (§1). What the manifest changes is that the mapping becomes a durable, machine-checkable artifact instead of an emergent property of two scripts agreeing — and a wrong pairing is an irreversible privacy breach, so making it an explicit reviewed object is the point.

### 4.3 Where the manifest lives — decided on privacy grounds

The manifest carries employee email addresses. That single fact settles it by elimination:

- **Not git-tracked.** Repo history is permanent, and a tracked file would ride the project-knowledge export into a Claude project.
- **Not client-visible.** Never in a shared Drive tree.

What remains: **`payslip/releases/{month}/`** — gitignored but durable on the operational machine — and/or a payroll-only operational Drive folder for retention beyond one machine, **with the manifest's own sha256 recorded in Run A's trajectory**. The trajectory anchors the audit chain (*which* manifest was reviewed is provable forever) while the personal data stays out of the repo and out of exports. Run B verifies the manifest hash first, then the per-file hashes.

### 4.4 Addresses reach the send script only via the manifest — a transport constraint

Guarding stdout guards the back door only. `tool_called` events carry `tool_input` (`docs/rig/specs.md:621`), and for `run_command` that includes the full argument list (`api/docs/t3-implementation-notes.md:32`) — so an address passed as a script argument, or as a per-send env var the agent sets, enters the trajectory through the front door while a logging rule is still being honoured.

> Addresses reach the send script **only** via the manifest file the script reads. Never via command arguments, and never via environment the agent sets per send.

**Done-check for it:** for each address in the run's manifest, grep the **entire trajectory** for that exact string — expect zero. Then the same needles against the send log — also zero. Exact-match against the real secret set at whole-file scope has no false positives and verifies the actual claim. This is stronger and cheaper than scanning `tool_called` payloads for `@`, which is simultaneously too narrow (leakage can land in `tool_result` or an observation) and too noisy.

Note `email_send.py:250` currently prints `Sent: {employee_id} → {config['to_address']}` — harmless today because that is the single shared address, and exactly the line that would emit every employee's address in Run B.

### 4.5 The send log uses id + hash entries

`(employee_id, sha256, timestamp)` — **no addresses**. It is a durable record of who was mailed, so address entries would pull it into §4.3's regime and leave two artifacts to protect instead of one. With id+hash entries the manifest remains the sole artifact carrying the mapping, and the send log lives anywhere operational.

### 4.6 Omissions are invisible in the review surface

`email_send.py:230-233` skips an employee with a stderr warning when the PDF is missing. stderr goes to the trajectory, not to payroll's inbox — so thirty emails look complete whether there were thirty employees or thirty-one. **Run B must refuse to release when Run A reported any skip**; Run A already counts them.

### 4.7 Irreversibility and idempotence

A wrong Drive upload is overwritten; a wrong email is not unsent. Per `CLAUDE.md` §Python script conventions' explicit-sink-selection rule, Run B requires an explicit release flag and raises at eval time when absent — fail closed, never default to live send.

Separately, SMTP has no update-in-place equivalent: re-running Run B mails everyone twice without the §4.5 send log checked before each send.

### 4.8 Release needs its own template

`email/data/payslip_email_template.html` contains `Email: {{employee_email}}` — review scaffolding. Sent to the employee it reports their own address back to them. Release needs that line stripped or a second template, so **release is not literally "forward the same mail"**, which someone will otherwise assume.

---

## 5. Dependencies

| # | Dependency | State |
|---|---|---|
| 1 | **The orchestrator duplicate** — `email/agents/email_orchestrator.exs` and `email_orchestrator2.exs` both exist; orch2 uses the raise-at-eval-time pattern from `docs/agent-creation-guide.md` and orch1 does not; **Rig's plan card shows orch1 wired**. | **Blocking. Has no backlog row** as of 2026-09-07 — flagged in the session's technical brief and never filed. Adding a third email agent on top of an unresolved duplicate is how the duplicate becomes permanent, and an L milestone is the most expensive moment to discover that. |
| 2 | `DRIVE_TEMPLATES_FOLDER_ID` is documented in no runbook. `email_download_template.py:75-77` exits 1 without it, which blocked a live August send on 2026-09-07 (run `email-orch-dWIgxw`). | Recorded in **BL-191**'s evidence block. Run B needs the template download, so this bites again unless BL-191 lands first or Run B is given a committed-template fallback. |
| 3 | **BL-192** — `email_send.py:220` calls `strptime` inside a display expression, so a malformed month raises an uncaught `ValueError` rather than exiting 1. | Filed, open, S/low. Not blocking, but Run B inherits the same argument surface and should not inherit the defect. |

---

## 6. Proposed ticket split

Not tickets yet — the milestone doc is approved before issues are generated (methodology §4).

- **t1** — resolve dependency 1: one email orchestrator, the raise-at-eval-time pattern, Rig pointed at it.
- **t2** — Run A writes the hashed manifest to `payslip/releases/{month}/`; manifest sha256 into the trajectory. No send-side change.
- **t3** — `email_send.py` gains a release mode: envelope from `employee_email`, manifest-driven selection, hash verification, release-variant template, fail-closed flag.
- **t4** — the send log, and the refuse-on-skip rule.
- **t5** — `email_release_orchestrator.exs` and the Rig plan-card surface for the release gate.
- **t6** — runbook, and the §4.4 done-check wired into the sprint.

Sizing rule (methodology §6): one ticket = one session = one artifact boundary. t3 is the one at risk of stretching.

---

## 7. Open questions for the arbiter

1. **Does dependency 1 get a row before this milestone starts, or is it folded into t1?** A row makes it visible if the milestone slips; folding it in is one fewer artifact.
2. **Retention of `payslip/releases/{month}/`.** How long, and does it need to survive machine loss? That decides whether the payroll-only Drive copy in §4.3 is optional or required.
3. **Does Run B need a per-employee dry run?** §1 argues the review emails are the human surface and no additional preview is needed. If payroll disagrees, that is a t5 scope change, not a t3 one.

---

## 8. What this milestone does not change

- Run A's flow, `payslip/output/` as a per-employee archive, and `merge_employee_payslips.py`'s dependence on it.
- `drive_upload.py` — fixed under BUG-001 on 2026-09-07 and out of scope here.
- The single-shot nature of `mix aetheris run`. §2 is a constraint to design within, not a thing to fix.
