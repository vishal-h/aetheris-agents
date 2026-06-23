# docbuilder/agents/context_builder.exs
#
# m3 context builder (t2). Turns a natural-language request into a concrete
# DOCBUILDER_CONTEXT JSON and writes it to output/confirmed_context.json for the
# orchestrator (t4) to consume.
#
# Inputs (env, read at eval time):
#   DOCBUILDER_TENANT   — required; selects the tenant catalogue + scopes the run log.
#   DOCBUILDER_REQUEST  — the natural-language request, e.g.
#                         "Invoice for XYZ Inc for June 2026, same as last month".
#
# Tools: read_file (catalogue + run log), write_file (confirmed_context.json).
#
# NOTE (t3 hand-off): in t2 the LLM does best-effort resolution. The precise invoice
# number FY/sequence increment is computed deterministically by resolve_last_run.py in
# t3 — until then the agent treats invoice_number/amount_due as PROVISIONAL.

agent_root = Path.expand(Path.join(Path.dirname(__ENV__.file), ".."))

tenant = System.get_env("DOCBUILDER_TENANT") || raise "DOCBUILDER_TENANT not set"

request =
  case System.get_env("DOCBUILDER_REQUEST") do
    nil -> ""
    v -> v
  end

model    = System.get_env("AETHERIS_MODEL")    || "claude-haiku-4-5-20251001"
provider = System.get_env("AETHERIS_PROVIDER") || "anthropic"

catalogue_rel = "data/templates/#{tenant}/catalogue.json"
run_log_rel   = "data/run_log.json"

system_prompt = """
You are the docbuilder **context builder**. Turn a natural-language request into a
concrete DOCBUILDER_CONTEXT JSON object for tenant "#{tenant}", then write it for the
orchestrator to consume. You DECIDE the field values; you do not run any pipeline.

Read these first (use read_file):
  - Catalogue:  #{catalogue_rel}
        The valid doc_type / variant values for this tenant.
  - Run log:    #{run_log_rel}
        Prior runs as a JSON array (may be absent or empty). Each entry is
        {tenant, doc_type, variant, run_id, timestamp, context, outputs}.
        Use it for "same as last month" / "like last time".

The request is in the user message below.

Workflow:
  1. read_file the catalogue (#{catalogue_rel}). Decide the doc_type + variant the request
     refers to. If the request names a doc type not in the catalogue, say so and STOP.

  2. Decide whether this is a RECURRING request — "same as last month", "like last time",
     "the usual", or any request to repeat a prior document for an existing client.

  3a. RECURRING → resolve it deterministically from the run log. Do NOT compute dates or
      invoice numbers yourself — a script owns that math:
        run_command  command: "python3"
                     args: ["scripts/resolve_last_run.py",
                            "--tenant", "#{tenant}",
                            "--doc-type", "<DOC_TYPE>",
                            "--client-name", "<CLIENT>",
                            "--target-month", "<YYYY-MM>",
                            "--output", "output/confirmed_context.json"]
        - <DOC_TYPE> : the doc type from step 1.
        - <CLIENT>   : the client named in the request (a substring like "XYZ" is fine).
        - <YYYY-MM>  : the month the request asks for, e.g. "June 2026" -> "2026-06".
                       OMIT the --target-month element entirely if the request names no
                       month (the script defaults to the current month).
        Then:
        - If stdout is {"status": "no_prior_run", ...}: there is no matching prior run —
          go to step 3b (build from the request).
        - Otherwise the script WROTE output/confirmed_context.json (date bumped to
          month-end, invoice number incremented with the correct financial year).
          read_file it and go to step 4. Do NOT alter the date, invoice_number, or FY —
          the script owns that.

  3b. FRESH request (not recurring, or no prior run) → build the DOCBUILDER_CONTEXT from
      the request + catalogue. Required for every context: title, client_name,
      client_email, date. For invoices ALSO: invoice_number, client_address, amount_due.
      Do NOT invent client data — if a required field is in neither the request nor a
      prior run, LIST what is missing and STOP. write_file the context (a single JSON
      object, not wrapped) to "output/confirmed_context.json".

  4. Present the final context (the contents of output/confirmed_context.json) as pretty
     JSON under the heading:
       "PROPOSED DOCBUILDER_CONTEXT (review before rendering):"
     Then print the path "output/confirmed_context.json".

Rules:
  - All paths are relative to the sandbox root; overlay_base_dir is nil (files persist).
  - Output strictly the documented fields; do not add unknown keys.
  - You read the catalogue + run log, optionally call resolve_last_run.py, and write the
    context JSON — nothing else. For recurring requests the script computes the date and
    invoice number; you never compute those yourself.
"""

user_prompt =
  if request == "" do
    "No request was provided. Report that DOCBUILDER_REQUEST is required, and stop."
  else
    "Build and confirm the DOCBUILDER_CONTEXT for this request: #{request}"
  end

%Aetheris.RunConfig{
  run_id:           "docbuilder-ctx-#{Aetheris.ID.generate()}",
  mode:             :record,
  provider:         provider,
  model:            model,
  label:            "Docbuilder Context Builder",
  sandbox_path:     agent_root,
  overlay_base_dir: nil,
  max_steps:        15,
  context_strategy: :full,
  # run_command is listed but unused in t2 — t3 adds a resolve_last_run.py call, which
  # is then a prompt-only edit (keeps the t2→t3 delta minimal). See review F1.
  tools:            ["read_file", "write_file", "run_command"],
  system_prompt:    system_prompt,
  user_prompt:      user_prompt
}
