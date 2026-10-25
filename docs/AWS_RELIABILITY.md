# AWS evidence reliability — A2

The core backend can acknowledge a duplicate trace while S3 has no trace object. Its client also ignores HTTP error responses. A2 reproduces those failures and provides a separate competition evidence service; it does not patch the pinned core or its safety policy.

Assessment: October 22, 2026. **Local tests and template validation pass. AWS deployment and storage remain UNVERIFIED.** All AWS service interactions in tests use deterministic fakes or SDK Stubber. A local upload plan is not a cloud receipt.

## What inspection found

| Existing core behavior | Failure | Competition implementation |
| --- | --- | --- |
| DynamoDB write before S3; duplicate short-circuit | Failed S3 PUT followed by retry returns `duplicate_ignored` with no object | Conditional S3 write, actual byte readback, conditional index write, strongly consistent index readback |
| HTTP response ignored | 403/500 does not create a cloud failure record | Only an exact, identity/checksum-bound HTTP 200 acknowledgement is accepted |
| No explicit socket timeout/retry contract | Latency and retry outcome unclear | Explicit SDK/socket timeouts, at most three HTTP attempts per packet, bounded backoff |
| Index and S3 contents not compared | Duplicate IDs can hide differing payloads | Conflicting bytes or index values return 409; no overwrite or successful receipt |
| Upload occurs during each simulated step | Network work can delay the agent | Uploader runs separately against completed immutable local evidence |
| HTTP API IAM configuration incomplete | Current SAM translator rejects the original template | Competition template sets `EnableIamAuthorizer: true` and default `AWS_IAM` |

The original-core reproduction tests pass by demonstrating the defects; that does not mean the original backend is reliable. Do not use the core deploy script or `/traces` client for competition cloud verification.

## Evidence and acknowledgement contract

`scripts/evidence_cloud.py` reads the eight known A1 artifact names, verifies their provenance hashes and rejects symlinks, missing files, non-PASS runs and bundles larger than 64 MiB. It leaves source artifacts unchanged. It generates an inventory and deterministic bundle identity, then divides files into at most 128 KiB raw chunks. The canonical packet includes bundle ID, sequence, filename, part position/count, file SHA-256, chunk SHA-256 and base64 bytes. A separate inventory packet binds all filenames, sizes, checksums and the recorded core commit.

`cloud/competition_cloud/protocol.py` defines `aegis-evidence-v1`. Requests are limited to 256,000 decoded JSON bytes and 4,096 possible packet sequence values. The client checks complete artifact reconstruction and inventory hashes before transmitting. This protocol is intentionally separate from the original core trace API.

For each valid packet, `storage.ingest`:

1. Writes canonical packet bytes to `evidence/<bundle-id>/<sequence>.json` with `IfNoneMatch: *`.
2. On an existing object, reads it rather than treating existence as success. It hashes the actual bounded response body; metadata and ETags alone are insufficient.
3. Rejects different bytes with 409. Otherwise conditionally inserts a DynamoDB index containing identity, object key, payload hash, completion flag and expiry.
4. Reads the index with `ConsistentRead=True` and compares identity/key/checksum/completion. Only then returns `stored_verified`, bundle ID, sequence, object key and the canonical payload checksum.

Transient service exceptions and timeouts return 503, never a storage success. Conditional write conflicts are resolved by checking stored content. A retry after a committed write with a lost response repeats the verification. An orphan object can acquire its missing index; a missing object with a matching existing index can be recreated and verified. Corrupt/conflicting objects are preserved for investigation and rejected.

