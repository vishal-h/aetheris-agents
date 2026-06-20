"""List the template catalogue for a tenant.

Reads `{templates_dir}/{tenant_id}/catalogue.json` and prints it to stdout.
The catalogue lists the tenant's doc types and per-variant metadata (versions,
output formats, base-file/narrative availability). This is the foundation for
LLM template selection in m2b; in m2a it is standalone (not called by the
orchestrator).

Exit 1 if the tenant directory or its catalogue.json is missing.
"""

import argparse
import json
import sys
from pathlib import Path


def load_catalogue(templates_dir, tenant_id):
    """Return the parsed catalogue dict for `tenant_id`.

    Raises FileNotFoundError if the catalogue does not exist.
    """
    path = Path(templates_dir) / tenant_id / "catalogue.json"
    if not path.exists():
        raise FileNotFoundError(
            f"catalogue not found for tenant '{tenant_id}': {path}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", required=True, help="tenant id")
    parser.add_argument("--templates-dir", default="data/templates",
                        help="templates root directory (default: data/templates)")
    args = parser.parse_args()

    try:
        catalogue = load_catalogue(args.templates_dir, args.tenant)
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(catalogue, indent=2))


if __name__ == "__main__":
    main()
