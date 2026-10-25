#!/usr/bin/env python3
"""Transform the local SAM template with network access disabled; retain security scope."""

import argparse
import hashlib
import json
import os
import socket
from pathlib import Path
from types import SimpleNamespace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.environ["AWS_EC2_METADATA_DISABLED"] = "true"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    import botocore.endpoint
    from samtranslator.translator.transform import transform
    from samtranslator.yaml_helper import yaml_parse

    def forbidden(*_args, **_kwargs):
        raise RuntimeError(
            "Network access forbidden during offline template inspection"
        )

    socket.create_connection = forbidden
    botocore.endpoint.Endpoint._send = forbidden
    source = Path("infra/template.yaml").read_bytes()
    template = yaml_parse(source.decode())
    # The translator requires a packaged URI; this placeholder is never uploaded/read.
    template["Resources"]["EvidenceFunction"]["Properties"]["CodeUri"] = {
        "Bucket": "offline-placeholder",
        "Key": "not-uploaded.zip",
    }
    translated = transform(template, {}, SimpleNamespace(load=dict))
    resources = translated["Resources"]
    api = resources["EvidenceApi"]["Properties"]["Body"]
    route = api["paths"]["/evidence"]["post"]
    permissions = {
        name: value["Properties"]
        for name, value in resources.items()
        if value["Type"] == "AWS::Lambda::Permission"
    }
    assert route["security"] == [{"AWS_IAM": []}]
    assert len(permissions) == 1
    permission = next(iter(permissions.values()))
    assert permission["Principal"] == "apigateway.amazonaws.com"
    assert "EvidenceApi" in json.dumps(permission["SourceArn"])
    result = {
        "mode": "offline_translation_only",
        "aws_service_calls": 0,
        "template_sha256": hashlib.sha256(source).hexdigest(),
        "code_uri_substitution": "offline placeholder only; no package upload",
        "transformed_resources": {
            name: value["Type"] for name, value in resources.items()
        },
        "post_evidence_security": route["security"],
        "security_schemes": api["components"]["securitySchemes"],
        "lambda_invocation_permissions": permissions,
        "execution_role": resources["EvidenceRole"]["Properties"],
        "bucket_policy": resources["EvidenceBucketPolicy"]["Properties"][
            "PolicyDocument"
        ],
        "retained_resources": [
            name
            for name, value in resources.items()
            if value.get("DeletionPolicy") == "Retain"
        ],
        "status": "PASS",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
