# AegisLand — final submission handoff

Deadline: **October 26, 2026, 11:45 PM PDT**. This is a local owner-review package; nothing has been published or submitted. Official requirements were [rechecked](docs/candidates/OFFICIAL_RULES_AUDIT_20261024.md).

## Verified results

- 121 competition tests pass; Lambda ZIP/source/dependency checks, lint, format and template checks pass. Full core suite: **215 passed, 1 optional CUDA integration skipped**, 216 collected,22m59s. See the [validation matrix](docs/candidates/OFFLINE_VALIDATION_MATRIX.md).
- Three retained OpenCV 5 scenarios: 230 decoded frames/events, no hardware commands. Fresh GPS/low-light run: 80 decisions unchanged. OpenCV performs substantive flow/edge/texture/compensation/CLAHE and video processing.
- Existing reviewed candidate is intact: `approval/final-hardening-20261023-r2/`, Lambda SHA256 `52e37629b1434e9a898448ddd5f63aa94ce367b1f552fdb5c082c92ea816aa39`. Reserved-word aliases and hardening pass offline; resources/IAM/encryption are unchanged.
- Historical AWS result remains **deployment PASS / storage FAIL 503 / teardown PASS**. Zero successful storage acknowledgements. Exact old ClientError code is unknown; the correction is not cloud-verified. Private evidence remains preserved outside temporary storage and Git.

## Deadline risks, in order

1. **Cloud verification:** the intended complete evidence-storage path remains unproven. The shortest safe attempt is the existing reviewed Phase A, followed by review and separate new-UUID Phase B. No new architecture or IAM expansion.
2. **Video and judge/source access:** record the real team introduction and working demo; upload an accessible video; share competition source **and access to the pinned core**; arrange a working live demonstration or approved endpoint. None is performed automatically.
3. **Owner eligibility/rights/form:** confirm team, registration, distribution/media rights and Agentic Vision selection; preview every actual Devpost field/link and submit. Earlier reports/ZIPs are historical.

## Exact next AWS authorization

> Authorize second Phase A only, using creditbridge-deployer in us-east-1, the privately configured AegisLand account/staging bucket and stack aegisland-opencv26-evidence: revalidate identity/security/teardown/manifest; upload exactly once the reviewed final-hardening-20261023-r2 Lambda ZIP with SHA256 52e37629b1434e9a898448ddd5f63aa94ce367b1f552fdb5c082c92ea816aa39; create one CREATE Change Set named aegisland-unreserved-hardening2-review1 and inspect it **without execution**. Preparation charges count toward the existing aggregate $5 planning target. No IAM/policy, quota, application or unrelated changes.

See [exact Phase A plan](approval/final-hardening-20261023-r2/PHASE_A_PLAN.md). [Phase B](approval/final-hardening-20261023-r2/PHASE_B_PLAN.md) requires another approval naming its **new UUID**, one execution, 34 planned HTTP attempts (ceiling 40, attempts=1), readback and complete teardown. Do not reuse the old UUID. The $0.921067 full-run estimate is not an actual bill or hard cap.

## Files and personal completion

- [Current report](submission/entry-20261024/TECHNICAL_REPORT.html), [judge entry/reproduction](submission/entry-20261024/START_HERE.md), [Devpost copy](submission/entry-20261024/DEVPOST.md).
- [2:55 recording plan](submission/devpost-final-materials-20261024/03_分秒镜头表.md), [four authentic captures/diagram](submission/entry-20261024/VISUAL_ASSETS.md). Record 1080p, show the actual trace transitions and cloud failure, hide private consoles. Use the current English narration and check the exported duration is under three minutes; the old 3:45 plan is historical/superseded.
- Source release target: `submission/final-20261024/`; its ZIP, public file manifest, checksum and static `VERIFICATION.json` are the release records. Extracted-package tests/inference were not run under the owner's lightweight-only instruction. The archive excludes private configuration/logs and the owner-specific staging plan. Lambda deployment ZIPs remain separate review artifacts.

Personally: approve or defer the bounded cloud attempt; confirm rights/eligibility/team; record/upload video; provide signed-out judge/source/report access and a demo arrangement; paste reviewed Devpost copy, select Agentic Vision, preview and press Submit with margin before the deadline. Keep October 27 free for the midterm. This handoff grants no AWS, merge or external-submission authority; branch publication follows only the owner's separate PR authorization.

## Frozen ZIP metadata — lightweight verification

Archive: `submission/final-20261024/aegisland-judge-source-candidate.zip` (local attachment, excluded from Git), **9,181,179 bytes**, 498 entries. SHA-256: `8a03304e33ba80f9c19a2ca69022bfd9369674f899497ceda4db6a6a6bb0cfe4`. ZIP integrity, every manifest hash, required-content and private-identifier/path scans pass. The large files are related packet evidence and CPU replay data. No tests, inference or cloud operations were rerun.

The archive remains unchanged. This external handoff/matrix metadata update follows the frozen snapshot; their copies inside the ZIP retain the build-time wording. The local attachment sidecar `submission/final-20261024/VERIFICATION.json` explicitly records static checks only, not an executed extraction/demo test. Complete local status is in the local-only `submission/final-20261024/UNCOMMITTED_FILES.txt`.

The published PR is an allowlisted source/documentation subset, not the frozen ZIP snapshot. Its commit SHA identifies the PR tree; the source ZIP SHA identifies only the separate immutable artifact. CI remains pending GitHub verification. See the artifact-boundary notes before running historical packagers.
