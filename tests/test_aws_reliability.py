from __future__ import annotations

import base64
import copy
import importlib.util
import io
import json
import re
import types
from pathlib import Path

import boto3
import pytest
import yaml
from botocore.exceptions import ClientError
from botocore.stub import Stubber
from competition_cloud.client import SignedTransport, check_packets, prepare, upload
from competition_cloud.protocol import (
    ARTIFACTS,
    MAX_BODY,
    acknowledgement,
    digest,
    encode,
    object_key,
)
from competition_cloud.storage import ingest

ROOT = Path(__file__).parents[1]


@pytest.fixture(autouse=True)
def no_aws_network(monkeypatch):
    import socket

    import botocore.endpoint

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Network calls forbidden in mocked AWS tests")

    monkeypatch.setattr(botocore.endpoint.Endpoint, "_send", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")


class Services:
    """Deterministic fake services with before/after-write failure injection."""

    def __init__(self, *, validate_expressions=True):
        self.objects = {}
        self.items = {}
        self.fail = None
        self.calls = []
        self.validate_expressions = validate_expressions
        self.meta = types.SimpleNamespace(
            client=types.SimpleNamespace(
                exceptions=types.SimpleNamespace(
                    ConditionalCheckFailedException=ClientError
                )
            )
        )

    def trip(self, point):
        self.calls.append(point)
        if self.fail == point:
            self.fail = None
            raise TimeoutError(point)

    def put_object(self, **kwargs):
        self.trip("s3_before_put")
        key = kwargs["Key"]
        if key in self.objects and kwargs.get("IfNoneMatch") == "*":
            raise ClientError({"Error": {"Code": "PreconditionFailed"}}, "PutObject")
        self.objects[key] = kwargs["Body"]
        self.trip("s3_after_put")

    def get_object(self, **kwargs):
        self.trip("s3_get")
        return {"Body": io.BytesIO(self.objects[kwargs["Key"]])}

    def put_item(self, **kwargs):
        # Case-specific DynamoDB service rule, not a full expression emulator.
        # SDK Stubber alone accepts arbitrary expression strings and missed this.
        names = kwargs.get("ExpressionAttributeNames", {})
        for reference in re.findall(
            r"attribute_not_exists\(([^)]+)\)", kwargs["ConditionExpression"]
        ):
            if self.validate_expressions and reference.upper() == "SEQUENCE":
                raise ClientError(
                    {
                        "Error": {
                            "Code": "ValidationException",
                            "Message": "Invalid ConditionExpression: Attribute name is a reserved keyword; reserved keyword: Sequence",
                        }
                    },
                    "PutItem",
                )
            if reference.startswith("#"):
                assert reference in names
        self.trip("ddb_before_put")
        item = kwargs["Item"]
        identity = (item["TraceId"], item["Sequence"])
        if identity in self.items:
            raise ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException"}}, "PutItem"
            )
        self.items[identity] = copy.deepcopy(item)
        self.trip("ddb_after_put")

    def get_item(self, **kwargs):
        self.trip("ddb_get")
        assert kwargs["ConsistentRead"] is True
        key = kwargs["Key"]
        return {"Item": self.items[(key["TraceId"], key["Sequence"])]}


def event(packet):
    return {
        "requestContext": {"http": {"method": "POST"}},
        "body": encode(packet).decode(),
    }


def packet():
    raw = b"real bytes in a mock packet"
    return {
        "protocol": "aegis-evidence-v1",
        "trace_id": "a" * 64,
        "sequence": 0,
        "artifact": "trace.jsonl",
        "part_index": 0,
        "part_count": 1,
        "file_sha256": digest(raw),
        "data_sha256": digest(raw),
        "data": base64.b64encode(raw).decode(),
    }


