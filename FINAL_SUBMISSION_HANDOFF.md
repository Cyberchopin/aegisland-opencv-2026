# AegisLand — final submission handoff

Deadline: **October 26, 2026, 11:45 PM PDT**. This is an owner-review package; the competition submission remains the owner's task. Official requirements were [rechecked](docs/candidates/OFFICIAL_RULES_AUDIT_20261024.md).

## Verified results

- Historical/saved result: 121 competition tests passed; Lambda ZIP/source/dependency checks, lint, format and template checks pass. Historical/saved full core suite: **215 passed, 1 optional CUDA integration skipped**, 216 collected,22m59s. See the [validation matrix](docs/candidates/OFFLINE_VALIDATION_MATRIX.md).
- Three retained OpenCV 5 scenarios: 230 decoded frames/events, no hardware commands. Saved GPS/low-light regression: 80 decisions unchanged. OpenCV performs substantive flow/edge/texture/compensation/CLAHE and video processing.
- Existing reviewed candidate is intact: `approval/final-hardening-20261023-r2/`, Lambda SHA256 `52e37629b1434e9a898448ddd5f63aa94ce367b1f552fdb5c082c92ea816aa39`. Reserved-word aliases and hardening pass offline; resources/IAM/encryption are unchanged.
- Current cloud result: **34/34 bounded HTTP requests passed** — unsigned 1/1, nominal 15/15, duplicate 15/15, negative 3/3. Cloud readback passed; reconstructed files byte-matched **9/9**. AWS test resources and the exact staging object were cleaned. See the [sanitized dated result](docs/AWS_PHASE_B_VERIFIED_20261025.md). The first failed storage run and its unknown historical error code remain preserved.

## Deadline risks, in order

1. **Video and delivery:** record the current 2:55 demonstration and provide judge-accessible source/report links and a real demonstration arrangement. The completed AWS test was cleaned; it is not a running public endpoint.
2. **Judge/source access:** share competition source **and access to the pinned core**; arrange a working live demonstration or approved endpoint. None is performed automatically.
3. **Owner eligibility/rights/form:** confirm team, registration, distribution/media rights and Agentic Vision selection; preview every actual Devpost field/link and submit. Earlier reports/ZIPs are historical.

## Cloud verification is complete

No further AWS operation is needed for this submission package. The [completed bounded test](docs/AWS_PHASE_B_VERIFIED_20261025.md) used the reviewed r2 artifact, exact typed ACKs, full readback and scoped cleanup. Actual costs remain unknown; planning targets were not enforceable caps. Historical approval plans are retained records, not instructions to rerun deployment.

## Files and personal completion

- [Current report](submission/entry-20261024/TECHNICAL_REPORT.html), [judge entry/reproduction](submission/entry-20261024/START_HERE.md), [Devpost copy](submission/entry-20261024/DEVPOST.md).
- [2:55 recording plan](submission/devpost-final-materials-20261024/03_分秒镜头表.md), [four authentic captures/diagram](submission/entry-20261024/VISUAL_ASSETS.md). Record 1080p, show the actual trace transitions and sanitized cloud success alongside the historical first failure; hide private consoles. Use the current English narration and check the exported duration is under three minutes; the old 3:45 plan is historical/superseded.
- Source release target: `submission/final-20261024/`; its ZIP, public file manifest, checksum and static `VERIFICATION.json` are the release records. Extracted-package tests/inference were not run under the owner's lightweight-only instruction. The archive excludes private configuration/logs and the owner-specific staging plan. Lambda deployment ZIPs remain separate review artifacts.

Personally: confirm rights/eligibility/team; record/upload video; provide signed-out judge/source/report access and a demo arrangement; paste reviewed Devpost copy, select Agentic Vision, preview and press Submit with margin before the deadline. Keep October 27 free for the midterm. This handoff grants no AWS, merge or external-submission authority; branch publication follows only the owner's separate PR authorization.

## Frozen ZIP metadata — lightweight verification

Archive: `submission/final-20261024/aegisland-judge-source-candidate.zip` (local attachment, excluded from Git), **9,181,179 bytes**, 498 entries. SHA-256: `8a03304e33ba80f9c19a2ca69022bfd9369674f899497ceda4db6a6a6bb0cfe4`. Saved ZIP integrity, manifest, required-content and privacy checks passed. The large files are related packet evidence and CPU replay data. Those archive checks were static. Current local documentation validation reran only the 121-test competition suite, with no inference or AWS calls; the full core result remains historical.

The archive remains unchanged. This external handoff/matrix metadata update follows the frozen snapshot; their copies inside the ZIP retain the build-time wording. The local attachment sidecar `submission/final-20261024/VERIFICATION.json` explicitly records static checks only, not an executed extraction/demo test. Complete local status is in the local-only `submission/final-20261024/UNCOMMITTED_FILES.txt`.

The published PR is an allowlisted source/documentation subset, not the frozen ZIP snapshot. Its commit SHA identifies the PR tree; the source ZIP SHA identifies only the separate immutable artifact. The existing commit has four successful GitHub checks; these local documentation updates have not been committed or run in GitHub CI. See the artifact-boundary notes before running historical packagers.
