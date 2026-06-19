import argparse
import json
import sys
from pathlib import Path


def _cell_text(cell):
    val = str(cell["value"])
    return f"**{val}**" if cell["bold"] else val


def _separator(n):
    return "| " + " | ".join(["---"] * n) + " |"


def generate_md(doc_spec, output_path):
    lines = []
    if doc_spec.get("title"):
        lines.append(f"# {doc_spec['title']}")
        lines.append("")

    for sheet in doc_spec["sheets"]:
        lines.append(f"## {sheet['name']}")
        lines.append("")
        rows = sheet["rows"]
        header_written = False

        for row in rows:
            cells_text = [_cell_text(c) for c in row["cells"]]
            lines.append("| " + " | ".join(cells_text) + " |")
            if row["type"] == "header" and not header_written:
                lines.append(_separator(len(row["cells"])))
                header_written = True

        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


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
        output_path = output_dir / f"{args.filename}.md"
        generate_md(doc_spec, output_path)
        print(str(output_path))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
