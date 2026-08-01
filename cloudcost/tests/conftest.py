import json
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

import aws_wire  # noqa: E402 - needs the sys.path line above

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


# =============================================================================== AWS (m2 t1)

#: Distinctive so a leak or a default-chain fallback is unambiguous in captured output.
CLOUDCOST_ACCESS_KEY = "AKIACLOUDCOSTRO00000"
CLOUDCOST_SECRET_KEY = "cc-aws-secret-SENTINEL-3f9a1c7e"
CLOUDCOST_SESSION_TOKEN = "cc-aws-token-SENTINEL-0d4b8e51"

#: What a fallback to boto3's default credential chain would sign with.
POISON_ACCESS_KEY = "AKIADEFAULTCHAIN0000"
POISON_SECRET_KEY = "aws-default-chain-DECOY-9b2f4d81"

REGION_A = "us-east-1"  # bootstrap region; carries every service and both paging idioms
REGION_B = "eu-west-1"  # disjoint resource ids, EC2 + RDS only
REGION_C = "ap-south-2"  # opted-in and entirely empty

ANY_REGION = "*"

#: `Credential=<access key>/<date>/<region>/<signing name>/aws4_request`. boto3 signs with the
#: *client's* configured region even when every region is pointed at one endpoint URL, so this
#: is how the stub observes which region a request was made for.
_CREDENTIAL_SCOPE = re.compile(r"Credential=([^/]+)/[^/]+/([^/]+)/([^/]+)/")

#: `service:Action` -> the result key an empty response must carry. Used by `empty()`, which
#: is always explicit: an unrouted call is a 400, never a silent `[]`.
AWS_RESULT_KEYS = {
    "ec2:DescribeInstances": "Reservations",
    "ec2:DescribeVolumes": "Volumes",
    "ec2:DescribeAddresses": "Addresses",
    "ec2:DescribeSnapshots": "Snapshots",
    "elbv2:DescribeLoadBalancers": "LoadBalancers",
    "elbv2:DescribeTargetGroups": "TargetGroups",
    "elbv2:DescribeTargetHealth": "TargetHealthDescriptions",
    "elbv2:DescribeTags": "TagDescriptions",
    "elb:DescribeLoadBalancers": "LoadBalancerDescriptions",
    "elb:DescribeTags": "TagDescriptions",
    "rds:DescribeDBInstances": "DBInstances",
    "rds:DescribeDBSnapshots": "DBSnapshots",
}

#: Every inventory call the sweep makes in a region.
AWS_INVENTORY_OPS = tuple(AWS_RESULT_KEYS)


class AWSStub:
    """A local stand-in for the AWS query/JSON endpoints.

    Serves recorded fixtures over real HTTP so the offline suite exercises boto3's actual
    request path — SigV4 signing, one client per swept region, paginators, error shaping —
    rather than a mocked-out client. (`botocore.stub.Stubber` registers on `before-call`,
    which short-circuits before `_make_request`, so signing never runs and there is no
    credential on any wire to assert against; it cannot express the poison guard at all.)

    Records every request it receives, and **enforces the access key id**: a request signed
    with anything other than `expected_access_key` gets a real 403 `InvalidClientTokenId`.
    That enforcement is what makes the default-chain poison guard a real assertion — against
    a permissive stub, a run that *had* fallen back to the poisoned default chain would be
    just as green as one that had not, and the guard would prove nothing.
    """

    def __init__(self, expected_access_key: str = CLOUDCOST_ACCESS_KEY) -> None:
        self.expected_access_key = expected_access_key
        self.requests = []
        self._routes = {}
        self._lock = threading.Lock()
        self._server = None
        self._thread = None

    # ----------------------------------------------------------------- configuration
    def route(self, key, fixture, region=ANY_REGION):
        """Serve `fixture` (a bare stem) for every `key` = "ec2:DescribeVolumes" in `region`."""
        service, action = key.split(":")
        body, ctype = aws_wire.encode(service, action, load_fixture(fixture))
        self._routes[(service, action, region)] = [(200, body, ctype)]

    def sequence(self, key, fixtures, region=ANY_REGION):
        """Serve `fixtures` in order for successive calls; the last repeats.

        This is what drives the paginators: page 1 carries a paging token, the last page
        does not. A repeating `route()` for a token-bearing page would loop forever.
        """
        service, action = key.split(":")
        self._routes[(service, action, region)] = [
            (200,) + aws_wire.encode(service, action, load_fixture(name)) for name in fixtures
        ]

    def empty(self, key, region=ANY_REGION):
        """An explicitly-empty result set — a region that carries none of this resource."""
        service, action = key.split(":")
        body, ctype = aws_wire.encode(service, action, {AWS_RESULT_KEYS[key]: []})
        self._routes[(service, action, region)] = [(200, body, ctype)]

    def fail(self, key, code, status=500, region=ANY_REGION):
        service, action = key.split(":")
        body, ctype = aws_wire.encode_error(service, code)
        self._routes[(service, action, region)] = [(status, body, ctype)]

    def route_fixtures(self, mapping, region=ANY_REGION):
        for key, fixture in mapping.items():
            self.route(key, fixture, region=region)

    # ---------------------------------------------------------------------- lifecycle
    def start(self):
        stub = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_POST(self):  # noqa: N802 - every AWS query/json call is a POST
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length).decode()
                scope = _CREDENTIAL_SCOPE.search(self.headers.get("Authorization", "") or "")
                access_key, region, signing_name = (
                    scope.groups() if scope else (None, None, None)
                )

                target = self.headers.get("X-Amz-Target")
                if target:
                    prefix, action = target.split(".")
                    service = aws_wire.SERVICE_BY_TARGET_PREFIX.get(prefix)
                    params = json.loads(raw) if raw else {}
                else:
                    form = {k: v[0] for k, v in parse_qs(raw).items()}
                    action = form.get("Action")
                    service = aws_wire.SERVICE_BY_VERSION.get(form.get("Version"))
                    params = form

                with stub._lock:
                    stub.requests.append(
                        {
                            "service": service,
                            "action": action,
                            "region": region,
                            "access_key": access_key,
                            "signing_name": signing_name,
                            "params": params,
                            "headers": dict(self.headers),
                        }
                    )
                    if access_key != stub.expected_access_key:
                        # AWS's own answer to a key it does not know. Without this branch a
                        # default-chain fallback would pass silently.
                        status, body, ctype = (403,) + aws_wire.encode_error(
                            service or "sts",
                            "InvalidClientTokenId",
                            "The security token included in the request is invalid.",
                        )
                    else:
                        entries = stub._routes.get(
                            (service, action, region)
                        ) or stub._routes.get((service, action, ANY_REGION))
                        if entries is None:
                            status, body, ctype = (400,) + aws_wire.encode_error(
                                service or "sts",
                                "NotStubbed",
                                f"no route for {service}:{action} in {region}",
                            )
                        elif len(entries) == 1:
                            status, body, ctype = entries[0]
                        else:
                            status, body, ctype = entries.pop(0)

                self.send_response(status)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
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
    def endpoint_url(self):
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def calls(self, key, region=None):
        service, action = key.split(":")
        return [
            request
            for request in self.requests
            if request["service"] == service
            and request["action"] == action
            and region in (None, request["region"])
        ]

    def regions_seen(self, key=None):
        if key is None:
            return {request["region"] for request in self.requests}
        return {request["region"] for request in self.calls(key)}

    def access_keys_seen(self):
        return {request["access_key"] for request in self.requests}


