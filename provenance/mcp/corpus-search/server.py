#!/usr/bin/env python3
"""
Corpus-search MCP server — stdio JSON-RPC 2.0.

Exposes five tools backed by DuckDB for searching the Provenance corpus.
Reads from stdin, writes responses to stdout. All logging goes to stderr —
any print() to stdout would corrupt the JSON-RPC stream.

Environment variables:
  CORPUS_DB_PATH             — required; path to DuckDB corpus file
  CORPUS_SEARCH_READ_ONLY    — default "true"; set "false" to open read-write
"""

import json
import os
import sys

import duckdb

_DB_PATH: str = os.environ.get("CORPUS_DB_PATH", "")
_READ_ONLY: bool = os.environ.get("CORPUS_SEARCH_READ_ONLY", "true").lower() != "false"

SERVER_INFO = {"name": "corpus-search", "version": "0.1.0"}

TOOLS = [
    {
        "name": "search_corpus",
        "description": (
            "Search the corpus by keyword and/or metadata filters. "
            "Returns documents from classifications joined with f2_file_index."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query":    {"type": "string",  "description": "Search terms (whitespace-tokenised, ILIKE against path/client/raw_excerpt)"},
                "client":   {"type": "string",  "description": "Filter by client ID (exact match)"},
                "fy":       {"type": "string",  "description": "Filter by financial year, e.g. FY2024"},
                "doc_type": {"type": "string",  "description": "Filter by document type"},
                "limit":    {"type": "integer", "description": "Max results (default 20)"},
            },
        },
    },
    {
        "name": "list_clients",
        "description": "List all known clients with file counts and document types.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_documents",
        "description": "List documents for a specific client, optionally filtered by FY and doc_type.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "client":   {"type": "string",  "description": "Client ID (required)"},
                "fy":       {"type": "string",  "description": "Financial year filter"},
                "doc_type": {"type": "string",  "description": "Document type filter"},
                "limit":    {"type": "integer", "description": "Max results (default 50)"},
            },
            "required": ["client"],
        },
    },
    {
        "name": "get_document_meta",
        "description": "Full metadata for a specific file path. Returns null if not found.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path (exact match)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "find_duplicates",
        "description": "Find all corpus entries sharing the same SHA-256 hash.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sha256": {"type": "string", "description": "SHA-256 hex digest"},
            },
            "required": ["sha256"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool handlers — each takes (conn, args) and returns a JSON-serialisable value
# ---------------------------------------------------------------------------

def tool_search_corpus(conn: duckdb.DuckDBPyConnection, args: dict) -> list:
    query    = args.get("query", "")
    client   = args.get("client")
    fy       = args.get("fy")
    doc_type = args.get("doc_type")
    limit    = int(args.get("limit", 20))

    conditions: list[str] = []
    params: list = []

    if query:
        for token in query.split():
            conditions.append(
                "(c.path ILIKE ? OR c.client ILIKE ? OR c.raw_excerpt ILIKE ?)"
            )
            params += [f"%{token}%", f"%{token}%", f"%{token}%"]

    if client:
        conditions.append("c.client = ?")
        params.append(client)
    if fy:
        conditions.append("c.financial_year = ?")
        params.append(fy)
    if doc_type:
        conditions.append("c.doc_type = ?")
        params.append(doc_type)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    sql = f"""
        SELECT c.path, c.client, c.financial_year AS fy, c.doc_type,
               c.confidence, c.raw_excerpt, c.status,
               f.size_bytes
        FROM classifications c
        JOIN f2_file_index f ON c.path = f.path
        {where}
        ORDER BY c.confidence DESC, c.path ASC
        LIMIT ?
    """
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    return [
        {
            "path":                r[0],
            "client":              r[1],
            "fy":                  r[2],
            "doc_type":            r[3],
            "confidence":          r[4],
            "raw_excerpt_preview": (r[5] or "")[:200],
            "status":              r[6],
            "size_bytes":          r[7],
        }
        for r in rows
    ]


def tool_list_clients(conn: duckdb.DuckDBPyConnection, args: dict) -> list:
    sql = """
        SELECT client,
               COUNT(*) AS file_count,
               LIST(DISTINCT doc_type ORDER BY doc_type) AS doc_types
        FROM classifications
        WHERE status IN ('proposed', 'approved')
        GROUP BY client
        ORDER BY client
    """
    rows = conn.execute(sql).fetchall()
    return [
        {"client": r[0], "file_count": r[1], "doc_types": r[2]}
        for r in rows
    ]


def tool_list_documents(conn: duckdb.DuckDBPyConnection, args: dict) -> list:
    client   = args.get("client")
    fy       = args.get("fy")
    doc_type = args.get("doc_type")
    limit    = int(args.get("limit", 50))

    conditions = ["c.client = ?"]
    params: list = [client]

    if fy:
        conditions.append("c.financial_year = ?")
        params.append(fy)
    if doc_type:
        conditions.append("c.doc_type = ?")
        params.append(doc_type)

    where = "WHERE " + " AND ".join(conditions)
    sql = f"""
        SELECT c.path, c.financial_year AS fy, c.doc_type,
               c.confidence, c.status, f.size_bytes, f.mime_type
        FROM classifications c
        JOIN f2_file_index f ON c.path = f.path
        {where}
        ORDER BY c.path
        LIMIT ?
    """
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    return [
        {
            "path":       r[0],
            "fy":         r[1],
            "doc_type":   r[2],
            "confidence": r[3],
            "status":     r[4],
            "size_bytes": r[5],
            "mime_type":  r[6],
        }
        for r in rows
    ]


def tool_get_document_meta(conn: duckdb.DuckDBPyConnection, args: dict) -> dict | None:
    path = args.get("path")
    sql = """
        SELECT c.path, c.client, c.financial_year AS fy, c.doc_type,
               c.confidence, c.raw_excerpt, c.status,
               f.size_bytes, f.mime_type, f.sha256
        FROM classifications c
        JOIN f2_file_index f ON c.path = f.path
        WHERE c.path = ?
        LIMIT 1
    """
    row = conn.execute(sql, [path]).fetchone()
    if row is None:
        return None
    return {
        "path":                  row[0],
        "client":                row[1],
        "fy":                    row[2],
        "doc_type":              row[3],
        "confidence":            row[4],
        "raw_excerpt":           row[5],
        "status":                row[6],
        "classification_status": row[6],
        "size_bytes":            row[7],
        "mime_type":             row[8],
        "sha256":                row[9],
    }


def tool_find_duplicates(conn: duckdb.DuckDBPyConnection, args: dict) -> list:
    sha256 = args.get("sha256")
    sql = """
        SELECT path, size_bytes, status, last_scanned::VARCHAR AS last_scanned
        FROM f2_file_index
        WHERE sha256 = ?
        ORDER BY path
    """
    rows = conn.execute(sql, [sha256]).fetchall()
    return [
        {
            "path":         r[0],
            "size_bytes":   r[1],
            "status":       r[2],
            "last_scanned": r[3],
        }
        for r in rows
    ]


TOOL_HANDLERS = {
    "search_corpus":     tool_search_corpus,
    "list_clients":      tool_list_clients,
    "list_documents":    tool_list_documents,
    "get_document_meta": tool_get_document_meta,
    "find_duplicates":   tool_find_duplicates,
}


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 dispatch
# ---------------------------------------------------------------------------

def _ok(req_id, result) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _tool_result(req_id, value) -> dict:
    return _ok(req_id, {
        "content": [{"type": "text", "text": json.dumps(value)}],
        "isError": False,
    })


def _tool_error(req_id, message: str) -> dict:
    return _ok(req_id, {
        "content": [{"type": "text", "text": message}],
        "isError": True,
    })


def handle_request(conn: duckdb.DuckDBPyConnection, req: dict) -> dict | None:
    """Dispatch one JSON-RPC request.  Returns None for notifications (no id)."""
    req_id = req.get("id")
    method = req.get("method", "")

    # Notifications carry no id — ignore silently
    if req_id is None:
        return None

    if method == "initialize":
        return _ok(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })

    if method == "tools/list":
        return _ok(req_id, {"tools": TOOLS})

    if method == "tools/call":
        name      = req.get("params", {}).get("name", "")
        tool_args = req.get("params", {}).get("arguments", {})
        handler   = TOOL_HANDLERS.get(name)
        if handler is None:
            return _err(req_id, -32601, f"unknown tool: {name}")
        try:
            result = handler(conn, tool_args)
            return _tool_result(req_id, result)
        except Exception as exc:
            print(f"tool error [{name}]: {exc}", file=sys.stderr)
            return _tool_error(req_id, str(exc))

    return _err(req_id, -32601, f"method not found: {method}")


def main() -> None:
    if not _DB_PATH:
        print("error: CORPUS_DB_PATH env var is required", file=sys.stderr)
        sys.exit(1)

    try:
        conn = duckdb.connect(_DB_PATH, read_only=_READ_ONLY)
    except Exception as exc:
        print(f"error: cannot open {_DB_PATH}: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"corpus-search MCP ready: {_DB_PATH}", file=sys.stderr, flush=True)

    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            req = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            print(json.dumps(_err(None, -32700, f"parse error: {exc}")), flush=True)
            continue
        try:
            resp = handle_request(conn, req)
            if resp is not None:
                print(json.dumps(resp), flush=True)
        except Exception as exc:
            print(
                json.dumps(_err(req.get("id"), -32603, f"internal error: {exc}")),
                flush=True,
            )

    conn.close()


if __name__ == "__main__":
    main()
