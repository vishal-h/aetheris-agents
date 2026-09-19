//! Run event stream consumer (BL-266 T3).
//!
//! One blocking thread per subscription reads the harness SSE stream
//! (`GET /api/playground/runs/:run_id/events`, harness `playground-api.md` §3.5)
//! and relays each frame to the webview as the app-wide Tauri event
//! `aetheris-run-stream`. The cursor lives only here: `UiFrame` has no cursor
//! field, so the webview never receives one.

use std::collections::hash_map::RandomState;
use std::collections::HashMap;
use std::hash::{BuildHasher, Hasher};
use std::io::{self, BufRead, BufReader};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex, MutexGuard};
use std::time::Duration;

use serde::{Deserialize, Serialize};
use tauri::{AppHandle, Emitter, State};

use crate::commands::playground::{require_connection, PlaygroundState};

/// The one Tauri event this module emits.
pub const RUN_STREAM_EVENT: &str = "aetheris-run-stream";

// ============================================================================
// State
// ============================================================================

/// Managed state: live subscriptions keyed by the webview-minted id.
pub struct RunStreamState {
    pub subs: Arc<Mutex<HashMap<String, RunStreamSub>>>,
}

impl RunStreamState {
    pub fn new() -> Self {
        RunStreamState { subs: Arc::new(Mutex::new(HashMap::new())) }
    }
}

impl Default for RunStreamState {
    fn default() -> Self {
        Self::new()
    }
}

pub struct RunStreamSub {
    pub subscription_id: String,
    pub run_id:          String,
    /// Set by unsubscribe; also the entry's identity token (see `remove_if_own`).
    pub cancel:          Arc<AtomicBool>,
    pub active:          bool,
    pub cursor:          Arc<Mutex<Option<String>>>,
    /// Last thread status, for logs and debugging only.
    pub status:          Option<String>,
}

type SubMap = Arc<Mutex<HashMap<String, RunStreamSub>>>;

fn lock<T>(m: &Mutex<T>) -> MutexGuard<'_, T> {
    m.lock().unwrap_or_else(|poisoned| poisoned.into_inner())
}

// ============================================================================
// Wire types — the harness frames (`lib/aetheris/stream/frame.ex`)
// ============================================================================

#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum WireFrame {
    Event   { cursor: String, event: StreamEvent },
    Control { control: StreamControl, reason: StreamEndReason, run_id: String, status: Option<String> },
}

