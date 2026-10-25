#!/usr/bin/env python3
"""Verify source, dependency and infrastructure identity offline, including imports."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = "final-hardening-20261023-r2"


def main():
    base = ROOT / "approval" / REVISION
    manifest = json.loads((base / "resource-manifest.json").read_text())
    previous = json.loads(
        (ROOT / "approval/unreserved/resource-manifest.json").read_text()
    )
    assert all(
        manifest[key] == previous[key]
        for key in ("resources", "iam", "resource_policies", "source_template_sha256")
    )
    artifact = ROOT / manifest["artifact"]["path"]
    assert (
        hashlib.sha256(artifact.read_bytes()).hexdigest()
        == manifest["artifact"]["sha256"]
    )
    with (
        zipfile.ZipFile(ROOT / previous["artifact"]["path"]) as old,
        zipfile.ZipFile(artifact) as new,
    ):
        assert set(old.namelist()) == set(new.namelist())
        changed = sorted(n for n in old.namelist() if old.read(n) != new.read(n))
        assert changed == [
            "competition_cloud/client.py",
            "competition_cloud/storage.py",
        ]
        for path in (ROOT / "cloud").rglob("*.py"):
            assert path.read_bytes() == new.read(str(path.relative_to(ROOT / "cloud")))
        assert all(not name.endswith((".so", ".pyc")) for name in new.namelist())
        assert {
            n: hashlib.sha256(new.read(n)).hexdigest() for n in new.namelist()
        } == manifest["artifact"]["file_hashes"]
    command = (
        "import socket; "
        "socket.create_connection=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('offline')); "
        "import sys; sys.path.insert(0,sys.argv[1]); "
        "import app,boto3,competition_cloud.storage; "
        "assert all(sys.argv[1] in m.__file__ for m in (app,boto3,competition_cloud.storage)); "
        "print('PASS: packaged handler, storage and pinned SDK imports')"
    )
    subprocess.run(
        [sys.executable, "-c", command, str(artifact)],
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    with tempfile.TemporaryDirectory(prefix="aegisland-offline-candidate-") as tmp:
        output = Path(tmp) / "template.json"
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/build_storage_remediation.py"),
                "render",
                "--revision",
                REVISION,
                "--artifact-bucket",
                "offline-fixture-aegisland-only",
                "--output",
                str(output),
            ],
            check=True,
        )
        rendered = json.loads(output.read_text())
        original = json.loads((base / "processed-template.OFFLINE.json").read_text())
        rendered["Resources"]["EvidenceFunction"]["Properties"]["Code"] = original[
            "Resources"
        ]["EvidenceFunction"]["Properties"]["Code"]
        assert rendered == original and output.stat().st_mode & 0o777 == 0o600
    print(
        "PASS: two explained modules; every dependency, IAM policy and resource unchanged"
    )


if __name__ == "__main__":
    main()
