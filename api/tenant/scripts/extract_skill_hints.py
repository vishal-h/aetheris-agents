#!/usr/bin/env python3
"""extract_skill_hints.py <trajectory_json>

Reads a trajectory JSON file (events array from `mix aetheris trajectory <run_id> --export`)
and extracts a skill hint JSON for injection into at1cmd on subsequent runs.

Output (stdout): skill hint JSON
Exit 0 always (analysis script); exit 1 on unreadable/invalid file.
"""

import json
import sys


def load_events(path: str) -> list[dict]:
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "events" in data:
        return data["events"]
    raise ValueError("Unrecognised trajectory format: expected array or object with 'events' key")


def extract_hints(events: list[dict]) -> dict:
    tool_sequence: list[str] = []
    scripts: list[str] = []
    intent_type: str | None = None
    flags: list[str] = []
    record_count: int | None = None
    run_id: str | None = None
    max_step: int = 0

    for event in events:
        run_id = run_id or event.get("run_id")
        step = event.get("step", 0)
        if step > max_step:
            max_step = step

        if event["type"] != "tool_called":
            continue

        tool_name = event["payload"]["tool_name"]
        tool_sequence.append(tool_name)

        if tool_name != "run_command":
            continue

        args = event["payload"]["tool_input"].get("args", [])
        if not args:
            continue

        script_path = args[0]
        if script_path not in scripts:
            scripts.append(script_path)

        for arg in args[1:]:
            if not isinstance(arg, str) or '"intent_type"' not in arg:
                continue
            try:
                intent_json = json.loads(arg)
            except (json.JSONDecodeError, TypeError):
                continue

            if not intent_type and "intent_type" in intent_json:
                intent_type = intent_json["intent_type"]

            for flag in intent_json.get("flags", []):
                reason = flag.get("reason", "")
                if reason and reason not in flags:
                    flags.append(reason)

            if record_count is None and "payload" in intent_json:
                record_count = len(intent_json["payload"])

    return {
        "intent_type": intent_type,
        "step_count": max_step + 1,
        "tool_sequence": tool_sequence,
        "scripts": scripts,
        "flags": flags,
        "record_count": record_count,
        "extracted_from_run": run_id,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: extract_skill_hints.py <trajectory_json>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    try:
        events = load_events(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    hints = extract_hints(events)
    print(json.dumps(hints, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
