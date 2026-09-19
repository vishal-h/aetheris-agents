import { useEffect, useState } from 'react';
import { listen } from '@tauri-apps/api/event';
import { invoke } from '@tauri-apps/api/core';
import type { EventRow, RunStreamEmit, RunStreamSubscribeResult, UiFrame } from './types';

/** `poll`: streaming is not configured, or the stream handed back to polling. */
export type RunStreamMode = 'idle' | 'pending' | 'stream' | 'poll';

export interface RunStreamResult {
  mode:           RunStreamMode;
  /** Events received so far; `[]` once the stream is open. */
  data:           EventRow[] | null;
  error:          string | null;
  warning:        string | null;
  /** The status carried by `stream_end run_terminal`. */
  terminalStatus: string | null;
  isLive:         boolean;
  /** Set by `client_status reconnecting`, cleared by `connected`. */
  reconnecting:   boolean;
}

const EVENT_NAME = 'aetheris-run-stream';

const IDLE: RunStreamResult = {
  mode: 'idle', data: null, error: null, warning: null,
  terminalStatus: null, isLive: false, reconnecting: false,
};

let counter = 0;

type ControlFrame = Extract<UiFrame, { kind: 'control' }>;
type ClientErrorFrame = Extract<UiFrame, { kind: 'client_error' }>;

function applyControl(s: RunStreamResult, frame: ControlFrame): RunStreamResult {
  const ended = { ...s, isLive: false, reconnecting: false };
  switch (frame.reason) {
    case 'run_terminal':
      return { ...ended, terminalStatus: frame.status ?? null };
    case 'run_unavailable_on_node':
      return { ...ended, mode: 'poll' };
    case 'inconsistent_run_state':
      return {
        ...ended,
        mode: 'poll',
        warning: `stream ended: stored status ${frame.status ?? 'unknown'} disagrees with the run's terminal boundary — showing polled events`,
      };
    case 'auth_revoked':
      return { ...ended, error: 'stream ended: the API token was revoked' };
    case 'store_unavailable':
      // Rust reconnects; nothing changes here.
      return s;
  }
}

function describeClientError(frame: ClientErrorFrame): string {
  const http = frame.http_status !== null ? ` HTTP ${frame.http_status}` : '';
  const code = frame.code !== null ? ` ${frame.code}` : '';
  return `stream failed (${frame.reason}${http}${code}): ${frame.message}`;
}

/**
 * A run's events pushed from the harness SSE stream (BL-266 T3), via the
 * `aetheris-run-stream` Tauri event relayed by `commands/run_stream.rs`.
 *
 * The id is minted here, before subscribing, so every frame can be matched to
 * this subscription from the first one; that also isolates StrictMode's
 * double mount. When the API is not configured, `mode` goes to `poll` and the
 * caller keeps `useRunEvents`. A rejected subscribe also falls back to `poll`,
 * with a `warning` so the fallback is visible.
 */
export function useRunStream(runId: string | null): RunStreamResult {
  const [state, setState] = useState<RunStreamResult>(IDLE);

  useEffect(() => {
    if (!runId) {
      setState(IDLE);
      return;
    }
    counter += 1;
    const subscriptionId = `${runId}:${Date.now()}:${counter}`;
    let cancelled = false;
    let lastSeq = -1;
    setState({ ...IDLE, mode: 'pending' });

    const handle = (payload: RunStreamEmit) => {
      if (cancelled || payload.subscription_id !== subscriptionId || payload.run_id !== runId) return;
      const frame = payload.frame;
      switch (frame.kind) {
        case 'event': {
          // Wire order is seq order; guard anyway rather than trust delivery order.
          if (frame.event.seq <= lastSeq) {
            console.warn(`[useRunStream] dropped out-of-order event seq ${frame.event.seq} after ${lastSeq}`);
            return;
          }
          lastSeq = frame.event.seq;
          const event = frame.event;
          setState((s) => ({ ...s, data: [...(s.data ?? []), event] }));
          return;
        }
        case 'control':
          setState((s) => applyControl(s, frame));
          return;
        case 'client_error':
          setState((s) => ({ ...s, error: describeClientError(frame), isLive: false, reconnecting: false }));
          return;
        case 'client_status':
          setState((s) => ({ ...s, reconnecting: frame.state === 'reconnecting' }));
          return;
      }
    };

    const unlistenPromise = listen<RunStreamEmit>(EVENT_NAME, (e) => handle(e.payload));
    const subscribePromise = unlistenPromise
      .then(() => {
        if (cancelled) return null;
        return invoke<RunStreamSubscribeResult>('run_stream_subscribe', {
          request: { subscription_id: subscriptionId, run_id: runId },
        });
      })
      .then((result) => {
        if (cancelled || result === null) return;
        if (result.mode === 'stream') {
          setState((s) => ({ ...s, mode: 'stream', data: s.data ?? [], isLive: true }));
        } else {
          setState((s) => ({ ...s, mode: 'poll' }));
        }
      })
      .catch((e) => {
        if (cancelled) return;
        console.warn(`[useRunStream] subscribe failed for ${runId}: ${String(e)}`);
        setState((s) => ({
          ...s,
          mode: 'poll',
          warning: `live stream unavailable (${String(e)}) — showing polled events`,
        }));
      });

    return () => {
      cancelled = true;
      unlistenPromise.then((fn) => fn()).catch(() => {});
      // Chained, so an unsubscribe can never reach Rust before its subscribe.
      subscribePromise
        .then(() => invoke('run_stream_unsubscribe', { subscriptionId }))
        .catch(() => {});
    };
  }, [runId]);

  return state;
}
