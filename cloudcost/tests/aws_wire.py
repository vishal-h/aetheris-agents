"""Parsed-fixture -> AWS wire-format encoder, driven by botocore's own service models.

Fixtures are stored as *parsed* response dicts — what boto3 hands the adapter — because that
is what a reviewer can audit and what the normalizer unit tests read directly (mirroring
`load_fixture("do_volumes")["volumes"]`). `AWSStub` must answer in wire format, so this
module re-serializes them using the same shape metadata botocore's parser reads back.

It is model-driven, not hand-written: every element name, item tag and result wrapper comes
from `botocore.session.get_session().get_service_model(...)`, never from a table typed out
here. `test_every_fixture_round_trips_through_botocore` pins it — each fixture is encoded,
handed to the *real* botocore parser, and compared to the fixture. If this encoder is wrong,
that test is red before any adapter test is, so a green adapter test cannot be an artifact of
a lenient encoder.

Keys beginning with `_` are fixture prose (`_comment`) and are skipped, so documenting a
fixture cannot corrupt the wire body.
"""

from __future__ import annotations

import json
from xml.etree.ElementTree import Element, SubElement, tostring

import botocore.session

_SESSION = botocore.session.get_session()

#: Every service the adapters talk to. The first six are the core sweep (m2 t1); the last four
#: are the t4 optimization spike. Nothing here is protocol-specific — `_protocol()` asks
#: botocore what each one resolves to.
SERVICES = (
    "ec2",
    "elb",
    "elbv2",
    "rds",
    "ce",
    "sts",
    "s3",
    "ecr",
    "secretsmanager",
    "cloudwatch",
)
MODELS = {service: _SESSION.get_service_model(service) for service in SERVICES}

#: form `Version=` -> service key. This is what disambiguates `elb` (2012-06-01) from
#: `elbv2` (2015-12-01): they share the action name `DescribeLoadBalancers`, the signing
#: name `elasticloadbalancing`, and even the result wrapper, so the API version is the only
#: field in the request that tells them apart.
SERVICE_BY_VERSION = {model.api_version: service for service, model in MODELS.items()}

#: `X-Amz-Target` prefix -> service key, for every service botocore resolves to the json
#: protocol: Cost Explorer, ECR, Secrets Manager and CloudWatch.
SERVICE_BY_TARGET_PREFIX = {
    model.metadata["targetPrefix"]: service
    for service, model in MODELS.items()
    if model.metadata.get("targetPrefix")
}

# Both routing tables are dicts keyed off service metadata, so a collision would not raise —
# it would silently drop a service and route its calls to whichever one won. Adding a service
# is exactly when that could happen, so it is asserted at import rather than discovered as a
# baffling `NotStubbed` later.
assert len(SERVICE_BY_VERSION) == len(SERVICES), "two services share an api_version"
assert len(SERVICE_BY_TARGET_PREFIX) == sum(
    1 for model in MODELS.values() if model.metadata.get("targetPrefix")
), "two services share an X-Amz-Target prefix"


def _protocol(model) -> str:
    """The protocol botocore will actually *parse with* — not the one it advertises.

    `ServiceModel.protocol` returns `metadata["protocol"]`, the service's preferred wire
    format. `resolved_protocol` returns the first entry of `metadata["protocols"]` that this
    botocore supports, and that is the one the serializer and the parser are built from. For
    every service here but one the two agree. CloudWatch advertises `smithy-rpc-v2-cbor` and
    resolves to `json` — encoding to what it *advertises* would produce a body the real parser
    never asked for. Read what botocore resolved, never a table typed out here.
    """
    return getattr(model, "resolved_protocol", None) or model.protocol


def _public(payload: dict) -> dict:
    return {key: value for key, value in payload.items() if not key.startswith("_")}


def _member_key_name(shape, member_name: str) -> str:
    """The element name botocore's XML parser will look for.

    Mirrors `botocore.parsers.BaseXMLResponseParser._member_key_name`: a *flattened* list is
    named by its member's serialization name, everything else by its own.
    """
    if shape.type_name == "list" and shape.serialization.get("flattened"):
        name = shape.member.serialization.get("name")
        if name is not None:
            return name
    return shape.serialization.get("name") or member_name


def _scalar_text(shape, value) -> str:
    if shape.type_name == "boolean":
        return "true" if value else "false"
    return str(value)


