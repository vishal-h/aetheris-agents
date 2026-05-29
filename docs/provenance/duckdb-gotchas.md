# DuckDB 1.5.3 — Known Gotchas (provenance scripts)

Discovered during m1 implementation. Check here before writing new SQL.

| # | What you might write | What to write instead | Discovered in |
|---|----------------------|-----------------------|---------------|
| D1 | `basename(path)` | `regexp_extract(path, '([^/]+)$', 1)` | `migration_queue` view (m1-002) |
| D2 | `LIST(col ORDER BY col LIMIT N)` | `LIST(col ORDER BY col)` then slice in Python | `_section_duplicate_groups` (m1-004) |

## D1 — `basename()` does not exist

DuckDB 1.5.3 has no `basename()` scalar function.

```sql
-- Bad
SELECT basename(path) FROM f2_file_index;

-- Good
SELECT regexp_extract(path, '([^/]+)$', 1) FROM f2_file_index;
```

## D2 — `LIST(col LIMIT N)` is invalid syntax

`LIMIT` is not a valid modifier inside `LIST()` aggregate in DuckDB 1.5.3.

```sql
-- Bad
SELECT LIST(path ORDER BY path LIMIT 3) FROM f2_file_index GROUP BY sha256;

-- Good — fetch full list, slice in Python
SELECT LIST(path ORDER BY path) FROM f2_file_index GROUP BY sha256;
# then: row[col][:3]
```

## D3 — FK ordering: `zip_inventory` row must exist before `zip_contents` inserts

`zip_contents.zip_path` is a FK referencing `zip_inventory.path`.  DuckDB
enforces FK constraints at insert time, so inserting a `zip_contents` row
before the parent `zip_inventory` row raises `ConstraintException`.

```python
# Bad — zip_inventory row may not exist yet
conn.execute("INSERT INTO zip_contents (id, zip_path, ...) VALUES (?, ?, ...)", [...])

# Good — ensure parent row first, even as status='pending'
conn.execute(
    "INSERT INTO zip_inventory (path, status) VALUES (?, 'pending') "
    "ON CONFLICT (path) DO NOTHING",
    [zip_path],
)
conn.execute("INSERT INTO zip_contents (id, zip_path, ...) VALUES (?, ?, ...)", [...])
```

The same pattern applies to any table with a FK.  The general rule: always
insert the referenced (parent) row before the referencing (child) row, using
`ON CONFLICT DO NOTHING` so it is safe to call even if the row already exists.
