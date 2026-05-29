"""
Validate search_agent.exs against a set of test queries.

Runs each query via `mix aetheris run` and checks the agent output:
- expected_paths: []   -> pass if >=1 result path appears in output (not "no documents found")
- expected_paths: null -> pass if agent reports graceful "not found" message (no error)
- expected_paths: [..] -> pass if >=1 expected path appears in output

Usage:
    python3 scripts/validate_search.py \\
        --db /data/corpus.duckdb \\
        --queries tests/fixtures/search_queries.json \\
        [--model claude-haiku-4-5-20251001] \\
        [--n 1] \\
        [--threshold 0.85] \\
        [--aetheris /path/to/aetheris] \\
        [--agent /path/to/search_agent.exs]

Exits 0 if pass_rate >= threshold (default 0.85), exits 1 otherwise.
"""

import argparse
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

_PATH_PATTERN = re.compile(r"/\S+\.\w{2,5}")
_NO_RESULTS_PATTERN = re.compile(r"no documents? found|no results? found|nothing found", re.IGNORECASE)

_REPO_ROOT = Path(__file__).parent.parent.parent
_DEFAULT_AETHERIS = _REPO_ROOT.parent / "aetheris"
_DEFAULT_AGENT = Path(__file__).parent.parent / "agents" / "search_agent.exs"
_DEFAULT_QUERIES = Path(__file__).parent.parent / "tests" / "fixtures" / "search_queries.json"


def run_query(query: str, db_path: str, agent_path: Path, aetheris_dir: Path, model: str | None) -> dict:
    env = {
        **os.environ,
        "PROVENANCE_DB_PATH": db_path,
        "CORPUS_SEARCH_MCP_ENABLED": "true",
        "SEARCH_QUERY": query,
    }

    cmd = ["mix", "aetheris", "run", str(agent_path)]
    if model:
        cmd += ["--model", model]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(aetheris_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout + result.stderr
        run_id = _extract_run_id(result.stdout)
        return {"output": output, "run_id": run_id, "exit_code": result.returncode, "error": None}
    except subprocess.TimeoutExpired:
        return {"output": "", "run_id": None, "exit_code": -1, "error": "timeout"}
    except Exception as exc:
        return {"output": "", "run_id": None, "exit_code": -1, "error": str(exc)}


def _extract_run_id(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if line.startswith("Run ID:"):
            return line.split(":", 1)[1].strip()
    return None


def score_query(case: dict, run_result: dict) -> dict:
    query = case["query"]
    expected_paths = case.get("expected_paths")  # None = no-results check; [] = any result
    output = run_result["output"]

    if run_result["error"]:
        return {"query": query, "passed": False, "result_count": 0,
                "run_id": run_result["run_id"], "reason": run_result["error"]}

    if expected_paths is None:
        # No-results query: pass if output contains a graceful "not found" message
        passed = bool(_NO_RESULTS_PATTERN.search(output))
        return {"query": query, "passed": passed, "result_count": 0,
                "run_id": run_result["run_id"],
                "reason": None if passed else "expected no-results message not found"}

    found_paths = _PATH_PATTERN.findall(output)
    result_count = len(found_paths)

    if expected_paths:
        # Specific paths expected: at least one must appear
        passed = any(p in output for p in expected_paths)
        reason = None if passed else f"none of {expected_paths} found in output"
    else:
        # Any result expected: at least one path and no "not found" message
        passed = result_count > 0 and not _NO_RESULTS_PATTERN.search(output)
        reason = None if passed else "no result paths found in output"

    return {"query": query, "passed": passed, "result_count": result_count,
            "run_id": run_result["run_id"], "reason": reason}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate search_agent.exs against test queries")
    parser.add_argument("--db", required=True, help="DuckDB corpus path")
    parser.add_argument("--queries", default=str(_DEFAULT_QUERIES),
                        help="JSON file with test queries")
    parser.add_argument("--model", default=None, help="Override model")
    parser.add_argument("--n", type=int, default=1, help="Runs per query (1 for CI)")
    parser.add_argument("--threshold", type=float, default=0.85,
                        help="Minimum pass rate to exit 0 (default 0.85)")
    parser.add_argument("--aetheris", default=str(_DEFAULT_AETHERIS),
                        help="Path to aetheris repo directory")
    parser.add_argument("--agent", default=str(_DEFAULT_AGENT),
                        help="Path to search_agent.exs")
    args = parser.parse_args()

    aetheris_dir = Path(args.aetheris)
    if not aetheris_dir.exists():
        print(f"Error: aetheris directory not found: {aetheris_dir}", file=sys.stderr)
        sys.exit(1)

    with open(args.queries) as f:
        queries = json.load(f)

    total = len(queries)
    results = []

    for i, case in enumerate(queries, 1):
        q = case["query"]
        print(f"[{i}/{total}] {q[:60]}...", file=sys.stderr, end=" ", flush=True)
        run_result = run_query(q, args.db, Path(args.agent), aetheris_dir, args.model)
        scored = score_query(case, run_result)
        results.append(scored)
        status = "PASS" if scored["passed"] else "FAIL"
        print(status, file=sys.stderr)
        if not scored["passed"] and scored.get("reason"):
            print(f"       reason: {scored['reason']}", file=sys.stderr)

    passed = sum(1 for r in results if r["passed"])
    pass_rate = passed / total if total > 0 else 0.0

    report = {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(pass_rate, 4),
        "threshold": args.threshold,
        "results": results,
    }

    print(json.dumps(report, indent=2))

    if pass_rate < args.threshold:
        print(
            f"\nFAIL: pass_rate={pass_rate:.0%} below threshold={args.threshold:.0%}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"\nPASS: pass_rate={pass_rate:.0%} >= threshold={args.threshold:.0%}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
