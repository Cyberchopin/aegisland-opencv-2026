# AegisLand least-privilege permission plan

This is an unapplied permission design. Read-only discovery through the owner-authorized CreditBridge profile does not authorize use of it as an AegisLand deployer. No users, roles, policies, keys, boundaries or existing bindings were created or changed.

Use a dedicated, owner-approved AegisLand deployment session and a narrowly scoped CloudFormation execution role. If suitable roles already exist, reuse only after explicit ownership/scope review; do not broaden CreditBridge's role or attach policies to its user. Account identifiers and final ARNs belong in private deployment configuration after review, not this public report.

| Principal | Required scope |
| --- | --- |
| Deployer session | CloudFormation create/describe/list changesets, describe stack events/resources, execute the reviewed changeset and approved delete for `aegisland-opencv26-evidence` only; S3 staging PUT/GET only in an approved project prefix. Pass only the approved CloudFormation execution role, conditioned on service `cloudformation.amazonaws.com`. |
| CloudFormation execution role | Create/read/delete the nine resources in the manifest, with template-required tagging, retention, encryption, public-block, lifecycle, concurrency, inline-role-policy and invocation-permission configuration. Fixed function/log paths and generated role/table/bucket names must be restricted to the AegisLand stack namespace. |
| Lambda execution role | Six application actions only: S3 GET/PUT on `evidence/*` in its bucket; DynamoDB GET/PUT on its table; log stream creation/event PUT in its log group. Trust only Lambda. No IAM administration or deletion. |
| Uploader session | `execute-api:Invoke` on this API's `v1/POST/evidence`. No direct table or object access. |
| Auditor session | S3 `GetObject` on this bundle's prefix, DynamoDB `GetItem` on its partition key; only approved billed reads. No scan/query/write by default. |
| Teardown session | Stack deletion and exact retained resource/staging deletion after receipt export. No broad bucket purge, unrelated table deletion or modification of CreditBridge. |

CloudFormation execution policy must explicitly enumerate provider operations instead of service-wide wildcards. Candidate action families for the final account-bound review:

- Lambda: create/get/delete function, add/remove invocation permission, set/delete reserved concurrency and the provider's necessary tag/read operations, restricted to the fixed AegisLand function ARN.
- HTTP API: required GET/POST/PUT/PATCH/DELETE operations for the new API and stage. Creation on the `/apis` collection cannot be reduced to a future API ID; restrict supported creation conditions and scope subsequent operations to the resolved API. Do not grant unrelated API mutation rights.
- DynamoDB: create/describe/delete this table, configure TTL/PITR, and necessary tag/read operations. The execution role does not need application item writes.
- S3: create/read/configure/delete only the new evidence bucket: encryption, all public-access blocks, conditional-write/TLS bucket policy, lifecycle, and necessary tag/read operations. Staging object permissions stay in the deployer role. Bucket emptying is a separately approved teardown operation.
- IAM: create/read/delete the stack-generated Lambda role, put/get/list/delete its inline policy, necessary tags and `PassRole` conditioned on `lambda.amazonaws.com`. No `CreateUser`, `CreateAccessKey`, arbitrary policy attachments or `iam:*`.
- Logs: create/read/delete the fixed log group and set its retention, plus required tagging operations. No log search or account-wide log access by default.

These are candidate provider permissions, not an executable guarantee that every CloudFormation provider call has been covered. Finalize exact API verbs, supported resource/condition keys, boundaries and final ARNs against the reviewed changeset. Some create/list operations require `Resource: '*'`; allow only the indispensable action on that scope, never a blanket service wildcard. Use project request-tag conditions where supported and preserve existing account controls. Do not add broad permissions in response to an AccessDenied without review.

Read-only simulations allowed 26 sampled actions, including role administration, on illustrative project resources. That is evidence of sampled capability, not a minimal scoped deployment grant and not approval. No policy currently establishes AegisLand ownership simply because its name contains “deployer.” The Lambda concurrency quota also blocks the present template independently of IAM permission.

The owner must approve identity selection, every new role/policy attachment, any quota adjustment, and the final resolved policies before deployment. Preparing a changeset or staging files also requires separate authorization. No account changes are part of A3.
