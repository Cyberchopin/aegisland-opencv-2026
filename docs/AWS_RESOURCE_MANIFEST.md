# Proposed resource manifest and teardown

Region: **us-east-1**. Proposed new stack: **aegisland-opencv26-evidence**. Status: **not created; deployment blocked by Lambda concurrency quota**. Existing CreditBridge stacks and resources are excluded from all mutation and cleanup scopes.

Offline transformation of `infra/template.yaml` produces nine service resources:

| Logical ID | Type / planned name | Exposure and persistence |
| --- | --- | --- |
| EvidenceApi | HTTP API, generated ID | Regional public HTTPS address, IAM-authenticated POST route; removed with stack |
| EvidenceApiv1Stage | HTTP API stage `v1` | Rate one request/second, burst two; removed with stack |
| EvidenceFunction | Lambda `aegisland-opencv26-evidence-evidence` | Arm64, Python 3.12, 256 MB, 25 s, reservation two; no function URL; removed with stack |
| EvidenceFunctionEvidencePermission | Lambda invocation permission | API Gateway principal, this API and POST `/evidence`, any stage of this API; removed with stack |
| EvidenceBucket | Generated private S3 bucket | AES256, public blocks, TLS/conditional-write policy, 30-day object expiry; **Retain** |
| EvidenceBucketPolicy | S3 bucket policy | Deny-only TLS/conditional-write protections; managed as stack resource |
| TraceTable | Generated on-demand DynamoDB table | Encrypted, TTL and PITR; **Retain** |
| EvidenceRole | Generated Lambda role | Six narrowly scoped application actions; removed with stack |
| EvidenceLogGroup | `/aws/lambda/aegisland-opencv26-evidence-evidence` | 14-day event retention; group removed with stack |

One CloudFormation stack tracks these resources. A separately approved S3 artifact bucket/prefix is needed for packaging. If a dedicated artifact bucket/policy must be created, add them to the approval and cleanup manifest first. No automatic `--resolve-s3` bootstrap stack or bucket is authorized.

Read-only discovery found no collision for the proposed stack, fixed Lambda name or log prefix. Two active unrelated stacks and one unrelated Lambda exist and must remain untouched. There were no HTTP APIs or DynamoDB tables in this region at inspection. Bucket/table/role physical names are not chosen yet; generated names and global bucket capacity must be verified before deployment. Do not rename or reuse an existing resource to work around a collision.

## Ordered, separately authorized teardown

1. Stop uploads; export sanitized receipts, inventory, source/template hashes and byte-comparison results locally. Confirm that no cloud object contains the only copy of evidence.
2. Match the exact approved account internally, region, stack, API, function and physical retained resource IDs against the deployment receipt. Do not select by a broad substring or shared project account.
3. Delete only the new stack after approval. Confirm API/stage, Lambda/permission, execution role and log group disappear. No CreditBridge update or deletion is permitted.
4. The retained S3 bucket and DynamoDB table still exist. Under explicit data-deletion approval, delete only the evidence bucket's contents and bucket and the exact table. Inspect actual versioning first; the template does not enable it, but configuration drift must not be assumed away. Never use an account-wide cleanup script.
5. Remove this deployment's staging objects under the approved prefix. Delete a staging bucket only if the owner approved its creation for this test, confirms it is unshared, and approves its deletion. Do not delete SAM bootstrap/shared buckets.
6. Record resource absence and retained backup state with approved read-only control-plane checks. A PITR-enabled deleted table leaves a system backup for 35 days at no additional cost; other backup or artifact retention can persist and needs separate review. TTL/lifecycle are delayed expiry mechanisms, not immediate teardown guarantees.

Plan API/Lambda removal within 24 hours after the verification window; any cloud retention through judging needs explicit owner approval and a revised cost window. Stack deletion alone does not stop retained table/PITR or S3 storage costs. Removing the stack's bucket policy while retaining its bucket also changes the remaining protection set; complete the approved retained-resource cleanup rather than leaving it unmanaged.

No teardown command was executed or pre-authorized. No actual resource identifiers or account IDs are included here; they are to be matched privately after an approved deployment.
