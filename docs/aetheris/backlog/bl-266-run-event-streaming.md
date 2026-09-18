# BL-266 — Run event streaming (design brief)

**Status:** design decided — tranches T0–T3 not started.
**Type:** design brief. A contract for T0–T3 cc:prompts, cited by item number (`§3 C5`).
**Date:** 2026-09-17
**Row:** BL-266. **Blocked by:** BL-267 (T1 only).
**Citations:** `H` = harness `aetheris` at `191970a`; `A` = `aetheris-agents` at `2cb3fa7`.
Paths under `deps/` are the versions pinned by harness `mix.lock@H`.

---

## 1. Scope

1.1. V1 streaming is durable-store-backed but live-notification-local. Terminal runs replay
from any VM sharing the store; non-terminal runs stream only from the VM hosting the run.

1.2. A client must connect to the hosting VM. Load-balanced multi-node routing without
affinity is unsupported.

1.3. Transports are SSE and WebSocket only. No raw socket.

## 2. Tranches

### T0 — transport-neutral core

No Plug, Bandit, SSE or WebSocket concepts. T0 emits event and control frames (§3 C8) that
T1 and T2 encode.

- T0.1 `Aetheris.StreamRegistry`: duplicate keys; a sibling in `Aetheris.Supervisor`,
  separate from `WaitRegistry`.
- T0.2 Post-commit wakeups inside `Store` (C3).
- T0.3 `runs.terminal_seq` column and migration (C5).
- T0.4 `Store.events_after/3` (C15).
- T0.5 Cursor codec (C8).
- T0.6 Catch-up state machine (C2, C4).
- T0.7 Terminal barrier (C5).
- T0.8 Store-loss recovery (C7).
- T0.9 Local-availability check (C6).
- T0.10 Stream admission cap (C9).
- T0.11 Core tests.

### T1 — SSE

Blocked by BL-267.

- T1.1 Route, auth, `Last-Event-ID` (C1, C11).
- T1.2 Heartbeat with token revalidation (C10).
- T1.3 Event/control framing and disconnect handling (C8, C10).
- T1.4 Harness `docs/aetheris/playground-api.md` (C13).

### T2 — WebSocket

- T2.1 Route, credential carrier, subprotocol negotiation (C11, C12).
- T2.2 Ping/pong.
- T2.3 Frames identical to T1 (C8).
- T2.4 Harness `docs/aetheris/playground-api.md` (C13).

### T3 — Rig

- T3.1 Rust `reqwest` SSE client, relaying frames to the webview as Tauri events.
- T3.2 Cursor persistence and reconnect.
- T3.3 Event/control union handling (C8).
- T3.4 `EventRow` compatibility (§4 F11).
- T3.5 Replaces `useRunEvents`/`useRunDetail` polling on this path.
- T3.6 BL-058 shared-envelope check.
- T3.7 `docs/rig/specs.md` Tauri command and event docs (C13).
- T3.8 A new envelope-parity drift arm (C13).
- T3.9 Fix the stale harness line references at `rig/src/hooks/useHarness.ts:152-153@A`.

## 3. Contract

**C1 — Connect.** Token auth (the existing `AuthPlug` token list) and run resolution happen
before SSE headers are sent or the WebSocket upgrade is performed.
- C1.1 `401`: missing or invalid token.
- C1.2 `404`: no `runs` row, including `schedule_*` pseudo-runs.
- C1.3 `400`: malformed cursor, or a cursor beyond the stored max `seq`.

**C2 — Replay.** No cursor replays from the start; a cursor resumes strictly after it. Then
live. Order is by `seq` only; `step` is not monotonic (§4 F7).

**C3 — Wakeups.** Sent from inside `Store`, after commit:
- C3.1 `{:event_appended, run_id, seq}` after `insert_event` returns `:ok`.
- C3.2 A status wakeup after every `upsert_run`.
- C3.3 A wakeup is a hint. The subscriber always reads `events_after(run_id, last_sent, 200)`,
  looping batches until empty, and coalesces queued wakeups.
