# Second Phase B — depends on a NEW reviewed Change Set UUID

**NOT AUTHORIZED.** The new Phase A has not occurred. There is no UUID to approve yet. Original UUID `9323089e-31ff-40c3-8cff-5060fa63f355` is historical and must not be reused.

## Separate approval after Phase A review

The owner must explicitly authorize execution exactly once of the resulting **new UUID**, creditbridge-deployer/us-east-1, stack aegisland-opencv26-evidence, the exact nine-resource manifest and new ZIP hash `52e37629b1434e9a898448ddd5f63aa94ce367b1f552fdb5c082c92ea816aa39`. Approval must cover one execution role and its existing reviewed inline policy, AWS-managed DynamoDB KMS effects/request charges, bounded paid verification, scoped failure-evidence preservation and full teardown including partial deployment. No additional IAM permissions, resource types or quota changes are included.

Before execution revalidate identity, exact UUID/CREATE_COMPLETE/AVAILABLE, complete paginated nine-Add manifest, account/region, staged ZIP checksum and canonical processed-template hash. No Modify/Remove/replacement, external RoleARN or capability beyond CAPABILITY_IAM. Reserve a durable exclusive ExecuteChangeSet ledger and fixed request token before dispatch; never retry an ambiguous execution.

```bash
aws cloudformation execute-change-set \
  --profile creditbridge-deployer --region us-east-1 \
  --stack-name aegisland-opencv26-evidence \
  --change-set-name "$AEGIS_NEW_APPROVED_CHANGE_SET_ARN" \
  --client-request-token aegisland-unreserved-hardening2-execution1
```

Read-only bounded status polling follows. On failure capture only new-stack events/resource IDs; do not alter IAM, retry deployment, change rollback behavior or reuse another project's resources. Perform the pre-authorized cleanup after rollback settles. Stop rather than force-delete an unexpected dependency/resource.

## Successful deployment acceptance

Require CREATE_COMPLETE and exactly nine actual owned resources. Verify Lambda CodeSha256, Python 3.12/Arm64/256 MB/25 s, environment targets and no reservation. Check the one Lambda-trusted role and its exact inline S3 Get/Put prefix, DynamoDB Get/Put table and log-stream actions; no managed policies. Check route POST /evidence uses AWS_IAM and the invoke permission is limited to this API/path (stage wildcard is disclosed). Check new evidence-bucket private/AES256 controls, table schema/TTL/PITR/AWS-managed KMS and 14-day log retention. Any drift aborts application tests.

Use an explicitly selected Boto3 session for creditbridge-deployer/us-east-1; a CLI --profile flag does not configure a different Python process. Do not use the general CLI uploader unchanged: its default is three attempts. Use the reviewed `upload(..., attempts=1)` interface, one process, immutable nominal bundle and one durable counter incremented before dispatch. Disable SDK retries. Space requests at least one second, sequentially awaiting every response. A client timeout can leave Lambda active, so send no follow-up after an unexpected result.

| Phase | HTTP attempts | Acceptance |
| --- | ---: | --- |
| Unsigned authentication | 1 | 401/403 only |
| Nominal bundle | 15 | Exact typed/checksum-bound stored_verified ACK for each |
| Same-byte duplicate replay | 15 | Same fifteen ACKs, same storage identities/content |
| Invalid protocol / checksum / conflicting metadata | 3 | 400 / 400 / 409 respectively |

**34 planned, absolute ceiling 40.** Margin is not permission for retry. Stop on unexpected auth result, status, 429/5xx, timeout, invalid ACK/hash/type or scope change. Expected negative statuses are planned outcomes. No other scenario, uploader, direct Lambda invoke, warmup/load test or resumption is authorized.

After all HTTP checks, read exactly fifteen known S3 bodies and fifteen consistent GetItem keys; reconstruct all nine files and require byte identity with originals. No scan/query. On failure preserve only relevant new-function logs (at most two streams/1000 events each), known attempted packet/index, new-stack metadata and receipts. Public logs must exclude raw messages/identifiers; private exports must be mode0600 and copied outside /tmp and Git before cleanup/session loss. Do not infer historical error codes from the new run.

## Cost and stop conditions

Adjacent model is a conservative $0.921067 full-run allowance, not a quote or actual bill. Two full-run allowances total $1.842134; first-run actual charges remain unknown. **Both attempts share the owner's aggregate $5 planning target**, not two separate budgets. No hard cap exists. Shared Lambda quota ten and API throttles do not cap charges or isolate CreditBridge. Stop before extra workload if costs approach the target or scope/account telemetry is uncertain; do not query charged billing/metrics/Insights APIs without approval. No new paid service, CMK, NAT or EC2 is proposed.

## Complete teardown and verification

Stop traffic; export receipts, logs and any partial evidence locally first. Record actual stack ID and exact created resource identities privately. Delete only this new stack using a fixed client token and wait for completion. After export, explicitly remove only the known bundle objects, its newly created retained evidence bucket and retained table; do not rely on TTL/lifecycle. Verify versioning, unexpected keys and multipart uploads before deletion; stop instead of purging unknown data. Delete only the exact new staging key after checksum/owner checks, never the owner-managed staging bucket. No IAM grants to fix cleanup.

Confirm stack, API/stage, function/invoke policy, role/inline policy, log group, retained bucket/table and exact staging key absent. Compare existing CreditBridge metadata/templates/code hashes with the private baseline, reporting differences without restoring anything. Preserve the AWS-managed DynamoDB key; a PITR system backup can persist up to 35 days, and CloudFormation deletion history/delayed billing can remain. Report residuals and unknown charges explicitly. Active demo window is at most one supervised hour; cleanup within 24 hours. Do not claim zero future account charges from DELETE_COMPLETE.
