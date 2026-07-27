import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

FIXTURES = Path(__file__).parent / "fixtures"
USE_CASE_ROOT = Path(__file__).parent.parent


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: marks tests requiring external tools")


def load_fixture(name):
    with open(FIXTURES / f"{name}.json") as fh:
        return json.load(fh)


class DOStub:
    """A local stand-in for the DO REST API.

    Serves recorded fixtures over real HTTP so the offline suite exercises the adapter's
    actual request path — outgoing headers, pagination link following, retry — rather than
    a mocked-out `requests`. Records every request it receives so tests can assert on what
    the adapter actually sent (this is what makes the shadow guard a real assertion).
    """

    def __init__(self):
        self.requests = []
        self._routes = {}
        self._lock = threading.Lock()
        self._server = None
        self._thread = None

    # ----------------------------------------------------------------- configuration
    def route(self, path, payload, status=200, headers=None):
        """Serve `payload` for every GET of `path`."""
        self._routes[path] = [(status, payload, headers or {})]

    def sequence(self, path, responses):
        """Serve `responses` in order for successive GETs of `path`; the last repeats.

        Each response is (status, payload) or (status, payload, headers).
        """
        normalized = [
            (r[0], r[1], r[2] if len(r) > 2 else {}) for r in responses
        ]
        self._routes[path] = normalized

    def route_fixtures(self, mapping):
        for path, fixture in mapping.items():
            self.route(path, load_fixture(fixture))

    # ---------------------------------------------------------------------- lifecycle
    def start(self):
        stub = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_GET(self):  # noqa: N802 - stdlib API
                parsed = urlsplit(self.path)
                with stub._lock:
                    stub.requests.append(
                        {
                            "path": parsed.path,
                            "query": parse_qs(parsed.query),
                            "headers": dict(self.headers),
                        }
                    )
                    entries = stub._routes.get(parsed.path)
                    if not entries:
                        status, payload, headers = 404, {"id": "not_found"}, {}
                    elif len(entries) == 1:
                        status, payload, headers = entries[0]
                    else:
                        status, payload, headers = entries.pop(0)

                body = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                for key, value in headers.items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):  # silence the stdlib access log
                pass

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()

    # ------------------------------------------------------------------------ helpers
    @property
    def base_url(self):
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    @property
    def api_base(self):
        return f"{self.base_url}/v2"

    @property
    def auth_headers(self):
        return [r["headers"].get("Authorization") for r in self.requests]

    def paths(self):
        return [r["path"] for r in self.requests]


#: Every endpoint the adapter sweeps, wired to its recorded fixture.
FULL_ROUTES = {
    "/v2/account": "do_account",
    "/v2/customers/my/balance": "do_balance",
    "/v2/customers/my/invoices": "do_invoices",
    "/v2/customers/my/invoices/aaaaaaaa-0000-1111-2222-333333333333/summary":
        "do_invoice_summary",
    "/v2/customers/my/billing_history": "do_billing_history",
    "/v2/volumes": "do_volumes",
    "/v2/reserved_ips": "do_reserved_ips",
    "/v2/snapshots": "do_snapshots",
    "/v2/load_balancers": "do_load_balancers",
}


@pytest.fixture
def do_stub():
    stub = DOStub().start()
    try:
        yield stub
    finally:
        stub.stop()


@pytest.fixture
def full_stub(do_stub):
    """A stub wired for a complete successful sweep, droplets paginated across two pages."""
    do_stub.route_fixtures(FULL_ROUTES)
    do_stub.sequence(
        "/v2/droplets",
        [(200, load_fixture("do_droplets_page1")), (200, load_fixture("do_droplets_page2"))],
    )
    return do_stub
