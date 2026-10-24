# AWS deployment gate — A2

**Quota-only authorization update:** the authorized request to 102 was not submitted: preflight found `AWSServiceRoleForServiceQuotas` absent. Role creation is forbidden, so the request stopped with zero submission attempts and no request ID. No deployment authority follows from the quota authorization, even if a future separately authorized request succeeds.

**A3 override:** the owner subsequently authorized only read-only discovery using the verified non-root profile in us-east-1. Discovery completed; no mutation, billed call or deployment was authorized. The Lambda concurrency quota of ten blocks the current reservation of two. [AWS_OWNER_APPROVAL.md](AWS_OWNER_APPROVAL.md) and [preflight results](AWS_PREFLIGHT_RESULTS.md) contain the current blockers, scoped actions, cost model and teardown approvals; they supersede A2's proposed readiness status and approval scope.

**Ready for owner review of a scoped deployment candidate; NOT authorized to deploy.** The competition implementation passes local failure tests and offline template validation. Deployment execution still requires the prerequisites below. No AWS account was queried, no credentials were changed, and no AWS service calls or deployment were performed in A2.

Use this repository's `infra/template.yaml` and `cloud/` sources. Do not deploy the original core template or run `.baseline/core/scripts/deploy_aws.sh`: its reliability bugs remain, and current SAM translation rejects its IAM authorizer configuration. The new `/v1/evidence` packet API is incompatible with the original `/v1/traces` client. Keep `AEGISLAND_TRACE_ENDPOINT` disabled for simulation.

## Gate status

| Status | Requirement |
| --- | --- |
| PASS | 60 mocked AWS tests, five A1 competition tests and 56 targeted core regressions |
| PASS | Runtime/test dependencies pinned; validator isolated and fully pinned |
| PASS | Offline SAM translation/schema lint, explicit IAM authorization flag and resource-scoped Lambda role |
| PASS | Local evidence plans validate original hashes and complete file reconstruction |
| PASS | Simulation runs without cloud upload; source policy and core pin unchanged |
| PASS | Local SAM CLI 1.145.0 build targeting Python 3.12 Arm64; staged dependency imports and source hashes checked on host Python 3.12 |
| UNVERIFIED | Target AWS account, commercial region, available Lambda concurrency, service permissions, regional service pricing and budget controls |
| UNVERIFIED | Deployed IAM enforcement, Arm64 runtime execution, real acknowledgements, consistency recovery, storage readback and cleanup |
| REQUIRED | Explicit owner authorization for the specific account, region, new stack, spending limit and calls below |

## Complete before executing a deployment

1. Review and pin the competition commit/source inventory with the owner. The current branch is `codex-a/stage-a1-baseline`, based on `4ba11c1781e51b6822a8bc329080fe903258fba4`; A1/A2 changes are local and uncommitted. Core remains pinned to `eda23d3ea646e8943287703c07a91e9a3b2909fb`.
2. Owner selects a **new** stack name, account ID, approved profile/role and commercial AWS region. The current uploader supports regional `execute-api.<region>.amazonaws.com` endpoints only. No reuse or migration of an existing core stack is planned. Confirm naming length and resource/concurrency quotas.
3. Agree a dollar ceiling, alert recipient, test window, maximum upload volume and stop conditions. Activate and verify the budget/alerts before deployment. A budget alert, rate limit and reserved concurrency are not hard cost caps.
4. Review CloudFormation deployment permissions and `iam:PassRole`. The deployed Lambda role is limited to S3 GET/PUT on its evidence prefix, DynamoDB GET/PUT on its table and log writes. Give the uploading identity only `execute-api:Invoke` for `POST /v1/evidence`; use a separately approved read-only auditing identity for storage verification. No anonymous or public object access is planned.
5. Verify the reviewed revision against the local SAM build and package hash inventory. A2 built with SAM CLI 1.145.0 and pinned runtime dependencies, and smoke-imported the package on host Python 3.12. Rebuild after any source changes, using `requirements-sam-lock.txt` in an isolated environment, telemetry disabled and `__SAM_CLI_APP_DIR` pointing into the workspace. Re-run the recorded offline lint, tests and package-import checks. Actual Lambda Arm64 execution remains unverified.
6. Inspect the resolved deployment changeset before execution. Confirm new resources only, IAM-authorized HTTP route, private encrypted bucket, conditional-write/TLS policy, on-demand encrypted table with TTL/PITR, Python 3.12 Arm64 Lambda (256 MB, timeout 25 s, concurrency two), API rate one/second, and 14-day Lambda logs. Account-specific permissions and generated resource behavior remain unverified until deployment checks.

## Concrete approval scope

Ask the owner to approve values for: account ID; profile/role; region; new stack name; dollar ceiling and alert recipient; expiration/cleanup date; and whether the following phases are authorized together or separately:

- Identity/quota/budget checks and changeset creation, including SAM packaging/staging S3 uploads and IAM resource creation.
- Changeset execution for this reviewed competition stack.
- One nominal evidence bundle (15 packets), followed by a second identical upload to test duplicates. Up to three HTTP attempts per packet means at most 90 POST attempts across those two invocations; each handler can issue up to four storage operations. Do not automatically upload all scenarios.
- One unsigned request to confirm denial, followed by signed requests and approved read-only S3/DynamoDB inspection to compare actual bytes and index checksums.
- Optional controlled interruption of the uploader process and restart using the same immutable bundle. No production resource corruption, policy changes or destructive storage fault injection is proposed.

No deployment or upload command has been executed. An approval for deployment does not implicitly authorize broader experiments, repeated upload loops, public hosting or changes to the safety policy.

After approval, the existing uploader interface is:

```bash
# Live, billable path. Run only within the owner's approved scope.
.venv/bin/python scripts/evidence_cloud.py \
  --evidence evidence/a1/final/nominal --output runs/approved-live-nominal \
  --upload --endpoint https://APPROVED_API.execute-api.APPROVED_REGION.amazonaws.com/v1 \
  --region APPROVED_REGION
```

The profile must be selected outside the repository through the approved credential mechanism. Use a fresh output directory. A missing/mismatched acknowledgement produces `incomplete` and a nonzero exit code; even a verified HTTP receipt must be cross-checked against actual storage for the deployment acceptance record. Do not place credentials in argv, documentation, artifacts or Git.

## Acceptance after an authorized deployment

Retain stack ID, source commit/hash, template/build hashes, SDK/SAM versions, region, resolved route authorization and approved resource identifiers. Verify that unsigned or unauthorized requests are denied. For the nominal bundle, require 15 matching packet acknowledgements, matching strongly consistent index reads, and actual S3 body checksums. Reconstruct all eight artifacts plus the inventory and compare them byte-for-byte with the local plan. Repeat the same upload: object/index identity must remain unchanged and every acknowledgement must still be verified.

Record timeouts and retry counts as observed, not inferred from configuration. Stop on conflicting storage, missing bytes, authorization failure, unexpected resources, ceiling breach or unverifiable receipt. Keep partial local receipts and the immutable source evidence. A failed deployment/upload does not satisfy the competition AWS gate.

The bucket and table use `Retain`; deleting the stack does not remove their data or stop all storage/PITR charges. Packaging buckets and retained resources also need an owner-approved cleanup plan. No cleanup or destructive action is authorized by A2. Preserve receipts before any approved cleanup, and finish this verification before the October 25 engineering freeze where possible.