def _emit(parent, tag: str, shape, value, item_tag: str) -> None:
    if value is None:
        # An absent value is an absent element — that is what "not returned" looks like on
        # the wire, and it is how the fixtures express an optional field being unset.
        return
    if shape.type_name == "structure":
        node = SubElement(parent, tag)
        for key, sub in _public(value).items():
            member = shape.members[key]
            _emit(node, _member_key_name(member, key), member, sub, item_tag)
    elif shape.type_name == "list":
        member_tag = shape.member.serialization.get("name") or item_tag
        if shape.serialization.get("flattened"):
            for item in value:
                _emit(parent, tag, shape.member, item, item_tag)
        else:
            node = SubElement(parent, tag)
            for item in value:
                _emit(node, member_tag, shape.member, item, item_tag)
    elif shape.type_name == "map":
        node = SubElement(parent, tag)
        for key, sub in value.items():
            entry = SubElement(node, "entry")
            SubElement(entry, shape.key.serialization.get("name") or "key").text = str(key)
            _emit(
                entry,
                shape.value.serialization.get("name") or "value",
                shape.value,
                sub,
                item_tag,
            )
    else:
        SubElement(parent, tag).text = _scalar_text(shape, value)


def _encode_rest_xml(model, action: str, payload: dict) -> bytes:
    """A rest-xml body (S3).

    Two things differ from the query protocols. There is no `{Action}Response` envelope and no
    `resultWrapper`: botocore's rest-xml parser matches the *root element's children* against
    the output shape and never looks at the root's tag, so the tag below is documentation, not
    contract. And there is no `ResponseMetadata` element — for rest-xml that is assembled from
    the HTTP headers, not the body.

    `GetBucketLocation` is the one hand-written case in this module, and it has to be:
    botocore's own comment on it reads "s3.GetBucketLocation cannot be modeled properly", so it
    ships a response handler (`handlers.parse_get_bucket_location`) that re-parses the raw body
    and takes `root.text` as the region. A body built from the output shape would nest the value
    one level down and that handler would read `None`. An *empty* element is faithful too: that
    is exactly what the real API returns for us-east-1, whose location constraint is the empty
    string, and the caller is responsible for reading absent as us-east-1.
    """
    if action == "GetBucketLocation":
        root = Element("LocationConstraint")
        constraint = _public(payload).get("LocationConstraint")
        if constraint:
            root.text = str(constraint)
        return tostring(root, encoding="utf-8")

    output = model.operation_model(action).output_shape
    root = Element(f"{action}Result")
    for key, value in _public(payload).items():
        member = output.members[key]
        _emit(root, _member_key_name(member, key), member, value, "member")
    return tostring(root, encoding="utf-8")


def encode(service: str, action: str, payload: dict, request_id: str = "req-fixture-1"):
    """(body_bytes, content_type) for a successful response to `action` on `service`."""
    model = MODELS[service]
    protocol = _protocol(model)
    if protocol == "json":
        version = model.metadata.get("jsonVersion", "1.1")
        return json.dumps(_public(payload)).encode(), f"application/x-amz-json-{version}"
    if protocol == "rest-xml":
        return _encode_rest_xml(model, action, payload), "application/xml"

    output = model.operation_model(action).output_shape
    # ec2's query dialect names list items `item`; the plain query protocol names them
    # `member`. Either way an explicit member serialization name (rds: `DBInstance`) wins.
    item_tag = "item" if protocol == "ec2" else "member"

    root = Element(f"{action}Response")
    wrapper = output.serialization.get("resultWrapper")
    target = SubElement(root, wrapper) if wrapper else root
    for key, value in _public(payload).items():
        member = output.members[key]
        _emit(target, _member_key_name(member, key), member, value, item_tag)

    if protocol == "ec2":
        SubElement(root, "requestId").text = request_id
    else:
        SubElement(SubElement(root, "ResponseMetadata"), "RequestId").text = request_id
    return tostring(root, encoding="utf-8"), "text/xml"


def encode_error(service: str, code: str, message: str = "stubbed failure"):
    """(body_bytes, content_type) for an error response botocore will raise correctly."""
    model = MODELS.get(service) or MODELS["sts"]
    protocol = _protocol(model)
    if protocol == "json":
        body = json.dumps({"__type": code, "message": message})
        return body.encode(), "application/x-amz-json-1.1"
    if protocol == "ec2":
        body = (
            f"<Response><Errors><Error><Code>{code}</Code>"
            f"<Message>{message}</Message></Error></Errors>"
            f"<RequestID>req-error-1</RequestID></Response>"
        )
        return body.encode(), "text/xml"
    if protocol == "rest-xml":
        # S3 errors are a bare `<Error>` root — no `ErrorResponse` wrapper. The distinction is
        # load-bearing here rather than cosmetic: `NoSuchLifecycleConfiguration` IS the
        # no-lifecycle signal, so it has to reach the caller as a real `ClientError` carrying
        # that code, not as an unparsed body.
        body = (
            f"<Error><Code>{code}</Code><Message>{message}</Message>"
            f"<RequestId>req-error-1</RequestId></Error>"
        )
        return body.encode(), "application/xml"
    body = (
        f"<ErrorResponse><Error><Type>Sender</Type><Code>{code}</Code>"
        f"<Message>{message}</Message></Error>"
        f"<RequestId>req-error-1</RequestId></ErrorResponse>"
    )
    return body.encode(), "text/xml"
