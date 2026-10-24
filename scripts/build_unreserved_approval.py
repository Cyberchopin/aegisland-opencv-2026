#!/usr/bin/env python3
"""Materialize the selected template, IAM inventory, Lambda artifact and cost model offline."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import zipfile
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "approval/unreserved"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(name, value):
    (OUTPUT / name).write_text(json.dumps(value, indent=2) + "\n")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    os.environ["AWS_EC2_METADATA_DISABLED"] = "true"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    import botocore.endpoint
    from samtranslator.translator.transform import transform
    from samtranslator.yaml_helper import yaml_parse

    def forbidden(*_args, **_kwargs):
        raise RuntimeError("AWS/network access forbidden in offline approval build")

    socket.create_connection = forbidden
    botocore.endpoint.Endpoint._send = forbidden
    source = ROOT / "infra/template.unreserved-review.yaml"
    source_bytes = source.read_bytes()
    assert (
        sha(source_bytes)
        == "70ab18de01293f495e7456984832b081f080ee02b58cfd30c0ba3e3aaa526b87"
    )
    template = yaml_parse(source_bytes.decode())
    assert (
        "ReservedConcurrentExecutions"
        not in template["Resources"]["EvidenceFunction"]["Properties"]
    )
    template["Resources"]["EvidenceFunction"]["Properties"]["CodeUri"] = {
        "Bucket": "REPLACE_WITH_APPROVED_AEGISLAND_ARTIFACT_BUCKET",
        "Key": "REPLACE_WITH_REVIEWED_ARTIFACT_KEY",
    }
    processed = transform(template, {}, SimpleNamespace(load=dict))
    resources = processed["Resources"]
    assert len(resources) == 9
    assert {k for k, v in resources.items() if v["Type"].startswith("AWS::IAM::")} == {
        "EvidenceRole"
    }
    role = resources["EvidenceRole"]["Properties"]
    assert "RoleName" not in role and len(role["Policies"]) == 1
    write_json("processed-template.OFFLINE.json", processed)

    stage = ROOT / ".baseline/sam-final/EvidenceFunction"
    prior = json.loads(
        (ROOT / "evidence/a2/lambda-build-hashes-final.json").read_text()
    )
    assert all(
        sha((stage / name).read_bytes()) == digest for name, digest in prior.items()
    )
    for path in (ROOT / "cloud").rglob("*.py"):
        assert (
            path.read_bytes() == (stage / path.relative_to(ROOT / "cloud")).read_bytes()
        )
    files = {
        str(path.relative_to(stage)): path.read_bytes()
        for path in sorted(stage.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }
    assert not any(name.endswith(".so") for name in files)
    artifact = OUTPUT / "function-artifact.zip"
    with zipfile.ZipFile(
        artifact, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as handle:
        for name, data in files.items():
            info = zipfile.ZipInfo(name, (2026, 10, 22, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            handle.writestr(info, data, compresslevel=9)
    with zipfile.ZipFile(artifact) as handle:
        assert handle.testzip() is None
        assert all(handle.read(name) == raw for name, raw in files.items())
    artifact_sha = sha(artifact.read_bytes())
    key = f"aegisland-opencv26-evidence/70ab18de/{artifact_sha}/function.zip"
    artifact.with_suffix(".zip.sha256").write_text(f"{artifact_sha}  {artifact.name}\n")
    manifest = {
        "status": "OFFLINE_APPROVAL_ONLY_NOT_DEPLOYED",
        "region": "us-east-1",
        "proposed_stack": "aegisland-opencv26-evidence",
        "source_template_sha256": sha(source_bytes),
        "processed_template_sha256": sha(
            (OUTPUT / "processed-template.OFFLINE.json").read_bytes()
        ),
        "resources": resources,
        "iam": {
            "new_roles": ["EvidenceRole"],
            "inline_policies": role["Policies"],
            "trust_policy": role["AssumeRolePolicyDocument"],
            "standalone_iam_policy_resources": [],
            "new_iam_users_or_access_keys": [],
            "new_cloudformation_service_role": False,
            "new_service_quotas_role": False,
        },
        "resource_policies": {
            name: value
            for name, value in resources.items()
            if value["Type"] in ("AWS::S3::BucketPolicy", "AWS::Lambda::Permission")
        },
        "out_of_stack_prerequisites": {
            "artifact_bucket": "owner-supplied existing AegisLand staging bucket; creation NOT included",
            "staging_object_key": key,
            "kms": "AWS-managed alias/aws/dynamodb; may be created by the service on first use; no customer-managed key",
            "cloudformation_stack": "new stack/change set; REVIEW_IN_PROGRESS placeholder possible before execution",
        },
        "artifact": {
            "path": "approval/unreserved/function-artifact.zip",
            "sha256": artifact_sha,
            "bytes": artifact.stat().st_size,
            "files": len(files),
            "file_hashes": {name: sha(raw) for name, raw in files.items()},
            "proposed_s3_key": key,
            "source": "previous validated SAM package; all five current cloud source modules match",
        },
    }
    write_json("resource-manifest.json", manifest)
    # Conservative budgeting inputs, not a quote, measured bill or hard enforcement.
    rows = [
        (
            "Lambda requests",
            "40 requests x $0.30 / million",
            Decimal(40) * Decimal("0.30") / 1000000,
        ),
        (
            "Lambda duration",
            "40 x 0.25 GB x 60 billed seconds x $0.00002 / GB-second",
            Decimal(40) * Decimal("0.25") * 60 * Decimal("0.00002"),
        ),
        ("API Gateway", "40 requests x $2 / million", Decimal(40) * 2 / 1000000),
        (
            "S3 requests including staging/readback/cleanup",
            "150 PUT + 100 LIST at $0.01/1000; 250 GET at $0.001/1000",
            Decimal(250) * Decimal("0.01") / 1000
            + Decimal(250) * Decimal("0.001") / 1000,
        ),
        ("S3 evidence and staging storage", "0.25 GB-month x $0.10", Decimal("0.025")),
        (
            "DynamoDB requests",
            "150 WRU at $1/million + 150 RRU at $0.50/million",
            Decimal(150) * Decimal("1.50") / 1000000,
        ),
        (
            "DynamoDB storage",
            "1 GB-month planning allowance x $0.30; not a minimum billable size claim",
            Decimal("0.30"),
        ),
        ("DynamoDB PITR", "1 GB-month planning allowance x $0.25", Decimal("0.25")),
        (
            "KMS requests",
            "1000-request allowance x $0.01/1000; no free-tier offset",
            Decimal("0.01"),
        ),
        (
            "CloudWatch log ingestion and retention",
            "0.01 GB x $1 ingestion + 0.01 GB-month x $0.10",
            Decimal("0.011"),
        ),
        (
            "Approved diagnostic API allowance",
            "rounding reserve; no Insights/GetMetricData query planned",
            Decimal("0.01"),
        ),
        ("Internet egress", "0.25 GB x $0.20", Decimal("0.05")),
        (
            "Account telemetry/rounding contingency",
            "unverified existing Config/CloudTrail effects; no new service enabled",
            Decimal("0.25"),
        ),
    ]
    total = sum(row[2] for row in rows)
    write_json(
        "cost-estimate.json",
        {
            "status": "CONSERVATIVE_OFFLINE_PLANNING_ALLOWANCE_NOT_HARD_CAP",
            "region": "us-east-1",
            "currency": "USD",
            "free_tier_or_credits_assumed": False,
            "rows": [
                {"service": name, "basis": basis, "usd": float(value)}
                for name, basis, value in rows
            ],
            "planning_total": float(total),
            "rounded_operating_allowance": 1,
            "proposed_owner_authorization_ceiling": 5,
            "active_test_window": "one supervised hour, stack cleanup within 24 hours",
            "storage_allowance_window": "up to one month as a contingency; prompt cleanup planned",
            "excludes": [
                "tax",
                "unrelated CreditBridge/account usage",
                "uncontrolled traffic",
                "scope expansion",
            ],
            "kms_key_rental": "zero for AWS-managed key; request charges included; no customer-managed key proposed",
            "iam_and_standard_aws_cloudformation_control_plane": "no separate direct service charge modeled; backing services included",
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS_OFFLINE_ONLY",
                "aws_calls": 0,
                "resources": len(resources),
                "new_iam_roles": 1,
                "inline_iam_policies": 1,
                "artifact_sha256": artifact_sha,
                "artifact_bytes": artifact.stat().st_size,
                "planning_total_usd": float(total),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
