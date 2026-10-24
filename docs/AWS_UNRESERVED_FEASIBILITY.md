# Offline feasibility: AegisLand without reserved concurrency

**Recommendation:** use the separate no-reservation review variant for a short, supervised AWS evidence demo **if the owner accepts shared concurrency with CreditBridge**. This is the fastest technically feasible route around the quota blocker. It is not deployment approval, a hard spending cap or a guarantee of non-interference. If CreditBridge must have guaranteed capacity isolation, retain the reservation and pursue quota 1000 or an adequately provisioned separate account instead.

This assessment made no AWS account calls, quota requests, IAM changes, deployments or paid requests. It uses the owner's current quota of ten and the prior read-only account observations. The owner's console finding—quota increase requests must be at least 1000—supersedes the earlier proposed request value 102. No request for either value has been submitted. The old 102 request driver must not be used to pursue this option.

All pre-existing reports, ZIP, HTML report, storyboard, scripts inside that ZIP and other submission artifacts remain intact. The original `infra/template.yaml` remains unchanged. New assessment artifacts are separate.

## Can the stack function with quota ten?

**Yes, conditionally.** An unreserved Lambda uses the available shared regional pool. The rule that leaves 100 units unreserved constrains allocating a reservation; it does not prohibit running ordinary unreserved functions in an account whose quota is ten. Removing the property removes this particular creation-time concurrency blocker. Actual invocation still requires spare shared capacity, approved IAM and a successful deployment/runtime verification. [AWS concurrency behavior](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html)

One normal synchronous upload request needs one active invocation. The existing uploader waits for its response before sending the next packet, then pauses one second. It does not need fifteen concurrent executions to upload fifteen packets. No provisioned concurrency, extra function, queue, quota change or new vision feature is needed for this test.

However, omission removes both the guaranteed allocation and the per-function maximum of two. AegisLand can compete with the existing CreditBridge workload for the same ten slots; either workload can throttle the other. Authentication, a single controlled client and low request volume make a supervised test practical, but they do not create isolation. No CreditBridge traffic measurement was performed during this offline assessment, so available headroom is unverified.

## Precise minimum template change

The separate candidate is `infra/template.unreserved-review.yaml`, alongside the original so that `CodeUri: ../cloud/` resolves identically. Its only source change is:

```diff
       Timeout: 25
-      ReservedConcurrentExecutions: 2
       Role: !GetAtt EvidenceRole.Arn
```

**Omit the property.** Setting it to zero disables invocation; changing it to one still asks for a reservation and does not solve the pool constraint. Do not change account concurrency settings or existing functions. [AWS reserved-concurrency semantics](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html)

All nine generated resources remain the same except that the Lambda reservation property is absent. IAM/SigV4 authorization, Lambda role/policies, bucket policy, encryption configuration, table TTL/PITR, function memory/timeout, API throttles, retention and code are unchanged. There is no core safety-policy change. The original CI tests continue to verify the original reviewed template; the candidate has separate offline validation evidence and is not silently selected by CI or a deploy script.

## Request rate is not a concurrency limit

The API's rate target is one request/second with burst two. AWS documents that these throttles are best-effort targets, not guaranteed ceilings. With independent callers and a 25-second execution, even one request/second can demand roughly 25 concurrent invocations before Lambda throttling—more than this account permits. Therefore, API throttles alone cannot replace the removed Lambda cap. [HTTP API throttling](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-throttling.html)

The CLI's existing default permits three attempts per packet. A timeout may leave an earlier Lambda running; a retry can overlap it. Idempotency protects evidence identity/content, not concurrency isolation. Calling this path “one in-flight Lambda” would overstate its guarantee.

For the initial owner-authorized test, use the existing programmatic upload interface with **`attempts=1`**, one uploader process and no parallel checks. The offline failure injection confirms that a timeout then dispatches only one request and returns `incomplete`, without advancing to another packet. This needs no client/library code change, but the current CLI does not expose the attempts setting: do not use its three-attempt default for this first test.

The intended invocation configuration, **not executed**, is:

```python
# Only after deployment, billing and identity authorization.
plan, packets = prepare(local_nominal_directory)
result = upload(packets, approved_signed_transport, attempts=1, mode="aws_http")
# Persist this exact result before deciding whether any later request is permitted.
```

On any timeout, throttling, missing acknowledgement or storage conflict, stop the batch. Do not launch another client or manually retry while the prior invocation might still run. A cooldown alone does not prove completion; obtain approved diagnostics/confirmation before a new attempt. Do not resume an incomplete run automatically.

Optional further rate reduction, such as burst one and a lower rate target, is an additional reviewable template change, **not required for functional feasibility and not included in the one-line candidate**. It still would not provide a hard concurrency or spending cap.

## Minimal supervised demonstration

