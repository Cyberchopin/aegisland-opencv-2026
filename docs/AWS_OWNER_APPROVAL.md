# A3 AWS owner approval

**Latest authorization:** the owner authorized one Lambda quota request to 102 only, with no IAM/service-linked-role creation or deployment. Prechecks verified account/caller internally, us-east-1, quota `L-B99A9384`, current 10 and requested 102; the required `AWSServiceRoleForServiceQuotas` lookup returned `NoSuchEntity`. **No request was sent; no request ID exists.** All actions stopped at that prerequisite. Creating the role or otherwise expanding permissions needs separate owner direction. The deployment/IAM/billing approvals below remain ungranted.

**HOLD — read-only discovery completed; deployment is blocked and unauthorized.** The owner later verified a non-root IAM user and authorized only `creditbridge-deployer` for read-only discovery in us-east-1. AWS CLI 2.38.4 and the non-root caller were verified. This superseded the earlier offline-only instruction for discovery; it did not authorize any mutation or billed operation. No credentials, account identifiers, ARNs, budget recipients or existing resource names are published here.

Verified discovery / proposed deployment region: **us-east-1**. Proposed new stack: `aegisland-opencv26-evidence`. **The current template cannot reserve two Lambda executions in an account with quota 10.** Expected controlled-test allowance after that blocker is resolved: **under US$1**; proposed maximum owner-authorized incremental expense: **US$5**. Neither amount is a guaranteed bill cap.

## What is verified and what blocks approval

| Status | Check | Result / exact prerequisite |
| --- | --- | --- |
| PASS | CLI/profile/identity | CLI 2.38.4, authorized profile only, non-root IAM user; account identified internally and withheld. Other three profiles unused. |
| PARTIAL | Caller/deployment permissions | One attached policy, no inline policies or reported user boundary; all 26 sampled action/resource simulations allowed. AegisLand suitability, full provider permissions and effective organizational controls remain unverified. No permission changes authorized. |
| PASS | Existing-name checks | Proposed stack, fixed Lambda name and log-group prefix absent; unrelated stacks/functions observed and left untouched. |
| FAIL | Lambda concurrency | ConcurrentExecutions=10 and UnreservedConcurrentExecutions=10. Current two-execution reservation cannot preserve the required unreserved pool. No quota change requested and no template fallback applied. |
| PARTIAL | Other quotas | Roles 13/1000, stacks quota 2000, tables quota 2500; no observed role/stack/table count blocker. General-purpose bucket quota 10000, usage unverified. |
| PARTIAL | Budgets and alerts | Two budgets, four notifications and four subscriber bindings observed. AegisLand coverage, suitable thresholds and confirmed delivery still need owner review; actual costs/credits/taxes not queried. |
| PASS | Local implementation | A2: 65 competition tests, 56 targeted core tests, SAM build, template lint and package checks passed. No cloud success or deployed IAM claim follows from them. |

The initial offline snapshot is `evidence/a3/local-preflight.json`; it predates the CLI/identity update. Current results are in `evidence/a3/authorized-discovery-network.json` and [AWS_PREFLIGHT_RESULTS.md](AWS_PREFLIGHT_RESULTS.md). The source template and runtime are unchanged. The dedicated [permission plan](AWS_PERMISSION_PLAN.md) and [resource/teardown manifest](AWS_RESOURCE_MANIFEST.md) define the proposed isolated scope.

The owner authorized the following **read-only, non-billable control-plane** checks, which completed through the confirmed profile. Account IDs and ARNs stayed inside the process; only caller type, allow/deny/error codes, counts, quota values and collision flags were retained. The helper stops if the caller is root or an unexpected type. No other profile was used.

