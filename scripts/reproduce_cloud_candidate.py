#!/usr/bin/env python3
"""Rebuild the existing reviewed Lambda candidate in a disposable offline tree."""

import hashlib
import importlib.util
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = "final-hardening-20261023-r2"


def main():
    archive = ROOT / "approval/aegisland-unreserved-approval.zip"
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == (
        "50da7772bbb62c8c6c067ba10393de6b692f3f7b13253fd9b0f95a8774d18eb9"
    )
    spec = importlib.util.spec_from_file_location(
        "offline_candidate_builder", ROOT / "scripts/build_storage_remediation.py"
    )
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    with tempfile.TemporaryDirectory(prefix="aegisland-candidate-rebuild-") as tmp:
        tree = Path(tmp)
        with zipfile.ZipFile(archive) as source:
            for name in source.namelist():
                assert not Path(name).is_absolute() and ".." not in Path(name).parts
            source.extractall(tree)
        shutil.copyfile(archive, tree / "approval/aegisland-unreserved-approval.zip")
        shutil.copytree(
            ROOT / "cloud", tree / "cloud", ignore=shutil.ignore_patterns("__pycache__")
        )
        builder.ROOT = tree
        builder.OLD = tree / "approval/unreserved"
        builder.build(REVISION)
        candidate = Path("approval") / REVISION
        assert (tree / candidate / "function-artifact.zip").read_bytes() == (
            ROOT / candidate / "function-artifact.zip"
        ).read_bytes()
        assert json.loads(
            (tree / candidate / "resource-manifest.json").read_text()
        ) == json.loads((ROOT / candidate / "resource-manifest.json").read_text())
    print(
        "PASS: rebuilt ZIP bytes and complete manifest exactly match the reviewed candidate; no AWS or dependency download"
    )


if __name__ == "__main__":
    main()
