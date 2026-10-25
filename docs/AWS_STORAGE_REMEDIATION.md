# Offline storage investigation and candidate correction

**Historical result remains deployment PASS, cloud verification FAIL, teardown PASS.** This candidate has not been uploaded or deployed. The original [Phase B report](AWS_PHASE_B_RESULT.md), approval ZIP, failure receipts, simulation evidence, submission ZIP and storyboard are preserved unchanged.

## Evidence preservation and limits

First verified the private archive at `~/.local/share/aegisland/aws-phase-b/aegisland-phase-b-private-evidence.zip`, outside `/tmp` and Git. It is mode `0600`, 222,409 bytes, and matches the historical SHA-256 `6e717d25a48b709125dbc0b70fdf08d90ca26c23e2ace05d740c0014057af8a7`. Neither its contents nor private AWS identifiers were published. Only saved local evidence was inspected; no AWS calls or downloads occurred.

The precise **historical AWS service, operation and error code are UNVERIFIED**. All five saved Lambda log events were inspected: the sole storage warning records only `ClientError`. No raw exception response or traceback exists in the saved archive. An offline test cannot recover information the original logger discarded.

The confirmed live observations remain: unsigned HTTP 403; first signed packet HTTP 503 `storage_unverified`; one matching sequence-0 S3 object; no sequence-0 DynamoDB item; zero successful storage acknowledgements; no retry. These do not independently distinguish an S3 read denial from a DynamoDB validation/access/encryption error.

## Concrete defect and minimal correction

The deployed `PutItem` condition was:

```text
attribute_not_exists(TraceId) AND attribute_not_exists(Sequence)
```

`SEQUENCE` is a DynamoDB reserved word. Attribute names are valid in item/key schemas while still requiring aliases in expressions. The correction is:

```python
ConditionExpression="attribute_not_exists(#trace_id) AND attribute_not_exists(#sequence)",
ExpressionAttributeNames={"#trace_id": "TraceId", "#sequence": "Sequence"},
```

This preserves conditional insertion and duplicate identity. A modeled DynamoDB `PutItem / ValidationException` produces the observed S3-only/no-index/503 state. It is a **deterministic reproduction of a concrete expression defect**, not a recovered live error code or proof that no other live issue exists. AWS reference links, not fetched during this offline work: [expression attribute names](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ExpressionAttributeNames.html), [reserved words](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ReservedWords.html).

The original fake service ignored expression syntax, and Botocore Stubber checked expected parameters without evaluating DynamoDB expressions. Both therefore accepted the invalid condition. The strict fake now models this specific reserved-word rule; it is explicitly not a complete DynamoDB emulator. The original core write-order regression keeps expression validation disabled only for that historical test, so it continues to isolate the separate legacy ordering defect. Core code remains unchanged.

The only packaged module change is `competition_cloud/storage.py`: aliases plus safe diagnostics for S3 PutObject/GetObject and DynamoDB PutItem/GetItem. Failures log the controlled service/operation and a validated AWS error-code token. Raw AWS messages/responses, resource ARNs, credentials and tracebacks are excluded. The public 503 body, byte verification, conditional-write handling and acknowledgement contract remain unchanged.

## Actual role, table and encryption assessment

| Area | Saved evidence / conclusion |
| --- | --- |
| Role trust | Lambda service only; one inline policy; no saved permissions boundary |
| S3 | PutObject/GetObject grant matches the actual new bucket's `evidence/*` prefix; no missing action identified for conditional PUT and body GET |
| DynamoDB | PutItem/GetItem grant matches the actual new table; no UpdateItem, Query or Scan is used or needed |
| CloudWatch | CreateLogStream/PutLogEvents grant matches streams in the pre-created log group; runtime does not create the group |
| KMS | Evidence/staging S3 uses SSE-S3. DynamoDB uses the unchanged AWS-managed key configuration. Lack of a direct KMS grant alone does not establish a defect; no new KMS/IAM permission is proposed |
| Table | The reviewed deployed template defines string TraceId / numeric Sequence, matching the code, with TTL ExpiresAt and PITR. The saved deletion receipt confirms on-demand billing and SSE enabled/KMS, but does not include key-schema fields. No schema mismatch is established. Export records show no sequence-0 item after failure |
| Condition | Bare Sequence is invalid in the expression; aliasing fixes the syntax without changing table schema or security controls |

