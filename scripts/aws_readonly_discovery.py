#!/usr/bin/env python3
"""Owner-authorized, redacted control-plane discovery; no mutations or data-plane reads."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

PROFILE = "creditbridge-deployer"
REGION = "us-east-1"
STACK = "aegisland-opencv26-evidence"
ALLOWED = {
    ("sts", "get-caller-identity"),
    ("iam", "get-user"),
    ("iam", "list-attached-user-policies"),
    ("iam", "list-user-policies"),
    ("iam", "get-user-policy"),
    ("iam", "get-policy"),
    ("iam", "get-policy-version"),
    ("iam", "simulate-principal-policy"),
    ("iam", "get-account-summary"),
    ("cloudformation", "list-stacks"),
    ("cloudformation", "describe-stacks"),
    ("lambda", "get-account-settings"),
    ("lambda", "list-functions"),
    ("apigatewayv2", "get-apis"),
    ("dynamodb", "list-tables"),
    ("logs", "describe-log-groups"),
    ("service-quotas", "list-service-quotas"),
    ("budgets", "describe-budgets"),
    ("budgets", "describe-notifications-for-budget"),
    ("budgets", "describe-subscribers-for-notification"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Refuse replacement before any credential use or AWS request.
    with args.output.open("x") as handle:
        handle.write("{}\n")
    result = {
        "mode": "owner_authorized_readonly_control_plane",
        "region": REGION,
        "proposed_stack": STACK,
        "calls": [],
        "raw_responses_retained": False,
        "other_profiles_used": False,
        "mutations": 0,
        "data_plane_requests": 0,
    }
    env = os.environ.copy()
    env.update(
        AWS_MAX_ATTEMPTS="1",
        AWS_RETRY_MODE="standard",
        AWS_PAGER="",
        AWS_EC2_METADATA_DISABLED="true",
    )

    def persist():
        args.output.write_text(json.dumps(result, indent=2) + "\n")

    def call(service, operation, *parameters):
        if (service, operation) not in ALLOWED or len(result["calls"]) >= 80:
            raise ValueError("Read-only allowlist/call bound exceeded")
        command = [
            shutil.which("aws") or "aws",
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
            "5",
            service,
            operation,
            *parameters,
        ]
        try:
            response = subprocess.run(
                command,
                env=env,
                capture_output=True,
                text=True,
                check=False,
                timeout=15,
            )
        except subprocess.TimeoutExpired:
            result["calls"].append(
                {"service": service, "operation": operation, "status": "LOCAL_TIMEOUT"}
            )
            persist()
            return None
        entry = {
            "service": service,
            "operation": operation,
            "status": "PASS" if response.returncode == 0 else "UNVERIFIED",
        }
        if response.returncode:
            match = re.search(
                r"An error occurred \(([A-Za-z0-9_.-]+)\)", response.stderr
            )
            entry["error_code"] = match.group(1) if match else "CLI_OR_NETWORK_ERROR"
            if (
                service == "cloudformation"
                and operation == "describe-stacks"
                and "does not exist" in response.stderr
            ):
                entry["not_found"] = True
        result["calls"].append(entry)
        persist()
        return json.loads(response.stdout) if response.returncode == 0 else None

    try:
        version = subprocess.run(
            [shutil.which("aws") or "aws", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        result["cli_version"] = re.search(r"aws-cli/[0-9.]+", version.stdout).group(0)
        identity = call("sts", "get-caller-identity")
        if not identity:
            result["identity"] = "UNVERIFIED"
            return 1
        arn, account = identity["Arn"], identity["Account"]
        # Owner confirmed an IAM user; do not proceed under root or another caller type.
        if arn.endswith(":root") or ":user/" not in arn:
            result["identity"] = "UNEXPECTED_CALLER; stopped"
            return 1
        result["identity"] = {
            "account_identified_internally": True,
            "type": "non_root_iam_user",
        }
        user_name = arn.rsplit("/", 1)[-1]
        user = call("iam", "get-user")
        result["permissions_boundary_present"] = (
            bool(user["User"].get("PermissionsBoundary")) if user else "UNVERIFIED"
        )
        attached = call("iam", "list-attached-user-policies", "--user-name", user_name)
        inline = call("iam", "list-user-policies", "--user-name", user_name)
        policies = []
        for binding in (attached or {}).get("AttachedPolicies", [])[:10]:
            metadata = call("iam", "get-policy", "--policy-arn", binding["PolicyArn"])
            if metadata:
                document = call(
                    "iam",
                    "get-policy-version",
                    "--policy-arn",
                    binding["PolicyArn"],
                    "--version-id",
                    metadata["Policy"]["DefaultVersionId"],
                )
                if document:
                    policies.append(document["PolicyVersion"]["Document"])
        for name in (inline or {}).get("PolicyNames", [])[:10]:
            document = call(
                "iam",
                "get-user-policy",
                "--user-name",
                user_name,
                "--policy-name",
                name,
            )
            if document:
                policies.append(document["PolicyDocument"])
        statements = [
            s
            for p in policies
            for s in (
                p.get("Statement", [])
                if isinstance(p.get("Statement"), list)
                else [p["Statement"]]
            )
        ]
        result["caller_policy_summary"] = {
            "attached_count": len(attached["AttachedPolicies"])
            if attached
            else "UNVERIFIED",
            "inline_count": len(inline["PolicyNames"]) if inline else "UNVERIFIED",
            "documents_read": len(policies),
            "document_inspection_capped_at_ten_per_kind": True,
            "unconditional_allow_all_actions_all_resources": any(
                s.get("Effect") == "Allow"
                and s.get("Action") in ("*", ["*"])
                and s.get("Resource") in ("*", ["*"])
                and not s.get("Condition")
                for s in statements
            ),
            "policy_mentions_creditbridge": any(
                "creditbridge" in json.dumps(p).lower() for p in policies
            ),
            "policy_mentions_aegisland": any(
                "aegisland" in json.dumps(p).lower() for p in policies
            ),
            "effective_authority": "UNVERIFIED; simulations do not establish all effective controls",
        }
        scopes = {
            "cloudformation": (
                f"arn:aws:cloudformation:{REGION}:{account}:stack/{STACK}/*",
                [
                    "CreateStack",
                    "CreateChangeSet",
                    "DescribeStacks",
                    "ExecuteChangeSet",
                    "DeleteStack",
                ],
            ),
            "lambda": (
                f"arn:aws:lambda:{REGION}:{account}:function:{STACK}-evidence",
                [
                    "CreateFunction",
                    "GetFunction",
                    "AddPermission",
                    "PutFunctionConcurrency",
                    "DeleteFunction",
                ],
            ),
            "dynamodb": (
                f"arn:aws:dynamodb:{REGION}:{account}:table/{STACK}-TraceTable-UNRESOLVED",
                [
                    "CreateTable",
                    "GetItem",
                    "PutItem",
                    "UpdateContinuousBackups",
                    "UpdateTimeToLive",
                    "DeleteTable",
                ],
            ),
            "iam": (
                f"arn:aws:iam::{account}:role/{STACK}-EvidenceRole-UNRESOLVED",
                ["CreateRole", "PutRolePolicy", "PassRole", "DeleteRole"],
            ),
            "s3": (
                f"arn:aws:s3:::{STACK}-evidencebucket-unresolved/evidence/example.json",
                ["GetObject", "PutObject", "DeleteObject"],
            ),
            "apigateway": (
                f"arn:aws:apigateway:{REGION}::/apis",
                ["POST", "GET", "DELETE"],
            ),
        }
        simulations = {}
        for service, (resource, actions) in scopes.items():
            values = call(
                "iam",
                "simulate-principal-policy",
                "--policy-source-arn",
                arn,
                "--action-names",
                *[service + ":" + a for a in actions],
                "--resource-arns",
                resource,
            )
            simulations[service] = [
                {
                    "action": row["EvalActionName"],
                    "decision": row["EvalDecision"],
                    "missing_context_keys": row.get("MissingContextValues", []),
                }
                for row in (values or {}).get("EvaluationResults", [])
            ]
        result["permission_simulations"] = simulations
        result["simulation_limit"] = (
            "Illustrative unresolved names; not proof of deployability or organizational approval"
        )
        stacks = call("cloudformation", "list-stacks")
        active = [
            s
            for s in (stacks or {}).get("StackSummaries", [])
            if s["StackStatus"] != "DELETE_COMPLETE"
        ]
        result["stacks"] = {
            "active_count": len(active) if stacks else "UNVERIFIED",
            "names_withheld": True,
            "creditbridge_family_present": any(
                "creditbridge" in s["StackName"].lower() for s in active
            ),
        }
        proposed = call("cloudformation", "describe-stacks", "--stack-name", STACK)
        result["proposed_stack_collision"] = (
            True
            if proposed
            else False
            if result["calls"][-1].get("not_found")
            else "UNVERIFIED"
        )
        functions = call("lambda", "list-functions")
        result["lambda"] = {
            "function_count": len(functions["Functions"])
            if functions
            else "UNVERIFIED",
            "fixed_name_collision": any(
                f["FunctionName"] == STACK + "-evidence"
                for f in (functions or {}).get("Functions", [])
            )
            if functions
            else "UNVERIFIED",
        }
        settings = call("lambda", "get-account-settings")
        result["lambda_account_settings"] = settings if settings else "UNVERIFIED"
        apis = call("apigatewayv2", "get-apis")
        result["http_api_count"] = len(apis["Items"]) if apis else "UNVERIFIED"
        tables = call("dynamodb", "list-tables")
        result["table_count"] = len(tables["TableNames"]) if tables else "UNVERIFIED"
        groups = call(
            "logs",
            "describe-log-groups",
            "--log-group-name-prefix",
            "/aws/lambda/" + STACK + "-evidence",
        )
        result["fixed_log_group_collision"] = (
            bool((groups or {}).get("logGroups")) if groups else "UNVERIFIED"
        )
        summary = call("iam", "get-account-summary")
        result["iam_capacity"] = {
            k: v
            for k, v in (summary or {}).get("SummaryMap", {}).items()
            if k in ("Roles", "RolesQuota", "Policies", "PoliciesQuota")
        }
        quotas = {}
        for service in (
            "lambda",
            "apigateway",
            "dynamodb",
            "s3",
            "cloudformation",
            "iam",
        ):
            values = call(
                "service-quotas", "list-service-quotas", "--service-code", service
            )
            quotas[service] = [
                {
                    "name": q["QuotaName"],
                    "value": q["Value"],
                    "adjustable": q["Adjustable"],
                }
                for q in (values or {}).get("Quotas", [])
            ]
        result["service_quotas"] = quotas
        budgets = call("budgets", "describe-budgets", "--account-id", account)
        notifications, subscribers = 0, 0
        for budget in (budgets or {}).get("Budgets", [])[:5]:
            notes = call(
                "budgets",
                "describe-notifications-for-budget",
                "--account-id",
                account,
                "--budget-name",
                budget["BudgetName"],
            )
            for notification in (notes or {}).get("Notifications", []):
                notifications += 1
                recipients = call(
                    "budgets",
                    "describe-subscribers-for-notification",
                    "--account-id",
                    account,
                    "--budget-name",
                    budget["BudgetName"],
                    "--notification",
                    json.dumps(notification),
                )
                subscribers += len((recipients or {}).get("Subscribers", []))
        result["budgets"] = {
            "count": len(budgets["Budgets"]) if budgets else "UNVERIFIED",
            "notifications_observed": notifications,
            "subscribers_observed": subscribers,
            "budget_inspection_limit": 5,
            "values_and_recipients_withheld": True,
            "project_suitability": "UNVERIFIED; owner review needed",
        }
        result["status"] = "DISCOVERY_COMPLETE_WITH_UNVERIFIED_GATES"
        return 0
    finally:
        persist()
        print(
            json.dumps(
                {
                    "report": str(args.output),
                    "region": REGION,
                    "status": result.get("status", "INCOMPLETE"),
                    "identity": result.get("identity", "UNVERIFIED"),
                    "readonly_cli_operations": len(result["calls"]),
                    "mutations": 0,
                    "data_plane_requests": 0,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    raise SystemExit(main())
