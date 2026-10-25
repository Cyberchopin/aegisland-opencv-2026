#!/usr/bin/env python3
"""Create a fresh, audited judge-source candidate without altering old archives."""

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PATHS = {"docs/AWS_STAGING_BUCKET_PLAN.md"}
EXCLUDED_PARTS = {".aws", ".git", ".venv", ".baseline", ".agents", ".codex"}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build(destination):
    destination = destination.resolve()
    if destination.exists():
        raise ValueError(
            "Destination exists; historical releases cannot be overwritten"
        )
    if destination.parent != ROOT / "submission":
        raise ValueError("Use a new named directory directly under submission/")
    selected = [
        ROOT / n
        for n in (
            "README.md",
            "FINAL_SUBMISSION_HANDOFF.md",
            "core-pin.json",
            "pytest.ini",
            ".gitignore",
        )
    ]
    selected += list(ROOT.glob("requirements*.txt"))
    for directory in (
        "cloud",
        "scripts",
        "tests",
        "docs",
        "infra",
        "evidence",
        ".github",
    ):
        selected += [
            p
            for p in (ROOT / directory).rglob("*")
            if p.is_file()
            and "__pycache__" not in p.parts
            and p.suffix not in {".pyc", ".zip"}
        ]
    selected += [
        p for p in (ROOT / "submission").glob("*") if p.suffix in {".md", ".svg"}
    ]
    selected += [
        p for p in (ROOT / "submission/candidate-20261023").rglob("*") if p.is_file()
    ]
    selected += [
        p for p in (ROOT / "submission/entry-20261024").rglob("*") if p.is_file()
    ]
    # Include approval text and full manifests, without distributing Lambda SDK ZIPs.
    selected += [
        p
        for p in (ROOT / "approval").rglob("*")
        if p.is_file() and p.suffix in {".md", ".json", ".patch", ".sha256"}
    ]
    private_values = []
    config = Path.home() / ".config/aegisland/aws-owner.json"
    if config.exists():
        owner = json.loads(config.read_text())
        private_values = [
            str(owner["expected_account_id"]).encode(),
            owner["bucket"].encode(),
        ]
    payload = {}
    for path in sorted(set(selected)):
        relative = path.relative_to(ROOT)
        name = str(relative)
        if name in PRIVATE_PATHS:
            continue
        if path.is_symlink() or any(part in EXCLUDED_PARTS for part in relative.parts):
            raise ValueError("Unsafe path in release candidate")
        raw = path.read_bytes()
        if any(value in raw for value in private_values):
            raise ValueError(
                f"Private owner identifier detected; exclude and review {name}"
            )
        if re.search(rb"(?:AKIA|ASIA)[A-Z0-9]{16}", raw):
            raise ValueError(f"Credential-like token detected: {name}")
        payload[name] = raw
    manifest = {
        "status": "OFFLINE_OWNER_REVIEW_CANDIDATE_NOT_PUBLISHED",
        "competition_base_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "working_tree_snapshot": True,
        "core_source_included": False,
        "core_pin": json.loads((ROOT / "core-pin.json").read_text()),
        "clean_machine_initial_acquisition_needs_network": True,
        "cloud_history": "deployment PASS; storage verification FAIL; teardown PASS",
        "current_judge_entry": "submission/entry-20261024/START_HERE.md",
        "current_cloud_candidate": "approval/final-hardening-20261023-r2/resource-manifest.json",
        "current_cloud_candidate_verified_live": False,
        "omitted_private_source_paths": sorted(PRIVATE_PATHS),
        "lambda_dependency_archives_included": False,
        "private_configuration_or_logs_included": False,
        "files": {name: sha(raw) for name, raw in sorted(payload.items())},
    }
    manifest_raw = (json.dumps(manifest, indent=2) + "\n").encode()
    payload["PUBLIC_SOURCE_MANIFEST.json"] = manifest_raw
    destination.mkdir()
    archive = destination / "aegisland-judge-source-candidate.zip"
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for name, raw in sorted(payload.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 23, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, raw, compresslevel=9)
    with zipfile.ZipFile(archive) as output:
        assert output.testzip() is None
        assert all(output.read(name) == raw for name, raw in payload.items())
    (destination / "PUBLIC_SOURCE_MANIFEST.json").write_bytes(manifest_raw)
    digest = sha(archive.read_bytes())
    (destination / "aegisland-judge-source-candidate.zip.sha256").write_text(
        f"{digest}  {archive.name}\n"
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "files": len(payload),
                "sha256": digest,
                "published": False,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
