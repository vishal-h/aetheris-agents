# BL-095 — plan card rendered secret config values in clear (implementation notes)

Security fix, `rig/` frontend only. One new module (`hintVisibility.ts`), three changed lines in
`StepCard`, and one metadata flag flipped.

---

## Two preconditions checked first — one of them changed the design

**The row's line numbers were correct at HEAD**, contrary to the prompt's expectation that BL-097
had shifted them by ~10. `StepCard` sits at `:82-86` and the render at `:105-111`, *above* the
`suggestOpen` state BL-097 added at `:137+`. Re-derived rather than assumed; nothing to correct.

**The masked metadata is thinner than either the row or the prompt assumed.** Enumerating all 15
`STEP_CONFIG_HINTS` keys against `AGENT_CONFIG_DEFS`:

| finding | count |
|---|---|
| `masked: true` | **1** — `SMTP_PASSWORD` only |
| `masked: false` | 12 — including **`GOOGLE_SERVICE_ACCOUNT`** |
| no metadata at all | 2 — `DOCBUILDER_CONTEXT_FILE`, `DOCBUILDER_REQUEST` |
| reachable only via manifest `env_deps` | **0** |

This falsifies both candidate rules as written:

- **Mask-if-flagged** (the row's suggestion) hides `SMTP_PASSWORD` and leaves
  `GOOGLE_SERVICE_ACCOUNT` printing in clear — one of the two keys the row explicitly names as
  leaked.
- **"Show only if `masked === false`"** (the prompt's deny-by-default rule) *also* shows
  `GOOGLE_SERVICE_ACCOUNT`, because it is explicitly `masked: false`. The prompt's rule and its own
  acceptance criterion ("confirm GOOGLE_SERVICE_ACCOUNT shows as set, not its value") contradict
  each other against real data.

**Resolved by fixing the metadata, not by special-casing the rule.** `GOOGLE_SERVICE_ACCOUNT` is
now `masked: true` in `agentConfigDefs.ts`. It is the path to a service-account *key file* — a
credential locator — so masking it is defensible on its own merits and arguably should always have
been the case. The Settings row keeps its reveal toggle, so it stays editable.

The alternative was a second, plan-card-only secrecy list. Rejected: duplicated secrecy metadata is
the drift class this repo keeps paying for, and one flag with one meaning used in both places is
the honest model.

---

## The rule

`hintVisibility.ts`, three pure exports:

```ts
export function shouldShowValue(key: string, masked: MaskedMap): boolean {
  return masked.get(key) === false;
}
```

The single showing branch is an **explicit** `masked === false`. `true` hides; a key absent from
the map hides; anything else hides. `hintLine()` renders `KEY: value` when safe and `KEY: set`
otherwise — "set" rather than dropping the row, because *that a credential is configured* is the
useful part of the signal and leaks nothing.

**Why deny-by-default is load-bearing here rather than stylistic:** two hint keys carry no metadata
at all, and a mask-if-flagged rule prints whatever they hold. It also makes the safe direction
automatic for any hint key added later without a def — the failure mode becomes a visible "set"
prompting someone to add the metadata, instead of a silent leak.

**Source of truth is `AGENT_CONFIG_DEFS` alone**, deliberately narrower than the prompt's
"defs ∪ manifest `env_deps`". No hint key is reachable only via a manifest today (verified across
every committed `tools.json`), so the union buys nothing now and would mean pulling the whole tools
inventory into the orchestrator view for zero benefit. It can only ever *widen* what is shown, so
omitting it is the conservative direction: a manifest-only hint key renders as "set" rather than in
clear. Stated as a deliberate narrowing, not an oversight.

---

## Verification

No JS test harness exists in `rig/` (established BL-083, confirmed BL-086); none was invented. The
proof is a `bun` one-shot importing the **real** predicate and the **real** `AGENT_CONFIG_DEFS`, so
a regression in either the rule or the metadata fails it.

```
=== the two keys the row names as leaked ===
PASS  SMTP_PASSWORD hidden
PASS  GOOGLE_SERVICE_ACCOUNT hidden
PASS  SMTP_PASSWORD renders as status
PASS  GOOGLE_SERVICE_ACCOUNT renders as status

=== anti-vacuity control — a masked:false key IS shown ===
PASS  PAYSLIP_MONTH shown
PASS  PAYSLIP_MONTH renders its value
PASS  SMTP_HOST shown

=== deny by default — no metadata means hidden ===
PASS  unflagged key hidden        (DOCBUILDER_REQUEST)
PASS  unknown key hidden
PASS  empty-map key hidden

11 of 15 hint keys still render their value
ALL PASS
```

Two anti-vacuity arms, not one. The obvious cheat for this ticket is hiding everything, which would
satisfy every "hidden" assertion — so the proof also requires specific `masked: false` keys to
still show their values, **and** asserts that the count of value-rendering keys is non-zero. A
hide-everything fix fails on both.

The full 15-key table is printed each run, with any secret that renders a value marked `<-- LEAK`
and counted as a failure, so the check reports the whole surface rather than the two keys the row
happened to name.

`bun run lint` clean · `bun run build` clean · `drift_check --strict` 8 PASS / 0 FAIL / 1 WARN
(exempt staleness). No `specs.md` change — no command or payload field was touched.

---

## Owed — and this one is a merge gate

The rendered card is unverified. This is a **security** fix whose acceptance names a user-facing
observation, so per the BL-073 learning the click-through gates the merge rather than trailing it:
rebuild Rig (Tauri does not hot-reload), approve a payslip plan, and confirm `SMTP_PASSWORD` and
`GOOGLE_SERVICE_ACCOUNT` read `set` while `PAYSLIP_MONTH` still shows `2026-04`.

Worth checking in the same pass, since the flag flip reaches it: Settings → Google Drive now renders
the service-account path dotted with a reveal toggle.
