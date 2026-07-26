# BL-032 scout — WAL journal-mode behaviour

**Read-only investigation. No code changed.** Sync: harness `f79365a`, agents `e6377cc`, both
`origin/main`, both trees clean at start. Date: 2026-07-26.

Feeds the BL-032 decision (WAL made deterministic via connection lifecycle, **or**
opportunistic-WAL ratified permanent) and its three follow-ups — (a) `-wal` growth, (b) dirty-`-wal`
recovery under a read-only connection, (c) observability. **This memo does not adjudicate.** It
records evidence, with captured output, and names the two defects found on the way without touching
either.

Every `file:line` below was read first-hand at HEAD. Where a claim rests on inference rather than a
line read, it says so.

## Findings, shortest form

1. **Opportunistic WAL is being achieved, robustly — cadence is the wrong variable.** A
   delete-mode store with the real schema and 902 runs converted **70/70** across every cadence
   tried, including saturation by three hammering readers that completed **311,040** reads (§5.3).
   Short drained reads cannot block the conversion at any rate; only a *held* read snapshot can.
2. **But a held snapshot does not leave the store benignly in `delete` — it fails the harness
   boot, 10/10.** `store.ex:582`'s `:ok =` turns a refused conversion into a `MatchError` in
   `Store.init/1` → `failed to start child: Aetheris.Store` → the application does not start
   (§5.3 Arm E, §7a). The pragma is asserted, not opportunistic. An already-`wal` store is immune
   (Arm F), so the live store is not exposed; a fresh/`delete`-mode store is.
3. **Follow-up (a) is real but conditioned on that same held snapshot, not on Rig.** Polling:
   `-wal` plateaus at 1,007 pages with the main db growing. Held snapshot: 12,165 pages with the
   main db never advancing (§5.4). Rig holds no snapshot (§4).
4. **Follow-up (b) as stated did not reproduce.** A read-only connection recovered a 4.1 MB dirty
   `-wal` twice; it fails only when `-shm`/directory writes are denied (§6).
5. **Follow-up (c) confirmed** — the pragma's result row is discarded by `execute/2` and nothing
   logs, tests, or asserts the mode (§1).
6. **Two premises need correcting before BL-032 is written against them**: t4's "under continuous
   read-hammering it stays `delete`", and the ticket's "Rig polls at the ~200 ms floor" (it polls at
   2 s; the 200 ms is the harness CLI's own `await_run`) — §8, §5.1.

---

## 1. `Store.init/1` pragma sequence at HEAD — and the discarded result

`../aetheris/lib/aetheris/store.ex:562-589`, verbatim:

```elixir
  def init(_opts) do
    db_path = Application.fetch_env!(:aetheris, :db_path)
    :ok = File.mkdir_p!(Path.dirname(db_path))

    case Exqlite.Sqlite3.open(db_path) do
      {:ok, conn} ->
        # BL-007 t4. SQLite locks are per-STATEMENT, not per-connection, so contention
        # between a harness write and Rig's read-only handle is a timing race against
        # whatever Rig read is in flight — intermittent, not a held-connection block.
        # `busy_timeout` is load-bearing: a write that collides with an in-flight reader
        # waits (up to 5s) instead of erroring immediately, and `run_stmt/3` handles the
        # residual `:busy` so a collision degrades gracefully instead of crashing the
        # singleton Store. It is set FIRST so it also bounds the WAL-conversion attempt
        # below. `journal_mode=WAL` is opportunistic: it converts only when it can grab
        # the database at an idle instant (a reader in flight keeps the file in delete
        # mode), and when it does convert it removes reader/writer contention entirely —
        # worth keeping, but the fix rests on busy_timeout + `:busy` handling, not on WAL.
        :ok = Exqlite.Sqlite3.execute(conn, "PRAGMA busy_timeout=5000")
        :ok = Exqlite.Sqlite3.execute(conn, "PRAGMA journal_mode=WAL")
        :ok = create_tables(conn)
        {:ok, %{conn: conn}}

      {:error, reason} ->
        {:stop, reason}
    end
  end
```

Order confirmed: `busy_timeout=5000` (`:581`) **then** `journal_mode=WAL` (`:582`), as t4's r4
disposition describes.

**The result is discarded — follow-up (c) is a real gap at HEAD.** `PRAGMA journal_mode=WAL`
answers with a one-row result set carrying the *resulting* mode (`wal`, or `delete` if the
conversion could not be made). Line `:582` uses `execute/2`, whose contract returns no rows —
`../aetheris/deps/exqlite/lib/exqlite/sqlite3.ex:106-107`:

```elixir
  @spec execute(db(), String.t()) :: :ok | {:error, reason()}
  def execute(conn, sql), do: Sqlite3NIF.execute(conn, sql)
```

So the `:ok =` match asserts only that the statement *ran*, never that the mode changed. No
`prepare`+`step` path is used for either pragma; the only `prepare` sites in `store.ex` are
`:1749` (`execute_stmt`) and `:1772` (`fetch_rows`), neither touching journal mode.