#: Region-independent calls: the account id and the region enumeration itself.
AWS_GLOBAL_ROUTES = {
    "sts:GetCallerIdentity": "aws_sts_caller_identity",
    "ec2:DescribeRegions": "aws_ec2_regions",
}

#: region -> {service:Action -> fixture}. Resource ids are disjoint per region, so a sweep
#: that silently covers one region is detectable in the *emitted inventory*, not only in the
#: request log. Anything a region does not carry is routed `empty()` explicitly.
AWS_REGION_ROUTES = {
    REGION_A: {
        "ec2:DescribeVolumes": "aws_ec2_volumes_us_east_1",
        "ec2:DescribeAddresses": "aws_ec2_addresses_us_east_1",
        "ec2:DescribeSnapshots": "aws_ec2_snapshots_us_east_1",
        "elbv2:DescribeLoadBalancers": "aws_elbv2_load_balancers_us_east_1",
        "elbv2:DescribeTags": "aws_elbv2_tags_us_east_1",
        "elb:DescribeLoadBalancers": "aws_elb_load_balancers_us_east_1",
        "elb:DescribeTags": "aws_elb_tags_us_east_1",
        "rds:DescribeDBSnapshots": "aws_rds_snapshots_us_east_1",
    },
    REGION_B: {
        "ec2:DescribeInstances": "aws_ec2_instances_eu_west_1",
        "ec2:DescribeVolumes": "aws_ec2_volumes_eu_west_1",
        "ec2:DescribeAddresses": "aws_ec2_addresses_eu_west_1",
        "rds:DescribeDBInstances": "aws_rds_instances_eu_west_1",
    },
    REGION_C: {},
}

#: (region, key) pairs served by `sequence()` — excluded from the empty() backfill.
AWS_SEQUENCED = {
    (REGION_A, "ec2:DescribeInstances"),
    (REGION_A, "rds:DescribeDBInstances"),
    (REGION_A, "elbv2:DescribeTargetGroups"),
    (REGION_A, "elbv2:DescribeTargetHealth"),
}


@pytest.fixture
def aws_stub():
    stub = AWSStub().start()
    try:
        yield stub
    finally:
        stub.stop()


@pytest.fixture
def full_aws_stub(aws_stub):
    """Wired for a complete successful three-region sweep.

    Region A carries every service, EC2 instances paginated on `NextToken` and RDS instances
    on `Marker` (the two idioms differ and are covered independently); region B carries a
    disjoint EC2 + RDS set and no load balancers; region C is opted-in and entirely empty.
    """
    aws_stub.route_fixtures(AWS_GLOBAL_ROUTES)
    aws_stub.route("ce:GetCostAndUsage", "aws_ce_cost_and_usage")

    aws_stub.sequence(
        "ec2:DescribeInstances",
        ["aws_ec2_instances_us_east_1_page1", "aws_ec2_instances_us_east_1_page2"],
        region=REGION_A,
    )
    aws_stub.sequence(
        "rds:DescribeDBInstances",
        ["aws_rds_instances_us_east_1_page1", "aws_rds_instances_us_east_1_page2"],
        region=REGION_A,
    )
    # Target groups/health are queried once per load balancer, in fixture order: the ALB has
    # a registered target, the NLB has none (the idle-LB shape).
    aws_stub.sequence(
        "elbv2:DescribeTargetGroups",
        ["aws_elbv2_target_groups_alb", "aws_elbv2_target_groups_nlb"],
        region=REGION_A,
    )
    aws_stub.sequence(
        "elbv2:DescribeTargetHealth",
        ["aws_elbv2_target_health_alb", "aws_elbv2_target_health_empty"],
        region=REGION_A,
    )

    for region, routes in AWS_REGION_ROUTES.items():
        aws_stub.route_fixtures(routes, region=region)
        for key in AWS_INVENTORY_OPS:
            if key not in routes and (region, key) not in AWS_SEQUENCED:
                aws_stub.empty(key, region=region)
    return aws_stub