def send_to(services):
    def send(body):
        result = ingest(
            {"requestContext": {"http": {"method": "POST"}}, "body": body.decode()},
            services,
            services,
            "mock-bucket",
            now=lambda: 0,
        )
        return result["statusCode"], result["body"].encode()

    return send


@pytest.fixture
def packets(tmp_path):
    for name in ARTIFACTS:
        (tmp_path / name).write_bytes(name.encode())
    hashes = {
        name: digest((tmp_path / name).read_bytes())
        for name in ARTIFACTS
        if name != "provenance.json"
    }
    (tmp_path / "provenance.json").write_text(
        json.dumps(
            {"status": "PASS", "sha256": hashes, "core_commit": "test_fixture_only"}
        )
    )
    return prepare(tmp_path)[1]


@pytest.mark.parametrize(
    "point",
    [
        "s3_before_put",
        "s3_after_put",
        "s3_get",
        "ddb_before_put",
        "ddb_after_put",
        "ddb_get",
    ],
)
def test_partial_failure_is_not_success_and_retry_repairs(point):
    services = Services()
    services.fail = point
    first = ingest(event(packet()), services, services, "mock-bucket")
    assert first["statusCode"] == 503
    assert "stored_verified" not in first["body"]
    second = ingest(event(packet()), services, services, "mock-bucket")
    assert json.loads(second["body"]) == acknowledgement(packet())
    assert len(services.items) == len(services.objects) == 1


def test_duplicate_requires_rechecking_object_and_index():
    services = Services()
    for _ in range(2):
        assert (
            ingest(event(packet()), services, services, "bucket")["statusCode"] == 200
        )
    assert services.calls.count("s3_get") == services.calls.count("ddb_get") == 2
    assert len(services.objects) == len(services.items) == 1


def test_first_packet_condition_accepts_reserved_sort_key_name():
    services = Services()
    result = ingest(event(packet()), services, services, "mock-bucket")
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == acknowledgement(packet())
    assert len(services.objects) == len(services.items) == 1


@pytest.mark.parametrize(
    ("method", "service", "operation", "code"),
    [
        ("put_object", "s3", "PutObject", "AccessDenied"),
        ("get_object", "s3", "GetObject", "AccessDenied"),
        ("put_item", "dynamodb", "PutItem", "ValidationException"),
        ("get_item", "dynamodb", "GetItem", "AccessDeniedException"),
    ],
)
def test_storage_diagnostics_identify_operation_without_private_messages(
    monkeypatch, caplog, method, service, operation, code
):
    services = Services()
    private_message = "private-resource-identifier must never appear in logs"

    def fail(**_kwargs):
        raise ClientError(
            {"Error": {"Code": code, "Message": private_message}}, operation
        )

    monkeypatch.setattr(services, method, fail)
    result = ingest(event(packet()), services, services, "mock-bucket")
    assert result["statusCode"] == 503
    assert json.loads(result["body"]) == {"error": "storage_unverified"}
    assert f"service={service} operation={operation} code={code}" in caplog.text
    assert private_message not in caplog.text


def test_storage_diagnostics_redact_malformed_error_code(monkeypatch, caplog):
    services = Services()

    def fail(**_kwargs):
        raise ClientError(
            {"Error": {"Code": "secret/resource\ninjected", "Message": "private"}},
            "PutObject",
        )

    monkeypatch.setattr(services, "put_object", fail)
    assert (
        ingest(event(packet()), services, services, "mock-bucket")["statusCode"] == 503
    )
    assert "code=redacted" in caplog.text
    assert "secret/resource" not in caplog.text
    assert "injected" not in caplog.text


@pytest.mark.parametrize("corruption", ["object", "index", "missing_object"])
def test_inconsistent_storage_never_silently_passes(corruption):
    services = Services()
    ingest(event(packet()), services, services, "bucket")
    if corruption == "object":
        services.objects[object_key(packet())] = b"corrupt"
    elif corruption == "index":
        services.items[("a" * 64, 0)]["PayloadSHA256"] = "wrong"
    else:
        services.objects.clear()
    result = ingest(event(packet()), services, services, "bucket")
    assert result["statusCode"] == (200 if corruption == "missing_object" else 409)
    if corruption == "missing_object":
        assert services.objects[object_key(packet())] == encode(packet())


