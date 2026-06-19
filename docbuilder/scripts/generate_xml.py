import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def generate_xml(doc_spec, output_path):
    root = ET.Element("document")
    if doc_spec.get("title"):
        root.set("title", doc_spec["title"])

    for sheet in doc_spec["sheets"]:
        sheet_el = ET.SubElement(root, "sheet", name=sheet["name"])
        for row in sheet["rows"]:
            row_el = ET.SubElement(sheet_el, "row", type=row["type"])
            for cell in row["cells"]:
                cell_el = ET.SubElement(row_el, "cell")
                cell_el.text = str(cell["value"])

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(str(output_path), encoding="unicode", xml_declaration=False)


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
        output_path = output_dir / f"{args.filename}.xml"
        generate_xml(doc_spec, output_path)
        print(str(output_path))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
