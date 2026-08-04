# BL-086 — TrajectoryView: label steps by their `run_command` stage (implementation notes)

Pure frontend. One new module (`stageLabel.ts`), one badge line changed in `TrajectoryView.tsx`.
No harness change, no event change, retroactive on every trajectory already on disk.

These notes carry the payload enumeration done *before* coding, the two shape facts that would have
silently broken a reasonable implementation, and the payload groundwork BL-073 inherits.

---

## Enumeration first — 68 trajectories, 468 steps

Applied up front rather than after the fact, because BL-083's false docbuilder claim came from
trusting a row's description of data instead of reading it. Scanned every
`cloudcost-orch-*`, `docbuilder-orch-*` and `docbuilder-ctx-*` trajectory on disk.

**`tool_called` payload shape.**

```json
{"server_id": "aetheris_exec", "source": "mcp",
 "tool_input": {"args": ["scripts/fetch_aws.py", "--output-dir", "output/aws"],
                "command": "python3", "timeout_ms": 300000},
 "tool_name": "run_command"}
```

| fact | count | consequence |
|---|---|---|
| tool names present | `run_command` 360, `read_file` 68, `write_file` 32, `spawn_agent` 4, `wait_for_event` 4 | must key on `tool_name` |
| native tools carry only `{tool_name, tool_input}` | — | `server_id`/`source` are **not** reliable discriminators |
| `command` values | `python3` 336, `cat` 14, `bash` 4, `sh` 3, `ls` 2, one full shell line | `command === 'python3'` would under-match |
| args with exactly one `.py` | 331 | the normal case |
| args with no `.py` | 28 | must return null |
| args absent/null | **1** | must not throw |
| first `.py` not at `args[0]` | 0 | `.py`-search is headroom, not a fix |
| steps with >1 `run_command` | **0 of 468** | "first match wins" guards a case that does not occur |

**Two facts that would have broken a reasonable implementation:**

1. **There is no top-level `args`.** The script is at `tool_input.args[0]`. A naive
   `payload.args[0]` reads `undefined` on *every* real payload and would have shipped a feature
   that silently never fires — passing lint, build and a casual look at the UI.
2. **`args` is genuinely absent on one payload.** `docbuilder-ctx-orch-WRNyiQ` put an entire shell
   line in `command` with no `args` key (the p9 nested-`mix aetheris run` attempt that hit
   `ETXTBSY`). That is the real null case, not a hypothetical one.

**Docbuilder is coverable — no STOP.** The ticket asked to stop rather than half-cover it if
docbuilder's `run_command` were not a python-script shape. It is: `docbuilder-ctx-*` mixes
`read_file` with a `run_command` for `resolve_last_run.py`, and `docbuilder-orch-*` yields nine
stages in a row.

---

## The extractor

`rig/src/components/modules/harness/stageLabel.ts` — three pure exports, no React, no Tauri:

- `stageFromToolCallPayload(payload: unknown): string | null`
- `stageForStep(events): string | null` — first `tool_called` whose payload yields a stage
- `stepBadge(step, events): string` — `"Step 3 · fetch_aws"` or `"Step 3"`

Rules: `tool_name === 'run_command'` → `tool_input` must be an object → `args` must be an array →
first element that is a string ending `.py` → basename minus `.py`. Every other shape returns
`null`; nothing throws. `unknown` inputs and an explicit `isRecord` guard rather than trusting the
declared TS types, because the payload is `Record<string, unknown>` inflated from JSON
(`types.ts:238-247`) and TS gives no runtime guarantee about it.

`TrajectoryView.tsx` changes one line — `Step {step}` → `{stepBadge(step, events)}` — plus the
import. `StepGroup` already receives the step's `events`, so nothing was threaded through.

---

## Verification

**The derivation is offline-provable; only the rendered badge is not.** The proof runs the **real
exported function** — imported, not re-implemented — over on-disk trajectories via a `bun` one-shot
(`bl086_verify.ts`, in the review packet). No JS test harness exists in `rig/` (established at
BL-083: no vitest/jest/testing-library, no config) and none was invented.

**The rename that makes it non-vacuous.** The frontend never sees `trajectory.json` verbatim:
`trajectory.rs:98-100` maps `e["type"] → event_type`. The harness performs that same rename before
calling the extractor. Feeding the raw file shape instead would make every assertion pass
vacuously — `event_type` would be `undefined`, the extractor would correctly return `null` for
everything, and "no stage found" would look like a clean run. That is asserted directly as a
mutation control: the raw shape is fed in deliberately and must yield `null`.

Results — all pass:

| check | result |
|---|---|
| `cloudcost-orch-aws-3KU2NQ` | `fetch_aws → detect_orphans → compose_report_data → render_report`, step 4 plain |
| `docbuilder-ctx-0nDlug` | `resolve_last_run`; its three `read_file` steps stay plain |
| `docbuilder-orch-IOR8Mw` | nine stages, `list_templates … run_log_writer`, tail turns plain |
| `docbuilder-ctx-orch-WRNyiQ` | the args-absent payload degrades, does not throw |
| degrade matrix, 15 shapes | all `null`, none throws — includes the top-level-`args` trap |
| positive matrix, 5 shapes | includes `-u script.py` (flag first) and a dotted filename |
| mutation control | raw `type` shape → `null`, so the rename is load-bearing |

`bun run lint` clean · `bun run build` clean.

**`detect_optimization_signals` not covered by a live run.** It only appears when
`CLOUDCOST_OPTIMIZATION=1`, and no such run exists on disk. Nothing about it is special —
`scripts/detect_optimization_signals.py` is the same `run_command`/`args[0]` shape as its four
siblings, all of which are proven — so this is a coverage gap, not a risk. Stated rather than
quietly counted as covered.

**Owed: the rendered badge.** `TrajectoryView` loads through Tauri `invoke`, which does not resolve
headless, so the badge itself is unverified — the same limit as BL-083's group headings. The
derivation behind it is proven; the pixels are not.

---

## Groundwork for BL-073 — `tool_result` shapes, enumerated

BL-073 parses the render step's `tool_result`. Enumerated over the same 68 trajectories so it
inherits verified facts instead of re-deriving them:

**Four distinct payload key-sets — and two different result keys:**

| key-set | count |
|---|---|
| `{fs_hash, output, tool_name}` | 299 |
| `{duration_ms, fs_hash, output, tool_name}` | 153 |
| `{is_error, result, tool_name}` | 8 |
| `{result, tool_name}` | 8 |

**`output` vs `result` is live, not theoretical.** MCP/exec tools use `output`; native tools use
`result`. This is exactly **BL-046** ("Tool-result payload key is a convention, not a contract"),
confirmed against real data. BL-073 must read both or explicitly scope itself to `run_command`
results.

**`output` is a JSON *string*, and is sometimes null.** Types: `str` 452, `None` 16. Parsed, the
inner shapes are:

| inner key-set | count |
|---|---|
| `{duration_ms, exit_code, stderr, stdout}` | 291 |
| not JSON at all | 63 |
| `{exit_code, stderr, stdout}` | 53 |
| doc-specific payloads (`{doc_types, tenant_id}`, invoice/offer field maps) | 46 |

So reaching a render artifact path is a **three-level** parse — `payload.output` (string) →
`JSON.parse` → `.stdout` (string) → `JSON.parse` → `.file` — with a null check and a
non-JSON fallback at each level. `render_report.py`'s stdout carries `file`, `pdf`, `bytes`,
`template`. BL-073 should treat every level as fallible; 63 payloads on disk are not JSON at the
first level alone.
