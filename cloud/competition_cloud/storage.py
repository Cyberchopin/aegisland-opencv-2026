"""S3 bytes first, then a conditional DynamoDB index; verify both before ACK."""

from __future__ import annotations

import base64
import json
import logging
import re
import time

from .protocol import MAX_BODY, acknowledgement, digest, encode, object_key, validate


def error_code(exc: Exception) -> str:
    return getattr(exc, "response", {}).get("Error", {}).get("Code", "")


def response(status: int, payload: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(payload),
    }


def ingest(event: dict, s3, table, bucket: str, now=time.time) -> dict:
    if event.get("requestContext", {}).get("http", {}).get("method") != "POST":
        return response(405, {"error": "method_not_allowed"})
    try:
        body = event.get("body", "")
        if not isinstance(body, str) or len(body) > MAX_BODY * 2:
            return response(413, {"error": "request_too_large"})
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body, validate=True).decode("utf-8")
        if len(body.encode()) > MAX_BODY:
            return response(413, {"error": "request_too_large"})
        packet = json.loads(body)
        validate(packet)
        stored = encode(packet)
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        return response(400, {"error": "invalid_packet"})

    key = object_key(packet)
    checksum = digest(stored)
    service, operation = "s3", "PutObject"
    try:
        try:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=stored,
                ContentType="application/json",
                ServerSideEncryption="AES256",
                IfNoneMatch="*",
            )
        except Exception as exc:
            if error_code(exc) != "PreconditionFailed":
                raise
        # Never trust object metadata or the ETag as proof of the actual bytes.
        operation = "GetObject"
        stream = s3.get_object(Bucket=bucket, Key=key)["Body"]
        try:
            actual = stream.read(MAX_BODY + 1)
        finally:
            stream.close()
        if digest(actual) != checksum:
            return response(409, {"error": "object_conflict"})
        identity = {"TraceId": packet["trace_id"], "Sequence": packet["sequence"]}
        item = {
            **identity,
            "PayloadSHA256": checksum,
            "ObjectKey": key,
            "Complete": True,
            "ExpiresAt": int(now()) + 30 * 86400,
        }
        service, operation = "dynamodb", "PutItem"
        try:
            table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(#trace_id) AND attribute_not_exists(#sequence)",
                ExpressionAttributeNames={
                    "#trace_id": "TraceId",
                    "#sequence": "Sequence",
                },
            )
        except Exception as exc:
            if error_code(exc) != "ConditionalCheckFailedException":
                raise
        operation = "GetItem"
        indexed = table.get_item(Key=identity, ConsistentRead=True).get("Item", {})
        if indexed.get("Complete") is not True or any(
            indexed.get(field) != item[field]
            for field in (
                "TraceId",
                "Sequence",
                "PayloadSHA256",
                "ObjectKey",
            )
        ):
            return response(409, {"error": "index_conflict"})
        return response(200, acknowledgement(packet))
    except Exception as exc:  # noqa: BLE001 - ambiguous service outcomes are unverified.
        # Unknown/timeout outcome is never a successful acknowledgement.
        code = error_code(exc) or "unknown"
        if not isinstance(code, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", code):
            code = "redacted"
        # Never log Error.Message, full responses, credentials or resource ARNs.
        logging.getLogger(__name__).warning(
            "storage_unverified service=%s operation=%s code=%s exception=%s trace=%s sequence=%s",
            service,
            operation,
            code,
            type(exc).__name__,
            packet["trace_id"],
            packet["sequence"],
        )
        return response(503, {"error": "storage_unverified"})
