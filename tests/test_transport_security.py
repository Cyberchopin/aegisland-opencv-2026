"""Offline client boundaries; simulated denials do not validate AWS IAM itself."""

import datetime
import json
import types
from pathlib import Path

import boto3
import botocore.auth
import botocore.endpoint
import botocore.httpsession
import pytest
from botocore.credentials import Credentials
from competition_cloud.client import SignedTransport, prepare, upload
from competition_cloud.protocol import acknowledgement, encode

ROOT = Path(__file__).parents[1]


@pytest.fixture(autouse=True)
def no_aws(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Live AWS is forbidden")

    monkeypatch.setattr(botocore.endpoint.Endpoint, "_send", forbidden)
    monkeypatch.setattr(
        boto3,
        "Session",
        lambda **_: types.SimpleNamespace(
            get_credentials=lambda: Credentials("offline-key", "offline-secret")
        ),
    )


@pytest.mark.parametrize("reason", ["invalid_signature", "expired_timestamp"])
def test_signed_authentication_denial_stops_without_retry(monkeypatch, reason):
    sent = []
    date = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
    if reason == "expired_timestamp":
        monkeypatch.setattr(botocore.auth, "get_current_datetime", lambda: date)

    class HTTP:
        def __init__(self, **_kwargs):
            pass

        def send(self, request):
            assert request.headers["Authorization"].startswith("AWS4-HMAC-SHA256")
            if reason == "expired_timestamp":
                assert request.headers["X-Amz-Date"] == "20000101T000000Z"
            sent.append(request)
            return types.SimpleNamespace(
                status_code=403, content=encode({"message": reason})
            )

    monkeypatch.setattr(botocore.httpsession, "URLLib3Session", HTTP)
    _, packets = prepare(ROOT / "evidence/a1/final/nominal")
    transport = SignedTransport(
        "https://offline.execute-api.us-east-1.amazonaws.com/v1", "us-east-1"
    )
    result = upload(packets, transport, attempts=1, sleep=lambda _: None)
    assert result["status"] == "incomplete"
    assert result["acknowledged"] == []
    assert len(sent) == len(result["attempts"]) == 1


def test_transport_signatures_change_when_payload_changes(monkeypatch):
    signatures = []
    frozen = datetime.datetime(2026, 10, 23, tzinfo=datetime.timezone.utc)
    monkeypatch.setattr(botocore.auth, "get_current_datetime", lambda: frozen)

    class HTTP:
        def __init__(self, **_kwargs):
            pass

        def send(self, request):
            signatures.append(request.headers["Authorization"])
            assert "/us-east-1/execute-api/aws4_request" in signatures[-1]
            assert "Signature=" in signatures[-1]
            return types.SimpleNamespace(
                status_code=200,
                content=encode(acknowledgement(json.loads(request.body))),
            )

    monkeypatch.setattr(botocore.httpsession, "URLLib3Session", HTTP)
    _, packets = prepare(ROOT / "evidence/a1/final/nominal")
    transport = SignedTransport(
        "https://offline.execute-api.us-east-1.amazonaws.com/v1", "us-east-1"
    )
    transport(encode(packets[0]))
    transport(encode(packets[1]))
    assert len(signatures) == 2
    assert signatures[0] != signatures[1]


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://offline.execute-api.us-east-1.amazonaws.com/v1",
        "https://offline.execute-api.us-east-1.amazonaws.com/v1/other",
        "https://offline.execute-api.us-west-2.amazonaws.com/v1",
        "https://offline.execute-api.us-east-1.amazonaws.com.attacker.invalid/v1",
    ],
)
def test_transport_rejects_wrong_region_and_nonreviewed_destinations(endpoint):
    with pytest.raises(ValueError, match="regional AWS"):
        SignedTransport(endpoint, "us-east-1")
