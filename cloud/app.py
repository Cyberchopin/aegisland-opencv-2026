"""SAM Lambda entry point; clients are constructed only on invocation."""

import os

from competition_cloud.storage import ingest


def handler(event, _context):
    import boto3
    from botocore.config import Config

    config = Config(
        connect_timeout=1,
        read_timeout=2,
        retries={"total_max_attempts": 1, "mode": "standard"},
    )
    return ingest(
        event,
        boto3.client("s3", config=config),
        boto3.resource("dynamodb", config=config).Table(os.environ["TRACE_TABLE"]),
        os.environ["EVIDENCE_BUCKET"],
    )
