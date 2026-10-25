# A3 read-only AWS preflight results

**Deployment blocked by Lambda concurrency capacity. No resource changes performed.** The owner subsequently confirmed the non-root identity and authorized read-only discovery using `creditbridge-deployer` only, explicitly in us-east-1. That superseded the earlier offline-only instruction for discovery; it did not authorize deployment, IAM changes, quota requests or billable operations.

AWS CLI 2.38.4 was verified. STS identified the account internally and confirmed a non-root IAM user; the account ID, ARN, raw policy documents, resource names and budget recipients were not retained in public evidence. The other three profiles were not used. The initial sandboxed lookup failed; the authorized network-enabled run completed. Its redacted output is `evidence/a3/authorized-discovery-network.json` with the command record alongside it.

| Check | Observed result | Deployment implication |
| --- | --- | --- |
| Identity | Non-root IAM user; us-east-1 explicitly selected | Read-only discovery identity verified, not approved for AegisLand deployment |
| Caller policies | One attached policy, zero inline policies, no user permissions boundary reported | These observations do not establish project isolation or organizational approval |
| IAM simulations | All 26 sampled actions returned allowed on proposed/illustrative resource scopes; no missing context reported | Includes IAM role creation/policy/pass-role simulations, not actual role changes. Generated names, omitted actions, SCPs and effective deployment constraints still need review |
| CloudFormation | Two active stacks; CreditBridge-family resources exist; proposed new stack absent | Do not reuse or update existing stacks. Proposed name has no observed stack collision |
| Lambda | One existing function; proposed fixed function name absent | Existing workload must remain untouched |
| Logs | No group under the proposed function's log prefix | No observed fixed log-group collision |
| HTTP API / tables | Zero HTTP APIs and zero DynamoDB tables observed in this region | New project resources would be distinct; this is not proof of S3/global-name availability |
| Lambda concurrency | Regional quota 10; unreserved concurrency 10; template reserves two | **FAIL:** current reservation cannot preserve AWS's required unreserved pool |
| Other quota examples | IAM roles 13/1000; stacks quota 2000; tables quota 2500; general-purpose bucket quota 10000 | No obvious role/stack/table count blocker; bucket usage not queried. Full quota inventory retained without account identifiers |
| Budgets | Two budgets, four notifications and four subscriber bindings observed | Recipients/amounts withheld. Bindings need not be distinct recipients. AegisLand coverage, thresholds and delivery confirmation remain unverified |

The run used read-only STS, IAM/policy simulation, CloudFormation describe/list, Lambda configuration/list, HTTP API/table inventory, log-group metadata, Service Quotas and Budgets describe operations. AWS CLI handles pagination; policy document inspection was capped at ten per kind and budget notification inspection at five budgets (only one policy and two budgets were returned). No Cost Explorer, S3 object access, DynamoDB item access, Lambda invocation, paid log query, changeset, IAM write, quota request or other mutation was executed. CreditBridge resources were not modified.

Local verification after discovery: **68 competition tests passed** (65 A1/A2 tests plus three mocked discovery guard/redaction cases), and lint passed. The discovery tests use subprocess mocks only, including unexpected-identity stop cases; they do not use root credentials or repeat live AWS calls. Core source/policy and the SAM deployment template remain unchanged.

## Required decisions before a deployment request

1. Resolve concurrency **before creating the stack**. Prefer an owner-approved account/quota arrangement that permits the two-function reservation without taking capacity from CreditBridge. Under the current unreserved-pool rule, at least 102 available unreserved units would be needed before reserving two. An account-level quota change requires separate approval and was not requested. Alternatively prepare a separately reviewed quota-compatible template; do not silently remove the reservation or share CreditBridge's ten-execution pool.
2. Choose an AegisLand-scoped deployment/execution identity and staging prefix. The CreditBridge identity's simulated capabilities are not permission to repurpose it. Do not change its policy bindings or existing service resources.
3. Review the [permission plan](AWS_PERMISSION_PLAN.md), [resource manifest](AWS_RESOURCE_MANIFEST.md), exact changeset, budget suitability and teardown scope. Any role/policy, budget or staging creation requires explicit authorization.
4. Only after those decisions request the bounded live test: IAM/SigV4, two nominal uploads plus authentication/failure checks within 100 application requests, verified receipts/readback and approved cleanup.

Cost planning remains US$0.66973 under stated usage/storage assumptions, rounded to a US$1 test allowance and a proposed US$5 authorization ceiling. This is not an actual account-cost query or hard spending cap. See [owner approval](AWS_OWNER_APPROVAL.md). No deployment is ready to execute while the quota blocker remains.
