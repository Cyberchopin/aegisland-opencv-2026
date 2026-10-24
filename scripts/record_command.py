#!/usr/bin/env python3
"""Retain exact argv, stdout, stderr, status and time for a local verification command."""

import datetime
import json
import subprocess
import sys
from pathlib import Path

destination = Path(sys.argv[1])
command = sys.argv[2:]
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
result = subprocess.run(command, text=True, capture_output=True, check=False)
destination.parent.mkdir(parents=True, exist_ok=True)
with destination.open("x") as handle:
    json.dump(
        {
            "argv": command,
            "cwd": str(Path.cwd()),
            "started_utc": started,
            "finished_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        },
        handle,
        indent=2,
    )
print(result.stdout, end="")
print(result.stderr, end="", file=sys.stderr)
raise SystemExit(result.returncode)
