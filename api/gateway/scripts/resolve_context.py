#!/usr/bin/env python3
"""resolve_context.py <intent_json> <context_json> <vocabulary_jsonl>

Resolves the execution context needed to process an intent.
Merges prior context (from setup intents) with vocabulary doc lookups.

Output (stdout): JSON with resolved inst_id, course_map, term_name, unresolved_courses.
Exit 0 always (errors reported in output).
"""

import base64
import json
import sys
from pathlib import Path


def _inst_id_from_jwt(token: str) -> str | None:
    try:
        parts = token.split(".")
        payload = json.loads(base64.b64decode(parts[1] + "==").decode())
        inner = json.loads(payload["token"])
        return inner.get("ClientId")
    except Exception:
        return None


def _load_vocab(vocab_path: str) -> dict:
    records: dict = {"courses": {}, "terms": {}, "current_term": None}
    try:
        with open(vocab_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                rt = rec.get("record_type")
                if rt == "lookup" and rec.get("name") == "courses":
                    records["courses"][rec["label"]] = rec["id"]
                elif rt == "lookup" and rec.get("name") == "terms":
                    records["terms"][rec["label"]] = rec["id"]
                    if rec.get("current"):
                        records["current_term"] = rec["label"]
    except Exception:
        pass
    return records


def resolve(intent: dict, context: dict, vocab_path: str) -> dict:
    import os

    vocab = _load_vocab(vocab_path)

    # InstId: context first, then JWT
    inst_id = context.get("inst_id") or _inst_id_from_jwt(
        os.environ.get("CT_API_TOKEN", "")
    )

    # course_map: context overrides vocab
    course_map: dict[str, str] = dict(vocab["courses"])
    if context.get("course_map"):
        course_map.update(context["course_map"])

    # term_name default
    term_name = context.get("term_name") or vocab.get("current_term") or "Annual"

    # Find which courses in payload cannot be resolved
    payload = intent.get("payload", [])
    requested = {row.get("course", "") for row in payload if row.get("course")}
    unresolved = [c for c in requested if c and c not in course_map]

    return {
        "inst_id": inst_id or "",
        "course_map": course_map,
        "term_name": term_name,
        "unresolved_courses": unresolved,
    }


def main() -> None:
    if len(sys.argv) < 4:
        print("Usage: resolve_context.py <intent_json> <context_json> <vocabulary_jsonl>",
              file=sys.stderr)
        sys.exit(1)

    intent_json, context_json, vocab_path = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        intent = json.loads(intent_json)
    except json.JSONDecodeError:
        intent = {}

    try:
        context = json.loads(context_json)
    except json.JSONDecodeError:
        context = {}

    result = resolve(intent, context, vocab_path)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
