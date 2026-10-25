"""Versioned, bounded evidence packet and acknowledgement contract."""

from __future__ import annotations

import base64
import hashlib
import json
import re

PROTOCOL = "aegis-evidence-v1"
CHUNK_BYTES = 131072
MAX_BODY = 256000
MAX_PACKETS = 4096
ARTIFACTS = (
    "annotated.mp4",
    "trace.jsonl",
    "summary.json",
    "report.html",
    "opencv-build.txt",
    "stdout.txt",
    "stderr.txt",
    "provenance.json",
)
FIELDS = {
    "protocol",
    "trace_id",
    "sequence",
    "artifact",
    "part_index",
    "part_count",
    "file_sha256",
    "data_sha256",
    "data",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def validate(packet: dict) -> bytes:
    if not isinstance(packet, dict) or set(packet) != FIELDS:
        raise ValueError("invalid packet fields")
    if packet["protocol"] != PROTOCOL or packet["artifact"] not in (
        *ARTIFACTS,
        "bundle.json",
    ):
        raise ValueError("unsupported protocol or artifact")
    for name in ("trace_id", "file_sha256", "data_sha256"):
        if not isinstance(packet[name], str) or not re.fullmatch(
            r"[0-9a-f]{64}", packet[name]
        ):
            raise ValueError("invalid digest")
    for name in ("sequence", "part_index", "part_count"):
        if type(packet[name]) is not int:
            raise ValueError("packet counters must be integers")
    if not (
        0 <= packet["sequence"] < MAX_PACKETS
        and 0 <= packet["part_index"] < packet["part_count"] <= MAX_PACKETS
    ):
        raise ValueError("packet counters out of bounds")
    if not isinstance(packet["data"], str) or len(packet["data"]) > 4 * (
        (CHUNK_BYTES + 2) // 3
    ):
        raise ValueError("invalid encoded chunk size")
    raw = base64.b64decode(packet["data"], validate=True)
    if len(raw) > CHUNK_BYTES or digest(raw) != packet["data_sha256"]:
        raise ValueError("chunk checksum mismatch")
    return raw


def object_key(packet: dict) -> str:
    return f"evidence/{packet['trace_id']}/{packet['sequence']:08d}.json"


def acknowledgement(packet: dict) -> dict:
    return {
        "protocol": PROTOCOL,
        "status": "stored_verified",
        "trace_id": packet["trace_id"],
        "sequence": packet["sequence"],
        "payload_sha256": digest(encode(packet)),
        "object_key": object_key(packet),
    }
