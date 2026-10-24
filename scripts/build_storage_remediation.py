#!/usr/bin/env python3
"""Build or privately render the storage correction; no AWS calls or downloads."""

import argparse
import copy
import hashlib
import json
import os
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "approval/storage-remediation-1"
OLD = ROOT / "approval/unreserved"
ORIGINAL_ARCHIVE_SHA = (
    "50da7772bbb62c8c6c067ba10393de6b692f3f7b13253fd9b0f95a8774d18eb9"
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def build(revision="storage-remediation-1"):
    output_dir = ROOT / "approval" / revision
    archive = ROOT / "approval/aegisland-unreserved-approval.zip"
    assert digest(archive.read_bytes()) == ORIGINAL_ARCHIVE_SHA
    with zipfile.ZipFile(archive) as reviewed:
        for name in reviewed.namelist():
            assert (ROOT / name).read_bytes() == reviewed.read(name)
    previous = json.loads((OLD / "resource-manifest.json").read_text())
    assert (
        digest((ROOT / previous["artifact"]["path"]).read_bytes())
        == previous["artifact"]["sha256"]
    )
    assert (
        digest((ROOT / "infra/template.unreserved-review.yaml").read_bytes())
        == (previous["source_template_sha256"])
    )
    with zipfile.ZipFile(ROOT / previous["artifact"]["path"]) as original:
        files = {name: original.read(name) for name in original.namelist()}
    assert {name: digest(raw) for name, raw in files.items()} == previous["artifact"][
        "file_hashes"
    ]
    changed = []
    for path in sorted((ROOT / "cloud").rglob("*.py")):
        name = str(path.relative_to(ROOT / "cloud"))
        if files[name] != path.read_bytes():
            changed.append(name)
            files[name] = path.read_bytes()
    allowed = ["competition_cloud/storage.py"]
    if revision.startswith("final-hardening-20261023"):
        allowed = ["competition_cloud/client.py", "competition_cloud/storage.py"]
    assert changed == allowed, "Unexpected packaged source differences"
    assert not any(name.endswith((".so", ".pyc")) for name in files)
    output_dir.mkdir(exist_ok=False)
    artifact = output_dir / "function-artifact.zip"
    with zipfile.ZipFile(artifact, "x", zipfile.ZIP_DEFLATED) as output:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 23, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, raw, compresslevel=9)
    with zipfile.ZipFile(artifact) as built:
        assert built.testzip() is None
        assert all(built.read(name) == raw for name, raw in files.items())
    artifact_sha = digest(artifact.read_bytes())
    key = f"aegisland-opencv26-evidence/{revision}/{artifact_sha}/function.zip"
    artifact.with_suffix(".zip.sha256").write_text(
        f"{artifact_sha}  function-artifact.zip\n"
    )
    manifest = copy.deepcopy(previous)
    manifest.update(
        status="OFFLINE_CORRECTION_NOT_DEPLOYED_REQUIRES_NEW_APPROVAL",
        revision=revision,
        previous_artifact_sha256=previous["artifact"]["sha256"],
        changed_application_files=changed,
        infrastructure_changes=[],
        iam_changes=[],
        encryption_changes=[],
        proposed_change_set_name=(
            "aegisland-unreserved-hardening2-review1"
            if revision == "final-hardening-20261023-r2"
            else "aegisland-unreserved-hardening1-review1"
            if revision == "final-hardening-20261023"
            else "aegisland-unreserved-remediation1-review1"
        ),
    )
    manifest["artifact"] = {
        "path": str(artifact.relative_to(ROOT)),
        "sha256": artifact_sha,
        "bytes": artifact.stat().st_size,
        "files": len(files),
        "file_hashes": {name: digest(raw) for name, raw in files.items()},
        "proposed_s3_key": key,
        "source": "Verified original reviewed ZIP; listed source modules replaced; SDK unchanged",
    }
    manifest["out_of_stack_prerequisites"]["staging_object_key"] = key
    write_json(output_dir / "resource-manifest.json", manifest)
    # Byte-identical infrastructure and original bounded verification plan.
    for name in ("processed-template.OFFLINE.json", "verification-plan.json"):
        (output_dir / name).write_bytes((OLD / name).read_bytes())
    cost = json.loads((OLD / "cost-estimate.json").read_text())
    cost.update(
        status="OFFLINE_SECOND_RUN_PLANNING_ONLY_NOT_AUTHORIZED_NOT_A_BILL",
        revision=revision,
        actual_first_run_cost="UNAVAILABLE; no paid billing API used",
        previously_accepted_aggregate_target_usd=5,
        proposed_cumulative_two_full_run_allowance_usd=round(
            2 * cost["planning_total"], 6
        ),
        remaining_actual_budget="UNVERIFIED; do not assume a new separate $5 allowance",
        infrastructure_cost_delta="None; same resources, encryption and request ceiling",
    )
    write_json(output_dir / "cost-estimate.json", cost)
    write_json(
        output_dir / "build-provenance.json",
        {
            "aws_calls": 0,
            "downloads": 0,
            "original_approval_archive_sha256": ORIGINAL_ARCHIVE_SHA,
            "original_function_zip_sha256": previous["artifact"]["sha256"],
            "new_function_zip_sha256": artifact_sha,
            "changed_packaged_files": changed,
            "all_dependency_file_hashes_preserved": True,
            "source_template_sha256": manifest["source_template_sha256"],
            "processed_resources_identical": manifest["resources"]
            == previous["resources"],
            "packaging": "Deterministic ZIP reuse; not a new SAM or live Arm64 test",
        },
    )
    print(json.dumps({"status": manifest["status"], "artifact_sha256": artifact_sha}))


def render(bucket, output, revision="storage-remediation-1"):
    candidate = ROOT / "approval" / revision
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket):
        raise ValueError("Expected privately approved bucket name")
    output = output.resolve()
    if output.is_relative_to(ROOT):
        raise ValueError("Private account configuration must remain outside Git")
    manifest = json.loads((candidate / "resource-manifest.json").read_text())
    assert (
        digest((ROOT / manifest["artifact"]["path"]).read_bytes())
        == manifest["artifact"]["sha256"]
    )
    assert (
        digest((ROOT / "infra/template.unreserved-review.yaml").read_bytes())
        == (manifest["source_template_sha256"])
    )
    raw = (candidate / "processed-template.OFFLINE.json").read_bytes()
    assert digest(raw) == manifest["processed_template_sha256"]
    template = json.loads(raw)
    assert template["Resources"] == manifest["resources"]
    template["Resources"]["EvidenceFunction"]["Properties"]["Code"] = {
        "S3Bucket": bucket,
        "S3Key": manifest["artifact"]["proposed_s3_key"],
    }
    raw = (json.dumps(template, indent=2) + "\n").encode()
    assert len(raw) < 51200
    with os.fdopen(
        os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb"
    ) as handle:
        handle.write(raw)
    print(json.dumps({"aws_calls": 0, "private_template_sha256": digest(raw)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    building = actions.add_parser("build")
    rendering = actions.add_parser("render")
    rendering.add_argument("--artifact-bucket", required=True)
    rendering.add_argument("--output", type=Path, required=True)
    for action in (building, rendering):
        action.add_argument(
            "--revision",
            choices=(
                "storage-remediation-1",
                "final-hardening-20261023",
                "final-hardening-20261023-r2",
            ),
            default="storage-remediation-1",
        )
    args = parser.parse_args()
    if args.action == "build":
        build(args.revision)
    else:
        render(args.artifact_bucket, args.output, args.revision)