def test_same_identity_different_payload_is_conflict():
    services = Services()
    ingest(event(packet()), services, services, "bucket")
    changed = packet()
    changed["artifact"] = "summary.json"
    assert ingest(event(changed), services, services, "bucket")["statusCode"] == 409
    assert services.objects[object_key(packet())] == encode(packet())


@pytest.mark.parametrize(
    "change",
    [
        {"sequence": True},
        {"sequence": -1},
        {"trace_id": "../escape"},
        {"data": "!!!"},
        {"data_sha256": "b" * 64},
        {"part_count": 0},
        {"artifact": "credentials"},
        {"protocol": "wrong"},
        {"extra": 1},
    ],
)
def test_invalid_packet_is_rejected_before_storage(change):
    services = Services()
    malformed = {**packet(), **change}
    assert ingest(event(malformed), services, services, "bucket")["statusCode"] == 400
    assert not services.calls


@pytest.mark.parametrize("body", ["[]", "null", "{bad", "1"])
def test_invalid_json_or_shape(body):
    services = Services()
    request = event(packet())
    request["body"] = body
    assert ingest(request, services, services, "bucket")["statusCode"] == 400


def test_request_size_method_and_gateway_base64():
    services = Services()
    request = event(packet())
    request["body"] = "x" * (MAX_BODY + 1)
    assert ingest(request, services, services, "bucket")["statusCode"] == 413
    assert ingest({}, services, services, "bucket")["statusCode"] == 405
    request = event(packet())
    request["body"] = base64.b64encode(request["body"].encode()).decode()
    request["isBase64Encoded"] = True
    assert ingest(request, services, services, "bucket")["statusCode"] == 200


@pytest.mark.parametrize("status", [400, 401, 403, 404, 409, 413])
def test_terminal_http_failure_is_never_success_and_not_retried(packets, status):
    result = upload(packets, lambda _body: (status, b"{}"), sleep=lambda _: None)
    assert result["status"] == "incomplete" and not result["acknowledged"]
    assert len(result["attempts"]) == 1


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_server_failure_retries_are_bounded(packets, status):
    waits = []
    result = upload(packets, lambda _body: (status, b"{}"), sleep=waits.append)
    assert result["status"] == "incomplete" and len(result["attempts"]) == 3
    assert waits == [0.25, 0.5]


@pytest.mark.parametrize("body", [b"", b"{}", b"not json", b"null", b"x" * 65537])
def test_2xx_missing_or_invalid_acknowledgement_never_succeeds(packets, body):
    result = upload(packets, lambda _body: (200, body), sleep=lambda _: None)
    assert result["status"] == "incomplete" and len(result["attempts"]) == 3


def test_acknowledgement_for_wrong_packet_never_succeeds(packets):
    wrong = acknowledgement(packets[0])
    wrong["payload_sha256"] = "0" * 64
    result = upload(packets, lambda _: (200, encode(wrong)), sleep=lambda _: None)
    assert result["status"] == "incomplete"


def test_lost_ack_after_commit_is_idempotently_recoverable(packets):
    services = Services()
    send = send_to(services)
    first = True

    def lost_ack(body):
        nonlocal first
        result = send(body)
        if first:
            first = False
            raise TimeoutError("committed but response lost")
        return result

    result = upload(packets, lost_ack, sleep=lambda _: None)
    assert result["status"] == "stored_verified" and result["mode"] == "mock"
    assert len(result["attempts"]) == len(packets) + 1
    assert len(services.items) == len(services.objects) == len(packets)


