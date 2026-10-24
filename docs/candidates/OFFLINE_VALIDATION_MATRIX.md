# Final offline validation matrix — October 24, 2026

The previously interrupted 216-test collection is not a pass count. Exact argv, stdout/stderr, exit code and timing are in the linked JSON records. Python network connections are disabled for the full core run and final competition/package checks. No AWS service was contacted.

| Check | Actual result | Exact evidence |
| --- | --- | --- |
| Full pinned core suite | **215 passed, 1 skipped** in 1379.49s; optional native CUDA only | [complete command/output](../../evidence/submission-final-20261024/core-full-tests.json) |
| Competition suite | 121 passed | [command/output](../../evidence/submission-final-20261024/competition-tests.json) |
| Reviewed Lambda ZIP + source/dependency/manifest/imports | PASS | [check](../../evidence/submission-final-20261024/cloud-candidate-check.json) |
| Disposable exact candidate rebuild | PASS, ZIP bytes and complete manifest identical | [rebuild](../../evidence/submission-final-20261024/cloud-rebuild.json) |
| Python lint / formatting | PASS | [lint](../../evidence/submission-final-20261024/release-tools-lint.json), [format](../../evidence/submission-final-20261024/release-tools-format.json) |
| All two SAM sources and expanded candidate schema | PASS | [cfn-lint](../../evidence/submission-final-20261024/template-lint.json) |
| Dependency consistency | PASS | [pip check](../../evidence/submission-final-20261024/pip-check.json) |
| Current report/recording-document hashes and four retained captures (static PR refresh, no new execution) | PASS | [asset audit](../../evidence/submission-final-20261024/recording-assets-check.json) |
| Fresh prior GPS run and decision parity | 80 frames/events; all 80 decision dictionaries preserved | [parity](../../evidence/hardening/decision-and-hash-parity.json) |
| Historical source/demo hashes | PASS, three recorded scenario inventories | Same parity record; final historical-preservation audit follows source freeze |
| Public source archive/extraction | Static integrity, all file hashes, privacy/path and required-content checks PASS; 498 entries/9,181,179 bytes. Extracted-package tests/demo NOT RUN under owner instruction. Existing 121-test and fresh-demo records are historical saved results, not reruns | Release sidecar |
| Live corrected cloud storage | UNVERIFIED; no second live test authorized | [original failure](../AWS_PHASE_B_RESULT.md) |
| First deployment and teardown | Historical PASS; signed storage verification FAIL 503 | [record](../../evidence/aws-phase-b/result.json) |
| Current official requirements | Rechecked using public Devpost pages; signed-in form/eligibility not completed | [rules audit](OFFICIAL_RULES_AUDIT_20261024.md) |
| Video recording / source access / judge arrangement / submission | OWNER ACTION REQUIRED | [handoff](../../FINAL_SUBMISSION_HANDOFF.md) |

The full-core run uses the pinned unmodified source, one OpenCV thread, OMP/OpenBLAS limits and no optional native CUDA executable. These are test-resource settings, not a change to safety policy or a performance benchmark. CUDA integration may skip; its skip is reported separately. Host import checks are not new AWS Arm64 execution proof.

Historical red/green tests, malformed-index/ACK cases, concurrent requests, partial writes and negative-response tests remain in `evidence/storage-remediation/` and `evidence/hardening/`. Simulated 403 signature/time errors prove client stop behavior only. The first live error code remains unknown. The current Lambda SHA is 52e37629b1434e9a898448ddd5f63aa94ce367b1f552fdb5c082c92ea816aa39.

Frozen source ZIP SHA-256: `8a03304e33ba80f9c19a2ca69022bfd9369674f899497ceda4db6a6a6bb0cfe4`. Static sidecar: `submission/final-20261024/VERIFICATION.json`. This external metadata correction does not alter the ZIP or its packaged matrix. No new test, inference, upload, deployment or paid call occurred.
