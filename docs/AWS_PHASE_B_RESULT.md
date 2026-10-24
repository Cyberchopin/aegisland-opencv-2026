# Authorized Phase B: deployment passed, storage verification failed, teardown passed

This is an additive result record. The reviewed templates, approval ZIP, prior evidence, technical report and storyboard remain unchanged. Account identifiers and the owner-supplied staging bucket name are withheld.

## Actual outcome

| Check | Result | Evidence |
| --- | --- | --- |
| Exact reviewed Change Set revalidation | PASS | UUID `9323089e-31ff-40c3-8cff-5060fa63f355`; nine Add actions; no modifications, replacements, deletions or extra capabilities; server-side template matched Phase A |
| Single execution | PASS | One ExecuteChangeSet; stack `aegisland-opencv26-evidence` reached CREATE_COMPLETE in us-east-1 |
| Actual resources | PASS | Exactly the nine reviewed logical IDs/types, including one role and its one `evidence-only` inline policy; no extra permissions granted |
| Deployed Lambda / route | PASS | ZIP SHA matched reviewed artifact; Python 3.12 Arm64, 256 MB, 25-second timeout; POST /evidence uses AWS_IAM |
| Unsigned authentication test | PASS | HTTP 403, as expected |
| First signed nominal packet | **FAIL** | HTTP 503 `storage_unverified`; no successful storage acknowledgement |
| Bounded controller | PASS | Two total HTTP requests, one uploader, attempts=1, zero retries; all remaining application tests stopped |
| Complete nominal bundle / duplicate and negative tests | **UNVERIFIED** | Not completed after the first unexpected response; no second upload or workaround attempted |
| Partial storage preservation | PASS, partial only | One 1,618-byte S3 packet exported and byte-matched to the reviewed sequence 0; consistent GetItem found no index item |
| Authorized teardown | PASS | Stack resources and explicitly retained evidence bucket/table removed after local export; exact staging object removed |
| CreditBridge comparison | PASS for observed metadata | Existing stack metadata/templates and Lambda metadata unchanged before/after; shared-capacity impact was not measured |

The deployed resource list was EvidenceApi, EvidenceApiv1Stage, EvidenceFunction, EvidenceFunctionEvidencePermission, EvidenceBucket, EvidenceBucketPolicy, TraceTable, EvidenceRole and EvidenceLogGroup. Full physical IDs are retained privately; the public evidence records their SHA-256 fingerprints. The inline policy is embedded in EvidenceRole, not an additional resource.

## Failure boundary and next work

The Lambda logs report `ClientError`. The available logging does not establish the AWS error code or the exact failing service operation. A valid partial S3 object and absent DynamoDB item narrow the observed storage state but do not prove a root cause. Do not claim that a complete evidence bundle was stored, that idempotent replay succeeded in AWS, or that all cloud failure cases passed.

The highest-impact next task is an **offline** investigation of the reviewed storage/IAM/encryption path and error observability. Any changed artifact, policy, deployment, or further application request requires a new review and owner authorization. Do not widen IAM or retry the live demo under the completed Phase B authorization.

One pre-execution comparison initially stopped because the older Python SDK omitted the newer CloudFormation `DeploymentConfig` response field. Read-only comparison using the same AWS CLI as Phase A proved exact unchanged existing-resource metadata; execution occurred only after that check passed. No execution retry occurred.

## Evidence and costs

Sanitized results, the two actual HTTP receipts, incomplete uploader result, deployment resource fingerprints, partial-object checksum, failure-log excerpt, template hash, teardown summary and SHA-256 inventory are in [evidence/aws-phase-b](../evidence/aws-phase-b/result.json). These files are additive; 186 previously protected approval/evidence files were verified byte-identical.

Private full responses, deployed resource identities, failure logs and partial data exports are at `/tmp/aegisland-phase-b/`, with a mode-0600 archive `/tmp/aegisland-phase-b-private-evidence.zip`. They contain private account details and must not be committed or published. The owner configuration and credentials were not included in that archive. The archive checksum is recorded in the sanitized evidence. `/tmp` is temporary storage: preserve the private archive in owner-controlled private storage before the session is discarded.

Actual billed cost is **UNAVAILABLE**, not zero. No Cost Explorer, paid billing report, Insights query or GetMetricData query was used. The unchanged conservative full-demo planning estimate was $0.921067 against the accepted $5 planning ceiling. Only two application requests ran, but storage, deployment, logs, KMS/account telemetry and delayed billing can still incur charges. This estimate is not a measured bill or a hard cap.

## Teardown and residuals

Confirmed absent: new stack, HTTP API/stage, Lambda/invocation permission, execution role/inline policy, log group, retained evidence bucket and retained table, and the exact staging object. Partial evidence was exported before retained storage deletion, following the approved teardown plan. No subsequent application requests were dispatched.

The owner-managed staging bucket remains; its deletion was not authorized. The AWS-managed DynamoDB key, if initialized, was not modified. CloudFormation deletion history persists, and DynamoDB PITR may retain a system backup for up to 35 days. No manually created backup or customer-managed KMS key was introduced. These residuals and delayed billing prevent a claim of zero future account charges.
