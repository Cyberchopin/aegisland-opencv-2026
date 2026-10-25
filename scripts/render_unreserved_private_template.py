#!/usr/bin/env python3
"""Fill only the approved staging bucket/key in the offline expanded template; no AWS calls."""

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-bucket", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", args.artifact_bucket):
        parser.error("Expected a general-purpose approved S3 bucket name")
    if args.artifact_bucket.startswith("REPLACE"):
        parser.error("Bucket is unresolved")
    output = args.output.resolve()
    if output.is_relative_to(ROOT):
        parser.error(
            "Keep account-specific staging configuration outside the repository"
        )
    manifest = json.loads(
        (ROOT / "approval/unreserved/resource-manifest.json").read_text()
    )
    assert (
        hashlib.sha256(
            (ROOT / "infra/template.unreserved-review.yaml").read_bytes()
        ).hexdigest()
        == manifest["source_template_sha256"]
    )
    assert (
        hashlib.sha256((ROOT / manifest["artifact"]["path"]).read_bytes()).hexdigest()
        == manifest["artifact"]["sha256"]
    )
    processed = ROOT / "approval/unreserved/processed-template.OFFLINE.json"
    assert (
        hashlib.sha256(processed.read_bytes()).hexdigest()
        == manifest["processed_template_sha256"]
    )
    template = json.loads(processed.read_text())
    assert template["Resources"] == manifest["resources"]
    template["Resources"]["EvidenceFunction"]["Properties"]["Code"] = {
        "S3Bucket": args.artifact_bucket,
        "S3Key": manifest["artifact"]["proposed_s3_key"],
    }
    raw = (json.dumps(template, indent=2) + "\n").encode()
    assert len(raw) < 51200
    with os.fdopen(
        os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb"
    ) as handle:
        handle.write(raw)
    print(
        json.dumps(
            {
                "status": "PRIVATE_LOCAL_TEMPLATE_ONLY",
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "aws_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
