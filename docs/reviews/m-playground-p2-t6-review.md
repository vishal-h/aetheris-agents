# Review — m-playground-p2 t6 — round 1

Reviewer: claude-ui. Subject: `commands/playground.rs` + `lib.rs` wiring +
`types.ts`. Commit a76e5ec.

## Verdict

**Approved for merge** with findings 1–2 folded in and finding 3 carried
to t7. No round 2 required.

Core obligations verified: five commands present ✓; token never in a
`Serialize` type (explicit comment) ✓; `playground_connection_status`
always returns `Ok`, gates on `data.connected` ✓; registered in exactly
two places (`invoke_handler` + `manage`) ✓; `AETHERIS_API_TOKEN` read in
Rust at startup, never forwarded ✓; `AETHERIS_API_URL` + `AETHERIS_API_TOKEN`
env vars ✓; TS types mirror Rust structs with no `any` ✓.

`reqwest` dep choice justified in context (blocking HTTP for sync Tauri
commands; the existing codebase has no async Tauri command pattern to
follow). Noted for implementation notes — accepted.

## Findings

1. **[non-blocking, fold-in] `connection_status` probe sends no auth
   header.** The probe `GET /api/playground/policy` is sent without
   `Authorization: Bearer …`, so it always gets a 401 from the harness.
   A 401 is still a live server — the comment says so ("a 200 or 401 both
   mean the server is up") — and `Ok(_)` matches both, so `connected: true`
   is returned correctly. But the comment is the only thing making this
   intentional; the next reader will read "sends a GET, if Ok then
   connected" and add a token. Add an explicit comment at the `Ok(_)` arm:
   `// 200 (authed) or 401 (unauthed probe) both confirm the server is
   reachable — connected = true either way`.

2. **[non-blocking, fold-in] `reqwest::blocking::Client::new()` is
   constructed per call.** Each of the five commands creates a new client,
   which re-resolves DNS, re-negotiates TLS, and re-allocates a thread
   pool on every invocation. For five low-frequency Tauri commands this is
   not a performance problem, but it is inconsistent with the spirit of
   `PlaygroundState` as the connection holder. Store a
   `reqwest::blocking::Client` in `PlaygroundState` (constructed once at
   `manage` time) and share it. Alternatively — and simpler — add a
   `// intentional: low-frequency command, per-call client is acceptable`
   comment and leave it. Either is fine; the comment converts an
   oversight into a decision.

3. **[non-blocking, carried to t8] `specs.md §4` needs two new entries.**
   The five playground commands and `AETHERIS_API_URL` /
   `AETHERIS_API_TOKEN` env vars are new harness surface that `specs.md`
   and `runbook.md` don't yet reflect. t7 adds the Run Composer panel —
   t8 is the doc-sync ticket, but the env var table in `specs.md §1` and
   the Tauri command list in `specs.md §4` should land with t8, not
   silently after. Record in t8's milestone section.

## Positive notes

- `PlaygroundApiError` + `PlaygroundViolation` in `types.ts` — these
  aren't Rust structs, they're TS-only types for the 422 body that the
  frontend needs to parse from the raw error string. Unprompted addition,
  exactly right — the frontend hook will need them.
- `require_connection` helper eliminates the repeated
  `state.api_url/token` pattern cleanly. The error messages name the
  missing env var specifically — good diagnostic discipline.
- `playground_submit_run` returning the raw JSON body on non-202 (rather
  than a generic error string) is the right call for 422 — the violations
  list needs to reach the frontend intact.
- No `any` anywhere in the TS types. All optional fields use `?` not
  `| undefined`, consistent with the existing `types.ts` style.

## Cross-ticket notes

- t7 (Run Composer panel) is unblocked. The hook will use
  `PlaygroundSubmitRequest`, `PlaygroundPolicy`, `PlaygroundSandboxes`,
  `PlaygroundRunStatus`, `PlaygroundApiError`, `PlaygroundViolation` from
  `types.ts` — all present.
- t7 prompt should reference: connection-gating via
  `playground_connection_status` (gate the whole panel on
  `data.connected`); server-populated selectors (never hardcode allowlists
  — fetch from `playground_get_policy`); violation rendering from the
  structured `PlaygroundApiError` body; MRU via localStorage per the
  established pattern in `rig/CLAUDE.md`; no polling loop in the Composer
  (status is poll-on-demand from the hook, not a background task).
- Finding 3 (specs/runbook sync) is t8 scope — add to t8's milestone
  section now.
