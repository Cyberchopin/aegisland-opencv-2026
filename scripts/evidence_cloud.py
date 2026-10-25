#!/usr/bin/env python3
"""Prepare local evidence; --upload requires prior explicit owner authorization."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cloud"))
from competition_cloud.client import SignedTransport, prepare, upload
from competition_cloud.protocol import encode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--endpoint")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()
    plan, packets = prepare(args.evidence)
    if args.upload and not args.endpoint:
        parser.error("--upload requires an explicit --endpoint")
    output = args.output.resolve()
    if output.is_relative_to(args.evidence.resolve()):
        parser.error("output must be outside the immutable evidence directory")
    output.mkdir(parents=True, exist_ok=False)
    (output / "plan.json").write_bytes(encode(plan))
    (output / "packets.jsonl").write_bytes(
        b"\n".join(encode(p) for p in packets) + b"\n"
    )
    if not args.upload:
        print(
            json.dumps(
                {
                    "mode": "local_plan_only",
                    "bundle_id": plan["bundle_id"],
                    "packet_count": plan["packet_count"],
                }
            )
        )
        return 0
    result = {"mode": "aws_http", "status": "incomplete"}
    try:
        result = upload(
            packets, SignedTransport(args.endpoint, args.region), mode="aws_http"
        )
    finally:
        (output / "receipts.json").write_bytes(encode(result))
    print(json.dumps({"mode": result["mode"], "status": result["status"]}))
    return 0 if result["status"] == "stored_verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
