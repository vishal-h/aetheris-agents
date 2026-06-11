# Artifact schemas (canonical)

> These schemas are **normative**. `03-artifacts-and-handoffs.md` names the
> artifact families; this document defines them. `scripts/state_manager.py`
> is the single validator: every artifact is validated (`state_manager.py
> validate <path>`) at the orchestrator boundary before the next phase is
> spawned. The pack agent consumes only artifacts that carry a validation
> stamp. Agents never hand-construct these files — scripts emit them; agents
> decide when to invoke the scripts.
>
> Conventions: JSON, UTF-8, one artifact per file under `output/{task_id}/`.
> Field names snake_case. Timestamps ISO 8601 UTC. SHAs are full 40-char hex.
> `schema_version` starts at `"1.0"`; any breaking change bumps the major and
> the validator must support N and N-1.

---

## 0. Common envelope

Every artifact embeds this envelope at the top level. The per-family schemas
below add fields to it.

```json
{
  "schema_version": "1.0",
  "artifact_type": "diff_manifest",
  "task_id": "CHF-2026-0173",
  "issue_id": "JIRA-4821",
  "created_at": "2026-06-11T09:14:33Z",
  "created_by": "diff_analyzer.py@a1b2c3d",
  "workspace": "/sanctioned/tmp/chf/CHF-2026-0173/tenant-acme-2.4",
  "base_branch": "tenant/acme/2.4",
  "hotfix_branch": "chf/acme-JIRA-4821-null-deref",
  "base_sha": "9fceb02a4c0f6a3b…",
  "hotfix_sha": "1c002dd4b536e7…",
  "source_shas": ["e83c5163316f89bf…", "0d1d7fc32e5a947f…"],
  "confidence": "high",
  "blockers": [],
  "validation": null
}
```

| Field | Type | Rules |
|---|---|---|
| `schema_version` | string | required; semver `"major.minor"` |
| `artifact_type` | enum | required; one of the eight family names below |
| `task_id` | string | required; one hotfix request = one task_id; reused across all artifacts of the run |
| `issue_id` | string | required; tracker reference |
| `created_at` | string | required; ISO 8601 UTC |
| `created_by` | string | required; `script_name@git_sha_of_script` — provenance of the emitter |
| `workspace` | string | required; absolute path to the isolated worktree this artifact describes |
| `base_branch` / `hotfix_branch` | string | required where branches exist; `null` in pre-branch artifacts |
| `base_sha` / `hotfix_sha` | string\|null | resolved tip SHAs at emission time; the replay pins |
| `source_shas` | string[] | required; the commits being consolidated, in apply order |
| `confidence` | enum | required; `"high" \| "medium" \| "low"` — anything below `high` is a soft blocker the orchestrator must surface |
| `blockers` | Blocker[] | required (may be empty); **non-empty blockers halt the workflow** |
| `validation` | object\|null | written **only** by `state_manager.py validate`; emitting scripts set `null` |

**Blocker object:**

```json
{ "code": "CHERRY_PICK_CONFLICT", "message": "conflict in src/auth/session.c", "data": { "sha": "0d1d7fc3…", "files": ["src/auth/session.c"] } }
```

`code` is from the closed set in §9. Free-text goes in `message`; machine data
in `data`.

**Validation stamp** (added in place by the validator; presence = validated):

```json
"validation": { "validated_at": "2026-06-11T09:15:02Z", "validator": "state_manager.py@a1b2c3d", "schema_ok": true, "gate": "pass" }
```

`gate` is `"pass" | "fail"`. The pack agent's first action is asserting
`validation.gate == "pass"` on its input manifest (via script, not eyeball).

---

## 1. `diff_request`  — emitted by CHF-execute phase

Tells the diff agent what to compare. Nothing more — comparison *strategy* is
the diff agent's decision.

