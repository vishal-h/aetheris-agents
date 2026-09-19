# BL-266 T3 — implementation notes (Rig consumer for the run event stream)

`2026-09-19, at agents a137a09 / aetheris 2d93851. T3 lands in agents only; the harness is the
read-only server contract.` Contract: `docs/aetheris/backlog/bl-266-run-event-streaming.md`.
Plan: the T3 plan STOP, with rulings 1–17, O1 (a), O2 (a) plus `client_status`, O3, O4, and
amendments A and B. Notes live here rather than beside T0–T2's in the harness because T3 edits
no harness file.

## Decisions

- **`ClientErrorReason` is `unauthorized | bad_request | not_found | http | protocol`.** The
  plan named reasons for 401, 404 and parse failures only. 400 keeps the envelope `code`
  (e.g. `invalid_cursor`) beside `bad_request`; every other stopped 4xx is `http`.
- **A failed attempt is one that delivered no valid item and ends in a retry.** A session
  that delivered items and then hit EOF is not a failure, so `reconnecting` needs two empty
  attempts after it. `Liveness` owns this rule and the backoff reset, since amendment A and
  ruling 17 use the same "valid frame or heartbeat" predicate.
- **`Retry-After` is used exactly**, with no jitter and no cap, and it does not advance the
  backoff index.
- **`useRunStream` returns `reconnecting`**, beyond the plan's signature, because
  `client_status` needs a reader. The banner shows `reconnecting…` and the live spinner stops.
- **Parity-arm FAILs beyond the plan's list:** the UiFrame kind set must equal wire kinds plus
  the UI-only set, specs §9.4's kinds must equal UiFrame's, and UiFrame's tag must equal
  WireFrame's. These are amendment A's "UI-only variants beside `client_error`".

## Deviations

- **`#[serde(default)]` is not on `WireFrame::Control.status`.** Serde already reads a missing
  `Option` field as `None`, so the attribute would add nothing. Without it, the arm can fail on
  every field-level serde attribute on a wire type, with no allow-list.
- **Non-200 2xx and 3xx stop with `client_error http`.** O3 covers only 4xx and 5xx. reqwest
  follows redirects, so a 3xx should not normally reach the thread.
- **A client build failure emits `client_error http` and ends the thread.** No ruling covers it.
- **BL-272's heading has no `(#TBD)`**, which the O5 wording carried. Index-shaped rows carry
  none. The row body is the O5 wording.
- **`TrajectoryView.tsx` holds both a §2.8 commit-5 hunk and a commit-6 (T3.9) hunk.** Splitting
  them needs `git add -p`.

## Owed

- The click-through merge gate (plan §2.7). It is not run: a live harness with both env vars
  set, a running run streaming, then completing and reloading, then the same with the vars unset.
- BL-272 (O5) and BL-273 (O6), filed open.
