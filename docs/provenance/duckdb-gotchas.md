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
