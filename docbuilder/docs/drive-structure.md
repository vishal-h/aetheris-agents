# docbuilder — Drive structure & tenant onboarding

In m2b, template bundles and generated output live in a single Google **Shared Drive**
named `docbuilder`. The layout is **tenant-first**: each tenant has its own subtree, so
a tenant's folder can be shared independently for access control and onboarding.

The Shared Drive root folder ID is the only Drive env var: **`DRIVE_DOCBUILDER_ID`**.

> **Local fallback.** When `DRIVE_DOCBUILDER_ID` is unset, `list_templates.py` and
> `fetch_template.py` fall back to the committed flat files under
> `docbuilder/data/templates/` (m2a behaviour) — so local dev and tests run without
> Drive credentials. See §"Local vs Drive layout" for the path mapping.

---

## Folder tree

```
docbuilder/                              ← Shared Drive root  (DRIVE_DOCBUILDER_ID)
  {tenant_id}/                           ← one subtree per tenant (e.g. "demo")
    templates/
      catalogue.json                     ← doc-type catalogue for this tenant
      {doc_type}/                        ← e.g. "proposal"
        {version}/                       ← e.g. "v1"
          {doc_type}_{version}.json          ← structure + data config (required)
          {doc_type}_{version}.docx          ← docx branding base file (optional)
          {doc_type}_{version}.xlsx          ← xlsx branding base file (optional)
          {doc_type}_{version}.md.template   ← PDF narrative template (optional)
          {doc_type}_{version}.css           ← PDF narrative styles (optional)
    output/
      {client_name}_{doc_type}_{date}.xlsx   ← uploaded, renamed run outputs
      {client_name}_{doc_type}_{date}.docx
      {client_name}_{doc_type}_{date}.pdf
```

- **`templates/catalogue.json`** — read by `list_templates.py` for LLM selection.
- **`{doc_type}/{version}/`** — the *template bundle*. `fetch_template.py` does a
  **wide fetch**: it downloads the entire version subfolder in one call to a local
  cache dir, then the orchestrator points `--base-file` (xlsx/docx) and
  `--template-dir` (pdf narrative) at the cache.
- **`output/`** — `upload_output.py` writes the renamed run outputs here.

---

## Env var

| Variable | Description | Example |
|----------|-------------|---------|
| `DRIVE_DOCBUILDER_ID` | The `docbuilder` Shared Drive **root folder ID**. When set, `list_templates.py` / `fetch_template.py` read from Drive; when unset, they use the local flat files. | `0AB...xyz` |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Path to the service-account JSON used for Drive auth (same pattern as `drive/scripts/`). | `/secrets/docbuilder-sa.json` |

The service account must be a **member of the Shared Drive** (content-manager or
higher to upload output).

---

## Output filename convention

Run outputs are renamed by `rename_output.py` before upload:

```
{client_name}_{doc_type}_{date}.{ext}
```

- `client_name` is **slugified**: lowercased, spaces → underscores, non-alphanumeric
  (except `_` and `-`) stripped. `"Acme Corp"` → `acme_corp`.
- `doc_type` from `DOCBUILDER_CONTEXT` (or the filename prefix base if absent).
- `date` from `DOCBUILDER_CONTEXT`.

Example: `acme_corp_proposal_2026-06-20.pdf`.

---

## Tenant onboarding procedure

To onboard a new tenant `{tenant_id}` (in the `docbuilder` Shared Drive):

1. **Create the tenant subtree.** Under the Shared Drive root, create
   `{tenant_id}/templates/` and `{tenant_id}/output/`.
2. **Upload the catalogue.** Place `catalogue.json` at
   `{tenant_id}/templates/catalogue.json`. It lists the tenant's doc types and
   variants (see `list_templates.py` / the demo `catalogue.json` for the shape).
3. **Create the doc-type / version folders.** For each variant, create
   `{tenant_id}/templates/{doc_type}/{version}/`.
4. **Upload the template bundle.** Into each version folder, upload the
   `{doc_type}_{version}.json` config (required) and any optional branding/narrative
   assets (`.docx`, `.xlsx`, `.md.template`, `.css`).
   - **Base-file checklist (carried from m2a):** docx base files must define the
     `Heading 1` and `Table Grid` named styles, and xlsx/docx branding must be
     consistent across sheets; the narrative `.css` `@page` header/footer should match
     the docx base file's header/footer strings. (See README design decisions and the
     m2a base-file learning.)
   - **Cover-page subtitle is a placeholder.** The base file's cover page subtitle
     (`Prepared for: Client Name | Date: DD MMM YYYY`) is sample wording only — replace
     it with the tenant's standard cover wording during onboarding. (Per-run `client_name`
     and `date` are substituted at render time; the subtitle styling/phrasing in the base
     file is the tenant's to customise.)
5. **Verify.** With `DRIVE_DOCBUILDER_ID` set:
   ```bash
   python3 scripts/list_templates.py --tenant {tenant_id} | python3 -m json.tool
   ```
   The catalogue should list the doc types/variants you uploaded. Then a wide fetch:
   ```bash
   python3 scripts/fetch_template.py --tenant {tenant_id} --doc-type {doc_type} --version {version}
   ```
   should download the bundle to the local cache dir and print its path.
6. **Grant access.** Share the `{tenant_id}/` subtree with the tenant's reviewers as
   needed — access is per-tenant because the layout is tenant-first.

---

## Local vs Drive layout

The committed m2a flat files and the m2b Drive bundle differ in nesting:

| | Local (m2a flat, committed) | Drive (m2b bundle) |
|---|---|---|
| catalogue | `data/templates/{tenant}/catalogue.json` | `{tenant}/templates/catalogue.json` |
| config | `data/templates/{tenant}/{doc_type}_{version}.json` | `{tenant}/templates/{doc_type}/{version}/{doc_type}_{version}.json` |
| base files | `data/templates/{tenant}/{doc_type}_{version}.{docx,xlsx,...}` | `{tenant}/templates/{doc_type}/{version}/{doc_type}_{version}.{docx,xlsx,...}` |

`fetch_template.py` (t2) resolves the local fallback against the **nested** path
(`data/templates/{tenant}/{doc_type}/{version}/`). The committed demo currently uses
the **flat** layout, so t2 must either (a) add a nested demo bundle for local-fallback
tests, or (b) map the flat layout to the bundle shape. This is flagged for t2 — the
canonical Drive layout is the nested one documented above.
