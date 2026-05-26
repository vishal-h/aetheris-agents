#!/usr/bin/env python3
"""validate_intent.py <intent_json> <vocabulary_jsonl>

Validates a TAP intent packet against the vocabulary doc.
Checks required fields, enum lookups, and conditional rules.
Output: {"valid": bool, "errors": [...], "warnings": [...], "flags": [...]}
Exit 0 always (errors in report, not exit code).
"""

import json
import sys
from pathlib import Path


GENDER_LABEL_TO_ID = {"female": "0", "male": "1", "other": "90"}


def load_vocabulary(vocab_path: str) -> dict:
    intents: dict = {}
    fields: dict = {}
    rules: list = []
    lookups: dict = {}

    with open(vocab_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            rt = record.get("record_type")
            if rt == "intent":
                intents[record["name"]] = record
            elif rt == "field":
                fields[record["name"]] = record
            elif rt == "rule":
                rules.append(record)
            elif rt == "lookup":
                name = record["name"]
                lookups.setdefault(name, []).append(record)

    return {"intents": intents, "fields": fields, "rules": rules, "lookups": lookups}


def _fields_with_default(intent_name: str, vocab: dict) -> set[str]:
    """Return field names that have if_missing: use_default rules — not errors when absent."""
    defaulted = set()
    for rule in vocab["rules"]:
        if rule.get("intent") == intent_name and rule.get("if_missing") == "use_default":
            if "field" in rule:
                defaulted.add(rule["field"])
    return defaulted


def validate_row(row: dict, intent_def: dict, vocab: dict, row_label: str) -> list[str]:
    errors = []

    defaulted_fields = _fields_with_default(intent_def["name"], vocab)
    requires = intent_def.get("requires", [])
    for field in requires:
        if field in defaulted_fields:
            continue
        # map TAP field names to CSV row keys
        csv_key = _field_to_csv_key(field)
        value = row.get(csv_key) or row.get(field)
        if not value:
            errors.append(f"{row_label}: required field '{field}' is missing or empty")

    # Validate gender enum
    gender = row.get("gender")
    if gender is not None:
        valid_labels = {lk["label"].lower() for lk in vocab["lookups"].get("gender", [])}
        if gender.lower() not in valid_labels:
            errors.append(
                f"{row_label}: gender '{gender}' is not a valid value; "
                f"expected one of {sorted(valid_labels)}"
            )

    # Apply conditional rules
    for rule in vocab["rules"]:
        if "if" not in rule:
            continue
        condition = rule["if"]
        field_key = _field_to_csv_key(condition["field"])
        field_present = bool(row.get(field_key) or row.get(condition["field"]))
        should_apply = condition.get("present", False) == field_present

        if not should_apply:
            continue

        then = rule["then"]
        if "require_one_of" in then:
            one_of = then["require_one_of"]
            satisfied = any(
                row.get(_field_to_csv_key(f)) or row.get(f) for f in one_of
            )
            if not satisfied:
                errors.append(
                    f"{row_label}: '{condition['field']}' is present but none of "
                    f"{one_of} provided"
                )
        if "require" in then:
            for req_field in then["require"]:
                csv_key = _field_to_csv_key(req_field)
                if not (row.get(csv_key) or row.get(req_field)):
                    errors.append(
                        f"{row_label}: '{condition['field']}' is present but "
                        f"'{req_field}' is missing"
                    )

    return errors


def _field_to_csv_key(field: str) -> str:
    # Map TAP vocabulary field names to CSV column names used in parse_csv.py
    mapping = {
        "name": "name",
        "gender": "gender",
        "courseName": "course",
        "secName": "section",
        "termName": "termName",
        "dob": "date_of_birth",
        "doa": "date_of_admission",
        "email": "email",
        "mobile": "mobile",
        "rollNo": "roll_no",
        "admissionNumber": "admission_number",
        "fatherName": "father_name",
        "fatherEmail": "father_email",
        "fatherMobile": "father_mobile",
        "motherName": "mother_name",
        "motherEmail": "mother_email",
        "motherMobile": "mother_mobile",
        "guardianName": "guardian_name",
        "guardianGender": "guardian_gender",
        "guardianEmail": "guardian_email",
        "guardianMobile": "guardian_mobile",
    }
    return mapping.get(field, field)


def validate_intent(intent: dict, vocab: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    flags: list[dict] = []

    intent_type = intent.get("intent_type", "")
    intent_def = vocab["intents"].get(intent_type)
    if intent_def is None:
        errors.append(f"Unknown intent_type: '{intent_type}'")
        return {"valid": False, "errors": errors, "warnings": warnings, "flags": flags}

    payload = intent.get("payload", [])
    if not payload:
        warnings.append("Payload is empty")

    for i, row in enumerate(payload):
        name = row.get("name") or f"row_{i}"
        row_errors = validate_row(row, intent_def, vocab, name)
        errors.extend(row_errors)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "flags": flags,
    }


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: validate_intent.py <intent_json> <vocabulary_jsonl>", file=sys.stderr)
        sys.exit(1)

    intent_json_arg = sys.argv[1]
    vocab_path = sys.argv[2]

    try:
        intent = json.loads(intent_json_arg)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid intent JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    if not Path(vocab_path).exists():
        print(f"Error: vocabulary file not found: {vocab_path}", file=sys.stderr)
        sys.exit(1)

    try:
        vocab = load_vocabulary(vocab_path)
    except Exception as exc:
        print(f"Error loading vocabulary: {exc}", file=sys.stderr)
        sys.exit(1)

    report = validate_intent(intent, vocab)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