def test_partial_bundle_is_not_reported_complete(packets):
    services = Services()
    send = send_to(services)

    def partial(body):
        if json.loads(body)["sequence"] == 2:
            raise ConnectionError("offline")
        return send(body)

    result = upload(packets, partial, sleep=lambda _: None)
    assert result["status"] == "incomplete" and len(result["acknowledged"]) == 2
    assert len(result["attempts"]) == 5
    assert upload(packets, send, sleep=lambda _: None)["status"] == "stored_verified"


@pytest.mark.parametrize("attempts", [0, 4])
def test_invalid_retry_budget_rejected(packets, attempts):
    with pytest.raises(ValueError, match="Attempts"):
        upload(packets, lambda _: None, attempts=attempts)


def test_packets_must_reconstruct_all_files(packets):
    with pytest.raises(ValueError):
        check_packets(packets[:-1])
    damaged = copy.deepcopy(packets)
    damaged[2]["file_sha256"] = "f" * 64
    with pytest.raises(ValueError):
        check_packets(damaged)


@pytest.mark.parametrize(
    "scenario", ["nominal", "low_battery_intrusion", "gps_loss_low_light"]
)
def test_real_a1_artifacts_reconstruct_and_upload_to_mock_only(scenario):
    directory = ROOT / "evidence/a1/final" / scenario
    before = {
        p.name: digest(p.read_bytes()) for p in directory.iterdir() if p.is_file()
    }
    plan, packets = prepare(directory)
    assert prepare(directory) == (plan, packets)
    services = Services()
    result = upload(packets, send_to(services), sleep=lambda _: None)
    assert result["status"] == "stored_verified" and result["mode"] == "mock"
    for name in ARTIFACTS:
        parts = [
            json.loads(raw)
            for raw in services.objects.values()
            if json.loads(raw)["artifact"] == name
        ]
        reconstructed = b"".join(
            base64.b64decode(p["data"])
            for p in sorted(parts, key=lambda p: p["part_index"])
        )
        assert reconstructed == (directory / name).read_bytes()
    assert before == {
        p.name: digest(p.read_bytes()) for p in directory.iterdir() if p.is_file()
    }


def test_sdk_stubber_checks_real_s3_contract_and_failed_get():
    s3 = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id="mock",
        aws_secret_access_key="mock",
    )
    services = Services()
    with Stubber(s3) as stub:
        stub.add_response(
            "put_object",
            {},
            {
                "Bucket": "mock-bucket",
                "Key": object_key(packet()),
                "Body": encode(packet()),
                "ContentType": "application/json",
                "ServerSideEncryption": "AES256",
                "IfNoneMatch": "*",
            },
        )
        stub.add_client_error(
            "get_object", service_error_code="AccessDenied", http_status_code=403
        )
        assert ingest(event(packet()), s3, services, "mock-bucket")["statusCode"] == 503
        stub.assert_no_pending_responses()
    assert not services.items