```json
{
  …envelope…,
  "artifact_type": "diff_request",
  "test_gate": { "command": "make test-fast", "exit_code": 0, "log_ref": "output/CHF-2026-0173/test_run_01.log" },
  "applied_commits": [
    { "sha": "e83c5163316f89bf…", "applied_as": "f7d2a91…", "method": "cherry-pick", "conflicts": false }
  ],
  "exclude_globs": ["*.lock", "dist/**"],
  "notes": "string|null"
}
```

Rules: `test_gate.exit_code` must be 0 — a diff_request with a failing test
gate is invalid by schema. `applied_as` records the new SHA each source commit
became on the hotfix branch (cherry-pick rewrites SHAs; the diff agent needs
both).

## 2. `diff_manifest` — emitted by diff agent

The complete effective change set. The **only** input the pack agent may act on.

```json
{
  …envelope…,
  "artifact_type": "diff_manifest",
  "strategy": "linear",
  "strategy_rationale": "fast-forward ancestry confirmed; merge-base equals base_sha",
  "evidence_commands": [
    "git merge-base tenant/acme/2.4 chf/acme-JIRA-4821-null-deref",
    "git range-diff 9fceb02…1c002dd"
  ],
  "files": [
    { "path": "src/auth/session.c", "change": "modified", "old_sha": "blob:8ab686ea…", "new_sha": "blob:443db5e6…", "hunks": 3, "mode": "100644" },
    { "path": "src/auth/session_test.c", "change": "added",   "old_sha": null,            "new_sha": "blob:bd9dbf5a…", "hunks": 1, "mode": "100644" },
    { "path": "src/legacy/auth.c",      "change": "removed",  "old_sha": "blob:7f8b2c1d…", "new_sha": null,            "hunks": 1, "mode": "100644" },
    { "path": "src/auth/token.c",       "change": "moved",    "from_path": "src/token.c", "old_sha": "blob:…", "new_sha": "blob:…", "hunks": 0, "mode": "100644" }
  ],
  "generated_files": [ { "path": "build/version.h", "reason": "build-generated; rebuild on install" } ],
  "excluded_files":  [ { "path": "package.lock", "reason": "matches exclude glob *.lock" } ],
  "source_shas_confirmed": true
}
```

| Field | Rules |
|---|---|
| `strategy` | enum: `"linear" \| "range_diff" \| "patch_id" \| "tree_diff"` (06-diff-agent-contract) |
| `strategy_rationale` | required non-empty; "because it usually works" fails review |
| `evidence_commands` | required; the exact commands run — this is the replay/audit hook |
| `files[].change` | enum: `"modified" \| "added" \| "removed" \| "moved"`; `moved` requires `from_path` |
| `files[].old_sha` / `new_sha` | git blob SHAs, prefixed `blob:`; null per change semantics |
| `generated_files` | files that change but must be **rebuilt**, not copied; pack agent excludes them from the copy set and the install script triggers regeneration |
| `source_shas_confirmed` | must be `true`; `false` is only legal alongside a blocker |

The diff agent never emits packaging layout, install steps, or archives — a
manifest containing such fields is invalid.

## 3. `packaging_request` — emitted by orchestrator

Authorizes the pack phase and binds it to one validated manifest.

```json
{
  …envelope…,
  "artifact_type": "packaging_request",
  "diff_manifest_ref": "output/CHF-2026-0173/diff_manifest.json",
  "diff_manifest_sha256": "c4f7…",
  "target": { "tenant": "acme", "version": "2.4", "platform": "linux-x86_64" },
  "package_format": "tar.gz",
  "destination_root": "/opt/product"
}
```

`diff_manifest_sha256` is the integrity pin: `package_builder.py` recomputes
it and refuses on mismatch. Any field the pack agent would otherwise have to
guess (destination root, ownership defaults) lives here or is a blocker.

## 4. `packaging_manifest` — emitted by pack agent

