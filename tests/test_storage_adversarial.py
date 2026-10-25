"""Deterministic storage interleavings; never a substitute for AWS auth tests."""

from __future__ import annotations

import base64
import copy
import io
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

import pytest
from botocore.exceptions import ClientError
from competition_cloud.client import check_packets, prepare, upload
from competition_cloud.protocol import acknowledgement, digest, encode, object_key
from competition_cloud.storage import ingest

ROOT = Path(__file__).parents[1]


@pytest.fixture(autouse=True)
def prohibit_network(monkeypatch):
    import socket

    import botocore.endpoint

    def forbidden(*_args, **_kwargs):
        raise AssertionError("No network in adversarial storage tests")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(botocore.endpoint.Endpoint, "_send", forbidden)
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")


def make_packet():
    raw = b"immutable adversarial fixture"
    return {
        "protocol": "aegis-evidence-v1",
        "trace_id": "b" * 64,
        "sequence": 0,
        "artifact": "trace.jsonl",
        "part_index": 0,
        "part_count": 1,
        "file_sha256": digest(raw),
        "data_sha256": digest(raw),
        "data": base64.b64encode(raw).decode(),
    }


def event(packet):
    return {
        "requestContext": {"http": {"method": "POST"}},
        "body": encode(packet).decode(),
    }


class AtomicServices:
    """Atomic create-if-absent state with explicitly controlled service failures."""

    def __init__(self, *, workers=0):
        self.lock = threading.Lock()
        self.objects = {}
        self.items = {}
        self.calls = []
        self.object_writes = 0
        self.item_writes = 0
        self.barrier = threading.Barrier(workers) if workers else None
        self.failure = None
        self.corrupt_index_field = None

    def fail(self, operation):
        if self.failure and self.failure[0] == operation:
            _, code, after = self.failure
            if not after:
                raise ClientError({"Error": {"Code": code}}, operation)

    def fail_after(self, operation):
        if self.failure and self.failure[0] == operation:
            _, code, after = self.failure
            if after:
                raise ClientError({"Error": {"Code": code}}, operation)

    def put_object(self, **kwargs):
        if self.barrier:
            self.barrier.wait(timeout=5)
        with self.lock:
            self.calls.append("PutObject")
            self.fail("PutObject")
            assert kwargs["IfNoneMatch"] == "*"
            if kwargs["Key"] in self.objects:
                raise ClientError(
                    {"Error": {"Code": "PreconditionFailed"}}, "PutObject"
                )
            self.objects[kwargs["Key"]] = kwargs["Body"]
            self.object_writes += 1
            self.fail_after("PutObject")

    def get_object(self, **kwargs):
        with self.lock:
            self.calls.append("GetObject")
            self.fail("GetObject")
            raw = self.objects[kwargs["Key"]]
            return {"Body": io.BytesIO(raw)}

    def put_item(self, **kwargs):
        with self.lock:
            self.calls.append("PutItem")
            self.fail("PutItem")
            item = kwargs["Item"]
            key = (item["TraceId"], item["Sequence"])
            if key in self.items:
                raise ClientError(
                    {"Error": {"Code": "ConditionalCheckFailedException"}}, "PutItem"
                )
            self.items[key] = copy.deepcopy(item)
            self.item_writes += 1
            self.fail_after("PutItem")

    def get_item(self, **kwargs):
        with self.lock:
            self.calls.append("GetItem")
            self.fail("GetItem")
            assert kwargs["ConsistentRead"] is True
            key = kwargs["Key"]
            item = copy.deepcopy(self.items.get((key["TraceId"], key["Sequence"]), {}))
            if self.corrupt_index_field:
                field, value = self.corrupt_index_field
                item[field] = value
            return {"Item": item}


def run_ingest(services, packet=None):
    return ingest(
        event(packet or make_packet()),
        services,
        services,
        "fixture-bucket",
        now=lambda: 10,
    )


def test_concurrent_identical_requests_ack_one_object_and_index():
    services = AtomicServices(workers=8)
    with ThreadPoolExecutor(max_workers=8) as workers:
        results = list(workers.map(lambda _: run_ingest(services), range(8)))
    assert all(r["statusCode"] == 200 for r in results)
    assert all(json.loads(r["body"]) == acknowledgement(make_packet()) for r in results)
    assert services.object_writes == services.item_writes == 1
    assert len(services.objects) == len(services.items) == 1


def test_concurrent_conflicting_packets_never_overwrite_winner():
    services = AtomicServices(workers=2)
    original = make_packet()
    conflicting = dict(original, artifact="summary.json")
    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(
            workers.map(lambda p: run_ingest(services, p), [original, conflicting])
        )
    assert sorted(r["statusCode"] for r in results) == [200, 409]
    winner = json.loads(services.objects[object_key(original)])
    accepted = next(r for r in results if r["statusCode"] == 200)
    assert json.loads(accepted["body"]) == acknowledgement(winner)
    assert services.object_writes == services.item_writes == 1
    indexed = services.items[(original["trace_id"], 0)]
    assert indexed["PayloadSHA256"] == digest(encode(winner))


