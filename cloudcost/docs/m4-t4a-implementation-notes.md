# m4 t4a — the seam census

**Ticket:** t4a, the enumerating half of the t4 split. **Row:** BL-074 (not discharged by this
ticket). **Date:** 2026-08-06.
**HEADs at open:** agents `9962454`, harness `e75f838` — both clean, both level with `origin/main`.

This ticket **enumerates and reports**. It rules on nothing, edits none of the four shared
scripts, and closes no row. Every item below carries the two ruling-consequence fields so the
arbiter can rule without re-deriving; where the evidence points one way, the evidence is stated
and the sentence stops.

---

## 1. Why the method is the deliverable

BL-074 exists because m1 closed calling `STOPPED_STATES` *"the one seam where a provider's own
vocabulary reaches shared machinery"*, and m2 t1 found it was at least three. The row's point is
not the three fixes — all three landed — but the thing that produced them: the count came from
**observation, not enumeration**. Its Done-when therefore demands the sweep's *method* be recorded
*"so this is an enumeration and not another observation."*

An enumeration that finds fifty things but cannot say why there is no fifty-first has not
discharged that. §2 is the part a reader is meant to attack.

---

## 2. Method

### 2.1 Why a grep cannot do it

The subject is not a text pattern. It is *a value a provider could legitimately differ on*, and it
appears as a named constant, an inline literal in a comparison, a default in a `.get()`, a
hardcoded key name read off adapter-supplied data, a unit assumption, a currency assumption, a
rule predicate's structure — and, in four cases found here, as a predicate that is **absent**.

**A method that can only find named constants is a stop condition**, because named constants are
exactly the population the seven known leads already occupy. Of the 54 items censused below,
**19 are anchored on a module-level assignment and 35 are not**. A name-keyed sweep would have
returned at best the 19 and read as complete.

> **Counts corrected at review rounds 1 and 2.** The first draft said *"50 items … 21 named
> constants and 29 are not"*. All three figures were wrong — hand-counted, never derived.
>
> The sizes, established by counting item headings in each committed tree rather than asserted:
> **r0 (`53e3c9b`) held 53 items while its text said 50**; r1 added **X5** and holds **54**. A
> round-1 note claimed the census *"has always held 54"*, which was wrong in the round that added
> an item — caught at round 2, and it is the same defect one more time: a count claim inside the
> correction of count claims. Derivation, for both trees:
>
> ```
> $ git show 53e3c9b:cloudcost/docs/m4-t4a-implementation-notes.md \
>     | grep -cE '^#### (X|N|D|F|P|R)[0-9]+'      # -> 53
> $ git show cc34c67:… | grep -cE '^#### (X|N|D|F|P|R)[0-9]+'   # -> 54
> $ diff <(…53e3c9b… headings) <(…cc34c67… headings)            # -> only "> X5"
> ```
>
> The named/not split is derived from which items are anchored on an extraction-class-A node, and
> note which way the correction moved it: **19 / 35, not 21 / 29** — so the falsification of the
> name-keyed method is *stronger* than the first draft claimed, not weaker. The reviewer caught
> the first instance one section down (§6 said "Four" and listed eight); the headline census size
> was its sibling and the one figure a reader would have taken on trust. **Every count in this
> document is now derived by a command, and the command is shown beside the figure.**

### 2.2 The extraction — over-broad by construction

One AST pass over the four files, emitting eight classes. It is recorded here verbatim and is
re-runnable; the node counts it prints are the falsifiable part of the completeness claim.

> **Extended at review round 1.** Classes **G** (function-signature defaults) and **H** (literals
> in any call argument or keyword) were added after the reviewer observed that the completeness
> argument did not cover them: a literal default is not an `Assign`, `Compare`, `Call`, `Subscript`
> or `BinOp`, and class D reached only the two calls it names by function name. The extension added
> **112 nodes (406 → 518)** and **one census item** (**X5**). The rest classified out; the
> exclusion rows are in §2.5. Recorded as an extension rather than folded in silently, because
> which classes the pass covers *when* is the audit trail for the completeness claim.

```python
#!/usr/bin/env python3
"""t4a seam census — structural extraction over the four shared scripts.

Emits every AST node of eight classes. Deliberately over-broad: classification is done by
reading, afterwards, and every node is accounted for either as censused or as classified
out with a reason. Nothing here selects by identifier, substring, or prior mention.

Usage:  python3 seam_extract.py <dir-holding-the-four-scripts> [--list CLASS]
"""
from __future__ import annotations

import ast
import sys
from collections import Counter
from pathlib import Path

FILES = ("_normalized.py", "detect_orphans.py", "compose_report_data.py", "render_report.py")


def classify_nodes(tree):
    """Return {class_letter: [(lineno, source), ...]} for one module."""
    out = {k: [] for k in "ABCDEGH"}

    # A — every module-level assignment (named constants, whatever they are called)
    for n in tree.body:
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            tgt = n.targets[0] if isinstance(n, ast.Assign) else n.target
            out["A"].append((n.lineno, f"{ast.unparse(tgt)} = {ast.unparse(n.value)}"))

    for n in ast.walk(tree):
        # B — any comparison with a literal operand
        if isinstance(n, ast.Compare):
            operands = [n.left] + list(n.comparators)
            if any(isinstance(o, ast.Constant) for o in operands):
                out["B"].append((n.lineno, ast.unparse(n)))
            # E — membership / containment
            if any(isinstance(op, (ast.In, ast.NotIn)) for op in n.ops):
                out["E"].append((n.lineno, ast.unparse(n)))

        # C — literal key read via .get() or subscript
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get":
            if n.args and isinstance(n.args[0], ast.Constant):
                out["C"].append((n.lineno, ast.unparse(n)))
        if isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant):
            if isinstance(n.slice.value, str):
                out["C"].append((n.lineno, ast.unparse(n)))

        # D — literal in arithmetic, or a .get() default
        if isinstance(n, ast.BinOp) and (
            isinstance(n.left, ast.Constant) or isinstance(n.right, ast.Constant)
        ):
            out["D"].append((n.lineno, ast.unparse(n)))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get":
            if len(n.args) > 1:
                out["D"].append((n.lineno, ast.unparse(n)))
        # D — numeric precision literals in call kwargs/args (round(x, 2), indent=2)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "round":
            if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                out["D"].append((n.lineno, ast.unparse(n)))
        # D — every f-string / str format spec carrying a precision or a percent
        if isinstance(n, ast.FormattedValue) and n.format_spec is not None:
            out["D"].append((n.lineno, ast.unparse(n)))
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            if "%" in n.value and any(c in n.value for c in "YmdHMS"):
                out["D"].append((n.lineno, repr(n.value)))

        # G — literal defaults in a function signature (positional and keyword-only).
        # Not an Assign, Compare, Call, Subscript or BinOp, so classes A-E miss them.
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sig = n.args
            for d in list(sig.defaults) + [x for x in sig.kw_defaults if x is not None]:
                if isinstance(d, ast.Constant):
                    out["G"].append((n.lineno, f"def {n.name}(… = {ast.unparse(d)})"))

        # H — a literal in ANY call argument or keyword. Class D reaches only the two
        # calls it names by function name (.get(k, default), round(x, n)); every other
        # call's literals — argparse defaults, re.compile patterns, encoding= kwargs,
        # a helper invoked with a literal — sit in no other class.
        if isinstance(n, ast.Call):
            fname = (
                n.func.attr if isinstance(n.func, ast.Attribute)
                else n.func.id if isinstance(n.func, ast.Name)
                else ""
            )
            for arg in n.args:
                if isinstance(arg, ast.Constant) and not isinstance(arg.value, bool):
                    if fname == "get" and arg is n.args[0]:
                        continue  # already class C
                    if fname == "round" and len(n.args) > 1 and arg is n.args[1]:
                        continue  # already class D
                    out["H"].append((n.lineno, f"{fname}(… {ast.unparse(arg)} …)"))
            for kw in n.keywords:
                if isinstance(kw.value, ast.Constant) and not isinstance(kw.value.value, bool):
                    out["H"].append((n.lineno, f"{fname}({kw.arg}={ast.unparse(kw.value)})"))
    return out


def rule_predicates(tree):
    """Class F support — the predicate set of every top-level rule/modifier function.

    Structural absence is not an emittable node, so this lists what each rule *does*
    test, for a by-hand diff against its same-shaped siblings.
    """
    rows = []
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name.startswith(("rule_", "modifier_")):
            preds = []
            for sub in ast.walk(n):
                if isinstance(sub, ast.If):
                    preds.append((sub.lineno, ast.unparse(sub.test)))
            rows.append((n.name, n.lineno, preds))
    return rows


def main(argv):
    root = Path(argv[1]) if len(argv) > 1 else Path(".")
    want = argv[3] if len(argv) > 3 and argv[2] == "--list" else None
    grand = Counter()
    for name in FILES:
        tree = ast.parse((root / name).read_text())
        found = classify_nodes(tree)
        counts = {k: len(v) for k, v in found.items()}
        grand.update(counts)
        print(f"{name:26} " + "  ".join(f"{k}={counts[k]:>3}" for k in "ABCDEGH")
              + f"   total={sum(counts.values()):>3}")
        if want:
            for lineno, src in sorted(found[want]):
                print(f"    :{lineno:<4} {src}")
            print("  -- rule predicate sets --")
            for fn, lineno, preds in rule_predicates(tree):
                print(f"    {fn} (:{lineno})")
                for pl, p in preds:
                    print(f"        :{pl:<4} {p}")
    print("-" * 72)
    print("TOTAL".ljust(26) + "  ".join(f"{k}={grand[k]:>3}" for k in "ABCDEGH")
          + f"   total={sum(grand.values()):>3}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

| Class | Node predicate | What it reaches that a name sweep cannot |
|---|---|---|
| **A** | module-level `Assign` / `AnnAssign` | every named constant, including ones no lead names |
| **B** | `Compare` with a `Constant` operand | inline thresholds — `own <= 0`, `len(totals_by_currency) == 1` |
| **C** | `.get("k")` / `Subscript["k"]` | every hardcoded field name read off adapter data — the largest class |
| **D** | `BinOp` with a constant; `.get(k, default)`; `round(x, n)`; every format spec; every strftime literal | `/ 86400.0`, `round(…, 2)`, `{:,.2f}`, `{:.0%}` |
| **E** | `Compare` with `In` / `NotIn` | `state not in STOPPED_STATES`, `type not in SNAPSHOT_TYPES` |
| **F** | *(not emittable — see 2.3)* | predicates that are **absent** |
| **G** | literal default in a `FunctionDef` signature | `format_nz(empty="—")` — not an `Assign`, `Compare`, `Call`, `Subscript` or `BinOp`, so A–E miss it entirely |
| **H** | `Constant` in **any** call arg or keyword | `read_text(encoding="utf-8")`, `re.compile(…)`, every argparse `default=`/`action=`/`help=` — class D reached only `.get(k, d)` and `round(x, n)`, by name |

**Node counts, as printed:**

```
_normalized.py             A=  9  B=  1  C=  4  D=  5  E=  0  G=  0  H=  5   total= 24
detect_orphans.py          A= 19  B= 23  C= 81  D= 16  E=  4  G=  4  H= 29   total=176
compose_report_data.py     A=  7  B= 18  C=127  D= 29  E=  3  G=  5  H= 40   total=229
render_report.py           A=  6  B=  5  C= 36  D= 12  E=  1  G=  6  H= 23   total= 89
------------------------------------------------------------------------
TOTAL                     A= 41  B= 47  C=248  D= 62  E=  8  G= 15  H= 97   total=518
```

**518 nodes extracted; 54 censused.** Most of the extraction is noise — `is None` sentinels,
`__name__ == "__main__"`, `indent=2`, `.tmp` suffixes, `str | None` annotations. That is the
design. Over-breadth moves the place a value can be lost out of the extraction (where a loss is
invisible) and into the classification (where it is recorded).

### 2.3 Class F — the one class the AST cannot emit

A value a provider could differ on can be present as a **missing** literal, and no node carries an
absence. So the extraction is followed by a **per-rule predicate diff**: every `rule_*` and
`modifier_*` function's predicate set is listed by the same pass, and any predicate one rule
applies that a same-shaped sibling does not is censused. Printed set:

```
rule_unattached_volume (:165)
    :167  resource.get('type') != TYPE_VOLUME or resource.get('attached_to') is not None
    :170  age is None or age <= UNATTACHED_VOLUME_MIN_AGE_DAYS
rule_unassociated_static_ip (:187)
    :190  resource.get('type') != TYPE_STATIC_IP or resource.get('attached_to') is not None
    :194  age is not None
rule_aged_snapshot (:202)
    :210  resource.get('type') not in SNAPSHOT_TYPES
    :213  age is None or age <= ctx.snapshot_age_days
    :220  resource.get('attached_to') is None
