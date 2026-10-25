# Engineering assessment — offline hardening candidate, October 23

**The local demonstration is reproducible; cloud evidence storage and final submission are not ready.** The first real AWS stack deployed and was torn down successfully, but its first signed packet returned 503. The current candidate fixes reproducible defects without changing safety policy, dependencies, infrastructure or IAM. It still needs separately authorized live verification.

This document supplements preserved reports; it does not revise the historical cloud outcome. Start with [the current handoff](../../FINAL_SUBMISSION_HANDOFF.md), [validation matrix](OFFLINE_VALIDATION_MATRIX.md) and [judge entry](../../submission/entry-20261024/START_HERE.md). The recording target is the [current 2:55 plan](../../submission/devpost-final-materials-20261024/03_分秒镜头表.md); earlier handoffs and recording plans are historical/superseded.

## Confirmed strengths

- OpenCV 5 measurements feed a deterministic observe/reconsider/rescan/decision loop. Human-review states and the no-hardware command adapter are visible in actual traces. Emergency reserve behavior is not misrepresented as a universal human gate.
- Three fixed synthetic scenarios retain 230 events and decoded frames with hashes/provenance. A new GPS/low-light run preserves all 80 complete decision dictionaries and produces 80 decoded frames. These are correlated simulation samples, not independent missions or field accuracy.
- The pinned core remains clean at `eda23d3ea646e8943287703c07a91e9a3b2909fb`. Tests exercise policy, approval, GPS-denied behavior and PX4 shadow supervision without altering them.
- Stored object bytes and a consistent index read are required before acknowledgement. Conditional writes prevent overwrite; identical and conflicting concurrent requests are covered offline. No timeout, partial write or invalid acknowledgement is promoted to success.
- The historical nine-resource stack, IAM-authenticated route and deployed code hash were verified. Verification halted on error, partial evidence was exported and approved teardown completed. This is real deployment/failure evidence, not a cloud-storage success claim.

## Verified fixes and boundaries

| Finding | Classification | Candidate correction / proof |
| --- | --- | --- |
| Bare Sequence in DynamoDB condition | Confirmed expression defect; historical cause remains unproven | Aliases #trace_id/#sequence preserve conditional semantics; reserved-word fixture red→green and real SDK parameter contract |
| Numeric Complete=1/Decimal(1) accepted as True | Confirmed offline false-ack defect on malformed index | Require actual boolean True; two failing cases now reject with409 |
| ACK sequence=false/0.0 accepted as integer0 | Confirmed offline false-success defect | Require exact integer type; first malformed ACK stops attempts=1 upload as incomplete |
| Deeply nested JSON escaped validation | Confirmed offline input error | RecursionError now returns400 before storage; red→green test |
| Original logger retained only ClientError | Confirmed observability gap | Safe service/operation/error-code diagnostics; public failure body unchanged; no raw messages/ARNs/credentials |

Only `cloud/competition_cloud/storage.py` and `client.py` differ in the final Lambda ZIP from the original reviewed ZIP. All SDK/dependency bytes are identical. New tests live in `tests/test_storage_adversarial.py` and `tests/test_transport_security.py`; the original SDK contract and reserved-word fixture remain in `test_aws_reliability.py`. Packaging/check tools and CI changes improve review/reproduction without executing AWS.

The first live error's exact service, operation and code are **UNVERIFIED**: saved logs omitted them. DynamoDB PutItem/ValidationException is an explicit offline reproduction consistent with S3-only state. No KMS denial, missing IAM grant or table-schema error is established. Do not widen IAM or disable encryption based on that hypothesis.

Offline simulated signature/expired-time denials prove client stopping behavior, not live API Gateway authentication enforcement. The real unsigned403 and signed handler response are historical observations. Atomic service fakes exercise interleavings but cannot prove AWS availability, contention rates or distributed transaction semantics. Acknowledgement verifies bytes/index at observation time, not permanent retention or cross-service atomicity.

## Remaining risks and blockers

| Status | Item / consequence |
| --- | --- |
| FAIL | A complete bundle has not been verified in AWS; the working-cloud eligibility/demo gate remains open |
| UNVERIFIED | Final candidate runtime/storage behavior, effective permissions, quota headroom and actual aggregate bill |
| ACCEPTED RISK | Unreserved Lambda shares quota ten; one sequential uploader and best-effort throttles are not capacity isolation or spending caps |
| UNVERIFIED | Current official rules/form, eligibility/rights/team registration and source distribution permission; no external calls were made during hardening |
| FAIL | Recorded team/video, signed-out judge/source access and final Devpost publication are not completed here |
| LIMITATION | Fixed synthetic scenes and heuristic risk/confidence; commands do not change future scene frames or drive flight dynamics |
| LIMITATION | CPU smoke ran on a nonisolated host. Historical CUDA summary lacks raw CSV/profile/executable here; no new CUDA or speedup claim |
| KNOWN INPUT EDGE | Unsupported extreme-aspect-ratio profiling input can resize to one row and fail; verified demo dimensions work. Core is unchanged; do not use that arbitrary input in the deadline demo |

The final proposed cloud artifact is [final-hardening-20261023-r2](../../approval/final-hardening-20261023-r2/resource-manifest.json), SHA-256 `52e37629b1434e9a898448ddd5f63aa94ce367b1f552fdb5c082c92ea816aa39`. Earlier b26ed5… and intermediate396eb0… packages are preserved but are **not the final source candidate**. They must not be substituted into the next plan.

## Financial/security and historical preservation

Same nine resources, generated Lambda execution role, six scoped application actions and one inline policy; no extra grants, service-linked role, customer-managed key, paid service or quota request. Same conservative $0.921067 full-run planning model. Two full-run allowances total $1.842134; actual first-run charges remain unknown. All attempts share the accepted $5 planning target, not an enforced cap or new separate allowance.

The private Phase B ZIP is verified mode0600 at `~/.local/share/aegisland/aws-phase-b/aegisland-phase-b-private-evidence.zip`, outside temporary storage and Git, matching its historical SHA. Raw private evidence is not in the public package. The historical owner-specific staging-plan document is retained locally but ignored/omitted from public source because it contains the private configured bucket name. Its omission is explicit in the public package manifest; its source bytes are not rewritten.

No AWS call, paid query, deployment, push, merge or submission occurred during hardening. No local commit was made: the reviewed source archive/content manifest, base commit and core pin provide the candidate snapshot; owner-approved publication remains separate.
