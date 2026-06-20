import argparse
import csv
import json
import sys
from pathlib import Path


def _read_csv(path):
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def _read_json(path):
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError("JSON file must contain a top-level array")
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", default="main")
    parser.add_argument("path")
    parser.add_argument("--output", default=None,
                        help="write the raw JSON to FILE and print only the path "
                             "(default: print the raw JSON to stdout)")
    args = parser.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(json.dumps({"status": "error", "error": f"file not found: {args.path}"}), file=sys.stderr)
        sys.exit(1)

    try:
        ext = p.suffix.lower()
        if ext == ".csv":
            rows = _read_csv(p)
        elif ext == ".json":
            rows = _read_json(p)
        else:
            print(json.dumps({"status": "error", "error": f"unsupported file type: {p.suffix}"}), file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

    out = json.dumps({"key": args.key, "rows": rows})
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        print(args.output)
    else:
        print(out)


if __name__ == "__main__":
    main()