/// Same field names and types as `harness::EventRow` (BL-266 T3.4).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StreamEvent {
    pub id:         String,
    pub run_id:     String,
    pub step:       i64,
    pub seq:        i64,
    pub event_type: String,
    pub payload:    String,
    pub timestamp:  String,
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum StreamControl {
    StreamEnd,
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum StreamEndReason {
    RunTerminal,
    RunUnavailableOnNode,
    AuthRevoked,
    StoreUnavailable,
    InconsistentRunState,
}

// ============================================================================
// UI types — what the webview receives
// ============================================================================

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum UiFrame {
    Event   { event: StreamEvent },
    Control {
        control: StreamControl,
        reason:  StreamEndReason,
        run_id:  String,
        #[serde(skip_serializing_if = "Option::is_none")]
        status:  Option<String>,
    },
    /// Rig-side failure; final (BL-266 T3, ruling O2).
    ClientError {
        reason:      ClientErrorReason,
        http_status: Option<u16>,
        code:        Option<String>,
        message:     String,
    },
    /// Liveness of the connection; not final (BL-266 T3, amendment A).
    ClientStatus { state: ClientStatusState },
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ClientErrorReason {
    Unauthorized,
    BadRequest,
    NotFound,
    Http,
    Protocol,
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ClientStatusState {
    Reconnecting,
    Connected,
}

#[derive(Debug, Clone, Serialize)]
pub struct RunStreamEmit {
    pub subscription_id: String,
    pub run_id:          String,
    pub frame:           UiFrame,
}

#[derive(Debug, Deserialize)]
pub struct RunStreamSubscribeRequest {
    pub subscription_id: String,
    pub run_id:          String,
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RunStreamMode {
    Stream,
    Poll,
}

#[derive(Debug, Serialize)]
pub struct RunStreamSubscribeResult {
    pub mode: RunStreamMode,
}

/// Splits a wire frame into what the webview sees and the cursor Rust keeps.
pub(crate) fn split(w: WireFrame) -> (UiFrame, Option<String>) {
    match w {
        WireFrame::Event { cursor, event } => (UiFrame::Event { event }, Some(cursor)),
        WireFrame::Control { control, reason, run_id, status } => {
            (UiFrame::Control { control, reason, run_id, status }, None)
        }
    }
}

fn client_error(reason: ClientErrorReason, http_status: Option<u16>, code: Option<String>, message: String) -> UiFrame {
    UiFrame::ClientError { reason, http_status, code, message }
}

// ============================================================================
// SSE parser
// ============================================================================

#[derive(Debug, PartialEq)]
pub(crate) enum SseItem {
    Message { id: Option<String>, data: String },
    Comment,
}

/// Reads the next SSE item. `Ok(None)` is end of stream; a message cut off by
/// EOF is discarded. I/O errors, including the read timeout, are returned.
pub(crate) fn next_item<R: BufRead>(r: &mut R, line: &mut String) -> io::Result<Option<SseItem>> {
    let mut id: Option<String> = None;
    let mut data: Option<String> = None;
    loop {
        line.clear();
        if r.read_line(line)? == 0 {
            return Ok(None);
        }
        let text = line.strip_suffix('\n').unwrap_or(line);
        let text = text.strip_suffix('\r').unwrap_or(text);

        if text.is_empty() {
            if let Some(data) = data.take() {
                return Ok(Some(SseItem::Message { id: id.take(), data }));
            }
            id = None;
            continue;
        }
        if text.starts_with(':') {
            // The heartbeat. A comment inside a partial message is skipped.
            if id.is_none() && data.is_none() {
                return Ok(Some(SseItem::Comment));
            }
            continue;
        }
        let (field, value) = match text.split_once(':') {
            Some((f, v)) => (f, v.strip_prefix(' ').unwrap_or(v)),
            None => (text, ""),
        };
        match field {
            "id" => id = Some(value.to_string()),
            "data" => match data.as_mut() {
                Some(d) => {
                    d.push('\n');
                    d.push_str(value);
                }
                None => data = Some(value.to_string()),
            },
            _ => {}
        }
    }
}

/// Parses one SSE message into a wire frame and checks its two cursor copies
/// (BL-266 T3, amendment B): an event frame's `id:` must be present and equal
/// to its JSON `cursor`; a control frame must carry no `id:`.
pub(crate) fn decode_message(id: Option<&str>, data: &str) -> Result<WireFrame, String> {
    let frame: WireFrame =
        serde_json::from_str(data).map_err(|e| format!("unparseable frame: {}", e))?;
    match (&frame, id) {
        (WireFrame::Event { cursor, .. }, Some(id)) if id == cursor => Ok(frame),
        (WireFrame::Event { .. }, None) => Err("event frame without an id: line".to_string()),
        (WireFrame::Event { cursor, .. }, Some(id)) => {
            Err(format!("event id {:?} differs from its cursor {:?}", id, cursor))
        }
        (WireFrame::Control { .. }, None) => Ok(frame),
        (WireFrame::Control { .. }, Some(_)) => Err("control frame carries an id: line".to_string()),
    }
}

// ============================================================================
// Outcome mapping (ruling 17, O3)
// ============================================================================

#[derive(Debug, PartialEq)]
pub(crate) enum Action {
    /// Reconnect after this delay, or after the computed backoff when `None`.
    Retry(Option<Duration>),
    /// End the subscription, emitting the frame first when there is one.
    Stop(Option<UiFrame>),
}

/// `None` means the response opens the stream.
pub(crate) fn classify_http(status: u16, retry_after: Option<&str>, body: &str) -> Option<Action> {
    if status == 200 {
        return None;
    }
    if status == 429 || status == 503 {
        return Some(Action::Retry(retry_after.and_then(parse_retry_after)));
    }
    if (500..=599).contains(&status) {
        return Some(Action::Retry(None));
    }
    let (code, message) = parse_error_envelope(body);
    let reason = match status {
        401 => ClientErrorReason::Unauthorized,
        400 => ClientErrorReason::BadRequest,
        404 => ClientErrorReason::NotFound,
        _ => ClientErrorReason::Http,
    };
    let message = message.unwrap_or_else(|| format!("HTTP {}", status));
    Some(Action::Stop(Some(client_error(reason, Some(status), code, message))))
}

/// What the thread does after forwarding a `stream_end` control frame.
pub(crate) fn classify_control(reason: StreamEndReason) -> Action {
    match reason {
        StreamEndReason::StoreUnavailable => Action::Retry(None),
        StreamEndReason::RunTerminal
        | StreamEndReason::RunUnavailableOnNode
        | StreamEndReason::AuthRevoked
        | StreamEndReason::InconsistentRunState => Action::Stop(None),
    }
}

#[derive(Debug)]
pub(crate) enum SessionEnd {
    /// The body ended without a `stream_end` frame.
    Eof,
    Io(io::Error),
    /// A `stream_end` frame, already forwarded.
    Control(StreamEndReason),
    Protocol(String),
    Cancelled,
    EmitFailed,
}

pub(crate) fn classify_session_end(end: SessionEnd) -> Action {
    match end {
        SessionEnd::Eof => Action::Retry(None),
        SessionEnd::Io(e) => {
            log::info!("[run_stream] read failed: {}", e);
            Action::Retry(None)
        }
        SessionEnd::Control(reason) => classify_control(reason),
        SessionEnd::Protocol(message) => {
            Action::Stop(Some(client_error(ClientErrorReason::Protocol, None, None, message)))
        }
        SessionEnd::Cancelled | SessionEnd::EmitFailed => Action::Stop(None),
    }
}

/// Whole seconds only; an HTTP-date or anything else falls back to the backoff.
pub(crate) fn parse_retry_after(value: &str) -> Option<Duration> {
    let v = value.trim();
    if v.is_empty() || !v.bytes().all(|b| b.is_ascii_digit()) {
        return None;
    }
    v.parse::<u64>().ok().map(Duration::from_secs)
}

fn parse_error_envelope(body: &str) -> (Option<String>, Option<String>) {
    let value: serde_json::Value = match serde_json::from_str(body) {
        Ok(v) => v,
        Err(_) => return (None, None),
    };
    let error = value.get("error");
    let field = |k: &str| error.and_then(|e| e.get(k)).and_then(|v| v.as_str()).map(str::to_string);
    (field("code"), field("message"))
}

// ============================================================================
// Backoff and liveness (ruling 17, amendment A)
// ============================================================================

const BACKOFF_SECS: [u64; 5] = [1, 2, 4, 8, 15];

pub(crate) fn base_delay(attempt: usize) -> Duration {
    Duration::from_secs(BACKOFF_SECS[attempt.min(BACKOFF_SECS.len() - 1)])
}

/// Adds `fraction` of `d`, with `fraction` clamped to 0–20 %.
pub(crate) fn with_jitter(d: Duration, fraction: f64) -> Duration {
    d.mul_f64(1.0 + fraction.clamp(0.0, 0.2))
}

/// A jitter fraction in 0–20 %, from `RandomState` so no dependency is added.
fn jitter_fraction() -> f64 {
    let mut h = RandomState::new().build_hasher();
    h.write_u64(0);
    (h.finish() % 10_001) as f64 / 10_000.0 * 0.2
}

/// Tracks backoff and the non-final `client_status` emissions.
///
/// An attempt is successful once it delivers a valid item — a frame or a
/// heartbeat comment — never merely on HTTP 200.
#[derive(Debug, Default)]
pub(crate) struct Liveness {
    backoff_attempt:    usize,
    failures:           u32,
    reconnecting_shown: bool,
    item_this_attempt:  bool,
}

impl Liveness {
    pub(crate) fn begin_attempt(&mut self) {
        self.item_this_attempt = false;
    }

    /// Returns `Connected` once, on the first valid item after `Reconnecting`.
    pub(crate) fn on_valid_item(&mut self) -> Option<ClientStatusState> {
        self.item_this_attempt = true;
        self.failures = 0;
        self.backoff_attempt = 0;
        if self.reconnecting_shown {
            self.reconnecting_shown = false;
            return Some(ClientStatusState::Connected);
        }
        None
    }

    /// Called before a retry. Returns `Reconnecting` once, after the second
    /// consecutive attempt that delivered no valid item.
    pub(crate) fn end_attempt(&mut self) -> Option<ClientStatusState> {
        if self.item_this_attempt {
            return None;
        }
        self.failures += 1;
        if self.failures >= 2 && !self.reconnecting_shown {
            self.reconnecting_shown = true;
            return Some(ClientStatusState::Reconnecting);
        }
        None
    }

    pub(crate) fn next_backoff(&mut self) -> Duration {
        let d = base_delay(self.backoff_attempt);
        self.backoff_attempt += 1;
        d
    }
}

// ============================================================================
// Session
// ============================================================================

pub(crate) struct SessionCtx {
    pub cancel: Arc<AtomicBool>,
    pub cursor: Arc<Mutex<Option<String>>>,
}

impl SessionCtx {
    fn cancelled(&self) -> bool {
        self.cancel.load(Ordering::SeqCst)
    }
}

/// Reads one HTTP 200 body to its end. Cancellation is checked after every
/// read, before every emit and before every cursor update (ruling 5); the
/// cursor advances only after its frame was emitted.
pub(crate) fn run_session<R, E>(reader: &mut R, ctx: &SessionCtx, live: &mut Liveness, emit: &mut E) -> SessionEnd
where
    R: BufRead,
    E: FnMut(UiFrame) -> Result<(), String>,
{
    let mut line = String::new();
    loop {
        let item = next_item(reader, &mut line);
        if ctx.cancelled() {
            return SessionEnd::Cancelled;
        }
        let (id, data) = match item {
            Err(e) => return SessionEnd::Io(e),
            Ok(None) => return SessionEnd::Eof,
            Ok(Some(SseItem::Comment)) => {
                if let Some(state) = live.on_valid_item() {
                    if let Some(end) = emit_checked(ctx, emit, UiFrame::ClientStatus { state }) {
                        return end;
                    }
                }
                continue;
            }
            Ok(Some(SseItem::Message { id, data })) => (id, data),
        };

        let frame = match decode_message(id.as_deref(), &data) {
            Ok(f) => f,
            Err(message) => return SessionEnd::Protocol(message),
        };
        let (ui, cursor) = split(frame);
        let control = match &ui {
            UiFrame::Control { reason, .. } => Some(*reason),
            _ => None,
        };
        if let Some(end) = emit_checked(ctx, emit, ui) {
            return end;
        }
        if let Some(cursor) = cursor {
            if ctx.cancelled() {
                return SessionEnd::Cancelled;
            }
            *lock(&ctx.cursor) = Some(cursor);
        }
        if let Some(state) = live.on_valid_item() {
            if let Some(end) = emit_checked(ctx, emit, UiFrame::ClientStatus { state }) {
                return end;
            }
        }
        if let Some(reason) = control {
            return SessionEnd::Control(reason);
        }
    }
}

fn emit_checked<E>(ctx: &SessionCtx, emit: &mut E, frame: UiFrame) -> Option<SessionEnd>
where
    E: FnMut(UiFrame) -> Result<(), String>,
{
    if ctx.cancelled() {
        return Some(SessionEnd::Cancelled);
    }
    match emit(frame) {
        Ok(()) => None,
        Err(e) => {
            log::warn!("[run_stream] emit failed: {}", e);
            Some(SessionEnd::EmitFailed)
        }
    }
}

// ============================================================================
// Thread
// ============================================================================

struct ThreadCtx {
    subscription_id: String,
    run_id:          String,
    url:             String,
    token:           String,
    session:         SessionCtx,
    subs:            SubMap,
}

pub(crate) fn stream_request(
    client: &reqwest::blocking::Client,
    url:    &str,
    token:  &str,
    cursor: Option<&str>,
) -> reqwest::blocking::RequestBuilder {
    let req = client
        .get(url)
        .header("Authorization", format!("Bearer {}", token))
        .header("Accept", "text/event-stream");
    match cursor {
        Some(c) => req.header("Last-Event-ID", c),
        None => req,
    }
}

/// Sleeps in 250 ms slices; `false` if cancelled meanwhile.
fn sleep_cancellable(d: Duration, cancel: &AtomicBool) -> bool {
    let slice = Duration::from_millis(250);
    let mut left = d;
    while !left.is_zero() {
        if cancel.load(Ordering::SeqCst) {
            return false;
        }
        let step = left.min(slice);
        std::thread::sleep(step);
        left -= step;
    }
    !cancel.load(Ordering::SeqCst)
}

fn set_status(subs: &SubMap, id: &str, own: &Arc<AtomicBool>, status: &str) {
    let mut map = lock(subs);
    if let Some(entry) = map.get_mut(id) {
        if Arc::ptr_eq(&entry.cancel, own) {
            entry.status = Some(status.to_string());
        }
    }
}

/// Removes the entry only if it is still this thread's own (ruling O4): the id
/// alone cannot tell a re-subscribe under the same id from the original.
pub(crate) fn remove_if_own(subs: &SubMap, id: &str, own: &Arc<AtomicBool>) {
    let mut map = lock(subs);
    let is_own = map.get(id).map(|e| Arc::ptr_eq(&e.cancel, own)).unwrap_or(false);
    if is_own {
        map.remove(id);
    }
}

pub(crate) fn unsubscribe_in(subs: &SubMap, id: &str) {
    if let Some(entry) = lock(subs).get_mut(id) {
        entry.cancel.store(true, Ordering::SeqCst);
        entry.active = false;
    }
}

fn stream_thread<E>(ctx: ThreadCtx, mut emit: E)
where
    E: FnMut(UiFrame) -> Result<(), String>,
{
    // 45 s is three 15 s server heartbeats (harness `playground-api.md` §3.5).
    // The blocking client applies it as a deadline on each body read.
    let client = match reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(45))
        .connect_timeout(Duration::from_secs(10))
        .build()
    {
        Ok(c) => c,
        Err(e) => {
            log::warn!("[run_stream] client build failed: {}", e);
            let _ = emit(client_error(ClientErrorReason::Http, None, None, format!("client build failed: {}", e)));
            remove_if_own(&ctx.subs, &ctx.subscription_id, &ctx.session.cancel);
            return;
        }
    };

    let own = ctx.session.cancel.clone();
    let mut live = Liveness::default();
    loop {
        if ctx.session.cancelled() {
            break;
        }
        set_status(&ctx.subs, &ctx.subscription_id, &own, "connecting");
        live.begin_attempt();
        let cursor = lock(&ctx.session.cursor).clone();
        let action = match stream_request(&client, &ctx.url, &ctx.token, cursor.as_deref()).send() {
            Err(e) => {
                log::info!("[run_stream] {} connect failed: {}", ctx.run_id, e);
                Action::Retry(None)
            }
            Ok(resp) => {
                let status = resp.status().as_u16();
                let retry_after = resp
                    .headers()
                    .get("Retry-After")
                    .and_then(|v| v.to_str().ok())
                    .map(str::to_string);
                if status == 200 {
                    set_status(&ctx.subs, &ctx.subscription_id, &own, "open");
                    let mut reader = BufReader::new(resp);
                    classify_session_end(run_session(&mut reader, &ctx.session, &mut live, &mut emit))
                } else {
                    let body = resp.text().unwrap_or_default();
                    classify_http(status, retry_after.as_deref(), &body).unwrap_or(Action::Stop(None))
                }
            }
        };

        match action {
            Action::Stop(frame) => {
                if let Some(frame) = frame {
                    if !ctx.session.cancelled() {
                        let _ = emit(frame);
                    }
                }
                break;
            }
            Action::Retry(delay) => {
                if let Some(state) = live.end_attempt() {
                    if ctx.session.cancelled() || emit(UiFrame::ClientStatus { state }).is_err() {
                        break;
                    }
                }
                let delay = delay.unwrap_or_else(|| with_jitter(live.next_backoff(), jitter_fraction()));
                set_status(&ctx.subs, &ctx.subscription_id, &own, "backoff");
                if !sleep_cancellable(delay, &own) {
                    break;
                }
            }
        }
    }
    remove_if_own(&ctx.subs, &ctx.subscription_id, &own);
}

// ============================================================================
// Commands
// ============================================================================

/// `Poll` when the API is not configured: the caller keeps SQLite polling (ruling 8).
pub(crate) fn resolve_mode(api_url: &Option<String>, api_token: &Option<String>) -> RunStreamMode {
    if api_url.is_some() && api_token.is_some() {
        RunStreamMode::Stream
    } else {
        RunStreamMode::Poll
    }
}

#[tauri::command]
pub fn run_stream_subscribe(
    app:        AppHandle,
    state:      State<'_, RunStreamState>,
    playground: State<'_, PlaygroundState>,
    request:    RunStreamSubscribeRequest,
) -> Result<RunStreamSubscribeResult, String> {
    if resolve_mode(&playground.api_url, &playground.api_token) == RunStreamMode::Poll {
        return Ok(RunStreamSubscribeResult { mode: RunStreamMode::Poll });
    }
    let (api_url, token) = require_connection(&playground)?;

    let cancel = Arc::new(AtomicBool::new(false));
    let cursor = Arc::new(Mutex::new(None));
    {
        let mut subs = lock(&state.subs);
        if subs.contains_key(&request.subscription_id) {
            return Err(format!("duplicate subscription_id {}", request.subscription_id));
        }
        subs.insert(
            request.subscription_id.clone(),
            RunStreamSub {
                subscription_id: request.subscription_id.clone(),
                run_id:          request.run_id.clone(),
                cancel:          cancel.clone(),
                active:          true,
                cursor:          cursor.clone(),
                status:          None,
            },
        );
    }

    let ctx = ThreadCtx {
        subscription_id: request.subscription_id.clone(),
        run_id:          request.run_id.clone(),
        url:             format!("{}/api/playground/runs/{}/events", api_url, request.run_id),
        token,
        session:         SessionCtx { cancel, cursor },
        subs:            state.subs.clone(),
    };
    let subscription_id = request.subscription_id;
    let run_id = request.run_id;
    std::thread::spawn(move || {
        stream_thread(ctx, move |frame| {
            let payload = RunStreamEmit {
                subscription_id: subscription_id.clone(),
                run_id:          run_id.clone(),
                frame,
            };
            app.emit(RUN_STREAM_EVENT, payload).map_err(|e| e.to_string())
        })
    });

    Ok(RunStreamSubscribeResult { mode: RunStreamMode::Stream })
}

/// Sets the subscription's cancel flag and returns; the thread notices at its
/// next checkpoint. An unknown id is not an error (ruling 5).
#[tauri::command]
pub fn run_stream_unsubscribe(
    state:           State<'_, RunStreamState>,
    subscription_id: String,
) -> Result<(), String> {
    unsubscribe_in(&state.subs, &subscription_id);
    Ok(())
}

// ============================================================================
// Tests
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;
    use crate::commands::harness::EventRow;
    use std::io::{Cursor, Read};

    fn items(input: &str) -> Vec<SseItem> {
        let mut r = Cursor::new(input.as_bytes().to_vec());
        let mut line = String::new();
        let mut out = Vec::new();
        while let Some(item) = next_item(&mut r, &mut line).unwrap() {
            out.push(item);
        }
        out
    }

    fn msg(id: Option<&str>, data: &str) -> SseItem {
        SseItem::Message { id: id.map(str::to_string), data: data.to_string() }
    }

    /// The `playground-api.md` §3.5 event example, verbatim.
    const EVENT_DATA: &str = r#"{"cursor":"v1:3","kind":"event","event":{"id":"evt_aBc1dE","timestamp":"2026-09-18T10:00:03.000000Z","seq":3,"step":2,"run_id":"run_aBc1dE","event_type":"observation","payload":"{\"n\":3}"}}"#;
    const CONTROL_DATA: &str = r#"{"control":"stream_end","reason":"run_terminal","status":"done","kind":"control","run_id":"run_aBc1dE"}"#;

    fn event_data(seq: i64) -> String {
        format!(
            r#"{{"cursor":"v1:{seq}","kind":"event","event":{{"id":"e{seq}","timestamp":"t","seq":{seq},"step":0,"run_id":"r","event_type":"observation","payload":"{{}}"}}}}"#
        )
    }

    fn sample_event() -> StreamEvent {
        StreamEvent {
            id: "e1".into(), run_id: "r".into(), step: 0, seq: 1,
            event_type: "observation".into(), payload: "{}".into(), timestamp: "t".into(),
        }
    }

    // ---- SSE parser -------------------------------------------------------

    #[test]
    fn sse_single_event_message() {
        assert_eq!(items("id: v1:3\ndata: {}\n\n"), vec![msg(Some("v1:3"), "{}")]);
    }

    #[test]
    fn sse_control_has_no_id() {
        assert_eq!(
            items("id: v1:3\ndata: a\n\ndata: b\n\n"),
            vec![msg(Some("v1:3"), "a"), msg(None, "b")]
        );
        // An id on a message with no data is dropped at its blank line.
        assert_eq!(items("id: 1\n\ndata: b\n\n"), vec![msg(None, "b")]);
    }

    #[test]
    fn sse_comment_is_comment() {
        assert_eq!(items(": ping\n\n"), vec![SseItem::Comment]);
    }

    /// Returns at most 1–3 bytes per `read()`.
    struct Dribble { data: Vec<u8>, pos: usize, n: usize }

    impl Read for Dribble {
        fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
            self.n = self.n % 3 + 1;
            let take = self.n.min(buf.len()).min(self.data.len() - self.pos);
            buf[..take].copy_from_slice(&self.data[self.pos..self.pos + take]);
            self.pos += take;
            Ok(take)
        }
    }

    #[test]
    fn sse_frame_spanning_reads() {
        let input = format!("id: v1:3\ndata: {}\n\n: ping\n\ndata: {}\n\n", EVENT_DATA, CONTROL_DATA);
        let mut r = BufReader::with_capacity(4, Dribble { data: input.clone().into_bytes(), pos: 0, n: 0 });
        let mut line = String::new();
        let mut got = Vec::new();
        while let Some(item) = next_item(&mut r, &mut line).unwrap() {
            got.push(item);
        }
        assert_eq!(got, items(&input));
        assert_eq!(got.len(), 3);
    }

    #[test]
    fn sse_split_frames_back_to_back() {
        assert_eq!(
            items("id: 1\ndata: a\n\nid: 2\ndata: b\n\n"),
            vec![msg(Some("1"), "a"), msg(Some("2"), "b")]
        );
    }

    #[test]
    fn sse_crlf_lines() {
        assert_eq!(items("id: 1\r\ndata: a\r\n\r\n"), items("id: 1\ndata: a\n\n"));
        assert_eq!(items(": ping\r\n\r\n"), vec![SseItem::Comment]);
    }

    #[test]
    fn sse_multi_data_joined() {
        assert_eq!(items("data: a\ndata: b\n\n"), vec![msg(None, "a\nb")]);
    }

    #[test]
    fn sse_eof_mid_message_discarded() {
        assert_eq!(items("id: 1\ndata: a\n"), vec![]);
        assert_eq!(items("data: a\n\nid: 2\ndata: b"), vec![msg(None, "a")]);
    }

    #[test]
    fn sse_unknown_fields_ignored() {
        assert_eq!(items("event: x\nretry: 5\nid: 1\ndata: a\n\n"), vec![msg(Some("1"), "a")]);
    }

    #[test]
    fn sse_no_space_after_colon() {
        assert_eq!(items("id:v1:1\ndata:{}\n\n"), vec![msg(Some("v1:1"), "{}")]);
    }

    // ---- Wire types -------------------------------------------------------

    #[test]
    fn wire_event_from_contract_example() {
        let f: WireFrame = serde_json::from_str(EVENT_DATA).unwrap();
        assert_eq!(
            f,
            WireFrame::Event {
                cursor: "v1:3".into(),
                event: StreamEvent {
                    id: "evt_aBc1dE".into(),
                    run_id: "run_aBc1dE".into(),
                    step: 2,
                    seq: 3,
                    event_type: "observation".into(),
                    payload: "{\"n\":3}".into(),
                    timestamp: "2026-09-18T10:00:03.000000Z".into(),
                },
            }
        );
    }

    #[test]
    fn wire_control_each_reason() {
        let reasons = [
            ("run_terminal", StreamEndReason::RunTerminal),
            ("run_unavailable_on_node", StreamEndReason::RunUnavailableOnNode),
            ("auth_revoked", StreamEndReason::AuthRevoked),
            ("store_unavailable", StreamEndReason::StoreUnavailable),
            ("inconsistent_run_state", StreamEndReason::InconsistentRunState),
        ];
        for (text, reason) in reasons {
            for status in [None, Some("done")] {
                let status_json = status.map(|s| format!(r#","status":"{}""#, s)).unwrap_or_default();
                let data = format!(r#"{{"kind":"control","control":"stream_end","reason":"{}","run_id":"r"{}}}"#, text, status_json);
                let f: WireFrame = serde_json::from_str(&data).unwrap();
                assert_eq!(
                    f,
                    WireFrame::Control {
                        control: StreamControl::StreamEnd,
                        reason,
                        run_id: "r".into(),
                        status: status.map(str::to_string),
                    }
                );
            }
        }
    }

    #[test]
    fn wire_unknown_reason_is_error() {
        let data = r#"{"kind":"control","control":"stream_end","reason":"gone_fishing","run_id":"r"}"#;
        assert!(serde_json::from_str::<WireFrame>(data).is_err());
        let data = r#"{"kind":"telemetry","run_id":"r"}"#;
        assert!(serde_json::from_str::<WireFrame>(data).is_err());
        assert!(decode_message(None, r#"{"kind":"control","control":"stream_end","reason":"gone_fishing","run_id":"r"}"#).is_err());
    }

    #[test]
    fn split_event_strips_cursor() {
        let (ui, cursor) = split(serde_json::from_str(EVENT_DATA).unwrap());
        assert_eq!(cursor.as_deref(), Some("v1:3"));
        match ui {
            UiFrame::Event { event } => assert_eq!(event.seq, 3),
            other => panic!("expected an event, got {:?}", other),
        }
        let (_, cursor) = split(serde_json::from_str(CONTROL_DATA).unwrap());
        assert_eq!(cursor, None);
    }

    fn all_keys(v: &serde_json::Value, out: &mut Vec<String>) {
        match v {
            serde_json::Value::Object(m) => {
                for (k, v) in m {
                    out.push(k.clone());
                    all_keys(v, out);
                }
            }
            serde_json::Value::Array(a) => a.iter().for_each(|v| all_keys(v, out)),
            _ => {}
        }
    }

    #[test]
    fn emit_payload_never_serialises_cursor() {
        let frames = vec![
            split(serde_json::from_str(EVENT_DATA).unwrap()).0,
            split(serde_json::from_str(CONTROL_DATA).unwrap()).0,
            client_error(ClientErrorReason::Protocol, Some(400), Some("invalid_cursor".into()), "m".into()),
            UiFrame::ClientStatus { state: ClientStatusState::Reconnecting },
        ];
        for frame in frames {
            let payload = RunStreamEmit { subscription_id: "s".into(), run_id: "r".into(), frame };
            let mut keys = Vec::new();
            all_keys(&serde_json::to_value(&payload).unwrap(), &mut keys);
            assert!(!keys.iter().any(|k| k == "cursor"), "cursor leaked: {:?}", keys);
        }
    }

    #[test]
    fn ui_control_omits_absent_status() {
        let (ui, _) = split(
            serde_json::from_str(r#"{"kind":"control","control":"stream_end","reason":"auth_revoked","run_id":"r"}"#).unwrap(),
        );
        assert_eq!(
            serde_json::to_value(&ui).unwrap(),
            serde_json::json!({"kind":"control","control":"stream_end","reason":"auth_revoked","run_id":"r"})
        );
    }

    #[test]
    fn ui_client_error_serialises() {
        let f = client_error(ClientErrorReason::BadRequest, Some(400), Some("invalid_cursor".into()), "bad".into());
        assert_eq!(
            serde_json::to_value(&f).unwrap(),
            serde_json::json!({"kind":"client_error","reason":"bad_request","http_status":400,"code":"invalid_cursor","message":"bad"})
        );
    }

    #[test]
    fn ui_client_status_serialises() {
        assert_eq!(
            serde_json::to_value(UiFrame::ClientStatus { state: ClientStatusState::Reconnecting }).unwrap(),
            serde_json::json!({"kind":"client_status","state":"reconnecting"})
        );
        assert_eq!(
            serde_json::to_value(UiFrame::ClientStatus { state: ClientStatusState::Connected }).unwrap(),
            serde_json::json!({"kind":"client_status","state":"connected"})
        );
    }

    fn key_set(v: serde_json::Value) -> Vec<String> {
        let mut keys: Vec<String> = v.as_object().unwrap().keys().cloned().collect();
        keys.sort();
        keys
    }

    #[test]
    fn stream_event_keys_match_event_row() {
        let row = EventRow {
            id: "e1".into(), run_id: "r".into(), step: 0, seq: 1,
            event_type: "observation".into(), payload: "{}".into(), timestamp: "t".into(),
        };
        assert_eq!(
            key_set(serde_json::to_value(sample_event()).unwrap()),
            key_set(serde_json::to_value(row).unwrap())
        );
    }

    // ---- Amendment B: the two cursor copies -------------------------------

    #[test]
    fn cursor_copies_matching_id_and_cursor_succeeds() {
        assert!(matches!(decode_message(Some("v1:3"), EVENT_DATA), Ok(WireFrame::Event { .. })));
        assert!(matches!(decode_message(None, CONTROL_DATA), Ok(WireFrame::Control { .. })));
    }

    #[test]
    fn cursor_copies_missing_event_id_fails() {
        assert!(decode_message(None, EVENT_DATA).is_err());
    }

    #[test]
    fn cursor_copies_mismatched_cursors_fail() {
        assert!(decode_message(Some("v1:4"), EVENT_DATA).is_err());
    }

    #[test]
    fn cursor_copies_control_frame_with_id_fails() {
        assert!(decode_message(Some("v1:3"), CONTROL_DATA).is_err());
    }

    #[test]
    fn cursor_mismatch_in_session_is_final_protocol_error() {
        let body = format!("id: v1:9\ndata: {}\n\n", EVENT_DATA);
        let (end, emitted, cursor) = session(&body, false);
        assert!(emitted.is_empty());
        assert_eq!(cursor, None);
        assert!(matches!(
            classify_session_end(end),
            Action::Stop(Some(UiFrame::ClientError { reason: ClientErrorReason::Protocol, .. }))
        ));
    }

    // ---- Outcome mapping --------------------------------------------------

    fn stop_reason(a: Option<Action>) -> (ClientErrorReason, Option<String>) {
        match a {
            Some(Action::Stop(Some(UiFrame::ClientError { reason, code, .. }))) => (reason, code),
            other => panic!("expected a client_error stop, got {:?}", other),
        }
    }

    #[test]
    fn classify_http_table() {
        let env = |c: &str| format!(r#"{{"error":{{"code":"{}","message":"m"}}}}"#, c);
        assert_eq!(classify_http(200, None, ""), None);
        assert_eq!(stop_reason(classify_http(401, None, &env("unauthorized"))).0, ClientErrorReason::Unauthorized);
        assert_eq!(
            stop_reason(classify_http(400, None, &env("invalid_cursor"))),
            (ClientErrorReason::BadRequest, Some("invalid_cursor".into()))
        );
        assert_eq!(stop_reason(classify_http(404, None, &env("not_found"))).0, ClientErrorReason::NotFound);
        assert_eq!(classify_http(503, Some("5"), ""), Some(Action::Retry(Some(Duration::from_secs(5)))));
        assert_eq!(classify_http(503, None, ""), Some(Action::Retry(None)));
        // O3: 429 honours Retry-After; other 5xx back off; other 4xx stop.
        assert_eq!(classify_http(429, Some("7"), ""), Some(Action::Retry(Some(Duration::from_secs(7)))));
        assert_eq!(classify_http(500, Some("7"), ""), Some(Action::Retry(None)));
        assert_eq!(classify_http(502, None, "<html>"), Some(Action::Retry(None)));
        assert_eq!(stop_reason(classify_http(403, None, "")).0, ClientErrorReason::Http);
        assert_eq!(stop_reason(classify_http(422, None, "")).0, ClientErrorReason::Http);
    }

    #[test]
    fn classify_control_table() {
        assert_eq!(classify_control(StreamEndReason::StoreUnavailable), Action::Retry(None));
        for r in [
            StreamEndReason::RunTerminal,
            StreamEndReason::RunUnavailableOnNode,
            StreamEndReason::AuthRevoked,
            StreamEndReason::InconsistentRunState,
        ] {
            assert_eq!(classify_control(r), Action::Stop(None), "{:?}", r);
        }
    }

    #[test]
    fn backoff_sequence_and_cap() {
        let mut live = Liveness::default();
        for expected in [1u64, 2, 4, 8, 15, 15, 15] {
            let d = live.next_backoff();
            assert_eq!(d, Duration::from_secs(expected));
            let j = with_jitter(d, jitter_fraction());
            assert!(j >= d && j <= d.mul_f64(1.2), "{:?} outside [{:?}, 1.2×]", j, d);
        }
        assert_eq!(with_jitter(Duration::from_secs(10), 5.0), Duration::from_secs(12));
    }

    #[test]
    fn backoff_resets_on_frame_and_comment() {
        let mut live = Liveness::default();
        live.next_backoff();
        live.next_backoff();
        live.on_valid_item();
        assert_eq!(live.next_backoff(), Duration::from_secs(1));

        let body = ": ping\n\n".to_string();
        let mut live = Liveness::default();
        live.next_backoff();
        live.next_backoff();
        let ctx = SessionCtx { cancel: Arc::new(AtomicBool::new(false)), cursor: Arc::new(Mutex::new(None)) };
        run_session(&mut Cursor::new(body.into_bytes()), &ctx, &mut live, &mut |_| Ok(()));
        assert_eq!(live.next_backoff(), Duration::from_secs(1));
    }

    #[test]
    fn retry_after_parse() {
        assert_eq!(parse_retry_after("5"), Some(Duration::from_secs(5)));
        assert_eq!(parse_retry_after(" 12 "), Some(Duration::from_secs(12)));
        assert_eq!(parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT"), None);
        assert_eq!(parse_retry_after("-1"), None);
        assert_eq!(parse_retry_after("1.5"), None);
        assert_eq!(parse_retry_after("+5"), None);
        assert_eq!(parse_retry_after(""), None);
    }

    // ---- Amendment A: client_status ---------------------------------------

    #[test]
    fn status_initial_success_emits_nothing() {
        let mut live = Liveness::default();
        live.begin_attempt();
        assert_eq!(live.on_valid_item(), None);
        assert_eq!(live.end_attempt(), None);
    }

    #[test]
    fn status_single_failure_emits_nothing() {
        let mut live = Liveness::default();
        live.begin_attempt();
        assert_eq!(live.end_attempt(), None);
        live.begin_attempt();
        assert_eq!(live.on_valid_item(), None);
    }

    #[test]
    fn status_reconnecting_once_after_second_failure() {
        let mut live = Liveness::default();
        live.begin_attempt();
        assert_eq!(live.end_attempt(), None);
        live.begin_attempt();
        assert_eq!(live.end_attempt(), Some(ClientStatusState::Reconnecting));
        live.begin_attempt();
        assert_eq!(live.end_attempt(), None);
        live.begin_attempt();
        assert_eq!(live.end_attempt(), None);
    }

    #[test]
    fn status_connected_once_after_first_valid_item() {
        let mut live = Liveness::default();
        for _ in 0..2 {
            live.begin_attempt();
            live.end_attempt();
        }
        live.begin_attempt();
        assert_eq!(live.on_valid_item(), Some(ClientStatusState::Connected));
        assert_eq!(live.on_valid_item(), None);
    }

    #[test]
    fn status_connected_emitted_after_the_item_in_session() {
        for body in [format!("id: v1:1\ndata: {}\n\n", event_data(1)), ": ping\n\n".to_string()] {
            let mut live = Liveness::default();
            for _ in 0..2 {
                live.begin_attempt();
                live.end_attempt();
            }
            live.begin_attempt();
            let ctx = SessionCtx { cancel: Arc::new(AtomicBool::new(false)), cursor: Arc::new(Mutex::new(None)) };
            let mut emitted = Vec::new();
            run_session(&mut Cursor::new(body.into_bytes()), &ctx, &mut live, &mut |f| {
                emitted.push(f);
                Ok(())
            });
            let last = emitted.last().cloned();
            assert_eq!(last, Some(UiFrame::ClientStatus { state: ClientStatusState::Connected }));
            assert_eq!(emitted.iter().filter(|f| matches!(f, UiFrame::ClientStatus { .. })).count(), 1);
        }
    }

    #[test]
    fn status_http_200_with_dropped_body_is_not_connected() {
        let mut live = Liveness::default();
        for _ in 0..2 {
            live.begin_attempt();
            live.end_attempt();
        }
        // HTTP 200, then the body ends before any item.
        live.begin_attempt();
        let ctx = SessionCtx { cancel: Arc::new(AtomicBool::new(false)), cursor: Arc::new(Mutex::new(None)) };
        let mut emitted = Vec::new();
        let end = run_session(&mut Cursor::new(Vec::new()), &ctx, &mut live, &mut |f| {
            emitted.push(f);
            Ok(())
        });
        assert!(matches!(end, SessionEnd::Eof));
        assert!(emitted.is_empty());
        assert_eq!(live.end_attempt(), None);
        // Still reconnecting: the next real item is what reports `connected`.
        live.begin_attempt();
        assert_eq!(live.on_valid_item(), Some(ClientStatusState::Connected));
    }

    // ---- Session and thread state ------------------------------------------

    fn session(body: &str, cancel_after_first: bool) -> (SessionEnd, Vec<UiFrame>, Option<String>) {
        let ctx = SessionCtx { cancel: Arc::new(AtomicBool::new(false)), cursor: Arc::new(Mutex::new(None)) };
        let cancel = ctx.cancel.clone();
        let mut emitted = Vec::new();
        let mut live = Liveness::default();
        let end = run_session(&mut Cursor::new(body.as_bytes().to_vec()), &ctx, &mut live, &mut |f| {
            emitted.push(f);
            if cancel_after_first {
                cancel.store(true, Ordering::SeqCst);
            }
            Ok(())
        });
        let cursor = lock(&ctx.cursor).clone();
        (end, emitted, cursor)
    }

    #[test]
    fn run_session_respects_cancel() {
        let body = format!("id: v1:1\ndata: {}\n\nid: v1:2\ndata: {}\n\n", event_data(1), event_data(2));
        let (end, emitted, cursor) = session(&body, true);
        assert!(matches!(end, SessionEnd::Cancelled));
        assert_eq!(emitted.len(), 1);
        // Cancelled by the emit itself: the cursor checkpoint stops the update.
        assert_eq!(cursor, None);
    }

    /// Sets `cancel` on its first read, i.e. while `next_item` is blocked.
    struct CancelOnRead { inner: Cursor<Vec<u8>>, cancel: Arc<AtomicBool> }

    impl Read for CancelOnRead {
        fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
            self.cancel.store(true, Ordering::SeqCst);
            self.inner.read(buf)
        }
    }

    #[test]
    fn run_session_checks_cancel_after_read() {
        // A bad frame read while cancelled ends as Cancelled, not as a protocol error.
        let ctx = SessionCtx { cancel: Arc::new(AtomicBool::new(false)), cursor: Arc::new(Mutex::new(None)) };
        let mut r = BufReader::new(CancelOnRead { inner: Cursor::new(b"data: {not json\n\n".to_vec()), cancel: ctx.cancel.clone() });
        let end = run_session(&mut r, &ctx, &mut Liveness::default(), &mut |_| Ok(()));
        assert!(matches!(end, SessionEnd::Cancelled), "{:?}", end);
    }

    #[test]
    fn run_session_checks_cancel_before_each_emit() {
        // After `reconnecting`, a control frame is followed by `connected`; a
        // cancel set by the first emit must stop the second.
        let mut live = Liveness::default();
        for _ in 0..2 {
            live.begin_attempt();
            live.end_attempt();
        }
        live.begin_attempt();
        let ctx = SessionCtx { cancel: Arc::new(AtomicBool::new(false)), cursor: Arc::new(Mutex::new(None)) };
        let cancel = ctx.cancel.clone();
        let body = format!("data: {}\n\n", CONTROL_DATA);
        let mut emitted = Vec::new();
        let end = run_session(&mut Cursor::new(body.into_bytes()), &ctx, &mut live, &mut |f| {
            emitted.push(f);
            cancel.store(true, Ordering::SeqCst);
            Ok(())
        });
        assert!(matches!(end, SessionEnd::Cancelled), "{:?}", end);
        assert_eq!(emitted.len(), 1);
    }

    #[test]
    fn run_session_cursor_advances_after_emit() {
        let body = format!(
            "id: v1:1\ndata: {}\n\n: ping\n\nid: v1:2\ndata: {}\n\ndata: {}\n\n",
            event_data(1),
            event_data(2),
            CONTROL_DATA
        );
        let (end, emitted, cursor) = session(&body, false);
        assert!(matches!(end, SessionEnd::Control(StreamEndReason::RunTerminal)));
        assert_eq!(emitted.len(), 3);
        assert_eq!(cursor.as_deref(), Some("v1:2"));
    }

    #[test]
    fn run_session_emit_error_does_not_advance_cursor() {
        let ctx = SessionCtx { cancel: Arc::new(AtomicBool::new(false)), cursor: Arc::new(Mutex::new(None)) };
        let body = format!("id: v1:1\ndata: {}\n\n", event_data(1));
        let end = run_session(&mut Cursor::new(body.into_bytes()), &ctx, &mut Liveness::default(), &mut |_| {
            Err("webview gone".to_string())
        });
        assert!(matches!(end, SessionEnd::EmitFailed));
        assert_eq!(*lock(&ctx.cursor), None);
    }

    fn entry(id: &str, cancel: &Arc<AtomicBool>) -> RunStreamSub {
        RunStreamSub {
            subscription_id: id.into(),
            run_id: "r".into(),
            cancel: cancel.clone(),
            active: true,
            cursor: Arc::new(Mutex::new(None)),
            status: None,
        }
    }

    #[test]
    fn exit_removes_only_own_entry() {
        let subs: SubMap = Arc::new(Mutex::new(HashMap::new()));
        let old = Arc::new(AtomicBool::new(false));
        lock(&subs).insert("x".into(), entry("x", &old));
        unsubscribe_in(&subs, "x");
        assert!(old.load(Ordering::SeqCst));
        // Re-inserted under the same id before the old thread exits.
        let new = Arc::new(AtomicBool::new(false));
        lock(&subs).insert("x".into(), entry("x", &new));
        remove_if_own(&subs, "x", &old);
        assert!(lock(&subs).get("x").map(|e| Arc::ptr_eq(&e.cancel, &new)).unwrap_or(false));
        remove_if_own(&subs, "x", &new);
        assert!(lock(&subs).is_empty());
    }

    #[test]
    fn unsubscribe_unknown_is_ok_and_nonblocking() {
        let subs: SubMap = Arc::new(Mutex::new(HashMap::new()));
        unsubscribe_in(&subs, "nope");
        assert!(lock(&subs).is_empty());
        let c = Arc::new(AtomicBool::new(false));
        lock(&subs).insert("y".into(), entry("y", &c));
        unsubscribe_in(&subs, "y");
        let map = lock(&subs);
        let e = map.get("y").unwrap();
        assert!(!e.active);
        assert!(e.cancel.load(Ordering::SeqCst));
    }

    #[test]
    fn subscribe_unconfigured_returns_poll() {
        let some = Some("x".to_string());
        assert_eq!(resolve_mode(&None, &None), RunStreamMode::Poll);
        assert_eq!(resolve_mode(&some, &None), RunStreamMode::Poll);
        assert_eq!(resolve_mode(&None, &some), RunStreamMode::Poll);
        assert_eq!(resolve_mode(&some, &some), RunStreamMode::Stream);
        assert_eq!(
            serde_json::to_value(RunStreamSubscribeResult { mode: RunStreamMode::Poll }).unwrap(),
            serde_json::json!({"mode":"poll"})
        );
    }

    #[test]
    fn request_sets_last_event_id_only_with_cursor() {
        let client = reqwest::blocking::Client::new();
        let url = "http://127.0.0.1:1/api/playground/runs/r/events";
        let without = stream_request(&client, url, "tok", None).build().unwrap();
        assert!(without.headers().get("Last-Event-ID").is_none());
        assert_eq!(without.headers().get("Authorization").unwrap(), "Bearer tok");
        assert_eq!(without.headers().get("Accept").unwrap(), "text/event-stream");
        let with = stream_request(&client, url, "tok", Some("v1:7")).build().unwrap();
        assert_eq!(with.headers().get("Last-Event-ID").unwrap(), "v1:7");
    }
}