- C3.4 `last_sent` advances only after a successful write.

**C4 — Handover.** In order:
1. Subscribe.
2. Capture the stored high-water `H`.
3. Replay through `H`.
4. Process queued wakeups, accepting only `seq > H`.
5. Go live.

**C5 — Terminal.**
- C5.1 `runs.terminal_seq` is set in the same statement as the first terminal status write:
  `COALESCE(terminal_seq, (SELECT MAX(seq) FROM events WHERE events.run_id = runs.run_id), -1)`.
- C5.2 Later terminal writes, including the duplicate `failed`, do not move it.
- C5.3 The stream delivers events with `seq <= terminal_seq`, then sends `stream_end`
  (`reason: "run_terminal"`, with `status`) and closes.
- C5.4 Events with `seq > terminal_seq` are excluded from both live delivery and replay.
- C5.5 `-1` means terminal before any event.
- C5.6 `NULL` on a terminal row is a legacy row: deliver everything stored, then close. Its
  boundary is unknowable.
- C5.7 Terminal state is never inferred from event type.

**C6 — Local availability.** If durable status is non-terminal and `Admission.live?/1` is
false on this node:
1. Wait a bounded grace.
2. Recheck durable status and local liveness.
3. If unchanged: replay the eligible stored range, send `stream_end`
   (`reason: "run_unavailable_on_node"`), and close.

The grace value and the mid-stream trigger for liveness loss are T0 plan STOPs (§5).

**C7 — Store loss.**
1. The subscriber monitors the current Store pid. An exit from a Store call (`:noproc`,
   timeout) counts as Store loss.
2. Stop calling Store.
3. Resolve and monitor the replacement within a bounded window.
4. Catch up from `last_sent`.
5. Re-read durable status, then continue or close per C5.

A Store exit must not kill the subscriber before this runs.

**C8 — Frames.** A discriminated union, identical on both transports.
- C8.1 `{kind: "event", cursor: "v1:<seq>", event: {id, run_id, step, seq, event_type, payload, timestamp}}`.
  `payload` is the raw JSON string, matching Rig `EventRow` (§4 F11).
- C8.2 Cursors are opaque to clients.
- C8.3 `{kind: "control", control: "stream_end", reason, run_id, status?}`, with `reason` ∈
  `run_terminal | run_unavailable_on_node | auth_revoked`.
- C8.4 No frame ever includes `runs.config_json`.

**C9 — Admission.**
- C9.1 One per-node cap on concurrent streams, shared by SSE and WS, counting admitted
  streams regardless of run.
- C9.2 Register in `StreamRegistry`, then count. Over the cap: unregister, then `503` with
  `Retry-After`, before headers or upgrade.
- C9.3 The config key and its default are documented.
- C9.4 The slot is released on process exit.
- C9.5 No per-token or per-run caps.

**C10 — Connection process.**
- C10.1 It is the single owner of every network write.
- C10.2 A 15 s heartbeat via `send_after(self())`. Each tick revalidates the token against the
  current token list; on failure it sends `stream_end` (`reason: "auth_revoked"`) and closes.
- C10.3 Slow consumer: ThousandIsland `send_timeout` 30 s with close-on-timeout is the v1
  rule (§4 F10).
- C10.4 Mailbox growth is a recorded residual risk.

**C11 — Routes.**
- C11.1 `GET /api/playground/runs/:run_id/events` (SSE).
- C11.2 `GET /api/playground/runs/:run_id/events/ws` (WebSocket).
- C11.3 Errors use the playground error envelope.
- C11.4 The open status endpoints do not authorize reading event bodies.

**C12 — WebSocket credential.**
- C12.1 Either the `Authorization` header, or the browser subprotocols `aetheris.events.v1`
  plus `aetheris.bearer.<unpadded base64url token>`.
- C12.2 The server decodes and validates the credential entry and echoes only
  `aetheris.events.v1` (§4 F9).
