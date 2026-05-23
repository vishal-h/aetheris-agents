# T3 Implementation Notes

## Orchestrator sandbox_path deviation

The spec scaffold computes `agent_root` as one level above the script file:

```elixir
Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))
# → /path/to/aetheris-agents/drive/
```

However, the system prompt instructs the agent to run commands with args like
`drive/scripts/drive_download.py` and `payslip/agents/payslip_orchestrator.exs`.
These paths only resolve correctly when the CWD is the aetheris-agents root, not
the `drive/` subdirectory.

The orchestrator therefore uses two levels up:

```elixir
Path.expand(Path.join([Path.dirname(__ENV__.file), "..", ".."]))
# → /path/to/aetheris-agents/
```

This lets the system prompt args remain unchanged and match the directory structure
as documented in `drive/README.md`.

## Scope separation between download and upload

`drive_download.py` uses `drive.readonly` scope; `drive_upload.py` uses
`drive.file` scope. Rather than duplicating `build_service`, upload imports it from
download and passes the narrower upload scope:

```python
from drive.scripts.drive_download import build_service
service = build_service(scopes=UPLOAD_SCOPE)
```

This keeps authentication logic in one place and makes scope override explicit at
each call site.

## Upsert pattern in upload_file

`upload_file` queries for an existing file by name before uploading. If found, it
calls `files.update`; otherwise `files.create`. This makes re-runs idempotent:
repeating the upload for the same month overwrites the previous files rather than
creating duplicates.

## groupby requires sorted input

`drive_upload.main()` uses `itertools.groupby` to iterate over files per employee.
`groupby` only produces one group per contiguous run of equal keys, so it depends on
`collect_upload_files` returning results sorted by `(employee_id, path.name)`. A
comment in the source documents this invariant so future callers don't break it by
changing the sort.

## pageSize=10 in find_payroll_file

The Drive API can return an empty first page on new service account sessions even
when files exist. Using `pageSize=10` and taking the first result client-side avoids
a false-negative that `pageSize=1` would produce in that edge case.
