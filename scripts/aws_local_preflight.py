#!/usr/bin/env python3
"""Inspect AWS configuration metadata without resolving credentials or calling AWS."""

import argparse
import configparser
import importlib.util
import json
import os
import shutil
from pathlib import Path


def inspect_local():
    config = configparser.RawConfigParser()
    credentials = configparser.RawConfigParser()
    config_path = Path(
        os.environ.get("AWS_CONFIG_FILE", str(Path.home() / ".aws/config"))
    )
    credentials_path = Path(
        os.environ.get(
            "AWS_SHARED_CREDENTIALS_FILE", str(Path.home() / ".aws/credentials")
        )
    )
    errors = []
    for label, parser, path in (
        ("config", config, config_path),
        ("credentials", credentials, credentials_path),
    ):
        try:
            if path.is_file():
                with path.open() as handle:
                    parser.read_file(handle)
        except (OSError, configparser.Error) as exc:
            errors.append({"source": label, "error_type": type(exc).__name__})
    selected = (
        os.environ.get("AWS_PROFILE")
        or os.environ.get("AWS_DEFAULT_PROFILE")
        or "default"
    )
    section = selected if selected == "default" else "profile " + selected
    candidates = []
    for name in credentials.sections():
        cfg = name if name == "default" else "profile " + name
        candidates.append(
            {
                "is_selected": name == selected,
                "has_key_pair": all(
                    credentials.has_option(name, key)
                    for key in ("aws_access_key_id", "aws_secret_access_key")
                ),
                "has_session_token": credentials.has_option(name, "aws_session_token"),
                "configured_region": config.get(cfg, "region", fallback=None),
            }
        )
    return {
        "mode": "local_configuration_only",
        "aws_service_calls": 0,
        "aws_cli_available": bool(shutil.which("aws")),
        "boto3_available": importlib.util.find_spec("boto3") is not None,
        "selected_profile_is_default": selected == "default",
        "selected_region": os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or config.get(section, "region", fallback=None),
        "credential_profile_count": len(candidates),
        "credential_candidates_without_names": candidates,
        "credential_environment_present": any(
            os.environ.get(key)
            for key in (
                "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY",
                "AWS_SESSION_TOKEN",
                "AWS_WEB_IDENTITY_TOKEN_FILE",
                "AWS_CONTAINER_CREDENTIALS_FULL_URI",
                "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
            )
        ),
        "account_identity": "UNVERIFIED; no credential resolution or network use",
        "non_root_identity": "UNVERIFIED; confirmation required before credential use",
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inspect_local()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