Complete grep, whole harness repo, `--include=*.ex --include=*.exs --include=*.rs`:

```
$ grep -rn "journal_mode\|busy_timeout" ... | grep -v _build/ | grep -v /target/
lib/aetheris/store.ex:573:        # `busy_timeout` is load-bearing: a write that collides with an in-flight reader
lib/aetheris/store.ex:577:        # below. `journal_mode=WAL` is opportunistic: it converts only when it can grab
lib/aetheris/store.ex:580:        # worth keeping, but the fix rests on busy_timeout + `:busy` handling, not on WAL.
lib/aetheris/store.ex:581:        :ok = Exqlite.Sqlite3.execute(conn, "PRAGMA busy_timeout=5000")
lib/aetheris/store.ex:582:        :ok = Exqlite.Sqlite3.execute(conn, "PRAGMA journal_mode=WAL")
lib/aetheris/store.ex:1763:      # (BL-007 t4). With busy_timeout set this is now rare, but surface it as a normal
```

Six hits: four comment lines and the two pragma calls. **No log line, no test, no `doctor` check
asserts the mode in effect anywhere in the harness.** (`cli/commands/doctor.ex:46-54` only does
`File.exists?` — it opens no connection.) A silent failure-to-convert is currently undetectable
from inside the harness, which is exactly what (c) says.

---

## 2. Live journal mode of the real dev store

Probed read-only — `-readonly` cannot change journal mode, so the probe cannot convert what it
measures:

```
$ cd ~/sandbox/elixirws/aetheris
$ sqlite3 -readonly priv/aetheris.db "PRAGMA journal_mode; PRAGMA busy_timeout; PRAGMA wal_autocheckpoint; PRAGMA page_size;"
wal
0
1000
4096
--- exit 0 ---
```

Raw sidecar listing, before and after the probe:

```
$ ls -la priv/aetheris.db*
-rw-r--r-- 1 it it 23552000 Jul 26 15:28 priv/aetheris.db
-rw-r--r-- 1 it it    32768 Jul 26 17:52 priv/aetheris.db-shm
-rw-r--r-- 1 it it   593312 Jul 26 16:09 priv/aetheris.db-wal
   (after)
-rw-r--r-- 1 it it 23552000 Jul 26 15:28 priv/aetheris.db
-rw-r--r-- 1 it it    32768 Jul 26 19:00 priv/aetheris.db-shm
-rw-r--r-- 1 it it   593312 Jul 26 16:09 priv/aetheris.db-wal
```

Findings:

- **The live dev store is `wal`, not `delete`.** Both sidecars exist and the mode is persistent in
  the db header, so this is the steady state, not an artifact of the probe.
