-- Additive migration: add nullable enrichment jsonb column to gws_cse.
-- Idempotent (IF NOT EXISTS). Does not alter existing columns or indexes.
-- The live site ignores unknown columns; no downtime required.
ALTER TABLE gws_cse ADD COLUMN IF NOT EXISTS enrichment jsonb;
