# Review — hc-b2 — repair hc-c's specification before hc-c opens

Round 0's findings are the four raised against hc-b's artifact in the anatomy-ratification packet
(A, B, C, D) plus the structural finding about the gate's home. All were accepted by the reviewer
in hc-b2's ticket text; this file records them, their origins as the reviewer named them, and
their dispositions.

**Shape** follows `hc-b-review.md`: one `## Round <R>` section, appended, never rewritten;
reviewer findings verbatim; claude-code's disposition table beneath them.

---

## Round 0 — the findings hc-b2 was written to repair

**Raised at:** the hc-c anatomy-ratification read, against agents `a581a8c` / harness `b4d782a`.
**Accepted in:** hc-b2's ticket text, §"The four findings, accepted, with their origins named".

> - **A** — *"exactly two slots marked under R13"* against four marks across three fields.
>   **The number is mine**: hc-b's ticket text says *"with **exactly two** slots marked under
>   R13"*, and it was a prediction about anatomy that had not been written. It was wrong on both
>   units — four marks, three fields, neither is two — and the notes carried it instead of
>   counting. **Fourth instance of the carrier, and its origin is the reviewer's text.**
> - **B, C, D** — the gate. All accepted.
> - **§2's structural finding** — the gate's home, and hc-d's dangling resolver. Accepted, and my
>   ruling was right for the wrong reason.
>
> **And §5's closing observation is the one to keep:** *the R13-marked slots are sound; the slot
> that was confidently completed is the one that does not hold. Confidence, not deferral, is what
> needed the review.* That generalises past this round — **R13 flags known uncertainty, and known
> uncertainty is safe.** Record it in the canonical document beside R13 as an observed property of
> its first application.

### Dispositions

| Finding | Disposition |
|---|---|
| **A** — the R13 count | **fixed** at `hc-b-implementation-notes.md` §6, where the number lives. Marks and fields both derived and printed beside the figures; the origin recorded as the reviewer's prediction, carried rather than counted. The canonical document carried no count and still carries none |
| **B** — placeholder agent | **fixed, and the finding understated it.** See below |
| **C** — outcomes indistinguishable | **fixed.** Positive control first and separate; five verdict rows; `inconclusive` explicit and a gate failure; the anti-vacuity property stated in the gate's own text |
| **D** — two invocations, not one run | **fixed.** One invocation, `> stdout.txt 2> stderr.txt` |
| **Structural** — the gate's home | **fixed.** A named construct after the seven §6 fields in both hc-c and hc-d; `Done-check` keeps only what runs after the work |
| **Structural** — hc-d's dangling resolver | **fixed by marking, not authoring**, and R13 gains the reading that makes it a rule application |
| **§5's observation** | **recorded** beside R13 as an observed property of its first application |

### Finding B was worse than a placeholder

The finding said the gate named no agent, so it could not be checked to spawn a worker. G3's
reconnaissance found the premise itself impossible.
`../aetheris/lib/aetheris/agent/supervisor.ex:62` is
`defp worker_child_spec(%{provider: "stub", mcp_servers: []}), do: []` — **a stub-provider run
with no MCP servers never starts a worker, whatever its `tools:` list.** hc-b's gate specified *a
stub-provider run with a worker*, and **no agent file could have satisfied it**: the disqualifier
was the provider, not the missing path.

The credential-free route that does exist in code — `stub` plus non-empty `mcp_servers` — has **no
agent file**: all twenty files in `../aetheris/agents/` use `anthropic`, `ollama` or `gemini`. The
gate therefore runs on a **live local Ollama** (verified: `:11434` answers `200`,
`llama3.2:latest` served), which needs no API key but is an environmental dependency the gate now
checks first and names.

### One correction to the reviewer's framing of A, offered rather than pressed

The ticket calls A *"the fourth instance of the carrier"* with its origin in the reviewer's text.
Accepted as stated. Worth adding only that A's origin makes it a **different sub-shape** from the
other three: the earlier instances were counts taken over a population that existed and was
miscounted, where A was a **prediction about an artifact that had not been written yet** and was
then carried as though it had been counted. Recorded in the notes; not raised as a finding.

---

## Round 1

_Awaiting review. Findings land here verbatim; dispositions beneath them, in a later commit._