- **`-wal` is 593,312 B ≈ 145 pages at the file's 4096-byte page size, against
  `wal_autocheckpoint=1000` (SQLite's default, never overridden).** It is an order of magnitude
  below the checkpoint threshold: **checkpointing is working, and `-wal` is not growing unbounded.**
  This is the first direct evidence on follow-up (a), and it points the same way as §4.
- `busy_timeout` reads 0 because it is per-connection and this is a fresh probe connection — not a
  statement about the harness's connection, which sets 5000 (§1).
- The probe updated the `-shm` mtime (17:52 → 19:00). That is the shared-memory index being
  touched by a reader, not a write to the database; `aetheris.db` and `-wal` are byte-identical and
  mtime-identical throughout this session (re-verified at the end, under **Gates**).

---

## 3. Connection topology

### Harness side — one read-write connection *per OS process*, not one overall

Complete grep for connection opens across `lib/` (excluding `_build`/`deps`) returns a single site:
`lib/aetheris/store.ex:568` (`Exqlite.Sqlite3.open(db_path)`).

Within one BEAM instance that is one connection, serialized:

- singleton, globally named — `store.ex:65-67` (`GenServer.start_link(..., name: __MODULE__)`);
- state holds exactly one handle — `store.ex:26` (`@type state :: %{conn: Exqlite.Sqlite3.db()}`),
  built at `:584`;
- every read and write is a synchronous `handle_call` over that handle (e.g. `store.ex:592-594`);
  there are **no** `handle_cast`/`handle_info` clauses in `store.ex`, and no pool anywhere
  (`mix.exs:26` is raw `{:exqlite, "~> 0.27"}`; no Ecto, no DBConnection);
- `AgentTree.Store`, `Orb.Store`, `Skill.Store` are `defdelegate` façades to `Aetheris.Store`, and
  `Eval.Store` is a GenServer with empty state (`eval/store.ex:161-162`) — **none is a second
  connection**. `Sweep` holds none either; it calls `Store.*`.

**Across OS processes there are N read-write connections, one per BEAM.** `mix.exs:12`
(`escript: [main_module: Aetheris.CLI]`) and `mix.exs:20` (`mod: {Aetheris.Application, []}`) mean
every `mix aetheris` / escript invocation boots `Aetheris.Application`, which starts
`Aetheris.Store` (`application.ex:40`) → its own `open/1` at `store.ex:568` → **its own re-run of
both pragmas.** Concurrent `run`/`fork` CLI processes are therefore independent writers on one
file. This matters twice below (§5's convergence argument, and §6's cross-process reader).

`db_path` is `Application.fetch_env!(:aetheris, :db_path)` (`store.ex:565`), configured as the
relative `"priv/aetheris.db"` at `config/config.exs:4`. **`config/test.exs:3` sets `:memory:`** —
so the test suite never exercises WAL, sidecars, or file-level contention at all. No gate covers
any of this.

### Rig side — one long-lived read-only connection, confirmed against the code

`rig/CLAUDE.md` says the connection is opened read-only at startup in `HarnessState`. Confirmed at
HEAD, and it is **one long-lived reader, not per-call.**

`rig/src-tauri/src/lib.rs:16-19`:

```rust
pub struct HarnessState {
    pub conn: Option<Arc<Mutex<rusqlite::Connection>>>,
    pub path: Option<String>,
}
```

Opened once inside the Tauri `setup` hook — `rig/src-tauri/src/lib.rs:146-173`:

```rust
      // Open harness DB read-only if AETHERIS_DB_PATH is set
      let harness_state = match std::env::var("AETHERIS_DB_PATH") {
        Ok(path) => {
          match rusqlite::Connection::open_with_flags(
            &path,
            rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY
              | rusqlite::OpenFlags::SQLITE_OPEN_NO_MUTEX,
          ) {
```

…then `app.manage(harness_state);` at `:173`, i.e. held in managed state for the app's whole life.
`get_harness_conn` opens nothing — it only locks the existing connection
(`rig/src-tauri/src/commands/harness.rs:5-14`), and the guard drops at the end of each command, so
all harness commands serialize on one connection. Callers: `harness.rs:30,140,247,294`,
`usage.rs:35`.

Two details `rig/CLAUDE.md` does not record, both relevant here:

- the flag set is `SQLITE_OPEN_READ_ONLY | **SQLITE_OPEN_NO_MUTEX**` — correctness rests on the
  Rust `Mutex`, not SQLite's;
- **Rig issues no `PRAGMA` on this connection at all** — repo-wide grep for
  `pragma|busy_timeout|journal_mode` in `rig/src-tauri/src` returns only the `SQLITE_OPEN` matches.
  So Rig's `busy_timeout` is **0**: a contended read fails immediately with no retry. Bears on (b).

Rig's other connections are DuckDB, not SQLite, and irrelevant to `aetheris.db`: the app's own
read-write `data.db` (`rig/src-tauri/src/db/mod.rs:24-33`) and the read-only provenance corpus
(`lib.rs:119-144`). The only other reader of `aetheris.db` in either repo is transient:
`scripts/drift_check.py:511-513` (`file:{db_path}?mode=ro`).

---

## 4. Read-transaction shape — follow-up (a)'s premise does not hold

Follow-up (a) is conditioned on Rig "holding a long read snapshot", which is what blocks WAL
checkpointing. **It does not hold one.** Rig holds a long-lived *connection*; every *read* on it is
short and fully drained inside the one command call.

`harness_get_events` — `rig/src-tauri/src/commands/harness.rs:242-273`:

```rust
    let mut stmt = conn.prepare(sql).map_err(|e| format!("prepare error: {}", e))?;
    let rows = stmt
        .query_map(params![run_id], |row| { ... })
        .map_err(|e| format!("query error: {}", e))?;

    rows.collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("row error: {}", e))
```

One statement, drained into a `Vec` before returning; no cursor is handed to the frontend, so the
implicit read transaction lives only for that drain. `harness_get_run` (`harness.rs:289-320`) is a
single `conn.query_row` (`:309`). `harness_connection_status` is a single `query_row`
(`harness.rs:32-34`).

The **one** explicit transaction is `list_runs` — `harness.rs:186-224`:

```rust
    let tx = conn
        .unchecked_transaction()
        .map_err(|e| format!("read transaction error: {}", e))?;
```

It spans exactly two statements (the `LIMIT`ed row query and the `COUNT(*)` at `:220-222`) so the
badge describes the same snapshot as the rows, is never committed, and drops — implicit rollback —
at the end of `list_runs` (`:224-225`). Bounded by one command call; **not** held across polls.
`usage_stats_load` (`rig/src-tauri/src/commands/usage.rs:35-119`) issues four bare statements under
no transaction at all.

On the harness side there are **no explicit transactions anywhere**: case-insensitive grep of
`store.ex` for `BEGIN|COMMIT|ROLLBACK|SAVEPOINT|transaction` returns zero SQL hits (the
`checkpoint` matches at `store.ex:47,274-325` are the application-level run-checkpoint feature,
unrelated to WAL checkpointing). Every write is one autocommit statement — `execute_stmt/3`,
`store.ex:1748-1753` — prepared, stepped once, released. And there is **no
`PRAGMA wal_checkpoint`/`wal_autocheckpoint` call anywhere in either repo**, so `-wal` truncation
is entirely SQLite's default autocheckpoint.

**Consequence for (a):** no participant holds a snapshot that could pin the `-wal`, which is
consistent with §2's measured 145-page `-wal` on a 902-run / 20,834-event store, and with §5 Arm C.
Under the actual access pattern (a) is a non-hazard. It would become one only if a future consumer
held a read transaction open across polls — the `list_runs` pattern generalized, which is the thing
to watch rather than the thing observed.

---

## 5. Realistic fork-poll cadence vs. continuous hammering — the crux

### 5.1 First, a correction to the premise

The ticket asks about "TrajectoryView's BL-005 events-fallback polling at the ~200 ms floor". **At
HEAD there is no 200 ms anywhere in `rig/src`, and no floor or clamp.** `useRunEvents` invokes
`harness_get_events` (`rig/src/hooks/useHarness.ts:96`) on a fixed 2 s interval —
`useHarness.ts:127-132`:

```ts
  // Interval-based polling
  useEffect(() => {
    if (!activelyPolling || !runId) return;
    const id = setInterval(fetch, 2000);
    return () => clearInterval(id);
  }, [activelyPolling, runId, fetch]);
```

`useRunDetail` polls `harness_get_run` on the same 2 s cadence (`useHarness.ts:175,211`; its own
comment at `:207-208` says "Same 2s cadence as useRunEvents"). The fallback engages only after
`trajectory_load` has failed (`TrajectoryView.tsx:238-239`), and then runs both pollers — so a live
run in fallback issues **two short commands every 2 s**, each re-materializing the run's whole
event list (no `seq >` watermark in the SQL, `harness.rs:249-254`).

The 200 ms is real, but it belongs to the **harness CLI**, not Rig:
`../aetheris/lib/aetheris/cli/commands/run_helpers.ex:10` — `@poll_interval_ms 200`, slept at
`:144`, `:148`, `:157` inside `await_run`'s inactivity loop; the same constant appears at
`cli/commands/run.ex:19,:130`. Two consequences, and they pull in opposite directions:

- **Within one CLI process, that poll cannot contend with that process's own writes** — both go
  through the one serialized `Store` GenServer connection (§3).
- **Across concurrent CLI processes it is a genuine 200 ms cross-process reader**, because each
  process has its own read-write connection (§3). In the BL-030 fork pattern Rig spawns fork CLI
  children, so more than one harness process on the file is the normal case, not the exotic one.

So both cadences are live, from different sources. Both were run below, labelled, and neither is
allowed to stand in for the other.

### 5.2 Method

Every arm ran against **scratch copies**; `priv/aetheris.db` was never opened writable, moved, or
modified (**Gates** re-verifies). The seed is a consistent read-only backup of the real store,
flipped to `delete`:

```
$ sqlite3 -readonly priv/aetheris.db ".backup $S/seed_base.db"     # exit 0
$ sqlite3 $S/seed_base.db "PRAGMA journal_mode; SELECT COUNT(*) FROM runs; SELECT COUNT(*) FROM events;"
wal
902
20834
$ sqlite3 $S/seed_base.db "PRAGMA journal_mode=DELETE;"   ->  delete
$ sqlite3 -readonly $S/seed_base.db "PRAGMA journal_mode;" ->  delete
```

The db under test therefore carries the **real schema and real volume** (902 runs, 20,834 events),
in `delete` mode. A brand-new empty file would convert trivially — no other connection can hold
it — so testing only that would be vacuous; the case that can actually fail is an existing
delete-mode store with a reader attached.

Each trial drives the **real** `Store.init/1` (real Exqlite, real pragma order, real
`create_tables`, real boot sweep) rather than a hand-rolled imitation of the conversion, by
redirecting `db_path` without touching `config/`:

```
mix run --no-start boot.exs <abs_db_path> [hold_ms] [writes]
```

`boot.exs` **aborts with exit 9 if `:aetheris` is already started** — if `--no-start` ever failed,
the app would have opened the real store read-write, and the run must not proceed. It then
`put_env`s the scratch path, `ensure_all_started`s, and reads the mode back with `prepare` + `step`
— i.e. the observation the harness itself does not make (§1).

The reader is Rig-shaped: one `mode=ro` connection held for the process's whole life, issuing the
**exact SQL of `harness_get_events`** (`harness.rs:249-254`) once per tick and draining it with
`fetchall()`, with `busy_timeout=0` to match Rig (§3).

Per trial: reset the db to `delete` → **verify it reads `delete`, abort the arm if not** → attach
readers → wait 0.6 s → boot the harness → read the mode → tear readers down.

*Why this cannot pass vacuously:* the pre-boot assertion means a `wal` reading can only have been
produced by the boot under test; the probe is known to be able to report `delete`, because it does
so at the start of every trial; a negative control ran first (boot with **no** readers → converted),
so the arms measure interference rather than the mechanism's existence; and — the strongest form —
**Arm E does produce a non-`wal` outcome under this exact rig**, so an all-`wal` column is a
falsifiable result, not an unfalsifiable one.

### 5.3 Results

Six arms. `pre` is the verified pre-boot mode; `post_init` is the mode read back inside the booted
harness; `readers ok/locked` is the aggregate count of completed / `database is locked` reads
across the whole arm, so reader engagement is a measured number rather than an assumption.

| arm | reader shape | cadence | readers | reader `busy_timeout` | pre | trials | → `wal` | → `delete` | boot failed | readers ok / locked |
|---|---|---|---|---|---|---|---|---|---|---|
| **A1** | short drained reads (Rig-shaped) | 2000 ms | 1 | 0 (Rig's) | delete | 20 | **20** | 0 | 0 | 20 / 0 |
| **A2** | short drained reads | 200 ms | 1 | 0 | delete | 20 | **20** | 0 | 0 | 141 / 0 |
| **B** | short drained reads, saturated | none (hammer) | 3 | 0 (Rig's) | delete | 20 | **20** | 0 | 0 | **311,040** / 145,817 |
| **B2** | short drained reads, saturated | none (hammer) | 3 | 5000 | delete | 10 | **10** | 0 | 0 | 146,709 / 0 |
| **E** | **held** read snapshot | n/a | 1 | 0 | delete | 10 | 0 | 0 | **10** | 0 / 0 |
| **F** | **held** read snapshot | n/a | 1 | 0 | **wal** | 5 | **5** | 0 | 0 | 0 / 0 |

**A1/A2 — the realistic cadences convert, 40/40.** Every trial: `pre=delete post_init=wal
post_exit=wal boot_ok=1`, boot elapsed ~1.2 s. Honest caveat on their strength: the conversion
window is only ~1.2 s wide, so a 2 s-cadence reader issues about **one** read during it (ok=20 over
20 trials) and a 200 ms reader about seven (ok=141). These arms show the realistic case succeeding;
they are not by themselves a strong test of interference. That is what B is for.

**B — saturation does not prevent conversion either, 20/20.** Three hammering readers completed
**311,040** reads and were refused **145,817** times with `database is locked` during the arm, so
the contention was real and heavy — and it was the *readers* that lost, not the writer. This is the
result that contradicts t4's "under continuous read-hammering it stays `delete`": under saturation
at HEAD, on a real 902-run store, the store converted every single time. B2 rules out the reader's
own `busy_timeout` as the variable — readers that *wait* (5000 ms, 146,709 reads, 0 refusals)
likewise fail to stop it.

**The mechanism, which explains why cadence is the wrong variable.** SQLite releases a read lock
when a statement finishes stepping. Both Rig's `query_map(...).collect::<Vec<_>>()` and these
pollers drain fully per call, so no matter how fast or how many, they only ever hold the lock in
sub-millisecond slivers, and the writer's `busy_timeout=5000` outlasts them. **Cadence cannot block
the conversion; only a *held* snapshot can.** Measured duty cycle for the real query shape:
median **0.742 ms**, max **1.025 ms** per `harness_get_events`-shaped read (§5.4) — at Rig's 2 s
cadence that is a **0.037 %** duty cycle per poller.

#### Arm E — the falsification control, and a defect

Arm E holds an open read transaction, the one shape that can block the conversion. It does **not**
leave the store benignly in `delete`. **It fails the harness boot, 10/10, at ~5.8 s** — the
`busy_timeout=5000` is consumed, the pragma then returns an error, and `:ok =` raises. Verbatim,
`armE.crash` (47 lines; the head of it, uncut):

```
19:18:11.181 [notice] Application aetheris exited: Aetheris.Application.start(:normal, []) returned an error: shutdown: failed to start child: Aetheris.Store
    ** (EXIT) an exception was raised:
        ** (MatchError) no match of right hand side value: {:error, "database is locked"}
            (aetheris 0.1.0) lib/aetheris/store.ex:582: Aetheris.Store.init/1
            (stdlib 6.0.1) gen_server.erl:2057: :gen_server.init_it/2
            (stdlib 6.0.1) gen_server.erl:2012: :gen_server.init_it/6
            (stdlib 6.0.1) proc_lib.erl:329: :proc_lib.init_p_do_apply/3
```

Every trial: `post_init=ERR post_exit=delete boot_ok=0 rc=1 elapsed≈5.8s`.

**`store.ex:582` is `:ok = Exqlite.Sqlite3.execute(conn, "PRAGMA journal_mode=WAL")`.** The failure
is raised inside `Aetheris.Application.start` → `failed to start child: Aetheris.Store`, i.e. in
the supervision tree, not in this scout's driver script — so any entry point that boots the
application (`mix aetheris run`, `fork`, the escript) fails the same way.

**So the pragma is not opportunistic in the sense the comment claims.** `store.ex:577-580` says
WAL "converts only when it can grab the database at an idle instant … worth keeping, but the fix
rests on busy_timeout + `:busy` handling, not on WAL" — which reads as *failure to convert is
benign*. It is not benign: the `:ok =` makes a failed conversion **fatal to harness startup**. The
mode that "stays `delete`" in t4's model is a state this code path cannot actually reach on a
delete-mode store — the pragma either converts or takes the boot down.

**Arm F bounds the blast radius: an already-`wal` store is immune.** Same held snapshot, but the db
starts in `wal`: 5/5 booted fine in ~0.78 s, with no 5 s wait at all — setting WAL on a WAL db
needs no exclusive lock, so the pragma is a no-op that cannot fail. **The live dev store (§2) is
therefore not exposed.** Reachability needs both conditions together: a **`delete`-mode** store
(a fresh checkout, a new machine, CI, any store whose first boot has not yet converted) **and** a
reader holding a snapshot past 5 s at that boot. Rig at HEAD does not hold one (§4), so this is
latent, not firing — but it is latent behind exactly the property §4 says nothing enforces.

### 5.4 `-wal` growth — follow-up (a), measured both ways

Same workload each time (real harness, 2,000 real `upsert_run` + `insert_event` pairs) on a copy of
the real store already in `wal`, sampling `-wal` size once a second:

| | Rig-shaped 2 s poller | held snapshot |
|---|---|---|
| `-wal` at t=1s | 565 pages | 603 pages |
| `-wal` peak | **1,007 pages** (4,128,272 B) | **12,165 pages** (49,831,432 B) |
| main db file | 23,576,576 → **24,158,208** (grows) | 23,576,576 → **23,576,576** (never grows) |
| reads completed | 13 (median 0.742 ms, max 1.025 ms) | 1 row pulled, snapshot held |

Under the poller the `-wal` **plateaus at 1,007 pages** — the 1000-page autocheckpoint threshold —
and the main db grows throughout: checkpointing is running normally, and `-wal` is bounded.
Under the held snapshot the `-wal` grows to **12× the threshold** and the main db does not advance a
single byte: checkpointing is completely blocked, which is precisely (a)'s failure mode.

So **(a) is real, and conditioned on the same held snapshot as the boot crash** — not on cadence,
not on connection lifetime. Under the access pattern that exists at HEAD it does not occur, which
matches §2's 145-page `-wal` on the live store.

---

## 6. Follow-up (b) — dirty-`-wal` recovery under a read-only connection

The ticket says not to manufacture a crash unless it is cheap and non-destructive on a copy. It was
both, so it was measured. Entirely on copies; `priv/aetheris.db` was not involved.

Setup: a copy of the real store in `wal`, real harness writing 400 runs+events, then `kill -9` on
the BEAM mid-run. Post-crash state, no live writer (`pgrep` → none):

```
=== post-crash sidecars (no live writer) ===
23678976 dirty.db
   32768 dirty.db-shm
 4128272 dirty.db-wal
```

A 4.1 MB uncheckpointed `-wal` — the dirty-`-wal` state (b) is about.

| case | state | read-only result |
|---|---|---|
| **b1** | `-wal` + `-shm` as the crash left them | **SUCCEEDED** — 1,302 runs visible, including all 400 rows the killed writer had committed |
| **b2** | same `-wal`, `-shm` deleted (machine-restart shape) | **SUCCEEDED** — 1,302 runs; SQLite recreated the `-shm` |
| **b3** | same `-wal`, no `-shm`, **db and directory not writable** (`chmod 444` / `555`) | **FAILED** — `OperationalError: unable to open database file` |

**Follow-up (b) as stated did not reproduce; the real condition is narrower.** A read-only
*connection* recovers a dirty `-wal` perfectly well — it did so twice, surfacing the crashed
writer's committed rows — because WAL recovery needs write access to the **`-shm` sidecar and its
directory**, not to the main database, and `mode=ro` does not withhold that. It fails only when the
filesystem does (b3): a read-only mount, a db owned by another user, or restrictive directory
permissions. In the operator's actual layout (`priv/` user-owned and writable) Rig is **not** in
that window.

t4's condition-2 note — "a read-only connection cannot *recover* a dirty `-wal` left by a harness
crash with no live writer" — is therefore **too strong as written**; it holds only under
`-shm`-unwritable conditions, which is a permissions property of the deployment rather than a
property of `SQLITE_OPEN_READ_ONLY`. Its remedy clause is confirmed: the next harness write recovers
and checkpoints (`POST_INIT_MODE=wal`, `BOOT_OK`, main db 23,678,976 → grown).

Worth noting for whoever writes the decision: Rig sets **no `busy_timeout`** (§3), so in any window
where a read *is* refused, Rig fails immediately with no retry rather than waiting.

---

## 7. Defects found and not touched

Two, both left alone per the ticket. The first is demonstrated; the second is a code shape.

### 7a. `store.ex:582`'s `:ok =` makes a failed WAL conversion fatal to harness startup — demonstrated

Full evidence in §5.3 Arm E (10/10 boot failures, verbatim crash, ~5.8 s each) and Arm F (an
already-`wal` store is immune, 5/5). Restated as a finding:

- **What breaks.** On a **`delete`-mode** store, if any reader holds a read snapshot past the
  `busy_timeout=5000` window at boot, `PRAGMA journal_mode=WAL` returns
  `{:error, "database is locked"}`, the `:ok =` on `store.ex:582` raises `MatchError` in
  `Store.init/1`, and `Aetheris.Application.start` fails with
  `shutdown: failed to start child: Aetheris.Store`. The harness does not start at all.
- **Why it is a defect and not a documented trade-off.** The comment at `store.ex:577-580` presents
  WAL as opportunistic and its failure as benign ("the fix rests on busy_timeout + `:busy` handling,
  not on WAL"). The code contradicts the comment: the conversion is *asserted*, so it is
  load-bearing for boot. Note the asymmetry — `busy_timeout` at `:581` cannot fail, so only `:582`
  carries this.
- **Reachability at HEAD: latent, not firing.** It needs `delete` mode **and** a >5 s held snapshot
  at that boot. §2 shows the live store is `wal` (immune, per Arm F), and §4 shows no consumer holds
  a snapshot — Rig's longest is `list_runs`' two-statement `unchecked_transaction()`, bounded by one
  command call. The exposure is a fresh store (new checkout, new machine, CI, or any store whose
  first boot has not converted) plus a future long-snapshot reader.
- **Bearing on the decision.** "Ratify opportunistic WAL as permanent" currently ratifies a boot
  crash on a delete-mode store, because the pragma is not opportunistic in code. That is BL-032's to
  adjudicate, not this memo's — but the option as written does not describe the code as it is.

### 7b. `:busy` is handled on the write path only; the read path can crash the singleton `Store`

`run_stmt/3` — `../aetheris/lib/aetheris/store.ex:1756-1769` — is BL-007 t4's fix:

```elixir
  defp run_stmt(conn, stmt, params) do
    with :ok <- Exqlite.Sqlite3.bind(stmt, params),
         :done <- Exqlite.Sqlite3.step(conn, stmt) do
      :ok
    else
      # `step/2` returns the bare atom `:busy` on SQLITE_BUSY (not `{:error, _}`); left
      # unhandled it fell through to a WithClauseError that crashed the singleton Store
      # (BL-007 t4). With busy_timeout set this is now rare, but surface it as a normal
      # error so the caller fails gracefully instead of taking the Store (and every other
      # run sharing it) down.
      :busy -> {:error, :busy}
      {:error, reason} -> {:error, classify_error(reason)}
    end
  end
```

Its only caller is `execute_stmt/3` (`:1750`) — the **write** path. Reads go through
`fetch_rows/3` → `collect_rows/3` (`:1780-1786`):

```elixir
  defp collect_rows(conn, stmt, acc) do
    case Exqlite.Sqlite3.step(conn, stmt) do
      {:row, row} -> collect_rows(conn, stmt, [row | acc])
      :done -> {:ok, Enum.reverse(acc)}
      {:error, reason} -> {:error, reason}
    end
  end
```

There is no `:busy` clause, and `step/2` can return the bare atom —
`../aetheris/deps/exqlite/lib/exqlite/sqlite3.ex:261-262`:

```elixir
  @spec step(db(), statement()) :: :done | :busy | {:row, row()} | {:error, reason()}
  def step(conn, statement), do: Sqlite3NIF.step(conn, statement)
```

So a `:busy` returned to a read raises `CaseClauseError` inside the singleton `Store`'s
`handle_call`, taking down the Store and every run sharing it — the same crash class t4 fixed for
writes, still live for reads. (`fetch_rows`' `:ok = Exqlite.Sqlite3.bind(...)` at `:1773` likewise
raises where the write path returns a tuple.)

**Reachability is not demonstrated here** — it needs a *read* whose `busy_timeout=5000` expires. No
arm produced one: in Arm B the 145,817 refusals all landed on the external readers
(`busy_timeout=0`), never on the harness's own connection. Stated as a code-shape finding with both
specs quoted, not as a live bug. Naming it, not fixing it, per the ticket.

One flagged observation, since it changes how §5.1 should be read: `rig/CLAUDE.md`'s "What Not To
Do" still says *"Don't poll or auto-refresh from the frontend. Use Tauri events from the backend"*,
while `useHarness.ts:130,211` polls at 2 s by BL-005's design. The rule and the code disagree; the
code is the newer decision.

---

## 8. Citation decay

- **`store.ex` moved under t4's citations.** Exactly one commit has touched it since `059c92e`:
  `a935038` ("fix(BL-031 r2): exempt paused runs from the inactivity bound"), +18/−1, hunks at
  `@@ -1062` and `@@ -1070`; the file went 2168 → 2185 lines. So **citations below line 1062 are
  unshifted, and every citation above it is +17.** Concretely: t4's `run_stmt/3` crash citation
  `store.ex:1727` is `:1756` at HEAD; the pragma block is unmoved. Any BL-032 work quoting t4's
  `store.ex` line numbers must apply +17 above 1062.
- **The "~200 ms floor" is not decay, it is a misattribution** (§5.1). Rig has always polled at
  2 s in the code read here; 200 ms is `run_helpers.ex:10`. A BL-032 ticket written against
  "Rig polls at ~200 ms" would be reasoning about the wrong process.
- **Two t4 claims that BL-032's row inherits do not survive measurement.** The row should be
  corrected before it is used as a premise:
  - *"under continuous read-hammering it stays `delete`"* — not reproduced. Saturation with 311,040
    completed reads converted 20/20 (§5.3 Arm B), and reader `busy_timeout` is not the variable
    either (Arm B2). Cadence cannot block the conversion; only a held snapshot can, and that
    produces a **boot crash**, not a benign `delete` (§7a). The row's "SQLite can only convert the
    journal mode when no reads are in flight … the store may stay in `delete` mode indefinitely" is
    the model this contradicts: in-flight short reads do not prevent it, and "stays `delete`
    indefinitely" is not a state this code path reaches.
  - *"a read-only connection cannot recover a dirty `-wal`"* (condition 2 / follow-up (b)) — too
    strong. It recovered twice; the real gate is `-shm`/directory write permission (§6).
- **Unchanged and confirmed:** the pragma order (`busy_timeout` first), WAL's persistence in the
  header, and that the load-bearing part of t4's fix is `busy_timeout` + `:busy` handling rather
  than WAL itself.

---

## 9. What this does not settle

- **Reader fidelity.** The pollers are Python `sqlite3` (`file:…?mode=ro`), not `rusqlite` with
  `SQLITE_OPEN_READ_ONLY | SQLITE_OPEN_NO_MUTEX`. Both resolve to the same SQLite open flag and both
  release the shared lock when a statement finishes draining, which is the property the race turns
  on — but it is the same *class* of substitution t4 r4 called out, and it is not the Rig binary.
  Mitigations applied: the readers use Rig's actual SQL and Rig's actual `busy_timeout` (0), and
  Arm B2 shows the result is insensitive to that setting.
- **The writer is the real harness, not a simulation** — real `Store.init/1`, real pragma order,
  real `create_tables`, real boot sweep, real `upsert_run`/`insert_event`. Only `db_path` was
  redirected. But it is driven by `mix run --no-start` + `ensure_all_started`, not by
  `mix aetheris run`, so the CLI's own argument handling and `await_run` loop were not in the path.
  §5.3's crash is attributed to the supervision tree on the evidence of the crash text naming
  `Aetheris.Application.start` — that a `mix aetheris` entry point fails identically is inference
  from that, not a separate measurement.
- **No GUI in the loop.** No arm ran the real Rig app, so nothing here covers Tauri-level timing or
  the two-pollers-per-2 s pattern arriving from a real render loop.
- **A1/A2 are weak on their own.** At a ~1.2 s boot window, a 2 s poller overlaps it about once
  (§5.3). The interference claim rests on Arm B's saturation, not on A1/A2.
- **§7b is a code shape, not a demonstrated live bug** — no repro attempted.
- **No gate covers any of this.** `config/test.exs:3` is `:memory:` (§3), so `mix test` can neither
  regress nor protect the behaviour measured here, in either direction. §7a in particular would not
  be caught by the suite.
- **No decision is recorded here.** §§1–7 are the evidence for the three follow-ups; the
  adjudication is BL-032's.

---

## Gates

This scout changed no code, so the ticket-boundary gate set has nothing to regress and **none was
run** — stated rather than claimed green. The only tracked file added is this memo.

**The real dev store was never written.** Cross-checked at the end of the session against §2's
opening listing:

```
$ ls -la priv/aetheris.db*        (end of session)
-rw-r--r-- 1 it it 23552000 Jul 26 15:28 priv/aetheris.db      <- size + mtime unchanged
-rw-r--r-- 1 it it    32768 Jul 26 19:07 priv/aetheris.db-shm  <- mtime only (reader touch)
-rw-r--r-- 1 it it   593312 Jul 26 16:09 priv/aetheris.db-wal  <- size + mtime unchanged
```

`aetheris.db` and `-wal` are byte-identical and mtime-identical to the session's opening listing.
Only the `-shm` mtime moved, from read-only probes taking a read lock. Every arm, every copy, and
every write ran in the session scratchpad.

**Cross-repo status** — a one-repo check would silently pass an omission in the sibling:

```
$ git -C ../aetheris status --short   ->  (empty)         HEAD f79365a
$ git -C .            status --short   ->  ?? docs/reviews/bl-032-wal-scout.md
                                          HEAD e6377cc
```

The harness repo is untouched. This memo is the only change in either repo.