def test_sdk_stubber_verifies_complete_s3_and_dynamodb_contract():
    session = boto3.Session(
        aws_access_key_id="mock", aws_secret_access_key="mock", region_name="us-east-1"
    )
    s3 = session.client("s3")
    table = session.resource("dynamodb").Table("mock-table")
    identity = {"TraceId": packet()["trace_id"], "Sequence": 0}
    item = {
        **identity,
        "PayloadSHA256": digest(encode(packet())),
        "ObjectKey": object_key(packet()),
        "Complete": True,
        "ExpiresAt": 2592000,
    }
    typed = {
        "TraceId": {"S": identity["TraceId"]},
        "Sequence": {"N": "0"},
        "PayloadSHA256": {"S": item["PayloadSHA256"]},
        "ObjectKey": {"S": item["ObjectKey"]},
        "Complete": {"BOOL": True},
        "ExpiresAt": {"N": "2592000"},
    }
    with Stubber(s3) as s3_stub, Stubber(table.meta.client) as ddb_stub:
        s3_stub.add_response("put_object", {})
        s3_stub.add_response(
            "get_object",
            {"Body": io.BytesIO(encode(packet()))},
            {"Bucket": "mock-bucket", "Key": object_key(packet())},
        )
        ddb_stub.add_response(
            "put_item",
            {},
            {
                "TableName": "mock-table",
                "Item": item,
                "ConditionExpression": "attribute_not_exists(#trace_id) AND attribute_not_exists(#sequence)",
                "ExpressionAttributeNames": {
                    "#trace_id": "TraceId",
                    "#sequence": "Sequence",
                },
            },
        )
        ddb_stub.add_response(
            "get_item",
            {"Item": typed},
            {"TableName": "mock-table", "Key": identity, "ConsistentRead": True},
        )
        result = ingest(event(packet()), s3, table, "mock-bucket", now=lambda: 0)
        assert result["statusCode"] == 200
        assert json.loads(result["body"]) == acknowledgement(packet())
        s3_stub.assert_no_pending_responses()
        ddb_stub.assert_no_pending_responses()


@pytest.mark.parametrize("failure", ["connect", "read"])
def test_signed_transport_has_timeout_signs_and_surfaces_connection_failure(
    monkeypatch, failure
):
    import botocore.httpsession
    from botocore.credentials import Credentials
    from botocore.exceptions import ConnectTimeoutError, ReadTimeoutError

    captured = {}

    class HTTP:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def send(self, request):
            assert "Authorization" in request.headers
            assert request.url.endswith("/v1/evidence")
            error = ConnectTimeoutError if failure == "connect" else ReadTimeoutError
            raise error(endpoint_url="mock")

    monkeypatch.setattr(
        boto3,
        "Session",
        lambda **_: types.SimpleNamespace(
            get_credentials=lambda: Credentials("mock", "mock")
        ),
    )
    monkeypatch.setattr(botocore.httpsession, "URLLib3Session", HTTP)
    transport = SignedTransport(
        "https://abc.execute-api.us-east-1.amazonaws.com/v1", "us-east-1"
    )
    with pytest.raises(ConnectionError, match="unacknowledged"):
        transport(encode(packet()))
    assert captured["timeout"] == 27


def test_lambda_clients_disable_sdk_retries_and_have_explicit_timeouts(monkeypatch):
    import app

    services = Services()
    configs = []

    def client(_name, **kwargs):
        configs.append(kwargs["config"])
        return services

    def resource(_name, **kwargs):
        configs.append(kwargs["config"])
        return types.SimpleNamespace(Table=lambda _: services)

    monkeypatch.setattr(boto3, "client", client)
    monkeypatch.setattr(boto3, "resource", resource)
    monkeypatch.setenv("TRACE_TABLE", "mock-table")
    monkeypatch.setenv("EVIDENCE_BUCKET", "mock-bucket")
    assert app.handler(event(packet()), None)["statusCode"] == 200
    assert len(configs) == 2
    assert all(
        c.connect_timeout == 1
        and c.read_timeout == 2
        and c.retries["total_max_attempts"] == 1
        for c in configs
    )


def test_local_plan_never_constructs_transport_or_claims_upload(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location(
        "evidence_cli", ROOT / "scripts/evidence_cloud.py"
    )
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)

    def forbidden(*_args):
        raise AssertionError("Local planning must never create an AWS transport")

    monkeypatch.setattr(cli, "SignedTransport", forbidden)
    monkeypatch.setattr(
        cli.sys,
        "argv",
        [
            "evidence_cloud",
            "--evidence",
            str(ROOT / "evidence/a1/final/nominal"),
            "--output",
            str(tmp_path / "plan"),
        ],
    )
    assert cli.main() == 0
    assert (
        json.loads((tmp_path / "plan/plan.json").read_bytes())["mode"]
        == "local_plan_only"
    )
    assert not (tmp_path / "plan/receipts.json").exists()


