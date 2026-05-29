# hai-rig/m6: Classification review tab

## Context

The one interactive view in Rig. Auditors review proposed classifications and
approve or reject them without touching a terminal. This is the only write path
Rig owns — it calls `provenance_set_classification_status`.

## What to build

### `src/hooks/useClassifications.ts`

```typescript
interface UseClassificationsOptions {
  client?: string
  status?: string   // "proposed" | "needs_review" | "approved" | "rejected"
  limit?: number
}

function useClassifications(options?: UseClassificationsOptions):
  { data: ClassificationRow[], loading: boolean, error: string | null, refetch: () => void }

function useSetClassificationStatus():
  (path: string, status: "approved" | "rejected") => Promise<void>
```

`useSetClassificationStatus` uses `invoke("provenance_set_classification_status")`
with `reviewer: currentUser()` where `currentUser()` reads `process.env.USER ||
"unknown"` via a Tauri command or env var.

### `src/components/modules/provenance/ClassificationReview.tsx`

`ClassificationReview(): Tab[]` returning two tabs:

**Tab 1 — Pending review**

Filter bar at top:
- Client dropdown (populated from `list_clients` or client_breakdown)
- Status filter: All pending | Proposed | Needs review
- Confidence threshold slider (0 – 1.0, default show all)
- "Refresh" button

Table below, ordered by `confidence ASC` (lowest confidence first):

| Path (truncated) | Client | FY | Type | Confidence | Preview | Actions |
|-----------------|--------|-----|------|-----------|---------|---------|

Actions column: `Approve` (green) and `Reject` (red) buttons per row.

On approve/reject:
1. Disable the row buttons (prevent double-click)
2. Call `provenance_set_classification_status`
3. On success: remove the row from the table (optimistic update)
4. On error: re-enable buttons, show error toast

Bulk action bar (shows when rows are selected via checkboxes):
"Approve N selected" | "Reject N selected"

**Tab 2 — Review history**

Table of approved and rejected classifications:

| Path | Client | FY | Type | Decision | Reviewed by | Reviewed at |
|------|--------|-----|------|----------|-------------|------------|

Filter: by client, by decision (approved/rejected).

### No confirm dialog

Approve and reject are direct actions — no "Are you sure?" modal.
The action is reversible (re-run `approve_classifications.py` with a correction),
and a modal would slow the review workflow for large batches.

## Acceptance criteria

- [ ] Pending table shows `proposed` and `needs_review` rows
- [ ] Confidence column shows numeric value + visual indicator (colour)
- [ ] Approve button updates row status in DB and removes from pending list
- [ ] Reject button updates row status in DB and removes from pending list
- [ ] Bulk approve/reject works for selected rows
- [ ] Row buttons disabled during in-flight request (no double-submit)
- [ ] Error shown inline if `provenance_set_classification_status` fails
- [ ] Review history tab shows approved and rejected with reviewer name
- [ ] Filter by client works
- [ ] "Not connected" placeholder when corpus not connected
- [ ] No `any` TypeScript types
- [ ] No form tags — use onClick handlers (CLAUDE.md rule)

## Files to create

- `src/hooks/useClassifications.ts`
- `src/components/modules/provenance/ClassificationReview.tsx`

## Notes

**Optimistic update pattern.** On approve/reject, update local state
immediately (remove row from pending list) then call the Tauri command. On
error, restore the row. This makes the UI feel responsive for bulk review.

**Confidence colour.** Use Tailwind text colour:
- ≥ 0.85: `text-green-600`
- 0.70 – 0.85: `text-yellow-600`
- < 0.70: `text-red-600`

**`raw_excerpt` preview.** Show first 100 chars in the table cell, truncated
with `…`. Full excerpt on row hover via `title` attribute.

**Reviewer identity.** Pass `reviewer: navigator.userAgent` is not useful.
Use a Tauri command `get_system_username` that returns `std::env::var("USER")`
from the Rust side. Add this small command to `provenance.rs`.

**Large classification lists.** The `limit` parameter in
`provenance_classification_list` defaults to 100. Show a "Load more" button
rather than paginating — simpler to implement and sufficient for the expected
review batch sizes.
