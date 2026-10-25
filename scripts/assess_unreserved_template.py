#!/usr/bin/env python3
"""Offline equivalence and bounded-client checks for the no-reservation review variant."""

import copy
import hashlib
import json
import os
import socket
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cloud"))


def main():
    os.environ["AWS_EC2_METADATA_DISABLED"] = "true"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    import botocore.endpoint
    from competition_cloud.client import prepare, upload
    from competition_cloud.protocol import encode
    from samtranslator.translator.transform import transform
    from samtranslator.yaml_helper import yaml_parse

    network_attempts = []

    def forbidden(*_args, **_kwargs):
        network_attempts.append(True)
        raise RuntimeError("Network forbidden in offline feasibility assessment")

    socket.create_connection = forbidden
    botocore.endpoint.Endpoint._send = forbidden
    original = ROOT / "infra/template.yaml"
    candidate = ROOT / "infra/template.unreserved-review.yaml"
    line = "      ReservedConcurrentExecutions: 2\n"
    assert original.read_text().count(line) == 1
    assert candidate.read_text() == original.read_text().replace(line, "")

    def translated(path):
        template = yaml_parse(path.read_text())
        template["Resources"]["EvidenceFunction"]["Properties"]["CodeUri"] = {
            "Bucket": "offline-placeholder",
            "Key": "not-uploaded.zip",
        }
        return transform(template, {}, SimpleNamespace(load=dict))

    baseline = translated(original)
    proposal = translated(candidate)
    expected = copy.deepcopy(baseline)
    assert (
        expected["Resources"]["EvidenceFunction"]["Properties"].pop(
            "ReservedConcurrentExecutions"
        )
        == 2
    )
    assert proposal == expected
    assert len(proposal["Resources"]) == 9
    plan, packets = prepare(ROOT / "evidence/a1/final/nominal")
    sent = []

    def timeout_only(body):
        sent.append(body)
        raise TimeoutError("offline failure injection")

    outcome = upload(
        packets,
        timeout_only,
        attempts=1,
        sleep=lambda _: None,
        mode="offline_timeout_injection",
    )
    assert (
        len(sent) == 1
        and not outcome["acknowledged"]
        and outcome["status"] == "incomplete"
    )
    assert not network_attempts
    result = {
        "status": "PASS_OFFLINE_ONLY",
        "aws_calls": 0,
        "original_template_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
        "candidate_template_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
        "exact_source_change": "remove EvidenceFunction.Properties.ReservedConcurrentExecutions: 2",
        "transformed_change_only": "same property removed; all other generated resources/properties equal",
        "transformed_resources": len(proposal["Resources"]),
        "iam_auth_code_storage_and_policy_unchanged": True,
        "single_attempt_timeout": {
            "requests_dispatched": len(sent),
            "result": outcome["status"],
            "acknowledged": len(outcome["acknowledged"]),
        },
        "nominal_bundle_packets": plan["packet_count"],
        "nominal_raw_artifact_bytes": sum(
            f["bytes"] for f in plan["inventory"]["files"].values()
        ),
        "nominal_s3_packet_json_bytes": sum(len(encode(p)) for p in packets),
        "deployment_feasibility": "conditional on spare shared concurrency, approved IAM/deployment and live verification",
    }
    path = ROOT / "evidence/unreserved-feasibility/offline-assessment.json"
    with path.open("x") as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
