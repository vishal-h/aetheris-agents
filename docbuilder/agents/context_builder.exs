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

  3b. FRESH request (not recurring, or no prior run) → extract fields from the freeform
      request, validate them with a script, and self-correct once if needed. You do NOT
      decide what is required or invent values — the validator owns that.

      i.   Extract a raw field map from the request: title, client_name, client_email,
           date, doc_type, and for invoices invoice_number/client_address/amount_due, plus
           any unit_price / line_item_qty / currency the text states. Extract only what the
           text actually says — OMIT a field rather than guessing it. write_file it as a
           single JSON object to "output/raw_extraction.json".
      ii.  Validate + normalise:
             run_command  command: "python3"
                          args: ["scripts/validate_fields.py",
                                 "--input", "output/raw_extraction.json",
                                 "--output", "output/validated_extraction.json"]
           (command is "python3"; do NOT also put "python3" in args.)
      iii. Exit 0 → read_file "output/validated_extraction.json" and write_file its EXACT
           contents to "output/confirmed_context.json". Go to step 4.
      iv.  Exit 1 → read_file "output/validated_extraction.json" (the error payload
           {"missing":[...], "invalid":{...}}). Re-read the ORIGINAL request carefully for
           the named fields — the first pass often misses a field the request does state.
           Re-extract incorporating only what the request actually contains (never fabricate
           a rejected value), write "output/raw_extraction.json" again, and repeat step ii
           ONCE. (This run cannot pause for a human reply; the second pass is your own
           re-read, not an operator answer.)
      v.   If validation STILL fails after the second pass → reply with exactly one
           clarifying request naming the still-missing / still-invalid fields:
           "I need the following to proceed: <fields from the payload>. Please re-run with
           these included." Do NOT write output/confirmed_context.json. STOP.

  4. Present the final context (the contents of output/confirmed_context.json) as pretty
     JSON under the heading:
       "PROPOSED DOCBUILDER_CONTEXT (review before rendering):"
     Then print the path "output/confirmed_context.json".

Rules:
  - All paths are relative to the sandbox root; overlay_base_dir is nil (files persist).
  - You read the catalogue + run log, call resolve_last_run.py (recurring) or
    validate_fields.py (fresh), and write the context JSON — nothing else. The scripts own
    the date/invoice math (recurring) and the required-field/normalisation rules (fresh);
    you never compute, default, or fabricate a value a script asked for.
  - Never write output/confirmed_context.json from an exit-1 validation — only the
    validator's exit-0 output (or resolve_last_run.py's output) becomes the context.
  - run_command: command is the executable ("python3"); never repeat it inside args.
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
