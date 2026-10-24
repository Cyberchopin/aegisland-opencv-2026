# Historical morning handoff — superseded

**Historical/superseded:** use [FINAL_SUBMISSION_HANDOFF.md](../../FINAL_SUBMISSION_HANDOFF.md) and the [current 2:55 recording plan](../../submission/devpost-final-materials-20261024/03_分秒镜头表.md). The dated workflow below is retained as history, not the current release inventory.

**Keep the working local demo. Review one new cloud candidate, capture the video and finish access/eligibility gates. Do not add features.** Deployment previously passed, storage verification failed and teardown passed. The proposed correction is not yet cloud-verified.

1. Read [engineering assessment](ENGINEERING_ASSESSMENT.md) and [validation matrix](OFFLINE_VALIDATION_MATRIX.md). Use final-hardening-20261023-r2, not the preserved older correction or old Change Set UUID. The final Lambda SHA is `52e37629b1434e9a898448ddd5f63aa94ce367b1f552fdb5c082c92ea816aa39`.
2. If ready, approve **second Phase A only** using the exact wording in [PHASE_A_PLAN.md](../../approval/final-hardening-20261023-r2/PHASE_A_PLAN.md). This covers one new artifact upload and one CREATE Change Set, never execution. The existing private account/bucket must be revalidated; no live check was performed overnight.
3. Review the resulting new Change Set's nine Add actions, code hash, complete server template, policies and cost/permission limitations. Only then separately authorize [Phase B](../../approval/final-hardening-20261023-r2/PHASE_B_PLAN.md) with its **new UUID**, bounded verification and complete teardown. The first run's exact AWS error cannot be recovered from its old log. Stop at any unexpected response; no retry or IAM workaround.
4. In parallel, rehearse [the three-minute local demo](../../submission/candidate-20261023/DEMO_SEQUENCE.md), then record [the 2:45 script](../../submission/candidate-20261023/VIDEO_SCRIPT.md) with the real team introduction. Use the four [authentic frame captures](../../submission/candidate-20261023/screenshots/MANIFEST.json) and [current architecture](../../submission/candidate-20261023/ARCHITECTURE.svg). Show actual rescan/approval/decision evidence; label retained playback. The CPU path works without cloud credentials.
5. Confirm eligibility, reused-core rights/license, team/award selection, source/demo access and current official Devpost fields. Offline hardening did not refresh rules or inspect the form. Core/dependencies are not bundled; initial setup needs network. Test final links while signed out and choose a judge-accessible working local-demo arrangement. The ingestion API is not a judge interface.
6. Review the fresh source candidate's manifest and extraction result, plus the [current report addendum](../../submission/candidate-20261023/TECHNICAL_REPORT_ADDENDUM.md) and [Devpost copy](../../submission/candidate-20261023/DEVPOST_DESCRIPTION.md). Approve publication/submission separately. No implementation has been pushed or merged from this session.

Aim for an October 25 engineering freeze. Use October 26 for capture polish, access checks and submission well before **11:45 PM PDT**. Preserve October 27 for the midterm. If the next authorized cloud attempt fails, retain its evidence and make an owner decision on eligibility; do not spend the deadline widening IAM, writing kernels or building another product.

## Current package and preservation rules

The source-review ZIP is under `submission/final-hardening-20261023/` with a SHA file and `PUBLIC_SOURCE_MANIFEST.json`; use its extraction verification record, not the historical71-test package verification. The separate Lambda ZIP/manifest/cost model are under `approval/final-hardening-20261023-r2/`. The source archive omits Lambda dependency archives and private owner configuration/logs; the Lambda ZIP is a separate deployment review artifact.

The private Phase B archive is already checksum-verified outside `/tmp` and Git, mode0600, at `~/.local/share/aegisland/aws-phase-b/aegisland-phase-b-private-evidence.zip`. Never add it or owner configuration to Git. All earlier approvals, reports, failure receipts and prior submission ZIPs are preserved. No historical failure is relabeled as success.

## Stop boundary

There is no authorization for any next AWS API call, upload, Change Set, execution, paid query, extra workload, IAM edit, quota request, push, merge or Devpost submission. Ordinary offline fixes/tests may continue, but any source change after this snapshot requires rechecking the artifact/hash/manifest before another approval.