```json
{
  …envelope…,
  "artifact_type": "packaging_manifest",
  "packaging_request_ref": "output/CHF-2026-0173/packaging_request.json",
  "bundle": { "path": "output/CHF-2026-0173/acme-2.4-JIRA-4821.tar.gz", "sha256": "9e10…", "size_bytes": 48213 },
  "contents": [
    { "archive_path": "files/src/auth/session.c", "dest_path": "/opt/product/src/auth/session.c", "sha256": "0b7e…", "mode": "100644", "action": "replace" },
    { "archive_path": null, "dest_path": "/opt/product/src/legacy/auth.c", "sha256": null, "mode": null, "action": "delete" }
  ],
  "install_script": { "path": "install.sh", "sha256": "ab21…" },
  "rollback_script": { "path": "rollback.sh", "sha256": "cd43…" },
  "rollback_manifest_ref": "output/CHF-2026-0173/rollback_manifest.json",
  "checksums_file": "checksums.sha256",
  "verification": { "method": "extract_and_hash", "result": "pass" }
}
```

Rules: `contents[].action` ∈ `"replace" | "add" | "delete"`. Every entry must
trace 1:1 to a `diff_manifest.files` entry — `package_builder.py` enforces the
bijection (excluding `generated_files`) and any orphan is a blocker.
`verification.result` must be `"pass"`; the pack agent re-extracts the bundle
and re-hashes before emitting.

## 5. `rollback_manifest` — emitted by pack agent (via script)

The mirror image of the packaging manifest, captured **before** install ever
runs, so rollback is data-driven rather than script-cleverness.

```json
{
  …envelope…,
  "artifact_type": "rollback_manifest",
  "packaging_manifest_ref": "output/CHF-2026-0173/packaging_manifest.json",
  "preserve": [
    { "dest_path": "/opt/product/src/auth/session.c", "expected_pre_sha256": "8ab6…", "restore_action": "restore_file" },
    { "dest_path": "/opt/product/src/legacy/auth.c",  "expected_pre_sha256": null,    "restore_action": "recreate_from_backup" }
  ],
  "backup_strategy": "sidecar_targz",
  "notes": "install.sh creates /opt/product/.chf-backup/CHF-2026-0173.tar.gz before any replace"
}
```

`expected_pre_sha256` lets rollback detect drift: if the file on disk at
rollback time doesn't match what install replaced, rollback **halts and
escalates** instead of clobbering an unknown state.

## 6. `evaluator_report` — emitted by validator/eval tooling

Result of any validation gate (schema check, test gate audit, package verify,
or harness eval-suite run against a repo-factory scenario).

```json
{
  …envelope…,
  "artifact_type": "evaluator_report",
  "subject_ref": "output/CHF-2026-0173/packaging_manifest.json",
  "checks": [
    { "name": "schema", "result": "pass", "detail": null },
    { "name": "bijection_diff_to_package", "result": "pass", "detail": null },
    { "name": "checksums", "result": "fail", "detail": "src/auth/token.c: expected 0b7e… got 11aa…" }
  ],
  "overall": "fail"
}
```

`overall` is `"pass"` iff every check passes. A `fail` report auto-generates a
blocker on the subject artifact's phase.

## 7. `propagation_plan` — emitted by orchestrator (final phase)

Where this fix must also land, so consolidated hotfixes don't silently fork
the codebase.

```json
{
  …envelope…,
  "artifact_type": "propagation_plan",
  "completed_target": { "branch": "tenant/acme/2.4", "package_ref": "output/CHF-2026-0173/packaging_manifest.json" },
  "remaining_targets": [
    { "branch": "tenant/acme/2.5", "status": "pending", "task_id": null },
    { "branch": "release/2.4",     "status": "pending", "task_id": null },
    { "branch": "main",            "status": "pending", "task_id": null, "note": "forward-port, not cherry-pick — original commits already authored here?" }
  ],
  "ordering_rationale": "oldest active tenant version first per 04 loop ordering"
}
```