| Read-only inspection | Intended APIs / purpose |
| --- | --- |
| Identity | STS `GetCallerIdentity`; retain account/ARN internally only |
| Caller authority | Relevant IAM `GetUser`/`GetRole`, attached/inline policy reads and policy-version reads; `SimulatePrincipalPolicy` if allowed, using proposed resource scopes |
| Existing stacks | CloudFormation `ListStacks`/`DescribeStacks`, exact proposed-name check; no changeset creation |
| Fixed-name collisions | Lambda `GetFunctionConfiguration`, CloudWatch Logs `DescribeLogGroups` for the proposed prefix; no object/list-data scans |
| Capacity | Lambda `GetAccountSettings`, appropriate Service Quotas list/get operations and DynamoDB/API Gateway quota reads where supported |
| Budget alerts | Budgets describe budgets, notifications and subscriber metadata; redact all subscriber values and names |

Check pagination; denied or incomplete reads remain UNVERIFIED. Policy simulation cannot by itself establish effective permission under all boundaries, SCPs or resource policies. Do not call Cost Explorer: [its paginated API queries are charged](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html). No S3 object reads, DynamoDB data reads, Lambda invocations, log queries, changesets or billable test requests belong to this preflight authorization.

## Exact proposed resources and exposure

The reviewed file is `infra/template.yaml`; A3 makes no template change. Seven source resources expand into the following service resources when SAM transforms the API/function:

| Resource | Definition / exposure |
| --- | --- |
| HTTP API + v1 stage | Publicly reachable regional HTTPS endpoint; `POST /evidence` requires AWS IAM/SigV4. Public network reachability remains even though anonymous application access is denied. Rate one request/second, burst two. |
| Lambda + API invocation permission | Python 3.12 Arm64, 256 MB, 25 s timeout, concurrency two. Name `<stack>-evidence`. API Gateway service invocation permission must be scoped to this API/route in the resolved template. No function URL or hardware adapter. |
| Evidence S3 bucket + bucket policy | Generated physical name; private, AES256 encryption, all four public-access blocks, 30-day object expiry. Policy denies insecure transport and nonconditional PUTs on `evidence/*`. Bucket is retained. |
| DynamoDB table | Generated name; on-demand, encrypted, TTL enabled, PITR enabled. Table is retained. No public database endpoint granted by this template. |
| Lambda IAM execution role | Trusts only `lambda.amazonaws.com`; inline policy described below. No access keys created. |
| Lambda log group | `/aws/lambda/<stack>-evidence`, 14-day event retention. Stack deletion removes the group unless a future reviewed template changes retention policy. |

Offline transformation produced nine service resources and verified the route's `awsSigv4` scheme. The generated Lambda permission is scoped to this API and `POST /evidence`, with a stage wildcard (`*/POST/evidence`). The current template creates only `v1`; explicitly review that wildcard before deployment rather than claiming the invocation permission is stage-exclusive. Exact symbolic policies and resources, with no account IDs, are retained in `evidence/a3/security-inventory.json`. The inspection blocked network access and substituted an unuploaded placeholder package URI solely for local translation.

A CloudFormation stack and a deployment-artifact S3 location are also needed. Prefer an existing owner-approved artifact bucket with a dedicated prefix and encryption/public-access controls. If none is suitable, creating one extra private bucket and its policy needs separate approval. **Do not use automatic `sam --resolve-s3` bootstrap creation**: it can create an additional managed stack/bucket outside this inventory. No EC2, NAT gateway, VPC, custom domain, KMS customer key, provisioned concurrency, X-Ray configuration, website hosting or paid budget reports are requested.

Fixed-name collision checks cover the stack, Lambda and log group and found no collision. Generated bucket/table/role names avoid predictable-name assumptions but still require ownership review. [Lambda reserves an unreserved-concurrency pool](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html); the observed quota of ten cannot accommodate the template reservation. An owner-approved quota arrangement with at least 102 available unreserved units would permit reserving two under that rule. Do not request the increase or silently remove the reservation; a quota-compatible template alternative also needs separate review to avoid sharing/consuming CreditBridge capacity unexpectedly.

## IAM changes requiring approval

The new Lambda role has exactly these application actions:

- `s3:GetObject`, `s3:PutObject` on the new bucket's `evidence/*` prefix.
- `dynamodb:GetItem`, `dynamodb:PutItem` on the new table.
- `logs:CreateLogStream`, `logs:PutLogEvents` on this function's log-group streams.

It cannot delete data, query other tables, manage IAM, invoke another Lambda, operate drones or access a general S3 wildcard. The bucket's `Principal: '*'` appears in **Deny** statements, not a public Allow. Actual resolved policies and gateway authentication must still be checked after an authorized deployment.

Separate identities/scopes:

| Identity | Least-privilege plan; no grants applied in A3 |
| --- | --- |
| Owner/deployer | CloudFormation create/describe/execute/delete for this new stack only; artifact PUT/read only within the approved staging prefix. Pass only a designated CloudFormation execution role, with `iam:PassedToService=cloudformation.amazonaws.com`. |
| CloudFormation execution role | Create/manage/delete the listed stack resources; limit named Lambda/log resources and generated IAM roles to the stack prefix. Permit `iam:CreateRole`, inline-policy management, reads and deletion only for that Lambda role; `iam:PassRole` only for it, conditioned on `lambda.amazonaws.com`. No `iam:*`, administrator attachment or credential creation. Required service create operations that cannot be ARN-scoped need an explicit action allowlist and supported tag/request conditions. |
| Evidence uploader | Only `execute-api:Invoke` on this API's `v1/POST/evidence` route, using the approved non-root session. No S3/table permissions. |
| Receipt auditor | S3 GET on the specific evidence prefix and DynamoDB GET on the new table; scope table access by bundle partition key where practical. Any billed reads require approval. |
| Teardown operator | Delete only the approved stack, exact retained table/bucket and dedicated staging prefix; storage deletion separately approved after receipt export. |

If existing roles already have the required scope, create no additional deployer/uploader/auditor roles. Otherwise role/policy creation or attachment is another explicit IAM change requiring owner approval. An exact account-bound deployer policy cannot honestly be finalized before identity, staging bucket, boundaries and resolved physical names are known. Complete that review before execution, rather than granting broad permissions to make a failed deployment pass.

## Cost gate

