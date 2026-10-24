"""Prepare immutable local evidence packets and require matching server ACKs."""

from __future__ import annotations

import base64
import json
import math
import time
from pathlib import Path

from .protocol import (
    ARTIFACTS,
    CHUNK_BYTES,
    MAX_PACKETS,
    PROTOCOL,
    acknowledgement,
    digest,
    encode,
    validate,
)

RETRYABLE = {429, 500, 502, 503, 504}


def prepare(directory: Path) -> tuple[dict, list[dict]]:
    blobs = {}
    for name in ARTIFACTS:
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Missing or symlinked artifact: {name}")
        if path.stat().st_size > 64 * 1024 * 1024:
            raise ValueError("Artifact exceeds 64 MiB bound")
        blobs[name] = path.read_bytes()
    if sum(map(len, blobs.values())) > 64 * 1024 * 1024:
        raise ValueError("Bundle exceeds 64 MiB bound")
    provenance = json.loads(blobs["provenance.json"])
    if provenance.get("status") != "PASS":
        raise ValueError("Only validated local runs can be prepared")
    for name in ARTIFACTS:
        if name != "provenance.json" and provenance["sha256"].get(name) != digest(
            blobs[name]
        ):
            raise ValueError(f"Local provenance checksum mismatch: {name}")
    inventory = {
        "protocol": PROTOCOL,
        "core_commit": provenance["core_commit"],
        "files": {
            name: {"sha256": digest(raw), "bytes": len(raw)}
            for name, raw in sorted(blobs.items())
        },
    }
    manifest = encode(inventory)
    bundle_id = digest(manifest)
    packets = []
    for name, raw in [("bundle.json", manifest), *sorted(blobs.items())]:
        parts = max(1, math.ceil(len(raw) / CHUNK_BYTES))
        for index in range(parts):
            chunk = raw[index * CHUNK_BYTES : (index + 1) * CHUNK_BYTES]
            packets.append(
                {
                    "protocol": PROTOCOL,
                    "trace_id": bundle_id,
                    "sequence": len(packets),
                    "artifact": name,
                    "part_index": index,
                    "part_count": parts,
                    "file_sha256": digest(raw),
                    "data_sha256": digest(chunk),
                    "data": base64.b64encode(chunk).decode(),
                }
            )
    if len(packets) > MAX_PACKETS:
        raise ValueError("Too many packets")
    return {
        "bundle_id": bundle_id,
        "inventory": inventory,
        "packet_count": len(packets),
        "mode": "local_plan_only",
    }, packets


def check_packets(packets: list[dict]) -> None:
    if not 1 <= len(packets) <= MAX_PACKETS:
        raise ValueError("Invalid packet count")
    for sequence, packet in enumerate(packets):
        validate(packet)
        if (
            packet["sequence"] != sequence
            or packet["trace_id"] != packets[0]["trace_id"]
        ):
            raise ValueError("Invalid packet ordering or bundle identity")
    files = {}
    for packet in packets:
        files.setdefault(packet["artifact"], []).append(packet)
    if set(files) != {*ARTIFACTS, "bundle.json"}:
        raise ValueError("Incomplete artifact set")
    restored = {}
    for name, parts in files.items():
        if [p["part_index"] for p in parts] != list(range(parts[0]["part_count"])):
            raise ValueError("Missing or duplicate artifact parts")
        raw = b"".join(validate(p) for p in parts)
        if any(
            p["part_count"] != len(parts) or p["file_sha256"] != digest(raw)
            for p in parts
        ):
            raise ValueError("File reconstruction checksum mismatch")
        restored[name] = raw
    if digest(restored["bundle.json"]) != packets[0]["trace_id"]:
        raise ValueError("Bundle identity checksum mismatch")
    inventory = json.loads(restored["bundle.json"])
    if inventory["files"] != {
        name: {"sha256": digest(restored[name]), "bytes": len(restored[name])}
        for name in ARTIFACTS
    }:
        raise ValueError("Inventory checksum mismatch")


def upload(
    packets: list[dict],
    send,
    *,
    attempts: int = 3,
    sleep=time.sleep,
    mode: str = "mock",
) -> dict:
    if type(attempts) is not int or not 1 <= attempts <= 3:
        raise ValueError("Attempts must be between one and three")
    check_packets(packets)
    result = {
        "mode": mode,
        "bundle_id": packets[0]["trace_id"],
        "status": "incomplete",
        "packet_count": len(packets),
        "acknowledged": [],
        "attempts": [],
    }
    for packet in packets:
        accepted = False
        for attempt in range(1, attempts + 1):
            retry = True
            status = 0
            try:
                status, body = send(encode(packet))
                ack = json.loads(body) if len(body) <= 65536 else None
                accepted = (
                    status == 200
                    and isinstance(ack, dict)
                    and type(ack.get("sequence")) is int
                    and ack == acknowledgement(packet)
                )
                outcome = "verified" if accepted else "unverified_response"
                retry = status in RETRYABLE or 200 <= status < 300
            except (ValueError, TypeError):
                outcome = "invalid_acknowledgement"
                retry = status in RETRYABLE or 200 <= status < 300
            except (TimeoutError, ConnectionError):
                outcome = "transport_failure"
            except Exception:  # noqa: BLE001 - record failure; never infer a successful upload.
                outcome, retry = "unexpected_transport_failure", False
            result["attempts"].append(
                {"sequence": packet["sequence"], "attempt": attempt, "outcome": outcome}
            )
            if accepted or not retry:
                break
            if attempt < attempts:
                sleep(0.25 * 2 ** (attempt - 1))
        if not accepted:
            return result
        result["acknowledged"].append(ack)
        if packet["sequence"] < len(packets) - 1:
            sleep(1.0)  # Respect the proposed one-request/second API rate.
    result["status"] = "stored_verified"
    return result


class SignedTransport:
    """Explicit live transport. Local planning never constructs it."""

    def __init__(self, endpoint: str, region: str):
        import re

        if not re.fullmatch(
            r"https://[a-z0-9]+\.execute-api\."
            + re.escape(region)
            + r"\.amazonaws\.com/v1",
            endpoint,
        ):
            raise ValueError("Expected regional AWS execute-api /v1 endpoint")
        import boto3
        from botocore.httpsession import URLLib3Session

        self.session = boto3.Session(region_name=region)
        self.http = URLLib3Session(timeout=27)
        self.endpoint, self.region = endpoint, region

    def __call__(self, body: bytes) -> tuple[int, bytes]:
        from botocore.auth import SigV4Auth
        from botocore.awsrequest import AWSRequest
        from botocore.exceptions import ConnectionError as SDKConnectionError
        from botocore.exceptions import HTTPClientError

        request = AWSRequest(
            method="POST",
            url=self.endpoint + "/evidence",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        SigV4Auth(
            self.session.get_credentials().get_frozen_credentials(),
            "execute-api",
            self.region,
        ).add_auth(request)
        try:
            response = self.http.send(request.prepare())
        except (HTTPClientError, SDKConnectionError) as exc:
            raise ConnectionError("AWS HTTP request unacknowledged") from exc
        return response.status_code, response.content