The S3 condition follows [AWS conditional-write documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html). The template also denies nonconditional object writes to this prefix and denies insecure transport. [SAM's HTTP API IAM configuration](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-httpapi-httpapiauth.html) requires explicitly enabling the IAM authorizer.

## Retry and failure semantics

| Layer | Bound / behavior |
| --- | --- |
| Lambda SDK | Connect timeout 1 s, read timeout 2 s, `total_max_attempts=1`; no hidden SDK retries |
| Lambda | Timeout 25 s; reserved concurrency 2 |
| HTTP client | Socket timeout 27 s; SigV4 service `execute-api`, explicit region and regional HTTPS endpoint |
| Uploader | At most three attempts per packet; 0.25 s then 0.5 s retry waits; one-second spacing between acknowledged packets |
| Retryable | Transport connection/read failures; HTTP 429/500/502/503/504; missing or malformed 2xx acknowledgement |
| Terminal | Other HTTP failures, including 400/401/403/404/409/413; unexpected transport/configuration failures |
| Partial bundle | Stops at the first unacknowledged packet, returns `incomplete`, retains completed acknowledgements and attempt outcomes |
| Restart | Replays the same deterministic packets; does not skip entries based on old local receipts |

Socket timeouts are bounds on network operations, not a strict total wall-clock deadline under every DNS, credential-provider or slow-stream behavior. There is no infinite application retry loop. A new CLI invocation is a new owner-controlled attempt; repeated invocations are not automatically scheduled. API throttling is one request/second with a burst of two; it is not a spending cap.

The CLI writes `receipts.json` in its finalization path for an attempted live upload; exceptions leave it `incomplete` and cause a nonzero process exit. Overall `stored_verified` requires a matching acknowledgement for every locally reconstructed packet. Local-only preparation writes `plan.json` and `packets.jsonl`, prints `local_plan_only`, and never creates a receipt or constructs an AWS transport.

## Actual verification

| Check | Result | Retained evidence |
| --- | --- | --- |
| AWS reliability tests | PASS, 60 tests | `evidence/a2/aws-tests.json`, `aws-tests.xml` |
| All competition tests | PASS, 65 tests including five A1 tests | `evidence/a2/final-tests.json` |
| Targeted core regression | PASS, 56 tests | `evidence/a2/core-regression.json` |
| Python lint | PASS | `evidence/a2/lint.json` |
| Competition SAM translation/schema lint | PASS after IAM flag correction | `evidence/a2/template-lint-corrected.json` |
| Local SAM build targeting Python 3.12 Arm64 | PASS; SAM CLI 1.145.0 | `evidence/a2/sam-build-final.json` |
| Staged package smoke import and source hashes | PASS; pinned SDK versions, five matching source modules, no native shared objects | `evidence/a2/package-smoke-final.json`, `lambda-build-hashes-final.json` |
| Original core SAM template | FAIL with current translator; preserved unchanged | `evidence/a2/original-template-lint.json` |
| Fresh GPS/low-light simulation | PASS, 80 events and decoded frames | `evidence/a2/regression/gps_loss_low_light/` |
| AWS execution, real IAM denial, real storage receipts | UNVERIFIED | No AWS service calls made |

The tests cover failures before/after S3 and DynamoDB writes, read failures, exact duplicates, identity conflicts, missing/corrupt object state, corrupt index state, lost acknowledgement after commit, terminal/retryable HTTP failures, bounded retries, malformed/mismatched acknowledgements, partial bundles, payload validation, content tampering, client timeouts/signing and Lambda SDK configuration. Stubber validates real S3 and DynamoDB parameter/response contracts without service access.

All three actual A1 bundles are reconstructed from mocked S3 packet bytes and compared byte-for-byte against the original files. Their deterministic plans contain 15 packets (nominal), 22 (intrusion) and 17 (GPS/low light): 54 total, with no cloud success inferred. A successful first-attempt delivery of these plans would involve 54 HTTP/Lambda invocations, 108 S3 requests and 108 DynamoDB requests; retries and subsequent receipt audits add calls. This is a request count, not a price estimate.

The first expanded tests passed 58/58; additional contract and regression cases raised the final count to 65. The initial template lint failed because the IAM flag was missing; both failure and correction are retained. The initial validator installation hit sandbox DNS restrictions; installation succeeded after approved network access. The validator lives in an isolated environment so its newer AWS dependencies do not replace the runtime/test lock.

The first local SAM build failed because the sandbox blocked dependency downloads and SAM's default home-directory metadata location was read-only. The corrected build used a workspace configuration directory, disabled telemetry, dummy credentials and approved dependency downloads. It succeeded without invoking Lambda or deploying. After a docstring clarification, a final build and package audit confirmed the final sources. The staged package imported the pinned Boto3/Botocore versions and matched all five source modules on host Python 3.12. This is packaging evidence, not execution on AWS Arm64. The final generated template also passed offline lint.

## Reproduce without AWS calls

```bash
.venv/bin/python -m pip install -r requirements-aws-test.txt
.venv/bin/python -m pytest -q tests
.venv/bin/ruff check cloud scripts tests
.venv/bin/python scripts/evidence_cloud.py \
  --evidence evidence/a1/final/nominal --output runs/a2-plan-nominal
python3 -m venv .baseline/cfn-venv
.baseline/cfn-venv/bin/python -m pip install -r requirements-template-lock.txt
AWS_EC2_METADATA_DISABLED=true AWS_DEFAULT_REGION=us-east-1 \
  .baseline/cfn-venv/bin/cfn-lint -t infra/template.yaml
python3 -m venv .baseline/sam-venv
.baseline/sam-venv/bin/python -m pip install -r requirements-sam-lock.txt
SAM_CLI_TELEMETRY=0 __SAM_CLI_APP_DIR="$PWD/.baseline/sam-config" \
  AWS_EC2_METADATA_DISABLED=true AWS_DEFAULT_REGION=us-east-1 \
  AWS_ACCESS_KEY_ID=local-build-only AWS_SECRET_ACCESS_KEY=local-build-only \
  .baseline/sam-venv/bin/sam build --template-file infra/template.yaml \
  --build-dir .baseline/sam-final --cache-dir .baseline/sam-cache
```

The competition CI now includes the AWS tests and an isolated template-validation/SAM-build job. It remains UNVERIFIED on GitHub because nothing was pushed. Full dependency snapshots, commands, stdout/stderr and exit statuses are retained under `evidence/a2/`; SAM tooling is pinned separately in `requirements-sam-lock.txt`.

## Limits and deployment handoff

S3 and DynamoDB do not form one transaction. Receipts certify the content observed during verification, not permanent availability: external administrators, lifecycle expiry or later service failures can change it. The Lambda role cannot delete or overwrite evidence; corruption returns a conflict rather than an automatic destructive repair. There is no server-side bundle completion flag or hosted evidence browser; the client receipt ledger and inventory establish completeness, and a deployed readback audit must confirm reconstruction.

No real IAM permissions, account quotas, Lambda execution on Arm64, endpoint, latency, spend or storage behavior have been verified. Local tests cannot substitute for those checks. Deployment prerequisites and the exact approval scope are in [AWS_DEPLOYMENT_GATE.md](AWS_DEPLOYMENT_GATE.md).
