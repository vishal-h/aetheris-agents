import argparse
import csv
import io
import json
import sys
from pathlib import Path


def generate_csv(doc_spec, output_path):
    buf = io.StringIO()
    writer = csv.writer(buf)
    sheets = doc_spec["sheets"]
    multi = len(sheets) > 1

    for i, sheet in enumerate(sheets):
        if i > 0:
            buf.write("\n")
        if multi:
            buf.write(f"# Sheet: {sheet['name']}\n")
        for row in sheet["rows"]:
            writer.writerow([str(c["value"]) for c in row["cells"]])

    output_path.write_text(buf.getvalue(), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--filename", default="document")
    args = parser.parse_args()

    try:
        doc_spec = json.load(sys.stdin)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

    try:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{args.filename}.csv"
        generate_csv(doc_spec, output_path)
        print(str(output_path))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
