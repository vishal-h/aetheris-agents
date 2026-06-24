"""Chain the docbuilder context builder → orchestrator as two sequential runs.

Run **top-level** (e.g. by Rig via orchestrate_start's `.py` heuristic, or from a
shell) — NOT inside an `mix aetheris run` agent. A nested `mix aetheris run` fails:
the inner run's worker-binary recompile copies a binary the outer run holds open
(ETXTBSY). Run top-level, the two sub-runs are sequential — each worker exits and
frees the binary before the next (like the `docbuilder_context` sprint).

It exists as a Python script because `run_command` can't set per-invocation env (no
`env` field) and the exec-server allowlist blocks `sh`/`bash`; `python3` is allowlisted.
The env plumbing lives here:

  1. `mix aetheris run context_builder.exs`        env: TENANT + REQUEST
  2. verify output/confirmed_context.json exists + is valid JSON
  3. `mix aetheris run docbuilder_orchestrator.exs` env: TENANT + CONTEXT_FILE,
     DOCBUILDER_CONTEXT removed (orchestrator precedence is env > file)

With `--protocol`, emits the orchestrator newline-JSON protocol on stdout
(`plan` / `step_started` / `step_complete` / `orchestration_complete`) so Rig's
`useOrchestrator` drives the phase lifecycle. One-click: no stdin approval gate.
Without `--protocol`, prints a single JSON summary (for CLI/tests). Exit 0 only when
both sub-runs succeed.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

CONTEXT_BUILDER = "docbuilder/agents/context_builder.exs"
ORCHESTRATOR    = "docbuilder/agents/docbuilder_orchestrator.exs"


def _noop(_msg):
    pass


def _build_env(overrides, remove=()):
    """Start from the current environment, drop `remove` keys, apply `overrides`."""
    env = dict(os.environ)
    for k in remove:
        env.pop(k, None)
    env.update(overrides)
    return env


def run_sub_agent(agent_exs, aetheris_dir, env):
    """Run one `mix aetheris run <agent_exs>` from the aetheris mix project (cwd),
    with the given environment. Output captured. Returns the CompletedProcess."""
    return subprocess.run(
        ["mix", "aetheris", "run", agent_exs],
        env=env, cwd=aetheris_dir, capture_output=True, text=True,
    )


def build_plan(tenant, request):
    """The two-step plan, in the shape `useOrchestrator` expects. Step `agent` values
    match the t2 STEP_CONFIG_HINTS keys so the panel surfaces the relevant env vars."""
    return {
        "type": "plan",
        "request": request,
        "params": {"DOCBUILDER_TENANT": tenant, "DOCBUILDER_REQUEST": request},
        "steps": [
            {"id": "context_builder",
             "description": "Build the document context from the request",
             "agent": CONTEXT_BUILDER, "context": ""},
            {"id": "orchestrator",
             "description": "Render the document from the confirmed context",
             "agent": ORCHESTRATOR, "context": ""},
        ],
    }


def chain(tenant, request, aetheris_dir, agents_dir, on_event=_noop):
    """Run the two-step flow, emitting step_started/step_complete via `on_event`.
    Returns (summary_dict, exit_code)."""
    docbuilder = Path(agents_dir) / "docbuilder"
    context_builder = str(docbuilder / "agents" / "context_builder.exs")
    orchestrator    = str(docbuilder / "agents" / "docbuilder_orchestrator.exs")
    confirmed       = docbuilder / "output" / "confirmed_context.json"
    renamed         = docbuilder / "output" / "renamed.json"

    summary = {
        "status": None,
        "context_builder_exit": None,
        "orchestrator_exit": None,
        "confirmed_context_path": str(confirmed),
        "outputs": [],
    }

    def fail_step(step_id, message, stderr=None):
        on_event({"type": "step_complete", "step_id": step_id,
                  "status": "failed", "error": message})
        summary["status"] = "error"
        summary["error"] = message
        if stderr is not None:
            summary["stderr_tail"] = (stderr or "")[-800:]
        return summary, 1

    # Step 1 — context builder
    on_event({"type": "step_started", "step_id": "context_builder"})
    r1 = run_sub_agent(
        context_builder, aetheris_dir,
        _build_env({"DOCBUILDER_TENANT": tenant, "DOCBUILDER_REQUEST": request}),
    )
    summary["context_builder_exit"] = r1.returncode
    if r1.returncode != 0:
        return fail_step("context_builder",
                         f"context builder failed (exit {r1.returncode})", r1.stderr)
    if not confirmed.exists():
        return fail_step("context_builder",
                         "context builder did not write confirmed_context.json")
    try:
        json.loads(confirmed.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return fail_step("context_builder", f"confirmed_context.json is not valid JSON: {e}")
    on_event({"type": "step_complete", "step_id": "context_builder", "status": "done"})

    # Step 2 — orchestrator (DOCBUILDER_CONTEXT removed so the file is read)
    on_event({"type": "step_started", "step_id": "orchestrator"})
    r2 = run_sub_agent(
        orchestrator, aetheris_dir,
        _build_env(
            {"DOCBUILDER_TENANT": tenant, "DOCBUILDER_CONTEXT_FILE": str(confirmed)},
            remove=("DOCBUILDER_CONTEXT",),
        ),
    )
    summary["orchestrator_exit"] = r2.returncode
    if r2.returncode != 0:
        return fail_step("orchestrator",
                         f"orchestrator failed (exit {r2.returncode})", r2.stderr)
    on_event({"type": "step_complete", "step_id": "orchestrator", "status": "done"})

    # Outputs from the orchestrator's rename record (best-effort).
    try:
        data = json.loads(renamed.read_text())
        summary["outputs"] = [
            e["renamed"] for e in data if isinstance(e, dict) and "renamed" in e
        ]
    except (json.JSONDecodeError, OSError, TypeError):
        summary["outputs"] = []

    summary["status"] = "ok"
    return summary, 0


def main():
    parser = argparse.ArgumentParser(
        description="Chain docbuilder context builder -> orchestrator.")
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--request", required=True)
    parser.add_argument("--aetheris-dir", required=True,
                        help="path to the aetheris mix project (cwd for mix)")
    parser.add_argument("--agents-dir", required=True,
                        help="path to the aetheris-agents repo root")
    parser.add_argument("--protocol", action="store_true",
                        help="emit the orchestrator newline-JSON protocol on stdout "
                             "(default: print a single JSON summary)")
    args = parser.parse_args()

    if args.protocol:
        def emit(msg):
            print(json.dumps(msg), flush=True)

        emit(build_plan(args.tenant, args.request))
        _summary, code = chain(
            args.tenant, args.request, args.aetheris_dir, args.agents_dir, on_event=emit)
        emit({"type": "orchestration_complete"})
        sys.exit(code)

    summary, code = chain(args.tenant, args.request, args.aetheris_dir, args.agents_dir)
    print(json.dumps(summary, indent=2))
    sys.exit(code)


if __name__ == "__main__":
    main()