@pytest.mark.parametrize(
    ("operation", "code", "after", "objects", "items"),
    [
        ("PutObject", "ConditionalRequestConflict", False, 0, 0),
        ("PutObject", "InternalError", True, 1, 0),
        ("GetObject", "AccessDenied", False, 1, 0),
        ("PutItem", "ValidationException", False, 1, 0),
        ("PutItem", "AccessDeniedException", False, 1, 0),
        ("PutItem", "ProvisionedThroughputExceededException", False, 1, 0),
        ("PutItem", "InternalServerError", True, 1, 1),
        ("GetItem", "AccessDeniedException", False, 1, 1),
    ],
)
def test_ambiguous_service_failures_never_ack_and_explicit_replay_repairs(
    operation, code, after, objects, items
):
    services = AtomicServices()
    services.failure = (operation, code, after)
    result = run_ingest(services)
    assert result["statusCode"] == 503
    assert json.loads(result["body"]) == {"error": "storage_unverified"}
    assert len(services.objects) == objects
    assert len(services.items) == items
    services.failure = None
    repaired = run_ingest(services)
    assert json.loads(repaired["body"]) == acknowledgement(make_packet())
    assert services.object_writes == services.item_writes == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("TraceId", "c" * 64),
        ("Sequence", 1),
        ("PayloadSHA256", "0" * 64),
        ("ObjectKey", "unrelated/key"),
        ("Complete", False),
        ("Complete", 1),
        ("Complete", Decimal(1)),
        ("Complete", 0),
    ],
)
def test_inconsistent_index_never_reports_verified(field, value):
    services = AtomicServices()
    services.corrupt_index_field = (field, value)
    result = run_ingest(services)
    assert result["statusCode"] == 409
    assert "stored_verified" not in result["body"]


@pytest.mark.parametrize("field", list(make_packet()))
def test_missing_protocol_fields_never_touch_storage(field):
    services = AtomicServices()
    malformed = make_packet()
    del malformed[field]
    assert run_ingest(services, malformed)["statusCode"] == 400
    assert services.calls == []


def test_gateway_invalid_base64_never_touches_storage():
    services = AtomicServices()
    request = event(make_packet())
    request.update(body="not*base64", isBase64Encoded=True)
    assert ingest(request, services, services, "fixture-bucket")["statusCode"] == 400
    assert services.calls == []


def test_deeply_nested_json_is_rejected_before_storage():
    services = AtomicServices()
    request = event(make_packet())
    request["body"] = "[" * 10000 + "0" + "]" * 10000
    assert ingest(request, services, services, "fixture-bucket")["statusCode"] == 400
    assert services.calls == []


def test_truncated_s3_body_never_creates_an_index(monkeypatch):
    services = AtomicServices()
    monkeypatch.setattr(
        services, "get_object", lambda **_: {"Body": io.BytesIO(b"truncated")}
    )
    result = run_ingest(services)
    assert result["statusCode"] == 409
    assert not services.items


@pytest.mark.parametrize(
    "mutation", ["duplicate_sequence", "cross_bundle", "wrong_file_hash"]
)
def test_malformed_complete_bundles_fail_before_transport(mutation):
    _, packets = prepare(ROOT / "evidence/a1/final/nominal")
    packets = copy.deepcopy(packets)
    if mutation == "duplicate_sequence":
        packets[1]["sequence"] = packets[0]["sequence"]
    elif mutation == "cross_bundle":
        packets[1]["trace_id"] = "0" * 64
    else:
        packets[1]["file_sha256"] = "0" * 64
    sent = []
    with pytest.raises(ValueError):
        upload(packets, lambda body: sent.append(body), attempts=1)
    assert not sent


def test_only_one_attempt_after_ambiguous_timeout_with_committed_packet():
    _, packets = prepare(ROOT / "evidence/a1/final/nominal")
    services = AtomicServices()
    sends = []

    def send(body):
        sends.append(body)
        result = run_ingest(services, json.loads(body))
        assert result["statusCode"] == 200
        raise TimeoutError("response lost after successful commit")

    result = upload(packets, send, attempts=1, sleep=lambda _: None)
    assert result["status"] == "incomplete"
    assert len(result["attempts"]) == len(sends) == 1
    assert result["acknowledged"] == []
    assert services.object_writes == services.item_writes == 1


def test_fixture_bundle_still_roundtrips_after_duplicate_validation():
    _, packets = prepare(ROOT / "evidence/a1/final/nominal")
    check_packets(packets)
    services = AtomicServices()

    def send(body):
        response = run_ingest(services, json.loads(body))
        return response["statusCode"], response["body"].encode()

    first = upload(packets, send, attempts=1, sleep=lambda _: None)
    replay = upload(packets, send, attempts=1, sleep=lambda _: None)
    assert first["status"] == replay["status"] == "stored_verified"
    assert first["acknowledged"] == replay["acknowledged"]
    check_packets([json.loads(services.objects[object_key(p)]) for p in packets])


@pytest.mark.parametrize("wrong_type", [False, 0.0])
def test_acknowledgement_sequence_type_must_match_protocol(wrong_type):
    _, packets = prepare(ROOT / "evidence/a1/final/nominal")
    sends = []

    def send(body):
        packet = json.loads(body)
        sends.append(packet["sequence"])
        ack = acknowledgement(packet)
        if packet["sequence"] == 0:
            ack["sequence"] = wrong_type
        return 200, encode(ack)

    result = upload(packets, send, attempts=1, sleep=lambda _: None)
    assert result["status"] == "incomplete"
    assert sends == [0]
    assert result["acknowledged"] == []