`evidence/a3/cost-estimate.json` records a reproducible **planning model**, not a live AWS quote or maximum-bill guarantee. It uses rounded upper planning allowances, not hand-entered measurements: 100 total application HTTP requests, 256 MB Lambda with 60 billed seconds allowed per request, 250 S3 PUTs plus 250 GETs, 500 WRUs plus 500 RRUs, 0.25 GB-month S3/staging, 1 GB-month each for table and PITR, 10 MB logs and 0.25 GB egress. Storage allowances cover up to one month, though active testing is limited to 24 hours. Current public pricing pages were checked October 22: [Lambda](https://aws.amazon.com/lambda/pricing/), [API Gateway](https://aws.amazon.com/api-gateway/pricing/), [S3](https://aws.amazon.com/s3/pricing/), [DynamoDB](https://aws.amazon.com/dynamodb/pricing/), [CloudWatch](https://aws.amazon.com/cloudwatch/pricing/).

| Planning allowance | USD |
| --- | ---: |
| API and Lambda requests/duration | 0.03023 |
| S3 and DynamoDB request allowances | 0.00350 |
| S3/staging, table, PITR storage | 0.57500 |
| Logs and egress | 0.06100 |
| Total planning model | **0.66973** |
| Rounded controlled-test allowance | **1.00** |
| Proposed owner authorization ceiling | **5.00** |

The model excludes existing account spend, tax and uncontrolled traffic; it assumes no free tier or credits. Reconfirm account/region tariffs and the maximum planned volume before approval. A $5 authorization ceiling means stop and escalate before knowingly expanding scope; it is **not technically enforced** by the template. Unexpected traffic, persistence or delayed billing can exceed a planning estimate. If a guaranteed hard dollar cap is required, do not deploy this design under the current controls.

Two existing budgets with four notification/subscriber bindings were observed, without publishing names, amounts or recipient values. They are not automatically suitable for AegisLand. Verify coverage, thresholds and confirmed delivery, or obtain approval to create a monitoring-only project budget and notifications; do not change CreditBridge budgets or enable action budgets/paid emailed reports implicitly. [Budget monitoring and alerts are free](https://aws.amazon.com/aws-cost-management/aws-budgets/pricing/), but alerts and AWS billing data can be delayed and do not enforce a hard spending cap. Rate limits and concurrency also do not cap total spend.

## Authentication and failure-path acceptance

Local tests already cover signing, bad acknowledgements, bounded retries, corrupted/missing objects, partial writes and lost acknowledgements. Live acceptance would be limited to:

1. Verify the deployed route uses IAM and that the Lambda permission is tied to the intended API. One unsigned request must be rejected without evidence ingestion.
2. Make two nominal-bundle upload invocations, each with 15 packets and at most three attempts per packet: at most 90 upload POST attempts total. Verify exact checksum-bound receipts and duplicate identity/content stability.
3. Allow up to nine other application requests, keeping the total at 100 including the unsigned request. Use signed malformed payload/checksum and conflicting-content requests to confirm non-success; no deliberate storage corruption, resource-policy edits or production fault injection.
4. Perform approved, bounded S3/table readback to reconstruct every artifact byte-for-byte. Preserve sanitized receipts, counts and source/template hashes. No account/credential values in screenshots or videos.

Mocked tests remain explicitly mocked. A real success claim requires deployed receipts **and** actual readback. A stopped client can be replayed within the two-invocation budget; a third invocation, more scenarios, real resource fault injection or public hosting requires a new approval.

## Teardown and persistence

After receipt export, stop uploads and remove the public API/Lambda through an owner-approved stack deletion within 24 hours of verification. CloudFormation removes the API/stage, Lambda/permission, role/policy and log group. S3 and DynamoDB have `Retain`, so deleting the stack does **not** remove their data or end storage/PITR charges.

Separately obtain approval to empty/delete only the exact evidence bucket, delete the retained table, and remove only this deployment's staging objects. Delete a staging bucket only if it was created exclusively for this test and is empty; leave shared infrastructure untouched. DynamoDB deletion with PITR creates a system backup retained for 35 days at no additional cost, according to [AWS's documented behavior](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DocumentHistory.html). That is a persistence issue even when it adds no backup charge; inspect any other backups separately before claiming all persistence or costs have ended. Preserve only local, sanitized judge evidence unless the owner explicitly approves cloud retention through judging. Inventory retained resources and backups again after cleanup; never treat stack deletion alone as proof of zero future charges.

## Approval checklist — no action authorized yet

- Read-only discovery is complete; do not extend this authorization to deployment or billed reads.
- Resolve the Lambda quota blocker through a separately approved quota/account choice or local template review. No quota request, template change or resource mutation is authorized by discovery.
- Confirm us-east-1, the new stack name, staging location, account match internally and an AegisLand-scoped deployment/execution identity. Do not repurpose or modify the CreditBridge identity by assumption.
- Approve up to US$5 incremental expense under the bounded test plan, with an expected controlled-test allowance under US$1; confirm budget recipient and stop conditions.
- Approve any missing budget notifications, staging bucket, execution-role or uploader/auditor policy changes explicitly.
- Authorize staging PUTs, changeset creation, then review the exact changeset before a **separate execution approval**. Changeset creation is not treated as read-only preflight.
- Authorize the bounded live authentication/upload/readback test and the exact teardown scope, including retained data and possible backups. If teardown is not approved together, require its approval before deployment to avoid unmanaged persistence.

The read-only authorization is not deployment approval. Current status is **not ready to execute a deployment**, because concurrency and project-specific identity approval remain unresolved. The competition still lacks verified AWS execution. An AWS storage demo also does not replace the required judge-facing working application demonstration.
