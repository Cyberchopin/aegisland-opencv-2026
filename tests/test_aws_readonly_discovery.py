import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


def load_script():
    path = Path(__file__).parents[1] / "scripts/aws_readonly_discovery.py"
    spec = importlib.util.spec_from_file_location("readonly_discovery", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_discovery_stays_within_profile_read_allowlist_and_redacts_identity(
    monkeypatch, tmp_path
):
    module = load_script()
    account = "1" * 12
    calls = []
    fixtures = {
        ("sts", "get-caller-identity"): {
            "Account": account,
            "Arn": f"arn:aws:iam::{account}:user/private-user",
        },
        ("iam", "get-user"): {"User": {}},
        ("iam", "list-attached-user-policies"): {"AttachedPolicies": []},
        ("iam", "list-user-policies"): {"PolicyNames": []},
        ("iam", "simulate-principal-policy"): {"EvaluationResults": []},
        ("cloudformation", "list-stacks"): {"StackSummaries": []},
        ("lambda", "list-functions"): {"Functions": []},
        ("lambda", "get-account-settings"): {
            "AccountLimit": {"ConcurrentExecutions": 10}
        },
        ("apigatewayv2", "get-apis"): {"Items": []},
        ("dynamodb", "list-tables"): {"TableNames": []},
        ("logs", "describe-log-groups"): {"logGroups": []},
        ("iam", "get-account-summary"): {"SummaryMap": {}},
        ("service-quotas", "list-service-quotas"): {"Quotas": []},
        ("budgets", "describe-budgets"): {"Budgets": []},
    }

    def fake_run(command, **kwargs):
        if command[-1] == "--version":
            return subprocess.CompletedProcess(command, 0, "aws-cli/2.38.4", "")
        assert command[1:5] == [
            "--profile",
            "creditbridge-deployer",
            "--region",
            "us-east-1",
        ]
        assert kwargs["env"]["AWS_MAX_ATTEMPTS"] == "1"
        operation = tuple(command[12:14])
        assert operation in module.ALLOWED
        calls.append(operation)
        if operation == ("cloudformation", "describe-stacks"):
            return subprocess.CompletedProcess(command, 255, "", "stack does not exist")
        return subprocess.CompletedProcess(
            command, 0, json.dumps(fixtures[operation]), ""
        )

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module.shutil, "which", lambda _: "/mock/aws")
    output = tmp_path / "report.json"
    monkeypatch.setattr(
        __import__("sys"), "argv", ["discovery", "--output", str(output)]
    )
    assert module.main() == 0
    text = output.read_text()
    assert account not in text and "private-user" not in text
    result = json.loads(text)
    assert result["mutations"] == result["data_plane_requests"] == 0
    assert all(pair in module.ALLOWED for pair in calls)
    assert result["proposed_stack_collision"] is False


@pytest.mark.parametrize("caller", ["root", "assumed-role"])
def test_unexpected_identity_stops_all_further_discovery(monkeypatch, tmp_path, caller):
    module = load_script()
    calls = []

    def fake_run(command, **_kwargs):
        if command[-1] == "--version":
            return subprocess.CompletedProcess(command, 0, "aws-cli/2.38.4", "")
        calls.append(tuple(command[12:14]))
        arn = "arn:aws:iam::" + "1" * 12 + ":" + caller
        return subprocess.CompletedProcess(
            command, 0, json.dumps({"Account": "1" * 12, "Arn": arn}), ""
        )

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module.shutil, "which", lambda _: "/mock/aws")
    output = tmp_path / "report.json"
    monkeypatch.setattr(
        __import__("sys"), "argv", ["discovery", "--output", str(output)]
    )
    assert module.main() == 1
    assert calls == [("sts", "get-caller-identity")]
    assert json.loads(output.read_text())["identity"].startswith("UNEXPECTED_CALLER")
