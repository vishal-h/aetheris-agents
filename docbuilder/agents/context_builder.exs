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
  1. read_file the catalogue. Decide the doc_type + variant the request refers to. If the
     request names a doc type that is not in the catalogue, say so and STOP.
  2. read_file the run log. For "same as last month" (or similar), find the MOST RECENT
     entry (last in the array / latest timestamp) whose context matches the requested
     client_name and doc_type. Carry its stable fields forward VERBATIM:
     client_name, client_email, client_address, order_ref, order_effective_date, terms.
  3. Build the DOCBUILDER_CONTEXT for the NEW period the request asks for:
       - date: the requested period (for an invoice, the month-end of the requested month).
       - title / invoice_number / amount_due: update for the new period.
         ⚠ PROVISIONAL — the exact invoice-number sequence + financial-year increment is
         computed by a script in a later milestone step (t3). For now use the request's
         explicit values if given; otherwise mirror last month's and note it is provisional.
       - Required for every context: title, client_name, client_email, date.
         For invoices ALSO: invoice_number, client_address, amount_due.
  4. Do NOT invent client data. If a required field is neither in the request nor in a
     matching prior run, LIST what is missing and STOP — do not fabricate values.
  5. Present the resolved context as pretty JSON under the heading:
       "PROPOSED DOCBUILDER_CONTEXT (review before rendering):"
     This is the confirmation view for the operator.
  6. write_file the resolved context JSON to "output/confirmed_context.json"
     (a single JSON object — the context, not wrapped). Then print that path.

Rules:
  - All paths are relative to the sandbox root; overlay_base_dir is nil (files persist).
  - Output strictly the documented fields; do not add unknown keys.
  - You read the catalogue + run log and write the context JSON — nothing else.
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
