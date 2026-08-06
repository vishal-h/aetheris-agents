# m4 t3 — implementation notes

**Ticket.** Invert the hermetic prefix to an allowlist (BL-104); generalise the D2 credential
grep past AWS (BL-099). One pass, because the two interact: the inversion changes what reaches
the child at all, so the grep's target must survive the new list.

**Repos at ticket start.** `aetheris-agents` `04449db`, `aetheris` `f8bbac8` — both clean, both
level with `origin/main`.

**Carries taken (m4-consolidation §What t3, t4 and t5 inherit).** These notes take the `m4-`
prefix (`cloudcost/docs/t3-implementation-notes.md` is m1's and is untouched); the cycle document
is in `Touches` and is edited here.

---

## 1. Step-1 gate

| Gate | Result |
|---|---|
| **G0** fresh session; not in plan mode | pass — planning ran first, plan mode exited before the first edit |
| **G1** both repos clean; origin relationship | pass — clean and **level** before implementation; **ahead-by-N unpushed** after |
| **G2** passthrough list derived empirically, a recorded failure behind every entry | pass — §2, seven entries, seven transcripts |
| **G3** probe provably not on the allowlist; present in parent before absent in child | pass — both properties are assertions in the script, §3 |
| **G4** all commands cwd-independent | pass, with one self-caught slip recorded in §8 |
| **G5** eight `cloudcost/scripts/` blob hashes unchanged | pass — §7 |

---

## 2. The passthrough list, entry by entry (G2)

Built from **nothing**, adding only on a demonstrated failure, staged by hop so the derivation
did not burn a live agent run per candidate. Every failure below was observed, not predicted.

**Two properties, and the second was added at review r1.** Additive derivation proves an entry
fixed *the failure in front of it at the time*; it does not prove the entry is still load-bearing
once the list has grown. A list larger than necessary is the denylist defect with the sign
flipped. So each entry is now labelled with **which list its transcript was taken against**, and
every one that was partial has been re-run as a removal at the final list — §2b.

**And the derivation ran on one leg.** Only DigitalOcean's credential is present on this machine.
The six DO-leg entries are demonstrated end to end; **aws's and linode's `cred` names, and aws's
two `knob` names, are on the list by category selection rather than by an observed failure on
their own legs.** The selection is verified for all three providers and the knob mechanism is
demonstrated, but "every entry has a demonstrated failure behind it" means *on the leg that could
run*. Stated here, in `sprint.sh` beside `CC_ALLOW` where the list actually lives, and in §6.

### Passthroughs

| # | Name | The failure that put it there |
|---|---|---|
| 1 | `PATH` | `env: 'mix': No such file or directory`, exit 127 — nothing is executable |
| 2 | `HOME` | `** (RuntimeError) could not find the user home, please set the HOME environment variable` — `Mix.start/2` aborts in `Mix.Local.append_archives/0` |
| 3 | `LANG` | **silent output corruption** — see below |
| 4 | `ANTHROPIC_API_KEY` | run ends `failed` at step 0; trajectory event `error` reason `"could not fetch environment variable \"ANTHROPIC_API_KEY\" because it is not set"` |
| 5 | `CLOUDCOST_OPTIMIZATION` | **a fail-fast guard silently stops firing** — see below |
| 6 | `cred` names, from the adapter | without them the adapter cannot authenticate; the eval raises before the run |
| 7 | `knob` names, from the adapter | **a documented operator override silently disappears** — see below |

**3 — `LANG`, and it is the one worth reading.** Without it the BEAM falls back to latin1 native
name encoding and the `--json` payload's label is written as a bare `0xB7` where UTF-8 requires
`0xC2 0xB7`. Measured, not inferred:

```
archived capture (ambient env, pre-change):
  6f 73 74 20 c2 b7 20 44  69 67 69 74 61 6c 4f 63   |ost .. DigitalOc|
run with LANG stripped:
  6f 73 74 20 b7 20 44 69  67 69 74 61 6c 4f 63 65   |ost . DigitalOce|
```

This is the **Silent-wrong-answer** shape exactly: the line still parses, because `json_read`'s
reader opens with `errors='replace'`, so nothing downstream would ever have noticed. `LANG` is
passed through rather than fixed with an `ELIXIR_ERL_OPTIONS=+fnu` assignment (which also works,
verified) because passing it through reproduces the pre-change ambient behaviour exactly, which
is what BL-104's *"the legs all pass unchanged in behaviour"* asks for. **The residual is filed
as BL-112**: an operator whose `LANG` is unset gets latin1 today too, before and after this
ticket, and nothing anywhere reports it.

**5 — `CLOUDCOST_OPTIMIZATION`.** The orchestrator raises when it is `=1` on a non-AWS provider.
Three-way observation:

```
A. ambient env,       OPTIMIZATION=1 + provider=digitalocean -> exit 1, RuntimeError raised
B. prefix, NOT listed, same                                  -> exit 0   <-- guard gone, silently
C. prefix, listed,     same                                  -> exit 1, RuntimeError raised
```

A prefix that silently disables another component's fail-fast guard is the same defect class the
ticket exists to close, one layer down.

**7 — the `knob` names (`CLOUDCOST_AWS_REGION`, `CLOUDCOST_AWS_REGIONS`).** `runbook.md`'s env
table documents both as operator overrides. Stripped, the adapter's read returns `None`:

```
parent  (what the operator set):  CLOUDCOST_AWS_REGIONS -> 'eu-west-1,ap-south-1'
child   without the knob listed:  CLOUDCOST_AWS_REGIONS -> None
child   with it listed:           CLOUDCOST_AWS_REGIONS -> 'eu-west-1,ap-south-1'
```

**Stated to its limit:** the *mechanism* is demonstrated above; the *consequence* — the leg sweeps
the default region set while the operator believes it swept theirs — is read from
`fetch_aws.py:1085` (`regions = enumerate_regions(clients, os.environ.get(REGIONS_ENV))`) and is
**not observed end to end, because the AWS leg is not runnable on this machine** (§6).

### 2b. Minimality — every entry removed from the *final* list (review r1)

The table above records where each failure was **first** observed; the column below records the
list the transcript was taken against, and the removal result at the final DO list
(`PATH HOME LANG ANTHROPIC_API_KEY CLOUDCOST_OPTIMIZATION CLOUDCOST_DO_TOKEN`).

| Entry | First observed against | Removal at the final list |
|---|---|---|
| `PATH` | empty list (partial) | `exit=127` |
| `HOME` | `PATH` only (partial) | `exit=1 could not find the user home` |
| `LANG` | near-final, minus LANG (partial) | `native_name_encoding = :latin1` |
| `ANTHROPIC_API_KEY` | `PATH HOME` + cred (partial) | run `failed`, `[step:0 seq:2] error … "could not fetch environment variable \"ANTHROPIC_API_KEY\""` |
| `CLOUDCOST_OPTIMIZATION` | `PATH HOME LANG` (partial) | `eval exit=0` — the orchestrator's guard did not fire |
| `cred` (`CLOUDCOST_DO_TOKEN`) | **final list** — mutation 2, in the real sprint | `credential = stripped` |

**All six are load-bearing at the final list. The list is minimal, not merely sufficient.**

The AWS `knob` entries, at the final **AWS** list — mechanism only, the leg is not runnable:

```
full list                        REGION='us-east-1' REGIONS='eu-west-1,ap-south-1'
− CLOUDCOST_AWS_REGION           REGION=None        REGIONS='eu-west-1,ap-south-1'
− CLOUDCOST_AWS_REGIONS          REGION='us-east-1' REGIONS=None
```

**One false negative in my own matrix, recorded because it is the same class this ticket is
about.** The first run of it reported `− ANTHROPIC_API_KEY → still succeeded`. That was the
harness contaminating itself: I had exported `CLOUDCOST_OPTIMIZATION=1` so entry 5's row would
have something to detect, and on a DO leg that makes the orchestrator raise at *eval* time, so
the run never reached the LLM call and my grep for the run-failure line found nothing. A check
whose fixture silently changes what a sibling row tests. Re-run isolated, with the trajectory
event quoted rather than an exit code inferred.

### Assignments, not passthroughs — a reason each, not a failure

| Name | Why |
|---|---|
| `AWS_SHARED_CREDENTIALS_FILE=/dev/null` | **the trap that shaped the design.** Under the denylist this was assigned `/dev/null`. `env -i` would instead leave it **absent**, and absent is *not* `/dev/null` — absent restores boto3's default `~/.aws/credentials` lookup, and `HOME` is on the allowlist, so the file is reachable. Inverting naively would have re-opened the exact arm the denylist closed. |
| `CLOUDCOST_PROVIDER` | the selector, as before; it rides through the prefix rather than being exported, so the sprint never mutates its own environment |

### Hermetic against *names*, not deterministic in *values* (review r1)

Worth one sentence so nobody reads "hermetic" as "reproducible": **this ticket closed the name
surface, not the value surface.** `LANG` passes through, so the child inherits whatever locale the
operator has — which is the right call for BL-104's *legs pass unchanged in behaviour*, and which
means two operators can get different bytes out of the same sprint, one of them silently
corrupted. The prefix guarantees that no *unlisted* name reaches the run; it guarantees nothing
about the *values* of the listed ones. **BL-112** is the fix for the one case where that
difference is currently harmful, and is deliberately scoped away from here.

### What is *not* on the list, and is not meant to be

`LINODE_BILLING` — the live BL-104 instance, **still present in this session's environment** — is
covered by construction rather than by name, along with `AWS_REGION` and DO's own shadow names
(`DO_TOKEN`, `DIGITALOCEAN_ACCESS_TOKEN`), none of which the denylist ever carried. Its value was
not read, not used as the probe, and appears nowhere.

---

## 3. What changed in `sprint.sh`

### The prefix is a function, not an `env -i` array — and that is a D2 requirement

The obvious spelling of default-deny is `env -i NAME=value …`. **It breaks D2.** A credential
passed that way is an *argument*, readable from `/proc` by any user on the box, and D2 is
*"env-only — never an argument, never in a prompt"*. `cc_hermetic` instead runs in a subshell,
unsets every exported name not on the list, exports the two assignments, and `exec`s. No value is
ever re-typed, copied, or placed in an argv. Every call site wraps it in `( … )` so the unsets
cannot escape into the sprint's own environment.

Two options, both needed by the guards: `-x NAME` drops a name that *is* on the list, `-p PROV`
overrides the provider.

### The adapter's env surface is selected, never hand-typed — in three categories

The same treatment t2's rule-legibility check gives `CANONICAL_TYPES`. One bridge, read from the
adapter that actually reads the variables, feeding three consumers.

**Stated precisely, because "provider four touches nothing" would overstate it:** the poison
control, the survival arm and the D2 grep are now provider-agnostic and need no edit. The bridge
itself still carries a `MODULES` map (`digitalocean → fetch_do`, which is why it cannot be derived
from the provider name), and the credential preflight `case` is unchanged. A provider missing from
the map fails **loudly** at preflight, before any run — unlike the old strip list, whose omission
was silent. `runbook.md`'s add-a-provider wiring list is corrected to say so.

| Category | Constants read | Allowlisted? | D2 grep target? |
|---|---|---|---|
| `cred` | `TOKEN_ENV`, `ACCESS_KEY_ENV`, `SECRET_KEY_ENV`, `SESSION_TOKEN_ENV` | yes | **yes** |
| `knob` | `REGION_ENV`, `REGIONS_ENV` | yes | no — not secret, and its value legitimately appears in the report |
| `hazard` | `SHADOWING_ENV`, `ENDPOINT_REDIRECT_ENV` | **never** | no |

Resolved for all three providers (the two non-runnable legs' *selection* is verified even though
their runs are not):

```
digitalocean  cred[CLOUDCOST_DO_TOKEN]  hazard[DO_TOKEN DIGITALOCEAN_ACCESS_TOKEN]
aws           cred[CLOUDCOST_AWS_ACCESS_KEY_ID CLOUDCOST_AWS_SECRET_ACCESS_KEY
                   CLOUDCOST_AWS_SESSION_TOKEN]
              knob[CLOUDCOST_AWS_REGION CLOUDCOST_AWS_REGIONS]
              hazard[AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_PROFILE]
linode        cred[CLOUDCOST_LINODE_TOKEN]
              hazard[LINODE_CLI_TOKEN LINODE_TOKEN LINODE_CLI_API_HOST
                     LINODE_CLI_API_VERSION LINODE_CLI_API_SCHEME]
```

### A signal the inversion would have taken away, restored

Adjacent-case, and it is the finding I am least comfortable having nearly shipped without.
The old denylist **deliberately did not strip** `LINODE_CLI_API_HOST/_VERSION/_SCHEME`; its
comment says so, because they redirect where a credential is sent and *the adapter warns when
they are set* — stripping them would silence the only signal that hazard has. Default-deny strips
them. That is right for the run (an ambient redirect can no longer reach the adapter at all) and
wrong for the operator (the adapter never sees them, so it never warns, and the workstation is
still carrying the hazard).

So the sprint now reports it **from the parent, before the strip**, using the adapter's own
`hazard` names. It is a `warn`, not a `fail`: the run is safe; the workstation is the thing that
is not. Names only — no value is read.

### The poison control: structural, and provably non-vacuous

Both per-provider blocks (an AWS one and a Linode one, six arms) collapse to three arms, exactly
as BL-104 predicted — with default-deny there is nothing provider-specific to unset.

- **(i) the claim, structural.** Asserted over the child's *entire* key set: every name that
  reached the child is on the list. It **names no hazard at all**, which is the point — it covers
  `LINODE_BILLING`, `AWS_REGION`, the DO shadow names and every name nobody has thought of yet,
  by construction. Live: `8 name(s) reached the child, every one of them on the list`
  (`ANTHROPIC_API_KEY AWS_SHARED_CREDENTIALS_FILE CLOUDCOST_DO_TOKEN CLOUDCOST_PROVIDER HOME
  LANG PATH SHLVL`).
- **the permitted-extras set is derived, not hardcoded, and derived non-circularly.** Bash
  synthesises names for a child that inherits nothing (`LC_CTYPE` when `LANG` is unset, plus
  `PWD`/`SHLVL`/`_`); `SHLVL` is why the count is 8 and not 7. That set comes from `env -i`,
  **not** from `cc_hermetic`: deriving it from the mechanism under test would be circular — a
  leaking prefix would report the leaked names as "injected" and arm (i) would excuse exactly the
  failure it exists to catch.
- **(ii) the probe, both G3 properties.** Synthetic name and value. Asserted **absent from the
  allowlist before use** (otherwise a later edit could list it and the arm becomes a tautology),
  and observed **present in the parent** before being asserted **absent in the child**.
- **(iii) the credential survives**, on every provider rather than the two that happened to have
  an arm, with the name from the adapter. Prints `kept`/`stripped` only.

### The D2 grep

Runs on **every leg**, outside any provider gate, against that leg's own `cred` names. The
file-has-content-and-a-`run_id` gate is preserved per file. Two additions:

- **Decision 15 honoured:** `CC_D2_FILES=("$OUT_DIR/cloudcost/run.json")` is an array. Covering
  `run.err` when the harness round splits the streams is one entry, not a rewrite.
- **The anti-vacuity control the AWS arm lacked:** the same matcher, against a file constructed
  to contain the credential, **must find it** — else `fail`, because a matcher that cannot match
  reports clean forever. The file is `mktemp`-derived, mode `600`, and removed unconditionally by
  `trap … EXIT`; it is the one place in this case where a credential value is written to disk and
  it does not outlive the check. Verified afterwards that no bait file survives and that no
  sprint capture on disk carries the credential.

---

## 4. The BL-044-shaped question — reported, not fixed

**Finding: the three no-silent-fallback guards are NOT BL-044-shaped. They can detect a raise.**
BL-044 is about `mix aetheris` (`Mix.Tasks.Aetheris.run/1` discards `CLI.run/1`'s code). These
guards run `mix run --eval`, which has no such swallow. Verified in both directions:

```
POSITIVE CONTROL  the same command with nothing to raise about   -> exit 0
GUARD 1  aws + no key        -> exit 1  ** (RuntimeError) CLOUDCOST_PROVIDER=aws requires
                                           CLOUDCOST_AWS_ACCESS_KEY_ID and …
GUARD 2  linode + no token   -> exit 1  ** (RuntimeError) CLOUDCOST_PROVIDER=linode requires
                                           CLOUDCOST_LINODE_TOKEN to be set. …
GUARD 3  unknown provider    -> exit 1  ** (RuntimeError) CLOUDCOST_PROVIDER must be
                                           "digitalocean", "aws" or "linode", got: "nosuchcloud"
```

Appended to BL-044 as audit input: these three sites need no change when that row is fixed.

### But the real defect is one BL-044 does not name

**All three guards assert that an eval raises. None asserts *why*.** Any raise passes them,
including one caused by the environment change itself. That is the chaos-gate shape — an operand
that can silently become something other than what the check names while the check still reports
green. Guard 2 is the one whose ground this ticket moves, so it is the one that got the fix:
it now **matches the raise message**, not merely the exit code. Message before == after,
byte-identical, so the guard is still testing what its name says.

### Guard 2's change was forced, and here is the proof it was not cosmetic

The old line was `env -u CLOUDCOST_LINODE_TOKEN "${CC_HERMETIC[@]}" …`. Under the inversion an
**outer** `-u` is dead: the prefix re-exports every allowlisted name from the parent, and on a
Linode leg the token *is* allowlisted. Demonstrated with a synthetic token (presence-only check;
no network call, no real credential):

```
A. token absent from parent (this machine), -x inside the strip -> exit 1, credential raise
B. token PRESENT in parent, outer env -u  (the old spelling)    -> exit 0  <-- raise did NOT fire
C. token PRESENT in parent, -x inside the strip (the new line)  -> exit 1, credential raise
```

Had this been left alone, the Linode leg's fail-fast guard would have silently stopped firing the
first time anyone ran it with a token in the environment.

### Guards 1 and 3 — considered and kept, recorded as a negative

Guard 1's `env -u CLOUDCOST_AWS_*` **is itself a denylist**, three lines from the denylist this
ticket exists to invert, and Adjacent-case would normally say fix the class rather than the
instance. It stays, because **its failure direction is safe**: a credential arriving under a name
its `-u` list misses makes the eval *succeed*, so the guard fails **loudly**. It cannot pass
silently the way the run prefix could, which is the whole reason that one had to be inverted.
Bringing it under the allowlist would change what it tests without removing a risk, and would give
it a new way to raise vacuously. Same for guard 3.

Written down because otherwise the next reader finds an un-inverted denylist beside an inverted
one and cannot tell whether it was considered and kept or simply missed.

---

## 5. Mutation posture — all four, constructed, observed, restored

Each mutation was applied to `sprint.sh`, run, observed failing, and reverted; the file was
confirmed back to its ticket state after each.

| # | Constructed broken state | Observed |
|---|---|---|
| 1 | probe name added to `CC_ALLOW` | `[FAIL] the poison probe CC_T3_UNLISTED_PROBE is itself allowlisted — arm (ii) would be a tautology` — exit 1 |
| 2 | `cred` names not appended to `CC_ALLOW` | `[FAIL] the prefix stripped CLOUDCOST_DO_TOKEN — the digitalocean adapter could not authenticate` — exit 1 (arm (i) still passed at 7 names, which is the point of having both arms) |
| 3 | run output seeded with the live credential after the run | `[FAIL] CLOUDCOST_DO_TOKEN appears in run.json — D2 violated` |
| 4 | bait file built *without* the credential | `[FAIL] D2 anti-vacuity FAILED for CLOUDCOST_DO_TOKEN — the matcher cannot match this credential, so a clean result below would mean nothing` — exit 1 |

**Mutation 3 wrote a live credential into a sprint capture on disk.** It was located by content
(not by filename) and deleted, all other captures were swept for the same string and are clean,
and `sprint/` is gitignored so it was never a commit hazard. Recorded because the cleanup is part
of the posture, not an afterthought.

Mutation 3 exits **0**: `fail()` only prints (BL-077, tracked, deliberately unchanged here).

---

## 6. Done-check

### Legs run

| Leg | Credential | Result |
|---|---|---|
| **digitalocean** | `CLOUDCOST_DO_TOKEN` | **run, full leg, 16 `[OK]` / 0 `[FAIL]` / 0 `[WARN]`** |
| aws | `CLOUDCOST_AWS_ACCESS_KEY_ID` + `_SECRET_ACCESS_KEY` | **not runnable — not set in this environment** |
| linode | `CLOUDCOST_LINODE_TOKEN` | **not runnable — not set in this environment** |

No credential was minted or probed to make a leg runnable. **This is also the limit on §2's
derivation**: the passthrough list is demonstrated end to end on digitalocean and
category-derived for aws and linode. What would settle those two is a run on each with its
credential present — the removal matrix re-run at that leg's final list, which is one command
(§2b) once a credential exists.

What the two non-runnable legs *did* get: their adapter env surface is resolved and verified (§3), guard 2's Linode raise is exercised
with a synthetic token (§4), guard 1's AWS raise runs on every sprint, and the AWS `knob` failure
is demonstrated at the mechanism level (§2). What they did not get is an end-to-end run, and the
region-sweep consequence in §2 is the one claim resting on a read rather than a run.

### Sprint output, digitalocean leg, verbatim

```
=== uc-cloudcost — digitalocean cost report + orphan detection ===
[OK]    python3 found
[OK]    adapter env surface selected for digitalocean: cred=[CLOUDCOST_DO_TOKEN] knob=[none] hazard=[DO_TOKEN DIGITALOCEAN_ACCESS_TOKEN]
[OK]    no ambient digitalocean shadow/redirect names set (2 checked, from the adapter)
[OK]    CLOUDCOST_DO_TOKEN set
[OK]    cleared ../aetheris-agents/cloudcost/output/digitalocean (stale-artifact guard, scoped to this provider)
[OK]    cloudcost_orchestrator.exs evaluates (provider=digitalocean)
[OK]    CLOUDCOST_PROVIDER=aws + no key → eval raises (no-silent-fallback guard)
[OK]    CLOUDCOST_PROVIDER=linode + no token → eval raises, and with the credential raise (no-silent-fallback guard)
[OK]    unknown CLOUDCOST_PROVIDER → eval raises
[OK]    poison control: the probe name is not on the allowlist, so the check below can fail
[OK]    poison control: an unlisted ambient variable is visible without the prefix
[OK]    hermetic prefix is default-deny: 8 name(s) reached the child, every one of them on the list
[OK]    hermetic prefix strips an unlisted ambient variable (observed present in the parent, absent in the child)
[OK]    CLOUDCOST_DO_TOKEN survives the strip (digitalocean adapter's own credential)
[INFO]  Starting: uc-cloudcost orchestrator (provider=digitalocean)
[OK]    uc-cloudcost orchestrator → done (707 bytes)
[OK]    report: digitalocean/cloudcost_report_2026-08.html (14K), period 2026-08
[OK]    report_data.providers = [digitalocean] — the selected provider, and only it
[OK]    rule legibility: 18 resources evaluated, 0 skipped; types [compute_instance, load_balancer, volume] all drawn from the canonical set
[OK]    D2 anti-vacuity: the matcher finds CLOUDCOST_DO_TOKEN in a file built to contain it
[OK]    no CLOUDCOST_DO_TOKEN in run.json (searched a file with content and a run_id)
[INFO]  Run ID: cloudcost-orch-digitalocean-NZGYtg
```

The `[OK] no CLOUDCOST_DO_TOKEN in run.json` line is the one BL-099 was filed for: before this
ticket the DO leg had no D2 assertion at all, and was green either way.

### Encoding, verified on the final run

`sprint/20260806_200319/cloudcost/run.json` label bytes: `c2 b7` — valid UTF-8, matching the
archived pre-change captures. `LANG` is doing what it was added for.

---

## 7. `cloudcost/scripts/` blob hashes — unchanged

Verified at HEAD before the work and again after. No edit under `cloudcost/scripts/`; the bridge
reads constants that already existed.

```
f6589c6870ad7d66161d6f5ffe954c081362599d  _normalized.py
ee6027707a95f5d4046ef1ffac34eb9dab72efd1  compose_report_data.py
c756e414bb68e3c73d61bb469aea231f56de7768  detect_optimization_signals.py
fe8622f80d5a0b8adc8c3e3c86bdba539cf28106  detect_orphans.py
4c4db7393e20cb011f5e67f0435ad50fa273fbcf  fetch_aws.py
5a3ba664cb099f920f6f314babd33fdd8d7abd19  fetch_do.py
e4693617f8b7da3b9d73a3aede601106dca61d2c  fetch_linode.py
d14d8e3132aca3178509a1b68c37463c8d2a4601  render_report.py
```

---

## 8. Deviations, residuals and one self-caught slip

**Deviation — the hazard warn is new sprint output.** The ticket's *Do not generate* forbids "no
new sprint output state". This adds a `warn` line, not a new *state* (`warn` already exists in the
case, on the rule-legibility not-applicable arm). It is here because the inversion **removes** an
existing signal — the adapter's redirect warning — and shipping that removal silently would be a
regression introduced by a ticket about closing silent gaps. Declared rather than assumed
acceptable; revert it if the reviewer reads the fence more strictly than I have.

**Deviation — `cloudcost/m4-consolidation.md` edited.** Per the carry, this is a `Touches`
omission by design, not a deviation.

**Residual → BL-113, re-characterised at review r1.** The bridge hand-types the *constant* names
(`TOKEN_ENV`, `REGION_ENV`, `SHADOWING_ENV`, …), one level up from the env-var names, and carries
the provider→module `MODULES` map. That is strictly better than hand-typing the variables — an
adapter renaming `CLOUDCOST_LINODE_TOKEN` is followed automatically.

**My first filing of this row named the wrong half.** It said a missed *credential* constant is
missed silently. Established by mutating the bridge's tuples rather than reasoning: a missed
**mandatory** credential is the one case that fails **loudly** — on a single-cred provider the
empty-list guard fires at preflight (`could not read digitalocean's credential env names from its
adapter`, exit 1, before any run), and on a multi-cred provider the stripped name fails the
adapter at fetch. The genuinely silent cases are a missed **knob** (the override vanishes — §2's
entry 7 is that demonstration), a missed **optional** credential, a missed **hazard** (only the
operator warning is lost), and — the one that would actually cost something — a credential
**mis-categorised as a knob**, which is allowlisted into `CC_ALLOW` but never into
`CC_CRED_NAMES`, and the D2 grep iterates `CC_CRED_NAMES`. That is a D2 hole every leg reports
green. The row is rewritten against those; its Done-when now demands the mutation posture for the
silent cases specifically. The `MODULES` map fails loudly and is not part of the silent surface.

**Residual → BL-112.** The latin1 corruption is pre-existing and provider-independent: any harness
consumer, on any workstation with no `LANG`, silently gets malformed UTF-8 in `--json` payloads.
This ticket stops the sprint's prefix *causing* it; it does not fix the underlying fallback.

**A `Silent-wrong-answer` slip I caught in my own verification, recorded because the rule says
the author owns it.** A bridge probe was run with `scripts` as its path argument while cwd was
`aetheris/`, so it resolved to the harness's `scripts/` rather than `cloudcost/scripts/`. It
failed loudly (`ModuleNotFoundError`) rather than returning a plausible wrong answer, which is
luck, not method — a relative path in a cross-repo check is the command-binding carrier exactly.
Re-run bound to an absolute path.

**Untouched, as fenced:** `json_read` and its call sites; the rule-legibility assertion; the
redirect's stream topology (decision 13, streams stay merged); `fail()`'s effect on exit status;
`cloudcost/scripts/`; either repo's `lib/` or `src-tauri/`. No credential value appears in this
document, in the packet, or in any committed artifact — names only.
