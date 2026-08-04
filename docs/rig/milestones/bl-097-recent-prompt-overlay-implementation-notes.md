# BL-097 — Orchestrator: Recent prompt covers Run and the env disclosure (implementation notes)

Minimal unbreak. Four small edits in `rig/src/components/modules/orchestrator/OrchestratorView.tsx`.
No relayout, no relocation of Recent, `extra_env` panel and `ParamsStrip` untouched.

---

## Mechanism (one line)

The overlaying element is the **filter-suggestions dropdown**, not the Recent list: its visibility
was derived purely from `suggestions.length > 0`, and picking a Recent entry sets `request` to that
entry — which then trivially matches itself, so the absolutely-positioned list opened and could
never close.

Longer form, since the one line hides the part that matters:

- The dropdown is `absolute left-0 right-0 top-full mt-1 z-10` (`:178-179`) inside the `relative`
  wrapper that holds **only the textarea** (`:159`). It therefore paints outside the flow, over the
  env disclosure and Run.
- `suggestions = history.filter(h => h.toLowerCase().includes(request.toLowerCase()))` when the box
  is non-empty (`:133-135`).
- Recent's `onClick` was `setRequest(h)` (`:257` pre-fix). After it, `request === h`, so
  `h.includes(h)` is true — the open condition became permanently satisfied.
- No blur, Escape, or selection dismissal existed anywhere, so the only escape was unmounting the
  component (navigate away and back), which reset `request`.

The Recent list itself is innocent: it correctly hides once the box is populated (`:247`, gated on
an empty request).

**Wider than the reported repro.** Any *typed* text substring-matching a stored history entry
produced the same stuck overlay. Recent selection is simply the reliable way to reach it, because it
guarantees an exact self-match. Worth recording because a fix aimed only at the Recent handler would
have left the typed path broken and looked complete.

---

## The fix

Visibility becomes explicit state instead of a derived predicate:

| edit | line | change |
|---|---|---|
| new state | `:137-142` | `const [suggestOpen, setSuggestOpen] = useState(false)` + why-comment |
| textarea | `:167-169` | `onChange` also sets open; `onKeyDown` Escape closes; `onBlur` closes |
| render gate | `:177` | `suggestions.length > 0` → `suggestOpen && suggestions.length > 0` |
| dropdown item | `:184-188` | `onMouseDown` preventDefault + `onClick` closes after selecting |
| Recent item | `:259` | `onClick` closes as well as populating |

The `onMouseDown={(e) => e.preventDefault()}` on dropdown items is load-bearing and easy to drop as
noise: without it, `onBlur` fires on mousedown and unmounts the button before its `onClick` can
land, so selecting from the dropdown would silently do nothing. Preventing default keeps focus on
the textarea so the click completes.

---

## Verification

`bun run lint` clean, `bun run build` clean (`tsc -b && vite build`).

**Predicate check, pre- vs post-fix.** A faithful model of the visibility gate — *not* a DOM or
render test, and labelled as such:

| scenario | pre-fix | post-fix |
|---|---|---|
| initial (empty box) | controls clear | controls clear |
| clicked a Recent entry | **overlay covers Run/env** | controls clear |
| typing a matching substring | overlay covers Run/env | overlay covers Run/env |
| picked from the dropdown | **overlay covers Run/env** | controls clear |
| typed, then pressed Escape | **overlay covers Run/env** | controls clear |

Mutation control: the pre-fix gate was re-run against the repro input and does reproduce the bug, so
the check is capable of failing rather than passing vacuously.

**Row three is not a regression and is stated deliberately.** While you are actively typing a
matching substring the dropdown is open and does overlay the controls — that is what a dropdown
does, and it is the pre-existing intended behaviour. The difference is that it is now dismissible:
Escape, blur, or selecting an entry all close it, where previously nothing did. Making the dropdown
never overlay would require moving it out of the absolute layer, which is the relayout this row
explicitly excluded.

**Not verified interactively.** Rig is a Tauri desktop app; the frontend was started under `vite`
to attempt a browser check, but no browser automation was available in this session, so the
click-through confirmation — Run and the env disclosure clickable after selecting Recent, and a
second selection working inline — is owed to the operator. The predicate check and the build are
what is closed here.

---

## Follow-up, deliberately not built

Moving Recent into a scrollable right-side panel is recorded in the BL-097 row as a separate UX
enhancement. Note it is not purely cosmetic: it would also make Recent reachable while the request
box is populated, which the current design intentionally does not do (`:247` hides it on any
non-empty request). That is a behaviour change and deserves its own decision rather than being
folded into an unbreak.
