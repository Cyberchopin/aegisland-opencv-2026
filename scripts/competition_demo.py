#!/usr/bin/env python3
"""Run the pinned, unchanged core locally and retain verifiable competition evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = (
    "nominal",
    "low_battery_intrusion",
    "gps_loss_low_light",
    "gps_denied_camera_failure",
    "gps_denied_camera_flicker",
    "critical_battery_collision",
)


def git(core: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(core), *args], text=True).strip()


def check_core(core: Path) -> str:
    pin = json.loads((ROOT / "core-pin.json").read_text())
    commit = git(core, "rev-parse", "HEAD")
    if commit != pin["commit"]:
        raise ValueError(f"Core commit {commit} does not match pin {pin['commit']}")
    if git(core, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("Core working tree must be clean, including untracked files")
    return commit


def validate_artifacts(output: Path) -> dict:
    import cv2

    summary = json.loads((output / "summary.json").read_text())
    events = [
        json.loads(line) for line in (output / "trace.jsonl").read_text().splitlines()
    ]
    if not events or len(events) != summary["frames"]:
        raise ValueError("Trace count does not match summary")
    for index, event in enumerate(events):
        if event["sequence"] != index or not event["evidence"]["evidence_id"]:
            raise ValueError("Incomplete trace identity/sequence")
        if not event["decision"]["reasons"]:
            raise ValueError("Missing decision reasons")
        if event["command"].get("hardware_command_sent") is not False:
            raise ValueError("Expected simulation-only commands")
    video = cv2.VideoCapture(str(output / "annotated.mp4"))
    count = 0
    try:
        while True:
            ok, _frame = video.read()
            if not ok:
                break
            count += 1
    finally:
        video.release()
    if count != len(events):
        raise ValueError(f"Decoded {count} video frames for {len(events)} events")
    if (output / "report.html").stat().st_size == 0:
        raise ValueError("Empty report")
    return {
        "trace_events": len(events),
        "decoded_video_frames": count,
        "all_commands_simulation_only": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scenario", choices=SCENARIOS, default="gps_loss_low_light")
    args = parser.parse_args()
    core, output = args.core.resolve(), args.output.resolve()
    if output.is_relative_to(core):
        raise ValueError("Output must be outside the core checkout")
    commit = check_core(core)
    # mkdir is exclusive: a failed or previous run must never be silently overwritten.
    output.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env.pop("AEGISLAND_TRACE_ENDPOINT", None)
    env["PYTHONPATH"] = str(core / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    command = [
        sys.executable,
        "-m",
        "aegisland",
        "demo",
        "--scenario",
        args.scenario,
        "--output",
        str(output),
    ]
    manifest = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "core_commit": commit,
        "core_status_before": "clean",
        "competition_commit": git(ROOT, "rev-parse", "HEAD"),
        "competition_status": git(ROOT, "status", "--porcelain"),
        "entrypoint_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "core_pin_sha256": hashlib.sha256(
            (ROOT / "core-pin.json").read_bytes()
        ).hexdigest(),
        "command": command,
        "cwd": str(core),
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "environment_overrides": {
            k: env[k]
            for k in ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "PYTHONNOUSERSITE")
        },
        "cloud_mode": "disabled: AEGISLAND_TRACE_ENDPOINT removed from child environment",
        "status": "FAIL",
    }
    try:
        probe = [
            sys.executable,
            "-c",
            (
                "import cv2,numpy,aegisland,json; "
                "print(json.dumps({'opencv':cv2.__version__,'numpy':numpy.__version__,"
                "'core_module':aegisland.__file__})); print(cv2.getBuildInformation())"
            ),
        ]
        result = subprocess.run(
            probe, cwd=core, env=env, text=True, capture_output=True, check=False
        )
        (output / "opencv-build.txt").write_text(result.stdout + result.stderr)
        result.check_returncode()
        versions = json.loads(result.stdout.splitlines()[0])
        manifest["versions"] = versions
        if not versions["opencv"].startswith("5."):
            raise ValueError("Competition evidence requires OpenCV 5")
        if not Path(versions["core_module"]).is_relative_to(core / "src"):
            raise ValueError("Imported core is not the requested checkout")
        result = subprocess.run(
            command, cwd=core, env=env, text=True, capture_output=True, check=False
        )
        (output / "stdout.txt").write_text(result.stdout)
        (output / "stderr.txt").write_text(result.stderr)
        manifest["returncode"] = result.returncode
        result.check_returncode()
        manifest["validation"] = validate_artifacts(output)
        check_core(core)
        manifest["core_status_after"] = "clean"
        manifest["status"] = "PASS"
    except Exception as exc:
        manifest["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        manifest["finished_utc"] = datetime.now(timezone.utc).isoformat()
        manifest["sha256"] = {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(output.iterdir())
            if p.is_file()
        }
        (output / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": "PASS",
                "output": str(output),
                "validation": manifest["validation"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