- C12.3 More than one credential entry is rejected.
- C12.4 The credential is never logged.
- C12.5 Precedence when both a header and a subprotocol credential are present is a T2 plan
  STOP (§5).

**C13 — Docs ownership.**
- C13.1 T1/T2: harness `docs/aetheris/playground-api.md`.
- C13.2 T3: `docs/rig/specs.md` (Tauri command and events) and the envelope-parity arm. The
  existing `tauri_commands` arm does not replace envelope parity.

**C14 — Secrets gate.** Passed on the scout's H10 audit (§4 F13).
- C14.1 No credential-shaped values in event payloads; no write-time redaction is required for T1.
- C14.2 Payloads are token-protected business data.
- C14.3 Localhost remains the default bind.

**C15 — Reads.**
- C15.1 `Store.events_after/3` runs through the Store process and returns raw `payload_json`.
- C15.2 Batch 200, looping.
- C15.3 No second connection.
- C15.4 Measured maximum at scout time: 195 events and 402,271 bytes per run. A measurement,
  not a bound.

## 4. Scout facts relied on

- F1 Store is a single GenServer on one connection — `lib/aetheris/store.ex:684-706@H`.
- F2 Every `runs` write goes through `upsert_run`, an unconditional status overwrite —
  `lib/aetheris/store.ex:1393-1402@H`.
- F3 The loop is not stopped at terminal: it runs in a `Task.start_link` the server never stops, and
  `loop.ex` has no run-status check — `lib/aetheris/agent/server.ex:273-274@H`;
  `lib/aetheris/execution/loop.ex@H`.
- F4 Worker `:DOWN` appends without a status guard and does not persist `failed` —
  `lib/aetheris/agent/server.ex:564-580@H`.
- F5 Every `mix aetheris <cmd>` boots its own Store on the same file —
  `lib/aetheris/cli/commands/run_helpers.ex:345-351@H`; `lib/aetheris/application.ex:41-51@H`.
- F6 Post-terminal appends are in the DB: 4 `done` runs end `run_complete` → `error` —
  scout DB census of `priv/aetheris.db` at `H`, not reproducible from the tree.
- F7 `seq` is gapless in the DB (0 runs with `max(seq)+1 ≠ count`); `step` decreases along
  `seq` in 6 runs — same census.
- F8 `schedule_*` has no `runs` row — `lib/aetheris/scheduler.ex:164-169@H`.
- F9 Bandit does not negotiate subprotocols; the handshake sends `conn.resp_headers`, so the
  plug must set the echo — `deps/bandit/lib/bandit/websocket/handshake.ex:64-80` (bandit 1.12.5).
- F10 ThousandIsland send defaults are `send_timeout: 30_000`, `send_timeout_close: true`, and
  Aetheris passes no transport options —
  `deps/thousand_island/lib/thousand_island/transports/tcp.ex:50-56` (1.5.0);
  `lib/aetheris/api/server.ex:25@H`.
- F11 `EventRow` is `{id, run_id, step, seq, event_type, payload: string, timestamp}` —
  `rig/src/hooks/types.ts:184-193@A`.
- F12 `WaitRegistry` is a duplicate-key Registry using `Registry.dispatch` —
  `lib/aetheris/wait_registry.ex:22-25, 40-46@H`.
- F13 H10: payloads are written verbatim with no redaction (`lib/aetheris/store.ex:1312-1330@H`);
  DB census found 0 key-shaped values (`sk-`+20, `ghp_`/`github_pat_`, `AKIA`, bearer+16); the
  credential-capable surface is `runs.config_json` (`lib/aetheris/agent/server.ex:975-983@H`).

## 5. Open for plan STOPs

- T0: the grace value and the mid-stream liveness-loss trigger (C6); the `upsert_run` SQL
  form for C5.1; the Store-replacement wait bound (C7).
- T1: the stream cap's default value (C9.3).
- T2: credential precedence (C12.5).
