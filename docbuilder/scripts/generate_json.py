import argparse
import json
import sys
from pathlib import Path


def generate_json(doc_spec, output_path):
    out = {"title": doc_spec.get("title", ""), "sheets": []}
    for sheet in doc_spec["sheets"]:
        out["sheets"].append({
            "name": sheet["name"],
            "columns": [c["name"] for c in sheet["columns"]],
            "rows": [
                [c["value"] for c in row["cells"]]
                for row in sheet["rows"]
            ],
        })
    output_path.write_text(json.dumps(out, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--filename", default="document")
    parser.add_argument("--input", default=None, help="doc spec JSON file path (default: stdin)")
    args = parser.parse_args()

    try:
        src = open(args.input, encoding="utf-8") if args.input else sys.stdin
        doc_spec = json.load(src)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

    try:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{args.filename}.json"
        generate_json(doc_spec, output_path)
        print(str(output_path))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
