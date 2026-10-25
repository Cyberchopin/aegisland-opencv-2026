#!/usr/bin/env python3
"""One owner-authorized quota request, gated by read-only checks and an exclusive ledger."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

PROFILE = "creditbridge-deployer"
REGION = "us-east-1"
CODE = "L-B99A9384"
VALUE = 102
ROLE = "AWSServiceRoleForServiceQuotas"
DIRECTORY = Path("evidence/quota-102")
CHECKS = {}


def aws(service, operation, *parameters):
    allowed = {
        ("sts", "get-caller-identity"),
        ("iam", "get-user"),
        ("iam", "get-role"),
        ("iam", "simulate-principal-policy"),
        ("service-quotas", "get-service-quota"),
        ("service-quotas", "list-requested-service-quota-change-history-by-quota"),
        ("service-quotas", "request-service-quota-increase"),
        ("service-quotas", "get-requested-service-quota-change"),
    }
    if (service, operation) not in allowed:
        raise ValueError("Operation outside owner authorization")
    env = os.environ.copy()
    env.update(
        AWS_MAX_ATTEMPTS="1",
        AWS_RETRY_MODE="standard",
        AWS_PAGER="",
        AWS_EC2_METADATA_DISABLED="true",
    )
    command = [
        "aws",
        "--profile",
        PROFILE,
        "--region",
        REGION,
        "--no-cli-pager",
        "--output",
        "json",
        "--cli-connect-timeout",
        "3",
        "--cli-read-timeout",
        "15",
        service,
        operation,
        *parameters,
    ]
    result = subprocess.run(
        command, env=env, capture_output=True, text=True, check=False, timeout=35
    )
    if result.returncode:
        code = re.search(r"An error occurred \(([A-Za-z0-9_.-]+)\)", result.stderr)
        reason = code.group(1) if code else "CLI_OR_NETWORK_ERROR"
        raise RuntimeError(f"{service}:{operation}: {reason}")
    return json.loads(result.stdout)


def preflight():
    identity = aws("sts", "get-caller-identity")
    account, arn = identity["Account"], identity["Arn"]
    if (
        not re.fullmatch(r"[0-9]{12}", account)
        or ":user/" not in arn
        or arn.endswith(":root")
    ):
        raise ValueError("Unexpected identity; no request permitted")
    user = aws("iam", "get-user")["User"]
    if user["Arn"] != arn or user["UserId"] != identity["UserId"]:
        raise ValueError("Caller identity mismatch")
    quota = aws(
        "service-quotas",
        "get-service-quota",
        "--service-code",
        "lambda",
        "--quota-code",
        CODE,
    )["Quota"]
    if (
        quota["QuotaCode"] != CODE
        or quota["ServiceCode"] != "lambda"
        or quota["QuotaName"] != "Concurrent executions"
        or quota["GlobalQuota"]
        or not quota["Adjustable"]
        or f":{REGION}:{account}:lambda/{CODE}" not in quota["QuotaArn"]
    ):
        raise ValueError("Account, region or quota mismatch")
    summary = {
        "profile": PROFILE,
        "region": REGION,
        "account_match_verified_internally": True,
        "caller": "non_root_iam_user",
        "quota_code": CODE,
        "current_value": quota["Value"],
        "requested_value": VALUE,
    }
    CHECKS.update(summary)
    # A missing role MUST NOT be created implicitly by RequestServiceQuotaIncrease.
    role = aws("iam", "get-role", "--role-name", ROLE)["Role"]
    if (
        f"::{account}:role/aws-service-role/servicequotas.amazonaws.com/{ROLE}"
        not in role["Arn"]
        or "servicequotas.amazonaws.com"
        not in json.dumps(role["AssumeRolePolicyDocument"])
    ):
        raise ValueError("Existing Service Quotas role identity/trust mismatch")
    summary["service_linked_role_already_exists"] = True
    CHECKS.update(summary)
    permission = aws(
        "iam",
        "simulate-principal-policy",
        "--policy-source-arn",
        arn,
        "--action-names",
        "servicequotas:RequestServiceQuotaIncrease",
        "--resource-arns",
        quota["QuotaArn"],
    )
    rows = permission.get("EvaluationResults", [])
    if (
        len(rows) != 1
        or rows[0]["EvalDecision"] != "allowed"
        or rows[0].get("MissingContextValues")
    ):
        raise ValueError("Quota request permission unverified; no IAM change permitted")
    history = aws(
        "service-quotas",
        "list-requested-service-quota-change-history-by-quota",
        "--service-code",
        "lambda",
        "--quota-code",
        CODE,
    )
    if quota["Value"] >= VALUE:
        raise ValueError("Requested capacity already available; do not submit")
    if any(
        row.get("DesiredValue", 0) >= VALUE
        and row["Status"] in ("PENDING", "CASE_OPENED", "APPROVED")
        for row in history.get("RequestedQuotas", [])
    ):
        raise ValueError("Existing pending/approved request; do not submit another")
    return summary


def submit_once(summary, directory=DIRECTORY):
    directory.mkdir(parents=True, exist_ok=True)
    ledger = directory / "submission-attempt.json"
    # Record the attempt BEFORE sending. Ambiguous outcomes never trigger another submission.
    with ledger.open("x") as handle:
        json.dump(
            {**summary, "status": "SUBMISSION_ATTEMPT_STARTED", "automatic_retries": 0},
            handle,
            indent=2,
        )
    outcome = {
        **summary,
        "status": "UNKNOWN",
        "automatic_retries": 0,
        "request_attempts": 1,
        "deployment_authorized": False,
    }
    try:
        value = aws(
            "service-quotas",
            "request-service-quota-increase",
            "--service-code",
            "lambda",
            "--quota-code",
            CODE,
            "--desired-value",
            str(VALUE),
        )["RequestedQuota"]
        if value["QuotaCode"] != CODE or value["DesiredValue"] != VALUE:
            raise ValueError("Unexpected request response; do not retry")
        outcome.update(request_id=value["Id"], status=value["Status"])
    except Exception as exc:  # noqa: BLE001 - preserve one-attempt outcome, never retry a mutation.
        outcome["error_type"] = type(exc).__name__
        outcome["reason"] = (
            str(exc)
            if isinstance(exc, (ValueError, RuntimeError))
            else "Response not verified"
        )
    finally:
        ledger.write_text(json.dumps(outcome, indent=2) + "\n")
    return outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submit-once", action="store_true")
    args = parser.parse_args()
    CHECKS.clear()
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    if (DIRECTORY / "submission-attempt.json").exists():
        raise SystemExit(
            "Submission ledger already exists. No additional request will be sent."
        )
    try:
        summary = preflight()
    except Exception as exc:  # noqa: BLE001 - no credential/identifier-bearing CLI output.
        result = {
            **CHECKS,
            "status": "BLOCKED_BEFORE_SUBMISSION",
            "region": REGION,
            "quota_code": CODE,
            "requested_value": VALUE,
            "request_attempts": 0,
            "reason": str(exc)
            if isinstance(exc, (ValueError, RuntimeError))
            else type(exc).__name__,
        }
        (DIRECTORY / "preflight.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return 1
    (DIRECTORY / "preflight.json").write_text(json.dumps(summary, indent=2) + "\n")
    result = (
        submit_once(summary)
        if args.submit_once
        else {**summary, "status": "PREFLIGHT_ONLY"}
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] not in ("UNKNOWN", "BLOCKED_BEFORE_SUBMISSION") else 1


if __name__ == "__main__":
    raise SystemExit(main())