1. Obtain explicit owner acceptance of shared capacity and a quiet test window; select approved AegisLand deployment, uploader and auditor identities. Discovery authorization for `creditbridge-deployer` is not deployment authority.
2. Build/package the chosen candidate, confirm account/region privately, approve the staging prefix and inspect the exact new-stack changeset. No automatic `--resolve-s3` bootstrap creation or reuse of CreditBridge resources.
3. After separate execution/billing approval, verify route IAM authorization with one unsigned denial. Run only the nominal evidence bundle with one process and one attempt per packet.
4. If all fifteen packets are acknowledged, repeat that same bundle once to demonstrate duplicate handling. Then use approved S3/table readback to reconstruct and compare the actual bytes. Perform any agreed invalid/checksum/conflict request tests serially.
5. Cap the initial plan at **40 total application HTTP attempts**: thirty nominal/replay packet requests plus at most ten specifically approved authentication/failure checks. This is an operator/client plan, not a server-enforced account-wide counter. No third upload, extra scenario, load test or automatic retry is included.
6. Export receipts locally and perform explicitly approved stack plus retained-resource cleanup within the agreed window. Abort and report any unexpected resource, request volume, capacity effect or storage inconsistency.

No live command is authorized by this document. The test can establish a meaningful remote evidence component while the local perception and safety decisions remain independent of cloud availability. It does not establish production flight safety or guaranteed availability.

## Storage, cost and teardown

Measured offline from the actual nominal artifacts: **954,289 raw artifact bytes**, **15 packets**, and **1,278,941 bytes of canonical packet JSON** to store in S3. Replaying the identical bundle should leave fifteen objects and fifteen index items, not duplicate the dataset. The existing locally built Lambda artifact contains 20,848,803 uncompressed bytes; deployment staging storage is separate. These are local sizes, not cloud receipts or billed-byte measurements.

Keep the private bucket, conditional writes, encrypted table, TTL/PITR, bounded payloads, log retention and explicit receipt checks. Actual minimal storage is small, but `Retain` keeps the bucket/table after stack deletion. Remove the exact retained bucket/table and dedicated staging objects only with owner-approved data deletion; leave CreditBridge and shared buckets untouched. PITR-related system backup persistence and any retained artifacts must still be reviewed.

Removing reserved concurrency does **not** reduce the price of the same workload. Reserved concurrency has no allocation charge; a higher quota also does not provision paid instances by itself. Volume, duration, storage, logs, KMS and persistence drive the bill. The earlier under-US$1 controlled-test planning allowance and US$5 proposed authorization ceiling remain reasonable planning envelopes for this smaller request plan, not a new quote or guarantee. No free-tier/credit assumption should be used to justify approval. Budget alerts, API throttles and account quota ten do not enforce a hard dollar cap.

One cost detail needs explicit review: the original table has `SSEEnabled: true`, which selects an AWS-managed KMS key and can add KMS request charges. This was not separately itemized in the earlier US$0.66973 planning model; do not present that figure as a complete quote. The concurrency-only candidate preserves it. An optional additional change to `SSEEnabled: false` (or omission of the SSE specification) would retain encryption with an AWS-owned key and avoid that KMS usage path, but is **not included in this candidate** and requires review. No customer-managed key creation is proposed. [CloudFormation encryption selection](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-dynamodb-table-ssespecification.html), [DynamoDB encryption costs](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/EncryptionAtRest.html)

## Comparison with quota 1000

| Consideration | Omit reservation; retain quota ten | Request quota 1000; keep reservation two |
| --- | --- | --- |
| Current functional quota blocker | Removed for an unreserved function, subject to shared headroom | Resolved only after quota approval is applied |
| Source change | One property removed in separate review variant | Existing template unchanged |
| Service Quotas role | Not needed for this route because no quota request is made | Missing role remains a prerequisite; its creation needs separate authorization |
| Isolation | None within the shared pool; potential CreditBridge impact | AegisLand capped/allocated two; much larger remaining pool |
| Expected cost for identical tiny test | Same service usage costs | Same service usage costs; quota/reservation is not provisioned concurrency |
| Time to demo | No quota processing wait after remaining deployment approvals | Role/permission approval plus quota processing, with no deadline guarantee |
| Appropriate use | Explicitly accepted, supervised, brief single-client test | Preferred when isolation/continued operation is required |
| Remaining deployment/IAM/budget gates | All still apply | All still apply |

The console minimum of 1000 is an owner-observed request constraint. The mathematical reservation requirement discussed earlier was not proof that the service would accept a request for 102. No 1000 request is authorized or submitted. Do not retry the stopped 102 workflow or create its service-linked role under this assessment.

## Evidence and remaining blockers

- `evidence/unreserved-feasibility/offline-assessment.json`: network-disabled SAM transformation; only the reservation property differs, nine resources preserved; one-attempt timeout behavior verified; local bundle sizes measured.
- `evidence/unreserved-feasibility/candidate-lint.json`: candidate CloudFormation/SAM schema lint passes.
- `evidence/unreserved-feasibility/preserved-before.json` and the preservation audit: original artifacts and reviewed template remain byte-identical. This assessment does not rebuild the report or ZIP.

The remaining blockers are owner acceptance of shared capacity, an approved deployment/IAM identity and new runtime role, approved staging and budget/notification coverage, exact changeset/build review, paid test/readback authorization and teardown approval. Actual Lambda Arm64 execution, latency, storage receipts and workload interference remain unverified until an authorized live test.

**Fastest safe path before October 26:** review and approve the no-reservation variant plus the supervised single-attempt nominal test scope now, while keeping the existing report/video/Devpost work intact. Deployment itself still requires separate approval of the actual account-bound resources and IAM changes. If the owner cannot accept any contention risk to CreditBridge, stop this route and use quota 1000 with the original reservation or a suitably provisioned separate account; do not trade away that requirement to meet the deadline.
