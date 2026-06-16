# eduloka

Institute discovery pipeline. Replaces the legacy `ct-edux` CSE ingest with a
provider-swappable, replayable, medallion-layered pipeline landing in the same
`gws_cse` table the live site reads.

See **[`scripts/README.md`](scripts/README.md)** for the full pipeline design,
provider table, and run instructions.

See **[`runbook.md`](runbook.md)** for credentials, env vars, and operational
procedures.

See **[`milestone.md`](milestone.md)** for the ticket sequence and done
definition.
