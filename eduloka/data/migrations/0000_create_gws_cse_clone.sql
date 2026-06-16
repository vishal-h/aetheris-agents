-- Schema clone for integration testing — mirrors the Ecto-generated gws_cse DDL.
-- NOT for production use; apply only against a test database.
--
-- Column derivation from ct-edux lib/gws/cse.ex:
--   field :link, :string           → text
--   field :title, :string          → text
--   field :snippet, :string        → text
--   field :image, :string          → text
--   field :search_term, :string    → text
--   field :status, :integer        → integer
--   field :metatags, {:array, :map}→ jsonb[]   (Ecto array-of-map → Postgres jsonb[])
--   timestamps()                   → inserted_at/updated_at timestamp(0) NOT NULL, no DB default
CREATE TABLE IF NOT EXISTS gws_cse (
    id           bigserial PRIMARY KEY,
    link         text,
    title        text,
    snippet      text,
    image        text,
    search_term  text,
    status       integer,
    metatags     jsonb[],
    inserted_at  timestamp(0) NOT NULL,
    updated_at   timestamp(0) NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS gws_cse_link_index ON gws_cse (link);
