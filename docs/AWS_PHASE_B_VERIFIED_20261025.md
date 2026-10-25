# AWS evidence verification — completed bounded run

**PASS_CLEANED.** The corrected evidence-storage path passed **34/34 bounded HTTP requests**, with no application retries or redirects. This is a recorded real AWS test; opening the presentation does not invoke AWS or run inference.

| Gate | Observed result |
| --- | --- |
| Unsigned authentication | 1/1 passed; HTTP 403; the completed receipt was reused without resending |
| Signed nominal packets | 15/15 passed; exact typed, identity/checksum-bound ACKs |
| Same-byte duplicate replay | 15/15 passed; the same ACKs and storage identities |
| Planned negative cases | 3/3 passed; HTTP 400, 400, 409 with the expected error bodies |
| Cloud readback | PASS; 15 exact S3 object bodies and 15 strongly consistent DynamoDB item reads |
| Reconstruction | 9/9 files byte-matched the frozen local originals and SHA-256 values |
| Cleanup | Stack, Lambda, API, execution role, log group, retained evidence bucket/table and exact staging object removed; absence verified |

The application-request ceiling was 40; actual use was 34. The test used frozen nominal packets and no new inference. Cloud responses did not change the core safety decisions. TTL, object metadata, completion types, packet hashes and the reconstructed bundle manifest were checked.

The [sanitized result and nine file hashes](../submission/devpost-final-materials-20261024/verification/CLOUD_VERIFICATION_20261025.json) contain no account identifiers, ARNs, live endpoints, physical storage names, credentials or private evidence locations. Raw receipts remain private.

The first live attempt remains **deployment PASS / storage FAIL 503 / teardown PASS**. Its original logs did not retain the exact AWS service/operation/error code. The reserved-word defect was reproduced offline; this later success does not retroactively identify the first failure. The [historical report](AWS_PHASE_B_RESULT.md) and historical evaluations are unchanged.

The existing staging bucket was preserved. Actual billed costs are unknown; the aggregate $5 planning target was not a hard cap. An AWS-managed KMS key, possible PITR system backup, deletion history and delayed charges can persist. The removed API is not a current judge-accessible endpoint; arrange a live demonstration or another separately approved delivery method.

The frozen source and materials ZIPs remain unchanged historical snapshots. Current authoring pages and this dated addendum describe the later live verification; the source ZIP SHA does not identify these edits or a Git commit. Simulation, field safety, real-time performance and GPU claims retain their existing limits.