rule_idle_load_balancer (:227)
    :235  resource.get('type') != TYPE_LOAD_BALANCER or resource.get('attached_to') is not None
rule_stopped_compute_with_attached_storage (:248)
    :263  resource.get('type') != TYPE_COMPUTE_INSTANCE
    :265  resource.get('state') not in STOPPED_STATES
    :268  age is None or age <= STOPPED_COMPUTE_MIN_AGE_DAYS
    :271  not attached
rule_stopped_database_with_storage (:306)
    :319  resource.get('type') != TYPE_DATABASE
    :321  resource.get('state') not in STOPPED_STATES
    :323  resource.get('attached_to') is not None
    :326  own <= 0
    :329  age is None or age <= STOPPED_COMPUTE_MIN_AGE_DAYS
modifier_recent_activity (:364)
    :372  age is None or age > RECENT_ACTIVITY_WINDOW_DAYS
modifier_ephemeral_name (:386)
    :389  not isinstance(name, str)
    :392  not match
```

Four asymmetries fall out of that diff (F1–F4 below). None is reachable by any grep, and none is
named by any lead.

### 2.4 The classification criterion

Each extracted node is classified in or out by one question, applied by reading:

> **Does this value's correctness depend on a fact about a cloud provider** — its billing model,
> its vocabulary, its tag representation, its API's field semantics, its units, its currency —
> **rather than on a fact about Python, JSON, the filesystem, or this pipeline's own internal
> contract?**

Class C splits cleanly on it, and the split is the reason class C is 248 nodes but contributes few
items. Of 248, **38 distinct key names are read off adapter-supplied documents**; the rest are keys
these stages **write into their own output** (`"base_confidence"`, `"by_band"`, `"render_warnings"`)
or read back off a structure they built one function earlier. A written key is this pipeline's
downstream contract, not a seam — classified out, with that reason. Of the 38 read-side keys, 24
are the §Normalized schemas contract itself; the other 14 are intra-pipeline documents
(`report_data`, orphan candidates) being re-read by a later stage.

### 2.5 What was classified out, and why

| Reason | Approx. nodes | Examples |
|---|---|---|
| `None`-sentinel comparison — a Python fact, not a provider fact | ~40 (class B) | `age is None`, `parsed.tzinfo is None`, `binary is None` |
| Key **written** into this stage's own output | ~150 (class C) | `"base_confidence"`, `"by_band"`, `"delta_pct"`, `"render_warnings"` |
| Key read back off a structure built in the same module | ~60 (class C) | `row["amount"]`, `hit["evidence"]`, `band["band"]` |
| Serialization / filesystem mechanics | ~10 (class D) | `indent=2`, `path.suffix + ".tmp"`, `+ "\n"` |
| Type annotation parsed as a `BinOp` | 6 (class D) | `str \| None`, `dict \| None` |
| Module entry point | 4 (class B) | `__name__ == "__main__"` |
| Subprocess / argparse mechanics | ~5 | `result.returncode != 0`, `len(set(given.values())) > 1` |
| **G** — optional-parameter sentinel | 14 of 15 | `parse_args(argv=None)`, `fired(saving=None)`, `compose(period=None)`. A Python calling-convention fact. The fifteenth, `format_nz(empty="—")`, is **already censused** as part of R2 |
| **H** — already censused under another class | ~14 of 97 | `strftime("%Y-%m-%d")` → N4; `re.sub("[^a-z0-9]+")` → N6/P10; `re.compile("^(tmp-|ci-|test-)")` → D5; `fullmatch(r"\d{4}-\d{2}")` → P4; `max(0.0)`/`min(1.0)` → D9; `.get(k, 0.0)` ×4 → P6 |
| **H** — CLI surface (flag names, `help=`, `action=`, `description=`) | ~55 of 97 | `add_argument("--output-dir", default="output")`. The orchestrator contract, identical for every provider. `--snapshot-age-days` being the *only* threshold flag is censused separately as D3 |
| **H** — error/evidence message text | ~10 of 97 | `ValueError("inventory root is not a JSON object")`, `age_phrase("stopped instance age")`, the six `fired("rule_name")` identifiers (write-side) |
| **H** — serialization and glob mechanics | ~8 of 97 | `json.dumps(indent=2)`, `glob("*.json")`, `with_suffix(".pdf")` — a file-extension convention identical for every provider |

Exclusion reasons are recorded rather than counted away because a value lost to a *wrong exclusion
reason* is recoverable by a reader who disagrees with the reason; a value never extracted is not.

### 2.6 The completeness argument

1. The extraction is over the **AST**, so its coverage claim is *"every node of these seven
   emittable classes in these four files"*. A reader falsifies it by re-running the pass and
   diffing the node counts against the ones printed in §2.2. It is not a claim about my attention.

   **The claim is bounded by which classes exist, and that bound is where round 1 found it.**
   Classes A–E covered assignments, comparisons, key reads, arithmetic and membership; two
   populations sat in none of them, and the argument as first written did not say so. Adding G and
   H returned 112 nodes and one item (X5) — so the gap was **not** empty, and the honest reading is
   that the original completeness claim was true of the classes it named and silent about the ones
   it did not. The lesson is recorded rather than smoothed over: an AST-class census is complete
   *relative to its class list*, and the class list is the part that needs adversarial reading.
   Whether an eighth population remains is not something this method can answer from inside itself.
2. **Nothing is selected by identifier, substring, or prior mention.** The seven leads were checked
   *against* the census output afterwards (§4), never used to seed it. This is the load-bearing
   property: the census is downstream of the file's structure, not of what anyone already knew was
   in it.
3. The one class the AST provably cannot reach is **named** (F, structural absence) and has its own
   procedure (§2.3), which is itself mechanical and printed.
4. Every classified-out population has a stated reason (§2.5), so the failure mode is visible
   rather than silent.

### 2.7 What would **not** have counted

Stated explicitly, because each of these reads as satisfied unless the method says otherwise —
the same shape as t3's allowlist, where *"a recorded failure behind every entry"* read as satisfied
by additive transcripts until the subtractive removal test was applied. The analogue here is §2.5:
additive evidence (*here is what I found*) never establishes completeness; the **exclusion record**
is what makes the absence of a fifty-first item checkable.

- **"I searched for the known candidates and found them."** The seven leads are a lower bound, not
  a target. A census returning exactly seven has demonstrated a grep.
- **"I read the four files carefully."** Reading without an extraction has no falsifiable coverage
  claim — there is no artifact a reader can re-run and no count they can diff.
- **"I grepped `^[A-Z_]{4,} = `."** Name-keyed. It finds 41 module assignments and misses the 29
  censused items that are not named constants — including every class F item and the two strongest
  findings (X1, X2).
- **A count with no exclusion reasons.** "518 nodes, 54 censused" is not checkable; the other 464
  have to say why.
- **Treating the adapters as the census's evidence base.** They are the evidence for *current*
  divergence only. A sweep driven from what the three adapters happen to do would find no seam
  wherever all three currently agree — which is exactly where the fourth provider will break.

---

## 3. The census

54 items. Per-item fields are BL-074's adjudication inputs; **If schema-level** and
**If adapter-owned** are the two the ruling turns on and neither is omitted anywhere.

*Grouping declared:* six `CONFIDENCE_*` constants are censused as one item (**D8**) and the ~12
`round(…, 2)` money sites as one item (**N5**), because each group shares a single ruling surface —
a ruling on one is a ruling on all. The collapse is stated here so a reader sees a grouping rather
than infers a miss; per-constant lines are inside the item.

*Established-vs-reasoned:* **Diverges today** is read off the three adapters at the HEAD above.
**Could diverge** is reasoning, and is labelled as such by being in a different field.

### 3a. Cross-cutting — read off adapter data by more than one stage

#### X1 · `state`, for every value other than `stopped` — `_normalized.py:62`, read at `detect_orphans.py:265, 276, 321, 336`
- **Meets** — the resource entry's `state` field, from all three adapters.
- **Diverges today** — **yes, and widely.** The schema defines exactly *one* state value
  (`STATE_STOPPED = "stopped"`). Every other state is passed through raw: DO emits `attached`,
  `available`, `assigned`, `unassigned` and `raw.get("status")` (`fetch_do.py:366, 385, 406, 440`);
  AWS emits `raw.get("State")` verbatim plus `associated`/`unassociated`/`active`
  (`fetch_aws.py:528, 555, 600, 621, 649, 704`); Linode emits `raw.get("status")` verbatim and one
  hardcoded `None` (`fetch_linode.py:690, 817, 856, 977`). Three vocabularies, ~15 values, none
  canonical.
- **Could diverge** — it already does; the open question is what happens when a rule wants to key
  on a non-stopped state. Nothing keys on one **today**, which is why this has stayed invisible —
  but `detect_orphans.py:276` renders `f"state is '{resource.get('state')}'"` straight into
  evidence text, and `render_report.py` renders whatever arrives. So provider vocabulary reaches
  the delivered report verbatim, through shared machinery, right now.
- **If ruled schema-level** — §Normalized schemas enumerates a closed `state` set as it already
  does for `type`, `_normalized.py` gains `STATE_*` constants and a `CANONICAL_STATES` frozenset,
  and all three adapters map their remaining values onto it. Breaks: every adapter's non-stopped
  emission (14 sites), their fixtures, and any test asserting a raw provider state. This is seam #1
  finished rather than a new seam — `STOPPED_STATES` was closed for the *stopped* case only.
- **If ruled adapter-owned** — nothing changes in code, but the report's `state` column is
  documented as provider vocabulary and the §Normalized schemas entry for `state` says so
  explicitly, so no future rule is written against it. Breaks: nothing today; it forecloses any
  rule keying on a non-stopped state without a preceding schema change.
- **Consumers** — `detect_orphans.rule_stopped_compute_with_attached_storage` (`:265`),
  `rule_stopped_database_with_storage` (`:321`), both evidence strings (`:276`, `:336`);
  `render_report` via the candidate's evidence; `tests/test_detect_orphans.py:233–253`;
  `tests/test_fetch_linode.py:115`. **Not** the sprint case — its rule-legibility arm checks `type`
  membership only, so a non-canonical `state` passes it silently.

#### X2 · `size` — read at `detect_orphans.py:290`, `compose_report_data.py:403`
- **Meets** — the resource entry's `size` field.
- **Diverges today** — **yes.** The same physical unit is spelled three ways. AWS: `f"{gib}GiB"`
  (`fetch_aws.py:527, 599, 703`) and instance-type slugs (`:497, 678`). DO: `f"{gib}GiB"`
  (`:363, 405`) and size slugs (`:344, 439`). Linode: `f"{size_gb}GB"` (`:689`) and
  `f"{raw.get('size')}MB"` (`:976`). So a 100-unit volume reads `100GiB` on two providers and
  `100GB` on the third, for the same quantity.
- **Could diverge** — a provider expressing capacity in TB, in IOPS-provisioned units, or as a
  structured `{value, unit}` object.
- **If ruled schema-level** — `size` becomes a typed field (a number plus a unit, or a normalized
  string grammar), all three adapters change at 12 sites, and both consumers change. Breaks: every
  adapter fixture carrying a `size`; the evidence-string assertion in
  `tests/test_detect_orphans.py`; the rendered untagged-spenders column.
- **If ruled adapter-owned** — `size` is documented as a free-form human label, and the two
  consumers are confirmed as display-only (both are: `detect_orphans.py:290` interpolates it into
  an evidence sentence, `compose_report_data.py:403` copies it into `top_untagged_spenders`).
  Breaks: nothing today. Forecloses ever sorting, comparing or summing on `size`.
- **Consumers** — `detect_orphans.py:290` (evidence text), `compose_report_data.py:403`
  (`top_untagged_spenders`), `render_report`'s spenders table, `templates/report.html.j2`.

#### X3 · `tags` as a flat list of `str` — `_normalized.py:110–112` (`tags_of`)
- **Meets** — the resource entry's `tags` field.
- **Diverges today** — **yes, in construction.** AWS tags are `[{Key,Value}]` and are flattened to
  `k=v` (or bare `k` when the value is empty) by the adapter (`fetch_aws.py:421–439`); DO and
  Linode pass native flat strings through (`fetch_do.py:245`, `fetch_linode.py:341`). Two of the
  three cannot express a key/value pair natively.
- **Could diverge** — a provider with typed tag values, or with a namespace separator other than
  `=` (GCP labels, Azure `name`/`value` pairs).
- **If ruled schema-level** — `tags` becomes a list of objects or a mapping; `tags_of`,
  `has_keep_tag`, `tag_coverage` and every adapter change. Breaks: every fixture, `KEEP_TAG`'s
  match predicate, the coverage figure's shape.
- **If ruled adapter-owned** — the flat-string list stays the contract and the `k=v` convention is
  documented as an adapter-side flattening whose separator is part of the schema. Breaks: nothing
  today; leaves `KEEP_TAG` (D6) as the one place the convention is load-bearing.
- **Consumers** — `_normalized.tags_of` → `has_keep_tag` (`detect_orphans.py:112`),
  `tag_coverage` (`:135`), `compose_report_data.coverage_section` (`:375`); the sprint case does
  not read tags.

#### X4 · `last_activity_at` — `_normalized`-schema field, read at `detect_orphans.py:371, 431`
- **Meets** — the resource entry's `last_activity_at`.
- **Diverges today** — **no, and that is the finding: it is `None` on all three adapters, at
  every emission site** (`fetch_do.py:347, 368, 387, 408, 442`; `fetch_aws.py:502, 530, 559, 602,
  623, 651, 681`; `fetch_linode.py:660, 692, 819, 861, 979`). So `modifier_recent_activity` and
  `RECENT_ACTIVITY_WINDOW_DAYS` (D4) have never fired against any real inventory from any provider.
  The `detect_orphans.py:75–77` comment states this for DigitalOcean; it is in fact true fleet-wide.
- **Could diverge** — a provider exposing last-attach or last-access (AWS CloudTrail-derived, or an
  object-store last-access time) would make the modifier live for one provider and dead for two.
- **If ruled schema-level** — the field stays, with its universal-null status recorded so a reader
  does not mistake the modifier for exercised behaviour. Breaks: nothing.
- **If ruled adapter-owned** — the field and the modifier that reads it move behind an adapter
  capability declaration, so a provider that cannot supply it does not carry a permanently-dead
  scoring path. Breaks: `modifier_recent_activity`, `MODIFIERS`, the `parameters` echo (D22), and
  `tests/test_detect_orphans.py:419` which exercises the modifier from a synthetic fixture.
- **Consumers** — `detect_orphans.modifier_recent_activity` (`:371`), `timestamp_warnings`
  (`:431`), `identity`-adjacent evidence; `tests/test_detect_orphans.py:419`.

#### X5 · File-read/write encoding — specified in `render_report.py`, **absent** in the other two I/O sites — `detect_orphans.py:583, 613`; `compose_report_data.py:667, 678, 708`; cf. `render_report.py:334, 352, 381, 404`
*(Found at review round 1 by class H — the only item the class-G/H extension added.)*
- **Meets** — every adapter-supplied document, at the point it is decoded: the inventory JSON, the
  cost snapshot, the orphan-candidates file and every persisted history snapshot.
- **Diverges today** — **no**, and it is currently invisible for that reason: every value the three
  adapters emit is ASCII, so the platform default decodes them identically to UTF-8. The
  **asymmetry** is established, not reasoned: `render_report.py` passes `encoding="utf-8"` at all
  four of its I/O sites; `detect_orphans.py` (2 sites) and `compose_report_data.py` (3 sites) pass
  none and take `locale.getpreferredencoding()`.
- **Could diverge** — a provider whose resource `name`, `tags` or `region` carry non-ASCII (a
  customer-supplied CJK instance label, an accented region display name). Under a non-UTF-8 locale
  the read either raises `UnicodeDecodeError` — breaking the stdout contract with a traceback,
  which the stage-CLI rule forbids — or mis-decodes silently, and the mis-decoded name is then
  written into the candidate's `identity`, into the evidence text and into the rendered report.
  **This is BL-112 one layer down**: that row is the BEAM's latin1 fallback silently corrupting
  non-ASCII in `--json` payloads; this is the same failure in the Python stages, reached by the
  same locale, and neither is guarded by the other. It is also why the asymmetry matters rather
  than the absence alone — the one script that would *display* the corruption is the one that
  already specifies the encoding, so the corruption enters upstream of the only correct site.
- **If ruled schema-level** — the normalized schemas specify UTF-8 as the on-disk encoding, and all
  five unspecified sites pass `encoding="utf-8"` explicitly. Breaks: nothing — the two-line change
  is byte-neutral on every current artifact, which is exactly why it has stayed unnoticed.
- **If ruled adapter-owned** — not available in any useful form: the encoding governs how *shared
  machinery* decodes a file an adapter already wrote, and the adapters' own writers are outside
  BL-074's four-file scope. Recorded as a closed arm. (The adapters' write-side encoding is a
  separate question this census did not sweep — see §6.)
- **Consumers** — `detect_orphans.main` (`:613`) and `write_json` (`:583`);
  `compose_report_data.write_json` (`:667`), `read_document` (`:678`), `discover_bundles` (`:708`);
  transitively the history tree, since `persist_history` writes through `write_json`. No test pins
  an encoding; the sprint does not check one.

### 3b. `_normalized.py` — the schema module

#### N1 · `TYPE_*` ×7 and `CANONICAL_TYPES` — `:39–58` (`CANONICAL_TYPES = frozenset({…})`)
- **Meets** — the resource entry's `type`, from every adapter.
- **Diverges today** — **yes, by coverage.** `fetch_aws.py:41` imports all seven; `fetch_do.py:37`
  imports five (no `TYPE_DATABASE`, no `TYPE_DATABASE_SNAPSHOT`); `fetch_linode.py:49` imports six
  (no `TYPE_DATABASE`, no `TYPE_DATABASE_SNAPSHOT`). So two of the seven canonical types are
  emitted by AWS alone, and `rule_stopped_database_with_storage` is unreachable on two of three
  providers.
- **Could diverge** — provider four brings object storage, a Kubernetes cluster, a container
  registry, a managed cache — none of which the closed set can express, and `usable_resources`
  will pass them through as usable (N8).
- **If ruled schema-level** — it already is; the open sub-question is the **accessor** (BL-074's
  t2 observation): adapters import the seven `TYPE_*` names individually and never the set, so
  `CANONICAL_TYPES` has no declared public surface. Making one is a `__all__` or an accessor
  function. Breaks: nothing, additively.
- **If ruled adapter-owned** — not available for the values (that is seam #2, already closed at
  m2 t2 a′). It *is* available for the *set*: leave `CANONICAL_TYPES` private and have each
  consumer state its own accepted subset. Breaks: `../aetheris/scripts/sprint.sh:3025`, which
  imports the set by name.
- **Consumers** — `detect_orphans` (7 `TYPE_*` imports, `SNAPSHOT_TYPES`), all three adapters,
  **`../aetheris/scripts/sprint.sh:3025, 3048, 3055`** (rule-legibility arm — relocating or
  renaming this breaks the sprint, loudly, by design), `tests/test_detect_orphans.py:840, 851, 866,
  870`, `tests/test_fetch_do.py:65`, `tests/test_fetch_linode.py:78, 115`.

#### N2 · `STATE_STOPPED` — `:62` (`STATE_STOPPED = "stopped"`)
- **Meets** — the resource entry's `state`, for the stopped case only.
- **Diverges today** — **no.** All three adapters map their own spelling onto it: DO `off`
  (`fetch_do.py:345`), AWS `stopped` (`fetch_aws.py:500, 679`), Linode `offline` via
  `POWERED_OFF_STATUS` (`fetch_linode.py:658`). This is seam #1, closed and holding.
- **Could diverge** — a provider distinguishing `stopped` from `suspended`, `hibernated` or
  `deallocated`, where the billing consequence differs per sub-state.
- **If ruled schema-level** — it already is. The live question is whether the set widens (see X1).
  Breaks: n/a.
- **If ruled adapter-owned** — would re-open the seam m2 t2 a closed; recorded as available but
  contrary to the established ruling. Breaks: `STOPPED_STATES`, both stopped rules, all three
  adapters, `tests/test_detect_orphans.py:233–234`.
- **Consumers** — `detect_orphans.STOPPED_STATES` (`:93`), all three adapters,
  `tests/test_detect_orphans.py:233–234`, `tests/test_fetch_aws.py:929`,
  `tests/test_fetch_linode.py:115`.

#### N3 · `parse_timestamp` — ISO-8601-only, `Z`/`z` suffix, naive→UTC — `:65–78`
- **Meets** — the resource entry's `created_at` and `last_activity_at`, and the envelope's
  `generated_at`.
- **Diverges today** — **no.** All three adapters emit ISO-8601; the `Z`-suffix branch
  (`:70–71`) exists because at least one API returns `Z` rather than `+00:00`.
- **Could diverge** — a provider returning epoch seconds, RFC-2822, or a local-time string with no
  offset. The last is the dangerous one: `:76–77` silently assumes UTC for a naive timestamp, so a
  provider emitting local time would produce age errors of up to a day, in the direction that
  suppresses rule firings — a **silent** wrong answer, not a parse failure.
- **If ruled schema-level** — §Normalized schemas states ISO-8601-with-offset as required, and
  `parse_timestamp` **rejects** a naive timestamp instead of assuming UTC (it would then surface via
  `timestamp_warnings`). Breaks: any adapter or fixture emitting a naive stamp; would need a sweep
  of all three fixture sets first.
- **If ruled adapter-owned** — each adapter is responsible for emitting offset-bearing ISO-8601
  and `parse_timestamp`'s naive branch becomes dead defensive code, documented as such. Breaks:
  nothing today.
- **Consumers** — `detect_orphans.Context.age_days` (`:132`), `timestamp_warnings` (`:433`),
  `resolve_reference_date` (`:571, 574`), `compose_report_data.newest_timestamp` (`:124`).

#### N4 · `iso()` / `day()` format strings — `:82` (`"%Y-%m-%dT%H:%M:%SZ"`), `:86` (`"%Y-%m-%d"`)
- **Meets** — the timestamps re-emitted into `reference_date` and `as_of`.
- **Diverges today** — **no.** Output-side only; no adapter reads them.
- **Could diverge** — sub-second precision, if a provider's events need ordering finer than a
  second. `iso()` truncates silently — it does not round or warn.
- **If ruled schema-level** — the emitted-timestamp grammar is stated in §Normalized schemas as
  second-precision UTC. Breaks: nothing.
- **If ruled adapter-owned** — not available: these are emitted by shared machinery, not by any
  adapter. Recorded as an item where one arm is genuinely closed, rather than left blank.
- **Consumers** — `detect_orphans.detect` (`:525`), `age_phrase` (`:141–142`),
  `modifier_recent_activity` evidence (`:379–380`), `compose_report_data.newest_timestamp` (`:125`).

#### N5 · `money()` — `round(value, 2)`, uncoercible → `0.0` — `:89–94`, and the ~12 `round(…, 2)` sites it sets the convention for
- **Meets** — every `monthly_cost_estimate`, `line_items[].amount` and `totals.amount`.
- **Diverges today** — **no.** All three adapters declare `CURRENCY = "USD"`
  (`fetch_aws.py:71`, `fetch_do.py:56`, `fetch_linode.py:89`).
- **Could diverge** — 2dp is wrong for zero-decimal currencies (JPY, KRW) and for sub-cent unit
  pricing. Linode's own spec exposes `region_prices[]` at unit granularity
  (`docs/m3-linode-scout.md` §B6), and t3 already recorded a real sub-cent unit price
  (`unit_price 0.0015`, `fetch_linode.py:728`). A provider billing in JPY would have every
  amount silently gain two meaningless decimals; one billing per-request at 4dp would have
  amounts rounded to zero.
- **If ruled schema-level** — the minor-unit exponent becomes part of the cost snapshot (beside
  `currency`), and `money()` takes it. Breaks: `money()`'s signature and all 14 call sites across
  the four scripts; the rounding sites in `compose_report_data` (`:183, 191, 220, 292, 319, 333,
  334, 342, 419, 487, 500`) and `detect_orphans` (`:293, 409, 551`).
- **If ruled adapter-owned** — each adapter rounds to its own currency's minor unit before
  emitting, and `money()` becomes a coercion-only helper with no rounding. Breaks: the
  arithmetic-then-round order in `compose_report_data.service_totals` (`:191` sums rounded rows
  deliberately, *"so the column adds up on paper"*), which would need restating.
- **Consumers** — `detect_orphans` (`:274, 325, 286, 466, 517`), `compose_report_data`
  (`:177, 390, 404, 419, 420, 487`), **not** `render_report` (deliberately: `render_report.py:24–27`
  records that `money()`'s `0.0` fallback is wrong for a report, where absent must read as absent);
  `tests/test_compose_report_data.py:333`.

#### N6 · `provider_slug()` — `re.sub(r"[^a-z0-9]+", "-", …)` — `:97–107`
- **Meets** — the envelope's `provider` string.
- **Diverges today** — **no.** `digitalocean`, `aws`, `linode` are all already slug-safe.
- **Could diverge** — a provider name with a dot or a non-ASCII character (`e.on`, a CJK vendor
  name) would collapse to `-` and, for a fully non-ASCII name, to `"unknown"` — two providers could
  slug identically and overwrite each other's output file (D19).
- **If ruled schema-level** — the envelope's `provider` is constrained to a slug-safe token in
  §Normalized schemas and the function becomes a validator. Breaks: nothing today.
- **If ruled adapter-owned** — each adapter declares its own slug beside its display name. Breaks:
  `provider_slug` loses its only caller; `compose_report_data.slug` (P10) too.
- **Consumers** — `detect_orphans.main` (`:628`, output filename); `compose_report_data.slug` is a
  deliberate duplicate, frozen (P10).

#### N7 · `tags_of()` — element must be `str` — `:110–112`
See **X3** for the representation seam. The remaining local decision: a non-`str` element is
**dropped silently**, with no `skipped` entry and no warning.
- **Meets** — the resource entry's `tags` list elements.
- **Diverges today** — **no.** All three adapters emit `list[str]` by construction.
- **Could diverge** — an adapter emitting `[{k: v}]` would have every tag silently vanish, taking
  `tag_coverage` to 0.0 and turning off the untagged-in-tagged-account rule — a clean-looking zero.
- **If ruled schema-level** — the drop becomes a counted skip, surfaced the way
  `usable_resources` surfaces a malformed resource. Breaks: `tags_of`'s signature (it would need a
  skip sink); both callers.
- **If ruled adapter-owned** — each adapter guarantees `list[str]` and the filter is documented as
  defensive. Breaks: nothing today.
- **Consumers** — `has_keep_tag` (`:112`), `tag_coverage` (`:139`),
  `compose_report_data.coverage_section` (`:375`), `detect_orphans.detect` (`:504`).

#### N8 · `usable_resources()` — required-field set, presence not canonicality — `:115–132`
- **Meets** — the inventory's `resources[]` entries.
- **Diverges today** — **no**; all three adapters emit `resource_id` and `type` on every entry.
- **Could diverge** — this is BL-074's own t2 observation, confirmed: the check is
  `not resource.get("type")` (`:129`), so an **out-of-vocabulary** `type` passes as usable and then
  matches no rule, silently. A provider-four resource class outside `CANONICAL_TYPES` is counted in
  the tag-coverage denominator, counted in `totals.resources`, and evaluated by nothing.
- **If ruled schema-level** — `usable_resources` validates `type in CANONICAL_TYPES` and skips with
  a reason. Breaks: **the sprint's rule-legibility arm** — its `illegible` branch exists precisely
  because this validation is absent (`sprint.sh:3048`), and its `evaluated + skipped == resources`
  arm (`:3060`) would shift meaning; any fixture with a deliberately odd type;
  `tests/test_detect_orphans.py:866–870`.
- **If ruled adapter-owned** — each adapter guarantees canonical types and the gap is documented,
  with the sprint arm remaining the only enforcement. Breaks: nothing today, and it leaves the
  enforcement in a shell assertion rather than the module that owns the vocabulary.
- **Consumers** — `detect_orphans.detect` (`:483`), `compose_report_data.coverage_section`
  (`:371`), **`../aetheris/scripts/sprint.sh:3048–3060`** (all three arms),
  `tests/test_detect_orphans.py`, `tests/test_compose_report_data.py:606, 618`.

#### N9 · `tag_coverage()` — 4dp, empty → `0.0`, unweighted — `:135–140`
- **Meets** — the usable resource list from either stage.
- **Diverges today** — **no.**
- **Could diverge** — the ratio is per-resource and unweighted, so a provider whose inventory is
  dominated by cheap resources (many small volumes) reports high coverage while most *spend* is
  untagged, and vice versa. The 4dp rounding also fixes the resolution of the D7 threshold
  comparison.
- **If ruled schema-level** — the definition (per-resource, unweighted, 4dp) is stated in
  §Normalized schemas as the contract both stages must agree on — which is already the reason it
  lives here. Breaks: nothing.
- **If ruled adapter-owned** — not available: the whole reason this function is shared is that t2's
  and t3's figures are required to be equal (`_normalized.py:6–9`, `:118–120`). Recorded as a
  closed arm.
- **Consumers** — `detect_orphans.detect` (`:499`), `compose_report_data.coverage_section`
  (`:384, 412`), `tests/test_detect_orphans.py:438, 476`,
  `tests/test_compose_report_data.py:262, 270, 277, 851`.

### 3c. `detect_orphans.py` — the rule catalog

#### D1 · `UNATTACHED_VOLUME_MIN_AGE_DAYS = 14` — `:65` *(lead)*
- **Meets** — the resource's `created_at`, against the reference date.
- **Diverges today** — **no**; one global value, no adapter reads or overrides it.
- **Could diverge** — a provider billing volumes hourly with no minimum makes 14 days expensive
  to wait; one with a monthly minimum charge makes anything under 30 days pointless. This is
  BL-074's *"billing granularity"* case.
- **If ruled schema-level** — stays a global constant, with the rationale (why 14, not 7 or 30)
  recorded so the next provider has something to argue against. Breaks: nothing.
- **If ruled adapter-owned** — the inventory envelope or a per-provider config carries threshold
  overrides, and `Context` reads them per resource. Breaks: `Context.__init__`'s signature,
  `rule_unattached_volume`, the `parameters` echo (D22), the CLI's flag surface (only
  `--snapshot-age-days` exists today, D3), and the determinism claim in `detect()`'s docstring
  (`:479–481`) which would now depend on the inventory's own contents.
- **Consumers** — `rule_unattached_volume` (`:170, 181`), the `parameters` echo (`:529`),
  `tests/test_detect_orphans.py:80, 363, 374, 390, 418`.

#### D2 · `STOPPED_COMPUTE_MIN_AGE_DAYS = 30` — `:68` *(lead)*
- **Meets** — `created_at`, for **both** stopped rules.
- **Diverges today** — **no.** Deliberately one threshold for compute and databases
  (`:66–67`: *"a per-type fork would be a provider assumption wearing a type's clothes"*).
- **Could diverge** — the same billing-granularity case as D1, plus a per-type split: a provider
  where a stopped database's storage bills differently from a stopped instance's.
- **If ruled schema-level** — as D1. The existing comment is already a ruling in prose and should
  be promoted or replaced rather than left as a comment. Breaks: nothing.
- **If ruled adapter-owned** — as D1, and the compute/database sharing has to be re-decided,
  because an adapter overriding "the stopped threshold" now has to say which. Breaks: both stopped
  rules, `parameters` (`:530`), the shared-threshold rationale at `:66–67`.
- **Consumers** — `rule_stopped_compute_with_attached_storage` (`:268, 281`),
  `rule_stopped_database_with_storage` (`:329, 341`), `parameters` (`:530`),
  `tests/test_detect_orphans.py:173, 216`.

#### D3 · `DEFAULT_SNAPSHOT_AGE_DAYS = 30` — `:69`, overridable via `--snapshot-age-days` *(lead)*
- **Meets** — `created_at`, for both snapshot types.
- **Diverges today** — **no**; the sprint and every test use the default.
- **Could diverge** — as D1/D2, and note the asymmetry: this is the **only** age threshold with a
  CLI override. That asymmetry is itself the item — either all three are tunable or none is, and
  today the choice is unexplained.
- **If ruled schema-level** — the constant stays and the CLI override is documented as the
  operator-facing escape hatch the other two deliberately lack. Breaks: nothing.
- **If ruled adapter-owned** — as D1, and the CLI flag either goes or becomes an override-of-an-
  override. Breaks: `parse_args` (`:600–605`), `detect()`'s signature, `main` (`:623`).
- **Consumers** — `rule_aged_snapshot` (`:213, 217` via `ctx.snapshot_age_days`), `parse_args`
  (`:603–604`), `detect` (`:476`), `parameters` (`:528`), `tests/test_detect_orphans.py:139`
  (pins the value directly).

#### D4 · `RECENT_ACTIVITY_WINDOW_DAYS = 14` — `:78`
- **Meets** — `last_activity_at`. See **X4**: that field is `None` on all three adapters, so this
  threshold has never been exercised outside tests.
- **Diverges today** — **no**, vacuously.
- **Could diverge** — the window is meaningful only relative to a provider's activity-signal
  resolution; a provider reporting last-access daily and one reporting it hourly do not want the
  same window.
- **If ruled schema-level** — stays global, with X4's universal-null status recorded beside it so
  the constant is not read as tuned. Breaks: nothing.
- **If ruled adapter-owned** — travels with the capability declaration in X4. Breaks: as X4.
- **Consumers** — `modifier_recent_activity` (`:372, 380`), `parameters` (`:531`),
  `tests/test_detect_orphans.py:419`.

#### D5 · `EPHEMERAL_NAME_PATTERN = re.compile(r"^(tmp-|ci-|test-)")` — `:81`, case-sensitive *(lead)*
- **Meets** — the resource entry's `name`.
- **Diverges today** — **no**; no adapter influences it.
- **Could diverge** — naming conventions are an *account* property, not a provider property, which
  makes this the weakest schema-level candidate and the strongest candidate for a third category
  (neither schema nor adapter, but operator config). Separately, case-sensitivity is a real
  divergence surface: AWS resource names arriving from a `Name` tag are frequently capitalised
  (`fetch_aws.py:442`, `name_from_tags`), so `Tmp-worker` does not match while `tmp-worker` does —
  and `KEEP_TAG` (D6) case-folds where this does not. Two adjacent string matches in one module
  with opposite case policies.
- **If ruled schema-level** — the pattern stays global and its case policy is stated (the `:80`
  comment says *"Matched case-sensitively, as written"*, which records the behaviour but not the
  reason). Breaks: nothing.
- **If ruled adapter-owned** — wrong home on the evidence: the pattern describes tenant naming, not
  provider vocabulary. The available third option — operator-supplied — is recorded, not urged.
  Breaks: `modifier_ephemeral_name`, `MODIFIERS`, and the evidence string at `:398–399` which
  prints the pattern source into the report.
- **Consumers** — `modifier_ephemeral_name` (`:391, 399`), the rendered evidence sentence,
  `tests/test_detect_orphans.py:419`.

#### D6 · `KEEP_TAG = "keep=true"` and its match predicate — `:84`, matched at `:112` (`tag.strip().lower() == KEEP_TAG`) *(lead)*
- **Meets** — the resource's `tags` list, post-`tags_of`.
- **Diverges today** — **yes, in reachability.** The `k=v` spelling is native only on AWS, whose
  adapter constructs it (`fetch_aws.py:438`). On DO and Linode a tag is a flat string, so
  `keep=true` must be typed literally as a tag name; `docs/m3-linode-scout.md:925–928` establishes
  this for Linode — *"writable by hand but not a native key/value construct"* — and DO is the same
  shape (`fetch_do.py:245`). BL-074 already calls this *"an adapter convention masquerading as a
  shared constant"*; the census confirms it and adds the case-folding: `.lower()` here versus
  case-**sensitive** matching in D5.
- **Could diverge** — a provider with reserved tag namespaces, a different separator, or
  case-sensitive tag keys (where `Keep=true` and `keep=true` are distinct tags and folding merges
  two different intents).
- **If ruled schema-level** — the exclusion marker becomes a first-class normalized field
  (`keep: bool` on the resource entry), each adapter decides how its own tag surface expresses it,
  and shared machinery reads a boolean rather than parsing a string. Breaks: `has_keep_tag`,
  `detect()`'s exclusion branch (`:488–491`) and its `reason` text, all three adapters, every
  fixture carrying a keep tag.
- **If ruled adapter-owned** — each adapter declares its own keep-tag spelling and shared
  machinery reads it from the envelope. Breaks: `has_keep_tag`'s signature (it would need the
  inventory, not just the resource), and the `excluded[].reason` string at `:490` which prints the
  constant.
- **Consumers** — `has_keep_tag` (`:112`), `detect` (`:488, 490`), the rendered `excluded` list;
  `tests/test_detect_orphans.py`; **not** the sprint case.

#### D7 · `TAGGED_ACCOUNT_COVERAGE_THRESHOLD = 0.5`, strict `>` — `:88`, applied at `:500` *(lead)*
- **Meets** — `tag_coverage(resources)` over the whole usable inventory.
- **Diverges today** — **no.**
- **Could diverge** — the threshold decides whether the untagged-in-tagged-account governance rule
  fires **at all**, so it is a cliff: an account at 0.50 coverage reports nothing and one at 0.5001
  reports every untagged resource. Combined with N9's 4dp rounding, the cliff sits at a specific
  representable value. A provider whose resource classes largely cannot carry tags (Linode: IP
  addresses, backups and Managed Databases carry none — `docs/m3-linode-scout.md:921–922`) has its
  coverage structurally depressed by untaggable resources and can never cross the threshold, so the
  governance rule silently never fires on that provider.
- **If ruled schema-level** — stays global; the untaggable-resource-class distortion is recorded,
  and possibly the denominator becomes taggable-resources-only. Breaks: the denominator change
  would move `tag_coverage` (N9), which is contractually shared with t3 — so it is not a local edit.
- **If ruled adapter-owned** — the adapter declares which of its resource classes can carry tags,
  and the threshold is applied against a taggable denominator. Breaks: `tag_coverage`'s definition,
  therefore both stages, therefore the t2==t3 equality that is `_normalized.py`'s stated reason for
  existing.
- **Consumers** — `detect.account_uses_tags` (`:500`), the `reported` block (`:513–514, 541`),
  the evidence string that prints it as `{:.0%}`, `tests/test_detect_orphans.py:438, 476`.

#### D8 · The six `CONFIDENCE_*` base confidences — `:57–62` *(grouped; one ruling surface)*
`UNATTACHED_VOLUME 0.9` · `UNASSOCIATED_STATIC_IP 0.95` · `AGED_SNAPSHOT 0.7` ·
`IDLE_LOAD_BALANCER 0.85` · `STOPPED_COMPUTE_WITH_STORAGE 0.6` · `STOPPED_DATABASE_WITH_STORAGE 0.6`
- **Meets** — nothing adapter-supplied directly; each is the prior probability that a rule's
  firing means the resource is genuinely an orphan **on that provider**.
- **Diverges today** — **no.**
- **Could diverge** — the confidences encode how reliably a signal indicates waste, which is a
  provider fact. `attached_to is null` on a static IP is near-certain waste on a provider that
  charges for unassociated IPs (AWS, DO) and means nothing on one that does not charge for them at
  all. The banding (P1) then converts these into the HIGH/MEDIUM/LOW the report leads with, so a
  provider-wrong confidence is a provider-wrong headline.
- **If ruled schema-level** — the values stay global and are documented as cross-provider priors,
  with the reasoning recorded. Breaks: nothing.
- **If ruled adapter-owned** — the adapter supplies per-rule confidence adjustments, or the rule
  catalog becomes per-provider. Breaks: `fired()`'s callers (6 sites), `score()` (`:447–455`),
  every confidence assertion in `tests/test_detect_orphans.py` (`:80, 98, 114, 150, 173, 216, 268,
  363, 374, 380, 390, 418`) and `tests/test_compose_report_data.py:402` — 13 pinned values.
- **Consumers** — the six rules; `score` (`:447`); `compose_report_data.band_of` (`:430`) via the
  scored value; the report's band headline; the 13 tests above.

#### D9 · `MODIFIER_RECENT_ACTIVITY = -0.2`, `MODIFIER_EPHEMERAL_NAME = +0.1`, and `clamp` to `[0.0, 1.0]` — `:72–73`, `:409`
- **Meets** — a scored candidate's confidence, additively.
- **Diverges today** — **no.** X4 makes the `-0.2` unreachable on all three providers.
- **Could diverge** — the deltas' *size relative to the band cutoffs* (P1) is what matters: a
  `-0.2` moves a 0.9 candidate from HIGH to MEDIUM but a 0.95 one only to HIGH's boundary. Whether
  that is right depends on how much a provider's activity signal is worth, which is D4/X4's
  question. `clamp` also silently absorbs any over/under-shoot, so a modifier set that is too
  strong is invisible rather than erroneous.
- **If ruled schema-level** — the deltas stay global and the additive-then-clamp model is
  documented as the contract the bands are calibrated against. Breaks: nothing.
- **If ruled adapter-owned** — as D8. Breaks: `score` (`:453`), `tests/test_detect_orphans.py:419`
  (`0.9 - 0.2 + 0.1`), `:428` (`clamp(-0.3) == 0.0`).
- **Consumers** — `score` (`:453`), both modifiers' evidence strings (`:381, 400`),
  `tests/test_detect_orphans.py:419, 428`.

#### D10 · `STOPPED_STATES = frozenset({STATE_STOPPED})` — `:93`, applied at `:265` and `:321`
- **Meets** — the resource's `state`.
- **Diverges today** — **no.** m1's named seam, closed at m2 t2 a. It is now a one-element set
  derived from N2, which is why the item is here as a *closed* seam rather than an open one.
- **Could diverge** — only if X1 widens the state vocabulary; a provider distinguishing
  `deallocated` (no compute charge) from `suspended` (charged) would need both in the set, with
  different savings.
- **If ruled schema-level** — it already is. The residual question is whether a one-element
  frozenset should still exist as a separate name from `STATE_STOPPED`; today it is a seam marker
  kept for the history, and `tests/test_detect_orphans.py:234` asserts the derivation.
- **If ruled adapter-owned** — would re-open seam #1; available, contrary to the ruling already
  taken. Breaks: both stopped rules, `tests/test_detect_orphans.py:233–234, 253`.
- **Consumers** — both stopped rules; `tests/test_detect_orphans.py:233–234`, and `:253` which
  asserts the **source text** `'resource.get("state") not in STOPPED_STATES'` appears in the rule
  bodies — so renaming this constant breaks a test that reads source, not behaviour.

#### D11 · `SNAPSHOT_TYPES = frozenset({TYPE_SNAPSHOT, TYPE_DATABASE_SNAPSHOT})` — `:99`
- **Meets** — the resource's `type`.
- **Diverges today** — **yes, by coverage.** `TYPE_DATABASE_SNAPSHOT` is emitted by AWS alone
  (N1), so on DO and Linode this set is effectively `{snapshot}`.
- **Could diverge** — a provider with a third snapshot kind (volume-group snapshot, AMI/image
  distinct from snapshot). Linode already emits images *as* `TYPE_SNAPSHOT`
  (`fetch_linode.py` image normalizer), which is a mapping decision made in the adapter — the
  correct place, and worth recording as such.
- **If ruled schema-level** — the set stays here and widens with the vocabulary. Breaks: nothing.
- **If ruled adapter-owned** — an adapter declares which of its types are snapshot-shaped. Breaks:
  `rule_aged_snapshot` (`:210`), `tests/test_detect_orphans.py:851`.
- **Consumers** — `rule_aged_snapshot` (`:210`), `tests/test_detect_orphans.py:851`.

#### D12 · The age comparison convention — strict-greater, via `age <= threshold → no fire`, and `/ 86400.0` — `:135`, `:170`, `:213`, `:268`, `:329`, `:141`
- **Meets** — `created_at` against the reference date.
- **Diverges today** — **no.**
- **Could diverge** — three coupled decisions, none of which is a named constant and none of which
  a grep reaches. (1) Age is a **float** of days (`/ 86400.0`), so `age <= 14` excludes exactly
  14.0 days; the `:64` comment states the intent (*"strictly greater"*). (2) `age_phrase` prints
  `int(age)` (`:141`), **truncating**, so a resource of age 14.9 days renders as `14d` beside a
  `threshold >14d` that it did fire against — the evidence sentence reads as a contradiction. (3) A
  provider billing in whole days from a rounded creation time makes the fractional part meaningless.
- **If ruled schema-level** — the convention (float days, strict-greater, truncated display) is
  stated once in §Normalized schemas and the display truncation is fixed or documented. Breaks:
  the evidence strings only.
- **If ruled adapter-owned** — not available: age arithmetic is over normalized timestamps and
  belongs to no adapter. Recorded as a closed arm; the *thresholds* it compares against are D1–D4.
- **Consumers** — `Context.age_days` (`:130–135`), `age_phrase` (`:137–145`), all four age-gated
  rules, `modifier_recent_activity` (`:372`).

#### D13 · The stopped-compute **sum** billing assumption — `:293` (`saving = round(own + storage_total, 2)`)
- **Meets** — the instance's own `monthly_cost_estimate` plus every attached volume's.
- **Diverges today** — **yes, and the divergence is the design.** `:256–261` records it: DO bills
  a stopped droplet in full (own = full price), AWS bills no compute for a stopped instance
  (own = 0.0, and the EBS volume carries the charge). The sum is correct for both *because* each
  adapter encoded its own cost model. This is seam #3, closed at m2 t2 c, and it is the model the
  other items should be ruled against.
- **Could diverge** — the assumption that survives is *"only separately-inventoried storage is
  summed"* (`:260–261`). A provider that inventories storage separately **and** folds its cost into
  the instance's estimate would be double-counted, and nothing detects that. The census cannot rule
  it out from the three adapters — all three currently satisfy the assumption — so it is stated as
  the surviving risk rather than as a defect.
- **If ruled schema-level** — the cost snapshot declares whether storage is priced into the
  instance estimate, and the rule reads that flag. Breaks: the envelope (a new field), all three
  adapters, `rule_stopped_compute_with_attached_storage`, its evidence text.
- **If ruled adapter-owned** — the double-count risk is documented as a per-adapter obligation
  (*"a stopped instance's own estimate must exclude separately-inventoried storage"*) and asserted
  in each adapter's tests. Breaks: nothing in shared machinery; adds a per-adapter test obligation
  that does not exist today.
- **Consumers** — `rule_stopped_compute_with_attached_storage` (`:274–303`), `fired`'s `saving`
  override (`:148–155`), `score` (`:465–469`), `tests/test_detect_orphans.py:173`.

#### D14 · `own <= 0` — the storage-still-bills signal, database only — `:326`
- **Meets** — the database resource's `monthly_cost_estimate`.
- **Diverges today** — **vacuously no**: `TYPE_DATABASE` is AWS-only (N1), so this predicate runs
  on one provider.
- **Could diverge** — the predicate encodes *"a non-zero estimate on a stopped database means its
  allocated storage still bills"* (`:308–314`). That inference holds for RDS. On a provider that
  bills a stopped database's compute too, a non-zero estimate means something else and the saving
  is right for the wrong reason; on one that bills nothing, the rule correctly never fires. See
  also **F2**.
- **If ruled schema-level** — the storage-still-bills fact becomes explicit in the schema rather
  than inferred from a number's sign. Breaks: the rule's predicate and its evidence string
  (`:344–346`), the AWS adapter.
- **If ruled adapter-owned** — the inference is documented as an adapter obligation (*"a stopped
  database's estimate is exactly its still-billing storage"*). Breaks: nothing today; makes the
  AWS adapter's cost model load-bearing for a shared rule's correctness.
- **Consumers** — `rule_stopped_database_with_storage` (`:326`),
  `tests/test_detect_orphans.py:216`.

#### D15 · `attached_to` as the universal idle signal, and the join key `attached_to == resource_id` — `:167`, `:190`, `:220`, `:235`, `:323`; join at `:123–128`
- **Meets** — the resource entry's `attached_to`, joined against another entry's `resource_id`.
- **Diverges today** — **no** in shape; **yes** in what the adapters put there. AWS uses
  `instances[0] if instances else None` for a classic LB (`:652`) and
  `None if stopped else identifier` for a database (`:682`); DO uses `str(droplet_ids[0])`
  (`:369`). So the field is a single opaque string that different adapters derive differently, and
  where a resource has *several* attachments only the first is represented.
- **Could diverge** — a provider with genuinely many-to-many attachment (a volume mounted to
  several instances, an IP with several bindings) cannot express it, and the join at `:123–128`
  would under-report attached storage — which lowers the saving in D13, silently.
- **If ruled schema-level** — `attached_to` becomes a list, or gains a companion
  `attached_to_all`. Breaks: all five rule predicates, the `Context` join, every adapter, every
  fixture, and the `"tag:<name>"` convention in D16.
- **If ruled adapter-owned** — the one-attachment-only limitation is documented as a schema
  constraint each adapter must reduce to, with the reduction rule (first, or most significant)
  stated per adapter. Breaks: nothing today; makes `instances[0]` a contract rather than an
  accident.
- **Consumers** — all five rules that test it, `Context.volumes_by_attachment` (`:123–128`),
  `compose_report_data` (does not read it), the evidence strings at `:176, 192, 221, 241`.

#### D16 · The `"tag:<name>"` spelling — `:242` (evidence text), premise at `:230–232`
- **Meets** — the `attached_to` value a load balancer carries.
- **Diverges today** — **no**; the convention originates in m1's DO normalizer and no other
  adapter produces it. AWS's classic-LB path emits `instances[0]` and its v2 path `attached_to`,
  neither prefixed (`fetch_aws.py:620–652`).
- **Could diverge** — this is a **provider-specific string format described in shared machinery**,
  and it is the load-bearing premise of `rule_idle_load_balancer`: the rule is only correct because
  a tag-targeted LB is assumed to carry `attached_to == "tag:<name>"` and so never reach it. An
  adapter that does not follow the convention makes every tag-targeted LB an idle-LB candidate at
  0.85 confidence — a HIGH-band false positive. Nothing enforces the convention and no test asserts
  it.
- **If ruled schema-level** — the `tag:` prefix becomes part of the §Normalized schemas definition
  of `attached_to`, with the grammar stated. Breaks: nothing in code; adds an adapter obligation
  that AWS and Linode must be checked against.
- **If ruled adapter-owned** — the rule stops relying on a string prefix and reads a first-class
  field (e.g. `attachment_kind`), or the premise is dropped and the rule accepts the false
  positives. Breaks: `rule_idle_load_balancer`'s docstring premise, its evidence text, and any
  adapter emitting the prefix.
- **Consumers** — `rule_idle_load_balancer` (`:227–245`), the rendered evidence sentence.

#### D17 · `resolve_reference_date` — the fallback chain — `:562–577`
- **Meets** — the inventory envelope's `generated_at`.
- **Diverges today** — **no**; all three adapters emit `generated_at`.
- **Could diverge** — the third branch reads the **wall clock** (`:577`), which is the one place
  this otherwise-deterministic module is not. An adapter that omits or malforms `generated_at`
  turns every age rule non-reproducible, silently — `detect()`'s docstring claim of byte-identical
  output (`:479–481`) then holds only for the arguments, not for the file.
- **If ruled schema-level** — `generated_at` is required and the wall-clock branch raises rather
  than falling back. Breaks: any inventory without the field; `main`'s error path would widen.
- **If ruled adapter-owned** — each adapter guarantees `generated_at` and the fallback is
  documented as unreachable defensive code. Breaks: nothing today.
- **Consumers** — `main` (`:616`), `detect` (`:484`), everything age-gated.

#### D18 · The output filename `{provider}_orphan_candidates_{period}.json`, and `period or "unknown"` — `:624–630`
- **Meets** — the envelope's `provider` (via N6) and `period`.
- **Diverges today** — **no**; the three slugs are distinct.
- **Could diverge** — two providers slugging identically (N6) overwrite each other, which is the
  m1 open item closed at m2 t2 b returning by a different route. Separately, `period or "unknown"`
  means a provider that cannot report a period writes `..._unknown.json`, and a second such
  provider overwrites the first.
- **If ruled schema-level** — `provider` and `period` are required and slug-unique, stated in
  §Normalized schemas. Breaks: nothing today.
- **If ruled adapter-owned** — each adapter declares a unique slug (see N6). Breaks: `provider_slug`
  loses its caller.
- **Consumers** — `main` (`:628–631`), the sprint's artifact discovery
  (`sprint.sh:3040–3042`, `pick("*_orphan_candidates_*.json")` — which requires **exactly one**
  match, so a second provider's file in the same output directory fails the guard arm),
  `compose_report_data.discover_bundles` (`:706`).

#### D19 · `identity()` — the five carried fields — `:415–424`
- **Meets** — `resource_id`, `type`, `name`, `region`, `raw_ref` on the resource entry.
- **Diverges today** — **no**, all five are emitted by all three adapters. `raw_ref` is a
  provider-console URL and is by construction provider-shaped, correctly built in each adapter.
- **Could diverge** — `region` is the interesting one: it is carried and rendered but never
  compared, so a provider with no region concept (or a global resource) emits `None` and the report
  shows a blank column. A provider with a two-level region/zone hierarchy has nowhere to put the
  second level.
- **If ruled schema-level** — `region` gains an optional companion (`zone`), or is documented as
  a single opaque display string. Breaks: nothing for the documentation route.
- **If ruled adapter-owned** — the adapter flattens its own hierarchy into the one string, stated
  as an obligation. Breaks: nothing today.
- **Consumers** — `score` (`:457`), `detect`'s `excluded` and `untagged` blocks (`:490, 508`),
  `compose_report_data.orphan_section` (carries candidates through intact), the report's tables.

#### D20 · `timestamp_warnings` field pair `("created_at", "last_activity_at")` — `:431`
- **Meets** — the two timestamp fields of the resource entry.
- **Diverges today** — **no.**
- **Could diverge** — the tuple is a hardcoded restatement of *"the timestamp fields the schema
  has"*. A third timestamp added to the schema is not checked here unless someone remembers this
  line — the same duplication class as a hand-typed vocabulary, one level down.
- **If ruled schema-level** — the timestamp field set is named once in `_normalized.py` and both
  this function and the schema doc read it. Breaks: nothing; it is an additive extraction.
- **If ruled adapter-owned** — not available: the field set is the schema's, not any adapter's.
  Recorded as a closed arm.
- **Consumers** — `detect` (`:546`), the `warnings` block, the `partial` exit decision (`:633`),
  the sprint's `status` read.

#### D21 · The `parameters` echo — which thresholds are declared — `:527–533`
- **Meets** — nothing adapter-supplied; it is the self-description of the run.
- **Diverges today** — **no.**
- **Could diverge** — five thresholds exist as constants (D1–D4 plus the snapshot parameter) and
  five are echoed, so today it is complete. But the completeness is by hand: the six
  `CONFIDENCE_*`, the two modifier deltas, `KEEP_TAG`, `EPHEMERAL_NAME_PATTERN` and the band
  cutoffs are **not** echoed, so a report cannot state the full parameterization it was produced
  under. If any threshold becomes adapter-owned (D1–D4's second arm), this block is where that has
  to surface or the report silently stops describing itself.
- **If ruled schema-level** — the echo is declared to cover exactly the age thresholds and the
  coverage threshold, stated as such. Breaks: nothing.
- **If ruled adapter-owned** — the block must carry per-provider values, so it becomes a list
  rather than a mapping. Breaks: the payload shape, `compose_report_data` (which does not read it
  today — recorded as a negative), any consumer added later.
- **Consumers** — the emitted `orphan_candidates` payload only. **Not** read by
  `compose_report_data`, **not** by `render_report`, **not** by the sprint — so today it is
  write-only, which is itself worth the arbiter knowing.

### 3d. Class F — structural absences (found by the predicate diff, §2.3)

#### F1 · `rule_idle_load_balancer` has **no** age threshold, and no stated reason — `:227–245`
- **Meets** — nothing; the absence is the item. The rule fires on `type == load_balancer` and
  `attached_to is None`, with no age gate at all.
- **Diverges today** — **no**, in the sense that no adapter changes it. But it is the only rule
  whose missing age gate is **unexplained**: `rule_unassociated_static_ip` also has none and says
  why (F4). A load balancer created ten minutes ago, still being wired up, is a 0.85-confidence
  HIGH-band candidate.
- **Could diverge** — whether a zero-backend LB bills from creation is a provider fact. DO bills a
  load balancer per node from creation (`fetch_do.py:68`, `LOAD_BALANCER_NODE_MONTHLY`); AWS bills
  an ALB/NLB hourly from creation (`fetch_aws.py:148`). Both support the absence — but the absence
  is currently an accident, not a recorded decision, and a provider with a free grace period would
  need one.
- **If ruled schema-level** — an `IDLE_LOAD_BALANCER_MIN_AGE_DAYS` constant joins D1–D3, or the
  absence is documented the way F4's is. Breaks: nothing for the documentation route; adding a
  threshold changes the rule's firing set and `tests/test_detect_orphans.py:150`.
- **If ruled adapter-owned** — travels with D1–D3's second arm. Breaks: as D1.
- **Consumers** — `rule_idle_load_balancer` (`:227–245`), `tests/test_detect_orphans.py:150`.

#### F2 · `own <= 0` is applied to the stopped **database** rule and not to the stopped **compute** rule — `:326` vs `:248–303`
- **Meets** — `monthly_cost_estimate` on a stopped resource.
- **Diverges today** — **yes, and it is deliberate but asymmetric.** The compute rule requires
  attached storage instead (`:271`), so a stopped instance whose own estimate is 0.0 (AWS) and
  which has one attached volume still yields a candidate whose saving is the volume's cost. A
  stopped instance with **no** attached storage and a non-zero own estimate (DO, where a stopped
  droplet bills in full) yields **nothing** — the rule returns at `:272`. That is a real
  provider-differing gap: the DO case that costs the most money is the one case neither stopped
  rule covers.
- **Could diverge** — it already does, between DO and AWS, in opposite directions.
- **If ruled schema-level** — a third rule (stopped compute, no storage, non-zero own estimate),
  or the compute rule's `not attached` return becomes `not attached and own <= 0`. Breaks:
  `rule_stopped_compute_with_attached_storage`'s firing set, its saving arithmetic, its evidence
  text, `tests/test_detect_orphans.py:173`, and the sprint's candidate counts.
- **If ruled adapter-owned** — the gap is documented per provider (*"on a provider that bills
  stopped compute, an unattached stopped instance is not detected"*). Breaks: nothing; leaves a
  known blind spot recorded rather than closed.
- **Consumers** — both stopped rules; `tests/test_detect_orphans.py:173, 216`.

#### F3 · `rule_aged_snapshot` treats `attached_to is None` as **evidence**, every other rule treats it as a **gate** — `:220` vs `:167, 190, 235, 323`
- **Meets** — `attached_to` on a snapshot.
- **Diverges today** — **no.**
- **Could diverge** — the rule's docstring calls the heuristic *"age plus a source that is gone"*
  (`:205–207`), but the code requires only age; the source-is-gone half is appended as an evidence
  sentence when true and silently omitted when false. So a snapshot of a **live** volume fires at
  the same 0.7 confidence as one whose source is deleted, and the two are distinguishable in the
  report only by an evidence line's presence. On a provider where snapshots of live volumes are
  routine backups, that is a systematic false-positive source; on one where they are not, it is
  harmless.
- **If ruled schema-level** — either the gate is added (matching the docstring) or the docstring
  and the confidence are corrected to describe an age-only rule. Breaks: adding the gate changes
  the firing set and `tests/test_detect_orphans.py:114, 268`.
- **If ruled adapter-owned** — the adapter declares whether snapshots-of-live-sources are routine,
  and the rule reads it. Breaks: the envelope, all three adapters.
- **Consumers** — `rule_aged_snapshot` (`:202–224`), `tests/test_detect_orphans.py:114, 268, 380`.

#### F4 · `rule_unassociated_static_ip` has no age threshold, **with** a stated reason — `:187–199`
- **Meets** — `attached_to` on a static IP; no timestamp gate.
- **Diverges today** — **no.**
- **Could diverge** — the stated reason (`:188–189`: *"an unassociated static IP bills from the
  moment it is unassociated"*) is a **billing assumption about two named providers** — a DO
  reserved IP and an AWS Elastic IP — sitting in shared machinery, and it is confirmed by both
  adapters' price constants (`fetch_aws.py:145` `ELASTIC_IP_UNASSOCIATED_MONTHLY = 3.65`,
  `fetch_do.py:67` `RESERVED_IP_UNASSIGNED_MONTHLY = 4.38`). A provider that charges for static IPs
  whether associated or not, or not at all, breaks it. Recorded as the **positive control for
  class F**: this is what a documented absence looks like, and F1 is the same absence undocumented.
- **If ruled schema-level** — the assumption is stated in §Normalized schemas rather than in a
  rule's docstring, so a new adapter meets it as a contract. Breaks: nothing.
- **If ruled adapter-owned** — the adapter declares whether unassociated IPs bill immediately, and
  the rule reads the flag. Breaks: the envelope, all three adapters, the rule's evidence text
  (`:197`).
- **Consumers** — `rule_unassociated_static_ip` (`:187–199`), `tests/test_detect_orphans.py:98`.

### 3e. `compose_report_data.py`

#### P1 · `BAND_HIGH_MIN = 0.9`, `BAND_MEDIUM_MIN = 0.7` — `:55–56`, applied at `:430–435`
- **Meets** — the candidate's `confidence`, which D8/D9 produced.
- **Diverges today** — **no.**
- **Could diverge** — the cutoffs sit exactly on D8's values: `0.9` (unattached volume) and
  `0.7` (aged snapshot) are *both* band boundaries, so those two rules land in HIGH and MEDIUM by
  equality, and any per-provider confidence adjustment (D8's second arm) of even −0.01 moves a
  whole rule's output down a band. The bands are the report's headline grouping, so this is where a
  provider-differing confidence becomes a provider-differing conclusion.
- **If ruled schema-level** — the cutoffs stay global and their coincidence with D8's values is
  documented as intentional calibration rather than left to be rediscovered. Breaks: nothing.
- **If ruled adapter-owned** — bands become per-provider, which breaks the section's premise:
  `orphan_section` groups candidates from **all** providers into shared bands (`:441–444`), so
  per-provider cutoffs would make a band heterogeneous. Breaks: `BANDS`, `band_of`,
  `orphan_section`'s grouping, the emitted `bands` block the report renders as its cutoff legend,
  `tests/test_compose_report_data.py:402`.
- **Consumers** — `BANDS` (`:58–77`), `band_of` (`:430`), `orphan_section` (`:477, 486`), the
  rendered band legend, `templates/report.html.j2`, `tests/test_compose_report_data.py:402`.

#### P2 · `DEFAULT_TOP_UNTAGGED = 10` — `:80`, overridable via `--top-untagged`
- **Meets** — the untagged resource list, ranked by `monthly_cost_estimate`.
- **Diverges today** — **no.**
- **Could diverge** — the cap is applied **across all providers combined** (`:407`,
  `untagged[:top_untagged]` after a global sort), so at N=3 a provider with cheap resources can be
  entirely absent from the table while another fills all ten rows. That is a silent cap of exactly
  the kind decision D forbids elsewhere in this same file (`:530–534`, the region-coverage
  rationale) — and unlike the region list, nothing reports the truncation.
- **If ruled schema-level** — the cap becomes per-provider, or the payload records how many were
  dropped. Breaks: `coverage_section`'s return shape (`:396–408`), the report's table,
  `tests/test_compose_report_data.py:329–330`.
- **If ruled adapter-owned** — not available: the ranking is cross-provider by construction.
  Recorded as a closed arm; the reportable-truncation question stays open under the other.
- **Consumers** — `coverage_section` (`:407, 418`), `parse_args` (`:801`), the report's
  spenders table, `tests/test_compose_report_data.py:329–330`.

#### P3 · `RECONCILE_TOLERANCE = 0.01` — `:90`, applied at `:194`
- **Meets** — a provider's declared `totals.amount` against the sum of its `line_items[].amount`.
- **Diverges today** — **no**; all three adapters declare `source_granularity: "service"`
  (`fetch_aws.py:747`, `fetch_do.py:304`, `fetch_linode.py:554`), so line items and totals come
  from the same granularity.
- **Could diverge** — the tolerance is **absolute and currency-unit-denominated**: one cent. For a
  provider billing in a zero-decimal currency (N5) one unit is not one cent; for a large account,
  a proportional discrepancy well under a rounding error can exceed 0.01 absolute and warn
  spuriously; for a provider whose totals include tax that the line items do not (Linode carries a
  `TAX_SERVICE = "Tax"` constant, `fetch_linode.py:116`), the difference is structural rather than
  arithmetic.
- **If ruled schema-level** — the tolerance becomes relative, or is stated per currency alongside
  N5's minor-unit exponent. Breaks: `service_totals`'s reconcile branch (`:194–202`), the
  `reconciled` flag in the payload, the report's reconciliation note.
- **If ruled adapter-owned** — the adapter declares its own tolerance, or guarantees exact
  reconciliation. Breaks: the envelope, all three adapters.
- **Consumers** — `service_totals` (`:194`), the `by_provider[].reconciled` flag, the report's
  cost table, `month_on_month` (which re-runs `service_totals` over prior snapshots at `:276`, so
  the tolerance also governs historical data).

#### P4 · `prior_period` — the `\d{4}-\d{2}` period grammar and calendar-month assumption — `:103–112`
- **Meets** — the envelope's `period` from every document.
- **Diverges today** — **no**; all three adapters emit `YYYY-MM`.
- **Could diverge** — a provider billing on a non-calendar cycle (a 30-day anniversary cycle, or
  AWS's own consolidated-billing periods) cannot express its period here, and the failure is
  **silent in a specific way**: `prior_period` returns `None`, `month_on_month` reports
  `no_prior_month`, and `persist_history` writes nothing at all (`:741–743`) — so a provider on a
  non-calendar cycle gets a report with no month-on-month section and no persisted history,
  forever, with no warning.
- **If ruled schema-level** — `period` is specified as a calendar month in §Normalized schemas and
  a non-conforming value is a contract violation that warns. Breaks: `persist_history`'s silent
  return, `month_on_month`'s clean path.
- **If ruled adapter-owned** — each adapter maps its own cycle onto a calendar month and declares
  the mapping. Breaks: nothing in shared machinery; adds an adapter obligation.
- **Consumers** — `month_on_month` (`:258`), `persist_history` (`:741`), `load_prior_snapshots`
  (`:759`), `main` (`:863`), the history tree layout,
  `tests/test_compose_report_data.py:231, 244`.

#### P5 · The currency policy — one currency → scalar, otherwise `null` — `:217–236`, and the `"UNKNOWN"` bucket at `:219`
- **Meets** — each cost snapshot's `currency`.
- **Diverges today** — **no.** All three declare `USD`, so `grand_total` is always a scalar and
  the multi-currency branch has never fired outside tests.
- **Could diverge** — this is the item where the *absence* of divergence is load-bearing: the
  first non-USD provider makes `grand_total` `null` and `totals.cost_grand_total` `null`, which
  `render_report.format_amount` renders as an em dash (R2). So adding one EUR provider silently
  blanks the report's headline number for **every** provider. The behaviour is correct and
  deliberate (`:222–224`, *"a number with no meaning"*), and its blast radius is not recorded
  anywhere the operator would see.
- **If ruled schema-level** — conversion arrives (out of m1 scope by decision), or the report
  states per-currency headlines as first-class rather than as a fallback. Breaks: the `totals`
  block, the report header, `render_report`'s `nz` filter usage.
- **If ruled adapter-owned** — each adapter declares its currency (it does) and the *policy* stays
  shared. Recorded: this arm is effectively already taken for the value, and the open question is
  only about the policy.
- **Consumers** — `service_totals` (`:217–246`), `month_on_month` (`:339`), `compose`'s `totals`
  (`:650`), `render_report.currencies_by_provider` (`:175–184`), the report header and every
  amount cell.

#### P6 · `item.get("service") or "Unknown"` — `:176`
- **Meets** — a cost line item's `service` field.
- **Diverges today** — **no** in shape; **yes** in vocabulary. Service names are raw provider
  strings and are never normalized: AWS emits Cost Explorer service names, DO emits its own, Linode
  emits its own plus the literal `"Tax"` (`fetch_linode.py:116`). They are grouped by exact string
  (`:177`) and rendered verbatim.
- **Could diverge** — it already does; the consequence surfaces in `month_on_month`, which keys
  the delta on `(provider, service)` (`:279–280`), so **any** change in a provider's service naming
  between two months reports the old name as `removed` and the new one as `new`, with a full
  swing in both directions and no indication they are the same service.
- **If ruled schema-level** — a canonical service vocabulary, or a stable `service_id` beside the
  display name. Breaks: `service_totals`'s grouping, `month_on_month`'s keying, the history format
  (prior snapshots on disk carry the old names), all three adapters.
- **If ruled adapter-owned** — service names are documented as opaque provider strings whose
  stability across months is an adapter obligation. Breaks: nothing today; makes the MoM section's
  correctness depend on a provider's naming stability, which should then be said out loud.
- **Consumers** — `service_totals` (`:176–177`), `month_on_month` (`:279–283`), the report's
  service table and delta table, `tests/test_compose_report_data.py:231, 244`.

#### P7 · `SWEPT_REGIONS_KEY = "swept_regions"` and the `provider_extra` block — `:516`, read at `:539–540`
- **Meets** — the cost snapshot's `provider_extra` block, one named key.
- **Diverges today** — **yes.** Only AWS emits `swept_regions` (`fetch_aws.py:765`); DO and Linode
  emit a `provider_extra` block without it (`fetch_do.py:312`, `fetch_linode.py:562`). The absence
  is handled correctly — no entry, no section (`:541–542`).
- **Could diverge** — it already does. The item is here because it is the **one sanctioned read
  into the opaque provider block** (m2 A4), and the design is explicit that a generic pass-through
  would be the leak this milestone exists to prevent (`:511–515`). A second such key doubles the
  precedent, and there is no mechanism preventing a third — only the comment.
- **If ruled schema-level** — `swept_regions` is promoted out of `provider_extra` into a
  first-class optional envelope field, and the A4 exception disappears. Breaks: `fetch_aws.py:765`,
  `region_coverage_section`, `tests/test_render_report.py:404, 791`; the DO/Linode reports stay
  byte-identical either way.
- **If ruled adapter-owned** — the read stays as one named constant and the *rule* (exactly one
  named key, never a generic copy) is written down as a standing constraint rather than a comment.
  Breaks: nothing.
- **Consumers** — `region_coverage_section` (`:540`), `compose` (`:645`),
  `render_report.OPTIONAL_FIELDS` (`:84`), `templates/report.html.j2`,
  `tests/test_render_report.py:404, 791`.

#### P8 · `classify()` — shape discriminators `line_items` / `candidates` / `resources` — `:690–700`
- **Meets** — any parsed document, in `--input-dir` mode and when reading history.
- **Diverges today** — **no.**
- **Could diverge** — classification is by *presence of a list-valued key*, in a fixed order. A
  provider whose cost snapshot legitimately carries no line items (only a declared total, which
  `service_totals` supports at `:193`) returns `None` from `classify` and is **silently dropped**
  from `discover_bundles` (`:715–716`) with no warning and no `skipped` entry — the run composes a
  report missing that provider's costs and exits `ok`. It is also load-bearing for history:
  `load_prior_snapshots` accepts a document only if `classify(document) == "cost"` (`:768`).
- **If ruled schema-level** — documents carry an explicit `document_type` in the envelope and
  `classify` reads it. Breaks: all three adapters, `detect_orphans`'s output, every fixture, the
  history tree already on disk.
- **If ruled adapter-owned** — the shape contract stays and each adapter guarantees a `line_items`
  list even when empty. Breaks: nothing today; the silent-drop path stays and should at least warn.
- **Consumers** — `discover_bundles` (`:715`), `load_prior_snapshots` (`:768`),
  `tests/test_compose_report_data.py`.

#### P9 · `pct_change` — ×100.0, 2dp, zero base → `None` — `:115–119`
- **Meets** — two amounts from the cost snapshots.
- **Diverges today** — **no.**
- **Could diverge** — the zero-base rule means a service appearing for the first time reports
  `delta_pct: None` (rendered as an em dash, R2) rather than a growth figure, and one disappearing
  reports `-100.0`. The asymmetry is correct arithmetic but reads as a reporting inconsistency, and
  it is more visible on a provider whose service set churns (P6).
- **If ruled schema-level** — the convention stays and is documented. Breaks: nothing.
- **If ruled adapter-owned** — not available: it is arithmetic over normalized figures. Closed arm.
- **Consumers** — `month_on_month` (`:302, 321, 343`), `render_report.format_signed_pct` (`:119`),
  `tests/test_compose_report_data.py:231`.

#### P10 · `slug()` — a deliberate duplicate of `_normalized.provider_slug` — `:96–100`
- **Meets** — the envelope's `provider`, for the history filename.
- **Diverges today** — **no**; the two implementations are byte-identical in behaviour.
- **Could diverge** — two copies of a slug rule is the duplication class BL-074 sweeps, one level
  down. It is **deliberate and recorded**: `_normalized.py:100–104` states that §t2 (d) froze this
  file so the AWS run's *"compose ran unchanged"* result stayed a clean negative proof, with
  convergence deferred to BL-070. Reported so the arbiter knows the duplication is a held position,
  not an oversight — and so it is not re-flagged as a finding (the before-re-flagging rule).
- **If ruled schema-level** — converge on `provider_slug` when compose is next legitimately edited
  (BL-070's stated trigger). Breaks: the frozen-file property, which has already served its purpose.
- **If ruled adapter-owned** — as N6. Breaks: both copies lose their caller.
- **Consumers** — `persist_history` (`:749`); the history tree layout; **BL-070** owns the
  convergence.

#### P11 · `source_granularity` passthrough — `:210`
- **Meets** — the cost snapshot's `source_granularity`.
- **Diverges today** — **no**; all three emit `"service"`
  (`fetch_aws.py:747`, `fetch_do.py:304`, `fetch_linode.py:554`).
- **Could diverge** — the field exists to make D4's honesty claim checkable, but it is **copied
  into the payload and never tested** anywhere in the four scripts. A provider emitting
  `"account"`-granularity costs would have its figures grouped by service exactly as if they were
  service-level, and the only trace would be a string in the report. The mechanism that would catch
  it is the one thing the field is for.
- **If ruled schema-level** — the value is enumerated and `service_totals` refuses (or warns on)
  a granularity coarser than service. Breaks: `service_totals`'s return shape and warning list,
  the report's granularity note.
- **If ruled adapter-owned** — each adapter guarantees service-level granularity and the field
  becomes a declaration rather than a variable. Breaks: nothing today.
- **Consumers** — `service_totals` (`:210`), the report's `by_provider` table and granularity note.
  **Not** compared or validated anywhere.

### 3f. `render_report.py`

#### R1 · `SECTIONS` vs `OPTIONAL_FIELDS` membership — `:68–73`, `:84`
- **Meets** — the report payload's top-level sections.
- **Diverges today** — **yes, and correctly.** `region_coverage` is in `OPTIONAL_FIELDS`
  specifically because only AWS produces it (P7), and a `SECTIONS` member absent costs a rendering
  note and `exit 1` — so a DO run would fail forever (`:75–83`, `docs/m2-t4-implementation-notes.md:15–17`).
  This is the **positive control for the whole census**: a provider-differing value handled by
  putting it in the right tuple rather than by special-casing a provider.
- **Could diverge** — every future optional section faces the same fork, and the rule for choosing
  lives in a comment on the tuple.
- **If ruled schema-level** — the required/optional split is stated in §Normalized schemas so the
  tuple is derived from the contract rather than maintained beside it. Breaks: nothing.
- **If ruled adapter-owned** — not available: the renderer is deliberately blind to where a field
  came from, and a test asserts it (`:81–83`). Recorded as a closed arm, and as the shape the other
  items should be ruled toward.
- **Consumers** — `build_context` (`:208–220`), the `partial` exit decision (`:398, 434`),
  `templates/report.html.j2`, `tests/test_render_report.py:404, 791`.

#### R2 · Money and absence presentation — `format_amount` `{:,.2f}` and the em dash — `:94–101`, `:128–133`
- **Meets** — every amount arriving from the payload.
- **Diverges today** — **no.**
- **Could diverge** — two coupled assumptions. The `,` thousands separator and `.` decimal point
  are a locale choice hardcoded for every currency the report will ever carry; and the 2dp mirrors
  N5, so a zero-decimal currency prints `¥1,234.00`. The em-dash-for-absent rule is deliberate and
  right (`:96–98`, absent must not read as `0.00`), and it is what makes P5's multi-currency
  blanking visible rather than wrong.
- **If ruled schema-level** — the presentation reads the currency's minor-unit exponent from the
  payload (N5's first arm). Breaks: `FILTERS`, `templates/report.html.j2`,
  `tests/test_render_report.py:473, 493`.
- **If ruled adapter-owned** — not available: the renderer must not learn provider identity
  (`:81–83`). It could read a currency-descriptor field, which is N5's schema arm. Closed arm.
- **Consumers** — `FILTERS` (`:136–142`), `templates/report.html.j2`,
  `tests/test_render_report.py:473, 493`.

#### R3 · Percentage presentation — `format_ratio_pct` ×100 vs `format_signed_pct` not multiplied — `:111–125`
- **Meets** — `tag_coverage.coverage` (a fraction, N9) and `delta_pct` (already a percentage, P9).
- **Diverges today** — **no.**
- **Could diverge** — the two filters exist because the payload carries percentages in **two
  different units**, and the only thing keeping them apart is which filter the template applies.
  Applying the wrong one produces a well-formed, plausible, wrong number — the silent-wrong-answer
  shape — and nothing in the renderer can detect it, because both inputs are floats.
- **If ruled schema-level** — percentage-valued fields are named consistently in §Normalized
  schemas (a `_pct` suffix means already-percent, a `_ratio`/`coverage` means fraction) so the
  template's choice is derivable. Breaks: nothing; it is a naming discipline over existing fields.
- **If ruled adapter-owned** — not available; both figures are computed by shared machinery.
  Closed arm.
- **Consumers** — `FILTERS` (`:136–142`), `templates/report.html.j2`,
  `tests/test_render_report.py:473, 493`.

#### R4 · `PDF_BINARY = "wkhtmltopdf"` — `:88`
- **Meets** — nothing adapter-supplied.
- **Diverges today** — **no.**
- **Could diverge** — it does not, on any provider axis. **Censused and reported as not a seam**:
  it is an environment dependency, not a provider one, and it is included here rather than in §2.5
  because a reader checking the census against class A will look for it and its absence would read
  as a miss.
- **If ruled schema-level** — n/a; not a schema value.
- **If ruled adapter-owned** — n/a; not an adapter value. **This item cannot be ruled by BL-074's
  dichotomy**, and it is reported as such rather than forced into an arm.
- **Consumers** — `write_pdf` (`:268`), `parse_args` (`:314`), `tests/test_render_report.py`.

---

## 4. The census against the seven leads, both directions

### 4a. Leads → census (does each lead survive?)

| # | Lead | Source | Census item | Survives? |
|---|---|---|---|---|
| 1 | Rule-catalog age thresholds | BL-074 Scope | **D1, D2, D3** | **Yes**, all three. Split into three items because their ruling consequences differ — D3 alone has a CLI override, and that asymmetry is itself censused |
| 2 | `KEEP_TAG` spelling | BL-074 Scope | **D6** | **Yes**, and strengthened: the census establishes it diverges *today* in reachability (AWS constructs `k=v`; DO/Linode cannot express it natively), and adds the case-folding asymmetry against D5 |
| 3 | `EPHEMERAL_NAME_PATTERN` | BL-074 Scope | **D5** | **Yes**, but **weakened**: the evidence says it is a tenant-naming property, not a provider one, so neither of BL-074's two arms is a good fit. Reported as an item whose ruling may need a third category |
| 4 | `TAGGED_ACCOUNT_COVERAGE_THRESHOLD` | BL-074 Scope | **D7** | **Yes**, and strengthened: Linode's untaggable resource classes structurally depress coverage, so the governance rule can never fire there |
| 5 | `CANONICAL_TYPES` has no public accessor | t2 (BL-074 coupling) | **N1** | **Yes**, confirmed. Adapters import the seven `TYPE_*` individually; only `sprint.sh:3025` and the tests import the set |
| 6 | `usable_resources()` checks presence, not canonicality | t2 (BL-074 coupling) | **N8** | **Yes**, confirmed, with the consequence traced: an out-of-vocabulary type is counted in `totals.resources` and in the tag-coverage denominator, and evaluated by nothing |
| 7 | The sprint consumes `_normalized.CANONICAL_TYPES` | t2 (BL-074 coupling) | **N1** consumers, and **N8**, **D18** | **Yes**, and widened: the sprint depends on `_normalized` at three points, not one — the `CANONICAL_TYPES` import (`:3025`), the `evaluated + skipped == resources` arm which is only meaningful because of N8's gap (`:3060`), and the exactly-one-artifact guard which D18's filename scheme can break (`:3040`) |

**Seven leads, seven survive; none is refuted.** Three are strengthened by evidence the leads did
not have, one (lead 3) is weakened, and one (lead 7) is wider than filed.

### 4b. Census → leads (what the leads do not name)

**54 censused items. The seven leads name 8 of them** — lead 1 names three (D1, D2, D3), leads
2–4 name one each (D6, D5, D7), lead 5 and lead 7 both name N1, and lead 6 names N8. **The leads do
not name the other 46**, partitioned below by why they were missed. The partition is derived, not
counted: `LEAD` and `NAMED` are stated as item lists and the two rows are their set differences, so
a reader who disputes a membership can recompute the row.

| Why the leads missed it | Items |
|---|---|
| **Not anchored on a named constant** — invisible to any name-keyed sweep, whatever file it is in | X1, X2, X3, X4, X5, N3, N4, N5, N6, N7, N9, D12, D13, D14, D15, D16, D17, D18, D19, D20, D21, F1, F2, F3, F4, P4, P5, P6, P8, P9, P10, P11, R2, R3 **(34)** |
| **A named constant the leads did not list** — **seven** are in a file no lead reaches (every lead but 5–7 names `detect_orphans.py`): N2, P1, P2, P3, P7, R1, R4. The other **five** sit in `detect_orphans.py` itself and were simply not enumerated: D4, D8, D9, D10, D11 | N2, D4, D8, D9, D10, D11, P1, P2, P3, P7, R1, R4 **(12)** |

34 + 12 = 46. ✓ (7 + 5 = 12 within the second row.)

Two items are the strongest findings and both are in the first row: **X1** (`state` is canonical
for one value only; ~15 provider-vocabulary values flow through shared machinery into the rendered
report today) and **X2** (`size` is spelled `GiB` on two providers and `GB`/`MB` on the third for
the same quantity). Neither is a named constant, neither is in any lead, and both are **current**
divergences rather than potential ones. They are the census's own evidence that the method was not
name-keyed — a sweep that returned only the leads would have reported the seam class as closed.

---

## 5. Two observations, recorded without ruling

Both are things the sweep is uniquely placed to see. Neither is chased.

### 5a. A value in shared machinery that is *already* correctly adapter-owned

**`POWERED_OFF_STATUS = "offline"` — `cloudcost/scripts/fetch_linode.py:111`**, mapped onto
`STATE_STOPPED` at `:658` (`"state": STATE_STOPPED if status == POWERED_OFF_STATUS else status`).

The provider's own spelling is named as a constant **in the adapter**, and the canonical value is
imported from `_normalized`. DO does the same inline (`fetch_do.py:345`, `"off"`); AWS does the
same inline twice (`fetch_aws.py:500, 679`, `"stopped"`). This is the shape all three closed seams
were converted *into*, and it is recorded as the positive control: when the arbiter rules an item
adapter-owned, this is what the result looks like.

A second, at a different layer: **`render_report.OPTIONAL_FIELDS`** (R1) — a provider-differing
*section* handled by putting it in the right tuple rather than by teaching the renderer about
providers, with a test asserting the renderer stays ignorant (`render_report.py:81–83`).

### 5b. BL-074's mirror — duplicated identically across all three adapters

**`CURRENCY = "USD"`** is declared identically in all three: `fetch_aws.py:71`, `fetch_do.py:56`,
`fetch_linode.py:89`. Three copies of one value, and N5's 2dp rounding in shared machinery is
silently correct only because they agree.

Two lesser instances, in two of three: **`RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})`**
(`fetch_do.py:58`, `fetch_linode.py:91`) and **`MAX_PAGES = 100`** (`fetch_do.py:59`,
`fetch_linode.py:92`) — byte-identical pairs, absent from `fetch_aws.py` which uses botocore's own
retry configuration.

**This is BL-074 run backwards** — a value that arguably belongs *in* shared machinery rather than
provider vocabulary leaking *out* of it — and it is explicitly out of the row's scope. Noted here
because the sweep saw it and a later sweep would have to re-derive it; not chased, not filed, and
no ruling implied.

---

## 6. Deviations and limits

- **No ruling is supplied anywhere.** Where evidence points one way (X1's state vocabulary, N8's
  canonicality gap, F2's uncovered DO case), the evidence is stated and the sentence stops. Item
  order within each section follows source order, not preferred outcome.
- **R4 (`PDF_BINARY`) cannot be ruled by BL-074's dichotomy** — it is an environment dependency,
  not a provider one. It is reported as unrulable rather than forced into an arm, because a reader
  checking the census against class A would otherwise read its absence as a miss.
- **Nine items have one genuinely closed arm** — N4, N9, P2, P9, R2, R3, D12, D20 and X5. For the
  first eight the adapter-owned arm is unavailable because the value is computed by shared machinery
  over normalized data and no adapter can own it; for X5 it is unavailable because the encoding
  governs how shared machinery *decodes* a file an adapter already wrote. Each says so in the field
  rather than leaving it blank. *(Read `Four` and listed eight before review round 1 — a wrong count
  in the section a reader uses to check the census's own honesty. Corrected, and the correction left
  visible rather than silently absorbed.)*
- **Current divergence is established from the three adapters at agents `9962454`**, by reading
  their emission sites — not from running them. AWS and Linode credentials are not present in this
  environment (m4 t3's recorded limit still applies) and none was minted or probed. Every
  *"diverges today"* claim above cites adapter source lines, which is a read, and is labelled as
  such rather than presented as a run.
- **The census covers the four scripts BL-074 names, and the fifth candidate's exclusion is now
  established rather than inherited** *(review round 1)*. As first written this said only that
  `detect_optimization_signals.py` is not named by BL-074's Scope paragraph — which is true, and is
  a different claim from *"established not shared machinery"*. BL-074 exists because a bounded list
  was mistaken for a census, so "not in the list" is precisely the reasoning the row distrusts. The
  file was read. **It is AWS-specific at every level**: `PROVIDER = "aws"` hardcoded (`:93`); it
  imports fifteen names directly from `fetch_aws.py` (`:72`) including `AWSClients`,
  `load_credentials` and `enumerate_regions`; every one of its six signals is an AWS service concept
  (S3 lifecycle, incomplete multipart, ECR image accumulation, Secrets Manager staleness); it
  carries an AWS list-price rate table keyed by AWS region (`:146`); and it calls botocore directly.
  Its own docstring calls it *"a second lane, not an extension of the first"*, and decision G keeps
  the core pipeline from reading it. **So it is adapter-side, not shared machinery, and BL-074's
  four-file scope is confirmed complete** — the exclusion is a fact, not a boundary respected.

  **One thing the check surfaced, recorded as a negative.** Shared machinery *does* read this
  AWS-only script's artifact: `render_report.py --optimization-file` (`:300`, `:319–339`). It reads
  it as an opaque dict and hands it to the template, and the template learns nothing AWS-shaped from
  it — `grep -icE "s3|ecr|secret|aws|bucket" templates/report.html.j2` returns **1**, and that one
  hit is the substring `ecr` inside the word *"decrease"* (`:247`). Zero real matches. That is R1's
  positive control holding on the one path where it would have been easiest to break.

- **The adapters' own write-side encoding was not swept.** X5 censuses how shared machinery
  *decodes*; whether `fetch_aws.py`, `fetch_do.py` and `fetch_linode.py` specify an encoding when
  they *write* is outside BL-074's four-file scope and was not checked. Stated as a limit rather
  than left for the arbiter to assume either way.
