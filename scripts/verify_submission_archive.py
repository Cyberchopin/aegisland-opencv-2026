#!/usr/bin/env python3
"""Verify a source release and run it offline using the existing pinned local core."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main(release):
    archive = release / "aegisland-judge-source-candidate.zip"
    checksum = (
        (release / "aegisland-judge-source-candidate.zip.sha256").read_text().split()[0]
    )
    assert sha(archive.read_bytes()) == checksum
    config = Path.home() / ".config/aegisland/aws-owner.json"
    owner = json.loads(config.read_text())
    private_values = [
        str(owner["expected_account_id"]).encode(),
        owner["bucket"].encode(),
    ]
    with tempfile.TemporaryDirectory(prefix="aegisland-source-review-") as tmp:
        work = Path(tmp) / "source"
        work.mkdir()
        with zipfile.ZipFile(archive) as source:
            assert source.testzip() is None
            manifest = json.loads(source.read("PUBLIC_SOURCE_MANIFEST.json"))
            assert set(source.namelist()) == set(manifest["files"]) | {
                "PUBLIC_SOURCE_MANIFEST.json"
            }
            for name in source.namelist():
                path = Path(name)
                assert not path.is_absolute() and ".." not in path.parts
                assert not any(
                    p in {".git", ".aws", ".baseline", ".venv", ".private"}
                    for p in path.parts
                )
                assert (source.getinfo(name).external_attr >> 16) & 0o170000 != 0o120000
                raw = source.read(name)
                assert all(value not in raw for value in private_values), (
                    "Private owner identifier found"
                )
                assert not re.search(rb"(?:AKIA|ASIA)[A-Z0-9]{16}", raw), (
                    "Credential-like token found"
                )
                assert not re.search(
                    rb"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----", raw
                )
                if name in manifest["files"]:
                    assert sha(raw) == manifest["files"][name]
            assert "docs/AWS_STAGING_BUCKET_PLAN.md" not in source.namelist()
            source.extractall(work)
        env = {
            **os.environ,
            "AWS_EC2_METADATA_DISABLED": "true",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(work / "evidence/hardening/network-guard"),
            "GIT_TERMINAL_PROMPT": "0",
        }

        def run(args, cwd=work):
            result = subprocess.run(
                args, cwd=cwd, env=env, capture_output=True, text=True, check=False
            )
            assert result.returncode == 0, result.stdout + result.stderr
            return {
                "argv": args,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        # No remote is contacted: seed the same clean core and installed environment.
        core = work / ".baseline/core"
        core.parent.mkdir()
        run(
            [
                "git",
                "clone",
                "--quiet",
                "--no-hardlinks",
                "--no-checkout",
                str(ROOT / ".baseline/core"),
                str(core),
            ]
        )
        pin = manifest["core_pin"]["commit"]
        run(["git", "-C", str(core), "checkout", "--quiet", "--detach", pin])
        run(["git", "init", "--quiet"])
        run(
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "user.name=Archive reviewer",
                "-c",
                "user.email=reviewer@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "--quiet",
                "--allow-empty",
                "-m",
                "Local archive review baseline",
            ]
        )
        python = str(ROOT / ".venv/bin/python")
        tests = run([python, "-m", "pytest", "-q", "tests"])
        demo = run(
            [
                python,
                "scripts/competition_demo.py",
                "--core",
                str(core),
                "--scenario",
                "gps_loss_low_light",
                "--output",
                str(Path(tmp) / "demo"),
            ]
        )
        provenance = json.loads((Path(tmp) / "demo/provenance.json").read_text())
        assert (
            provenance["status"] == "PASS"
            and provenance["validation"]["trace_events"] == 80
        )
        verification = {
            "status": "PASS",
            "archive_sha256": checksum,
            "manifest_files": len(manifest["files"]),
            "private_owner_and_credential_scan": "PASS; every entry checked",
            "core_seed": "Local clone of existing clean pinned core; no network acquisition",
            "python_environment": "Existing locked .venv; not a clean-machine installation",
            "source_competition_git": "Temporary empty provenance commit; source pinned by archive manifest",
            "competition_tests": tests,
            "fresh_demo": demo,
            "trace_events_and_decoded_frames": provenance["validation"],
            "aws_calls": 0,
            "published": False,
        }
        with (release / "VERIFICATION.json").open("x") as output:
            json.dump(verification, output, indent=2)
            output.write("\n")
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "archive_sha256": checksum,
                    "files": len(manifest["files"]),
                    "competition_test_output": tests["stdout"].strip(),
                    "fresh_frames": 80,
                    "aws_calls": 0,
                }
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release", type=Path)
    main(parser.parse_args().release.resolve())
