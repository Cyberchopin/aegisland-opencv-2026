import importlib.util
from pathlib import Path

import pytest


def load_script():
    path = Path(__file__).parents[1] / "scripts/request_lambda_quota_102.py"
    spec = importlib.util.spec_from_file_location("quota_request", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_service_linked_role_stops_before_request(monkeypatch):
    module = load_script()
    account = "1" * 12
    arn = f"arn:aws:iam::{account}:user/mock-owner-approved-user"
    calls = []

    def fake_aws(service, operation, *_args):
        calls.append((service, operation))
        if operation == "get-caller-identity":
            return {"Account": account, "Arn": arn, "UserId": "mock-user"}
        if operation == "get-user":
            return {"User": {"Arn": arn, "UserId": "mock-user"}}
        if operation == "get-service-quota":
            return {
                "Quota": {
                    "QuotaCode": module.CODE,
                    "ServiceCode": "lambda",
                    "QuotaName": "Concurrent executions",
                    "GlobalQuota": False,
                    "Adjustable": True,
                    "Value": 10,
                    "QuotaArn": f"arn:aws:servicequotas:us-east-1:{account}:lambda/{module.CODE}",
                }
            }
        if operation == "get-role":
            raise RuntimeError("iam:get-role: NoSuchEntity")
        raise AssertionError("No other AWS operation allowed after missing role")

    monkeypatch.setattr(module, "aws", fake_aws)
    with pytest.raises(RuntimeError, match="NoSuchEntity"):
        module.preflight()
    assert module.CHECKS["current_value"] == 10
    assert not any(
        operation == "request-service-quota-increase" for _, operation in calls
    )


def test_exclusive_ledger_allows_only_one_submission(monkeypatch, tmp_path):
    module = load_script()
    calls = []

    def fake_aws(service, operation, *_args):
        calls.append((service, operation))
        return {
            "RequestedQuota": {
                "QuotaCode": module.CODE,
                "DesiredValue": 102,
                "Id": "mock-request-only",
                "Status": "PENDING",
            }
        }

    monkeypatch.setattr(module, "aws", fake_aws)
    assert module.submit_once({"requested_value": 102}, tmp_path)["status"] == "PENDING"
    with pytest.raises(FileExistsError):
        module.submit_once({"requested_value": 102}, tmp_path)
    assert len(calls) == 1


def test_timeout_does_not_retry_or_release_ledger(monkeypatch, tmp_path):
    module = load_script()
    calls = []

    def fake_aws(*args):
        calls.append(args)
        raise TimeoutError("ambiguous mock response")

    monkeypatch.setattr(module, "aws", fake_aws)
    assert module.submit_once({}, tmp_path)["status"] == "UNKNOWN"
    with pytest.raises(FileExistsError):
        module.submit_once({}, tmp_path)
    assert len(calls) == 1