def test_tampered_artifact_is_rejected_before_preparing(tmp_path):
    import shutil

    shutil.copytree(ROOT / "evidence/a1/final/nominal", tmp_path / "run")
    (tmp_path / "run/summary.json").write_text("tampered")
    with pytest.raises(ValueError, match="checksum mismatch"):
        prepare(tmp_path / "run")


def test_original_core_ignores_http_rejection(monkeypatch, tmp_path):
    import botocore.httpsession
    from botocore.credentials import Credentials

    monkeypatch.syspath_prepend(str(ROOT / ".baseline/core/src"))
    from aegisland.domain import jsonable
    from aegisland.trace import CloudTraceStore, JsonlTraceStore

    assert jsonable({"trace_id": "mock"}) == {"trace_id": "mock"}
    monkeypatch.setattr(
        boto3,
        "Session",
        lambda: types.SimpleNamespace(
            get_credentials=lambda: Credentials("mock", "mock")
        ),
    )
    monkeypatch.setattr(
        botocore.httpsession,
        "URLLib3Session",
        lambda: types.SimpleNamespace(
            send=lambda _: types.SimpleNamespace(status_code=403)
        ),
    )
    path = tmp_path / "trace.jsonl"
    store = CloudTraceStore(JsonlTraceStore(path), endpoint="https://mock.invalid")
    store.write({"trace_id": "mock"})
    assert path.exists()
    assert not path.with_suffix(".cloud-errors.log").exists()


def test_original_core_partial_upload_bug_is_reproduced(monkeypatch):
    # Isolate the legacy write-order defect from its separate expression defect.
    # The core implementation is historical, pinned and intentionally unchanged.
    services = Services(validate_expressions=False)
    monkeypatch.setenv("TRACE_TABLE", "mock-table")
    monkeypatch.setenv("EVIDENCE_BUCKET", "mock-bucket")
    fake = types.SimpleNamespace(
        resource=lambda _: types.SimpleNamespace(Table=lambda _: services),
        client=lambda _: services,
    )
    monkeypatch.setitem(__import__("sys").modules, "boto3", fake)
    spec = importlib.util.spec_from_file_location(
        "original_backend", ROOT / ".baseline/core/infra/trace_api/app.py"
    )
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    request = {
        "requestContext": {"http": {"method": "POST"}},
        "body": json.dumps({"trace_id": "abc", "sequence": 0}),
    }
    services.fail = "s3_before_put"
    with pytest.raises(TimeoutError):
        original.handler(request, None)
    result = original.handler(request, None)
    assert result["statusCode"] == 200
    assert json.loads(result["body"])["status"] == "duplicate_ignored"
    assert not services.objects


def test_sam_security_and_packaging_contract():
    class Loader(yaml.SafeLoader):
        pass

    Loader.add_multi_constructor(
        "!", lambda loader, tag, node: {tag: loader.construct_scalar(node)}
    )
    template = yaml.load((ROOT / "infra/template.yaml").read_text(), Loader=Loader)
    resources = template["Resources"]
    assert (
        resources["EvidenceApi"]["Properties"]["Auth"]["DefaultAuthorizer"] == "AWS_IAM"
    )
    assert resources["EvidenceApi"]["Properties"]["Auth"]["EnableIamAuthorizer"] is True
    function = resources["EvidenceFunction"]["Properties"]
    assert function["CodeUri"] == "../cloud/" and function["Handler"] == "app.handler"
    assert function["ReservedConcurrentExecutions"] == 2 and function["Timeout"] == 25
    policy = resources["EvidenceRole"]["Properties"]["Policies"][0]["PolicyDocument"]
    actions = {
        action for statement in policy["Statement"] for action in statement["Action"]
    }
    assert not actions.intersection(
        {"s3:DeleteObject", "dynamodb:DeleteItem", "s3:*", "dynamodb:*"}
    )
