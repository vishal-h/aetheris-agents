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

#: Every service the adapter talks to.
SERVICES = ("ec2", "elb", "elbv2", "rds", "ce", "sts")
MODELS = {service: _SESSION.get_service_model(service) for service in SERVICES}

#: form `Version=` -> service key. This is what disambiguates `elb` (2012-06-01) from
#: `elbv2` (2015-12-01): they share the action name `DescribeLoadBalancers`, the signing
#: name `elasticloadbalancing`, and even the result wrapper, so the API version is the only
#: field in the request that tells them apart.
SERVICE_BY_VERSION = {model.api_version: service for service, model in MODELS.items()}

#: `X-Amz-Target` prefix -> service key (Cost Explorer is the only json-protocol service).
SERVICE_BY_TARGET_PREFIX = {
    model.metadata["targetPrefix"]: service
    for service, model in MODELS.items()
    if model.metadata.get("targetPrefix")
}


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


def encode(service: str, action: str, payload: dict, request_id: str = "req-fixture-1"):
    """(body_bytes, content_type) for a successful response to `action` on `service`."""
    model = MODELS[service]
    if model.protocol == "json":
        return json.dumps(_public(payload)).encode(), "application/x-amz-json-1.1"

    output = model.operation_model(action).output_shape
    # ec2's query dialect names list items `item`; the plain query protocol names them
    # `member`. Either way an explicit member serialization name (rds: `DBInstance`) wins.
    item_tag = "item" if model.protocol == "ec2" else "member"

    root = Element(f"{action}Response")
    wrapper = output.serialization.get("resultWrapper")
    target = SubElement(root, wrapper) if wrapper else root
    for key, value in _public(payload).items():
        member = output.members[key]
        _emit(target, _member_key_name(member, key), member, value, item_tag)

    if model.protocol == "ec2":
        SubElement(root, "requestId").text = request_id
    else:
        SubElement(SubElement(root, "ResponseMetadata"), "RequestId").text = request_id
    return tostring(root, encoding="utf-8"), "text/xml"


def encode_error(service: str, code: str, message: str = "stubbed failure"):
    """(body_bytes, content_type) for an error response botocore will raise correctly."""
    model = MODELS.get(service) or MODELS["sts"]
    if model.protocol == "json":
        body = json.dumps({"__type": code, "message": message})
        return body.encode(), "application/x-amz-json-1.1"
    if model.protocol == "ec2":
        body = (
            f"<Response><Errors><Error><Code>{code}</Code>"
            f"<Message>{message}</Message></Error></Errors>"
            f"<RequestID>req-error-1</RequestID></Response>"
        )
        return body.encode(), "text/xml"
    body = (
        f"<ErrorResponse><Error><Type>Sender</Type><Code>{code}</Code>"
        f"<Message>{message}</Message></Error>"
        f"<RequestId>req-error-1</RequestId></ErrorResponse>"
    )
    return body.encode(), "text/xml"
