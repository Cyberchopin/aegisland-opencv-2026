# Second Phase A — final offline hardening candidate, NOT AUTHORIZED

This supersedes the earlier b26ed5… correction as the proposed next code candidate; every prior artifact/report remains immutable. Neither this candidate nor any subsequent Change Set exists in AWS. The old Change Set UUID must never be executed again.

## Exact owner approval

> Authorize second Phase A only, using creditbridge-deployer in us-east-1, the privately configured AegisLand account/staging bucket, and stack aegisland-opencv26-evidence: revalidate account, bucket controls, completed prior teardown, artifact and nine-resource manifest; upload exactly once final-hardening-20261023-r2/function-artifact.zip with SHA-256 52e37629b1434e9a898448ddd5f63aa94ce367b1f552fdb5c082c92ea816aa39; create exactly one CREATE Change Set named aegisland-unreserved-hardening2-review1; inspect it without execution. Minor preparation/storage charges count toward the existing aggregate $5 planning target. No IAM, bucket-policy, application, quota or unrelated changes are authorized.

## Preflight before either write

Use only the approved profile and explicit region. Load owner identifiers privately from `~/.config/aegisland/aws-owner.json`; do not expose them or resolve another profile. Reconfirm non-root expected-account match and bucket ownership with ExpectedBucketOwner. Require us-east-1, all four public blocks, BucketOwnerEnforced, SSE-S3/AES256, the exact HTTPS-only deny policy, disabled versioning/Object Lock and no unexpected staging contents. Require previous AegisLand stack/function/log names absent; never switch CREATE to UPDATE to clear a collision.

Compare this manifest with the original: exactly the same nine resources/properties, trust and inline policy, API permission, S3 deny policies and retention behavior. Only `competition_cloud/storage.py` and `competition_cloud/client.py` bytes differ in the ZIP; all dependency bytes match. Run `scripts/verify_hardening_candidate.py` offline and verify this ZIP's checksum. The two source differences are the reserved-word/diagnostic correction, strict completion/ACK types and nested-JSON rejection; none changes simulation decisions.

Record private existing CreditBridge stack/template/function metadata and use the same AWS CLI serialization as the prior baseline. Permissions needed for this phase: exact-key S3 PutObject/GetObject, scoped bucket-control reads, and CloudFormation CreateChangeSet/DescribeChangeSet/GetTemplate and relevant stack metadata reads. The profile is not certified AegisLand-only; explicit project scope and stop rules remain essential. Do not grant permissions on AccessDenied.

## Proposed commands — execute only after approval

Use umask 077, AWS_MAX_ATTEMPTS=1, AWS_RETRY_MODE=standard and AWS_PAGER empty. `AEGIS_REVIEW_DIR` is a new mode-0700 directory outside Git. Set the expected-account and bucket variables privately; no value is embedded here. Read `AEGIS_ARTIFACT_KEY` from `artifact.proposed_s3_key` in the adjacent manifest. Reserve an exclusive durable ledger before each write; no automatic rerun after ambiguous results.

```bash
.venv/bin/python scripts/build_storage_remediation.py render \
  --revision final-hardening-20261023-r2 \
  --artifact-bucket "$AEGIS_ARTIFACT_BUCKET" \
  --output "$AEGIS_REVIEW_DIR/packaged.json"

aws s3api put-object --profile creditbridge-deployer --region us-east-1 \
  --bucket "$AEGIS_ARTIFACT_BUCKET" --key "$AEGIS_ARTIFACT_KEY" \
  --expected-bucket-owner "$AEGIS_EXPECTED_ACCOUNT_ID" \
  --body approval/final-hardening-20261023-r2/function-artifact.zip \
  --server-side-encryption AES256 --checksum-algorithm SHA256 --if-none-match '*' \
  --output json > "$AEGIS_REVIEW_DIR/staging-put.json"
```

Require the returned checksum to match and AES256/unversioned state unchanged. Revalidate prerequisites before the second write; stop on any mismatch.

```bash
aws cloudformation create-change-set \
  --profile creditbridge-deployer --region us-east-1 \
  --stack-name aegisland-opencv26-evidence \
  --change-set-name aegisland-unreserved-hardening2-review1 \
  --change-set-type CREATE --capabilities CAPABILITY_IAM \
  --template-body "file://$AEGIS_REVIEW_DIR/packaged.json" \
  --client-token aegisland-unreserved-hardening2-review1 \
  --description 'Offline hardened evidence candidate; execution needs separate approval' \
  --output json > "$AEGIS_REVIEW_DIR/create-change-set.json"
```

No RoleARN, named-IAM capability, macro, custom resource, nested stack, automatic SAM staging or service-linked role. Read every page of the resulting Change Set and server-side processed template. Require CREATE_COMPLETE/AVAILABLE and nine Add actions only: EvidenceApi, EvidenceApiv1Stage, EvidenceFunction, EvidenceFunctionEvidencePermission, EvidenceBucket, EvidenceBucketPolicy, TraceTable, EvidenceRole and EvidenceLogGroup. Require exact manifest equality except the approved Code.S3Bucket/S3Key substitution, no reserved/provisioned concurrency, and only CAPABILITY_IAM. Preserve the full new ARN privately and report its UUID without account identifiers. Stop before execution.

If a timeout makes either write uncertain, inspect the same key/name/token read-only; do not repeat the request or create an alternative. Cancellation cleanup is also a write: authorize separately deletion of this unexecuted Change Set/empty review placeholder and exact uploaded key. No bucket deletion or policy modification is implied.