`status` ∈ `"pending" | "in_progress" | "done" | "skipped"`; a `skipped` entry
requires a `note`. As follow-up tasks spawn, their `task_id`s are written back
— the plan file is the one artifact that is **updated in place** (each update
logged in `CHF-STATE.md`).

## 8. `escalation_request` — emitted by any agent via `state_manager.py escalate`

The eighth family — `03` mandates structured escalation; this is its schema.

```json
{
  …envelope…,
  "artifact_type": "escalation_request",
  "phase": "chf_execute",
  "trigger": "CHERRY_PICK_CONFLICT",
  "summary": "Cherry-pick of 0d1d7fc3 conflicts in src/auth/session.c (3 hunks).",
  "evidence": ["output/CHF-2026-0173/conflict_0d1d7fc3.txt"],
  "options": [
    { "key": "A", "label": "Abort this target; continue remaining targets", "consequence": "tenant/acme/2.4 ships without JIRA-4821", "recommended": false },
    { "key": "B", "label": "Provide a manually resolved commit SHA to use instead", "consequence": "human resolves conflict on a side branch; rerun with CHF_RESOLVED_SHA", "recommended": true },
    { "key": "C", "label": "Drop commit 0d1d7fc3 from scope", "consequence": "partial fix; gap analysis required", "recommended": false }
  ],
  "response": null
}
```

Rules: 2–5 options; **exactly one** `recommended: true`; agents never invent a
"do it anyway" option. `response` is filled by the resume path (human or
webhook) as `{ "chosen": "B", "data": { "resolved_sha": "…" }, "answered_at": "…", "answered_by": "…" }`.
The schema is identical whether delivered by halt-and-report or by the
suspended-run webhook channel — that is deliberate (appendix §6).

---

## 9. Blocker / trigger code registry (closed set, v1)

`DIRTY_WORKTREE`, `BASE_BRANCH_UNRESOLVED`, `CHERRY_PICK_CONFLICT`,
`TEST_COMMAND_UNKNOWN`, `TEST_GATE_FAILED`, `DEPENDENCY_COMMIT_MISSING`,
`ANCESTRY_AMBIGUOUS`, `MANIFEST_INCOMPLETE`, `MANIFEST_INTEGRITY_MISMATCH`,
`DEST_LAYOUT_AMBIGUOUS`, `PERMISSIONS_AMBIGUOUS`, `WORKSPACE_CONFLICT`,
`SCHEMA_VALIDATION_FAILED`, `LOW_CONFIDENCE`, `STEERING_CONTRADICTION`.

Adding a code = PR to this file + validator update, same commit.

---

## 10. `CHF-STATE.md` line format

Not JSON (it is the human log), but each entry carries a machine-readable
fence so the eval `regex` scorer and replay tooling can parse it:

```markdown
## 2026-06-11T09:12:40Z — chf_execute — git_op
```json
{ "event": "cherry_pick", "sha": "e83c5163…", "exit_code": 0, "applied_as": "f7d2a91…" }
```
Cherry-picked e83c516 cleanly (auth null-deref fix).
```

Required event coverage per `08-state-and-audit.md`: `init`,
`branch_resolution`, every `git_op`, `test_run`, `artifact_emitted` (with
path + sha256), `steering_applied`, `escalation`, `final_state`.

---

## 11. Validator behaviour summary (`state_manager.py validate`)

1. Parse JSON; reject non-UTF-8, trailing garbage, duplicate keys.
2. Check envelope: all required fields, enum membership, SHA formats,
   `created_by` provenance present.
3. Check family schema (this doc).
4. Cross-checks: ref'd files exist and their recorded sha256 matches;
   `source_shas` consistent across the artifact chain for the task_id;
   bijection rule for packaging manifests.
5. `blockers` non-empty or `confidence != "high"` → `gate: "fail"` with the
   blockers echoed (low confidence maps to code `LOW_CONFIDENCE`).
6. Stamp `validation` in place; exit 0 on pass, 1 on fail; emit an
   `evaluator_report` either way.