Saved evidence does not establish an actual KMS denial, throttling, missing key grant, organization policy denial, or incorrect table schema. Do not add permissions or disable encryption to resolve an unobserved cause.

The S3-first path intentionally permits a partial object when the subsequent index stage fails. It must return 503, never success. A separately authorized replay checks actual existing bytes, conditionally inserts the missing index, then uses a consistent read before acknowledgement. It is not an atomic cross-service transaction or a guarantee of permanent storage. Conflicting data remains 409; unknown outcomes remain unverified; the supervised demo still uses attempts=1 with no automatic replay.

## Offline validation

- New regression against old code: **1 failed**, returned 503 instead of 200. With the correction: **1 passed**. Exact commands/outputs: [red](../evidence/storage-remediation/red-regression.json), [green](../evidence/storage-remediation/green-regression.json).
- **77 competition tests passed**, including three real local scenario bundles reconstructed in mocked storage, idempotency/partial failures, four diagnostic stages and privacy checks. [Results](../evidence/storage-remediation/competition-tests-final.json).
- **56 targeted pinned-core regression tests passed**; safety policy unchanged. [Results](../evidence/storage-remediation/core-regression.json).
- Ruff and expanded-template cfn-lint passed. New ZIP handler/SDK imports and private renderer passed; only storage.py content differs from the reviewed original ZIP. This is not a live Arm64 test. [Package verification](../evidence/storage-remediation/package-verification-final.json).

One intermediate full-suite run exposed the historical core fixture's expression handling; its explicit ordering-only mode fixed the fixture, without changing core. One packaging verification initially compared ZIP entry order instead of file contents; corrected verification proves identical file sets/dependencies and one changed module. All intermediate outputs are retained.

## Revised deployment and cost gate

Candidate: [resource-manifest.json](../approval/storage-remediation-1/resource-manifest.json), [build provenance](../approval/storage-remediation-1/build-provenance.json), [cost estimate](../approval/storage-remediation-1/cost-estimate.json), [commands and approvals](../approval/storage-remediation-1/COMMANDS.md).

- Same `infra/template.unreserved-review.yaml`, same nine resources, one new execution role with the same inline policy; **no IAM-policy, resource, encryption or quota expansion** relative to the original reviewed design.
- New code SHA-256: `b26ed5b7c96660b2d263657da26e8a20bcb55c17c071dbd9dfbe3e0c3e0e97b2`.
- Dependencies are reused byte-for-byte from the verified original ZIP. No package downloads, CUDA work or safety-decision changes.
- Same conservative full-run planning allowance **$0.921067**. Two full-run allowances total **$1.842134**, not a measured aggregate bill. First-run actual charges remain unavailable. The prior $5 target must include all attempts; it is not reset or enforceable. No new workloads are authorized.
- The original 34-request plan remains: one unsigned denial, 15 nominal packets, one identical 15-packet replay, three expected negative cases; hard client ceiling 40, one uploader, attempts=1, stop on unexpected result. Preserve bounded diagnostics before teardown if another failure occurs.

Next approval is **second Phase A only**: revalidate the existing private account/bucket, approve one upload of this new exact ZIP and one CREATE Change Set named `aegisland-unreserved-remediation1-review1` on `aegisland-opencv26-evidence`, using `creditbridge-deployer` / `us-east-1`, without execution. Its server-side template and all resources must then be reviewed. A second, separate Phase B approval must name the resulting **new** Change Set UUID and explicitly cover creation, bounded paid verification, diagnostic preservation and complete teardown under the aggregate spending target. The old UUID must never be executed again.

Until new authorization, submission work should use the existing truthful offline demo and record the real first AWS deployment/failure/teardown. A reliable cloud-storage success remains **UNVERIFIED**.
