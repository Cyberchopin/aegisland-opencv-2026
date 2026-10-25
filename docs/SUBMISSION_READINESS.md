# Submission readiness — Stages A1–A3

**Local baseline works. The submission is not yet ready.** The offline technical report is written; verified AWS execution, judge access arrangement, recorded submission video and final publication remain outstanding.

## Quota authorization and offline package update

The owner authorized **one** Lambda concurrency quota request to 102 through the verified profile in us-east-1, with no IAM or service-linked-role creation. The precheck verified the non-root caller/account internally and `L-B99A9384`, current value 10, requested value 102. IAM `GetRole` for `AWSServiceRoleForServiceQuotas` returned `NoSuchEntity`. **Stopped before submission: zero request attempts, no request ID, no pending request from this attempt.** No IAM, CreditBridge resource or deployment changes were made. The missing role requires separate owner direction; the limited authorization does not permit creating it implicitly.

Completed offline owner-review deliverables: [technical report](TECHNICAL_REPORT.md), [Devpost copy](../submission/DEVPOST.md), [recording script](../submission/VIDEO_SCRIPT.md), updated [storyboard](VIDEO_STORYBOARD.md), [judge entry point](../submission/JUDGE_START_HERE.md) and [release checklist](../submission/SUBMISSION_CHECKLIST.md). The local review archive is generated with a file inventory/hash; it is not uploaded or a final source commit. The latest suite passes **71 competition tests**, including three new mocked quota guard cases; lint passes. Retained core regression remains 56 tests and core/runtime/template hashes are unchanged.

The technical report is now written, superseding older “outline only” status below. Actual AWS execution, quota resolution, judge-accessible publication, recorded video, team/rights confirmation and Devpost submission remain open gates.

## A3 update — October 22, 2026

**AWS deployment remains on HOLD.** After the initial offline-only decision, the owner verified a non-root IAM user and authorized only `creditbridge-deployer` for read-only discovery in us-east-1. CLI 2.38.4 and non-root identity were verified; the account ID was kept internal. Other profiles were not used. No deployment, resource changes or billable operations were performed.

Read-only discovery found a concrete blocker: Lambda concurrency quota and unreserved capacity are both ten, which cannot support the template's two reserved executions under the required unreserved-pool rule. No quota request or template fallback was applied. Proposed stack/function/log names have no observed collision. Two budgets have four notification/subscriber bindings, but project suitability remains unverified. Twenty-six sampled permission simulations allowed the proposed actions; that is neither full deployability proof nor approval to reuse the CreditBridge identity. See [actual preflight results](AWS_PREFLIGHT_RESULTS.md), [permission plan](AWS_PERMISSION_PLAN.md) and [resource manifest/teardown](AWS_RESOURCE_MANIFEST.md).

Local SAM translation verified nine generated resources, IAM/SigV4 route authentication, the resource-scoped Lambda role, private/TLS/conditional-write bucket policy and retained bucket/table. The generated Lambda API permission is restricted to the API and POST path but uses a stage wildcard. No source template, core policy or runtime behavior changed in A3.

Prepared [owner approval and cost/security gate](AWS_OWNER_APPROVAL.md): explicit IAM/staging/deployment/test/teardown approvals, account-check prerequisites and a bounded nominal-bundle verification plan. The conservative planning model totals US$0.66973 under its assumptions; propose a US$1 operating allowance and a US$5 owner authorization ceiling. This is not a bill guarantee or a hard cap; real tariffs, budget controls and account spend remain unverified.

Offline submission preparation is complete as planning material: [technical-report outline](TECHNICAL_REPORT_OUTLINE.md), [judge demo sequence](JUDGE_DEMO_SEQUENCE.md), and [4:40 video storyboard](VIDEO_STORYBOARD.md). The actual technical report, recorded video, judge arrangement and meaningful AWS execution are still pending. Preserve the October 25 engineering freeze and October 27 midterm.

## A2 update — October 22, 2026

The competition AWS candidate is ready for owner review of a scoped deployment approval. **Deployment execution remains gated** on account/region, budget, IAM/quotas and explicit authorization. There is still no evidence of actual AWS execution; the competition's cloud requirement remains unmet by this local work.

| Status | A2 finding |
| --- | --- |
| PASS | 60 deterministic mocked AWS tests, plus five A1 competition tests: 65 competition tests total |
| PASS | 56 targeted core regression tests; unchanged safety policy and clean core checkout |
| PASS | Competition backend verifies actual S3 bytes and a strongly consistent DynamoDB index before acknowledging storage |
| PASS | Bounded retries, explicit socket/SDK timeouts, checksum-bound acknowledgements, partial-bundle failure reporting and idempotent replay tested |
| PASS | All three A1 bundles reconstruct byte-for-byte through mocked storage; deterministic local plans contain 15, 22 and 17 packets |
| PASS | Fresh GPS/low-light simulation produces 80 valid events and decoded frames; retained A1 artifacts remain unchanged |
| PASS | Python lint and offline competition SAM template translation/schema validation |
| PASS | Local SAM build targeting Python 3.12 Arm64 and staged package imports/source-hash checks on the host; actual Lambda execution remains unverified |
| FAIL | Original core backend still has reproduced acknowledgement/partial-write bugs; original SAM template fails current translation because IAM authorizer enabling is missing |
| UNVERIFIED | Real deployment, IAM enforcement, Arm64 runtime execution, cloud receipts, spend and GitHub execution |

New code lives in `cloud/`, `infra/template.yaml` and `scripts/evidence_cloud.py`, with protocol/failure/SDK tests in `tests/test_aws_reliability.py`. This is a separate competition service, not an upstream safety or trace-client modification. The simulation wrapper stays local-only. Run the new evidence uploader after simulation and use its `/evidence` contract; do not enable the original core cloud client.

See [AWS reliability](AWS_RELIABILITY.md) for results and retained commands, and [AWS deployment gate](AWS_DEPLOYMENT_GATE.md) for exact prerequisites, approval scope, spend boundaries and post-deployment acceptance. Those documents supersede A1's proposed next task. The next action is owner review of this concrete candidate and confirmation of account/budget prerequisites, followed by an explicitly authorized nominal-bundle deployment verification.

The remaining A1 assessment below is retained as the inspection baseline. Its backend observations refer to the original pinned core, which A2 intentionally leaves unchanged.

Assessment date: October 21, 2026. Scope: local checkout inspection, official competition pages, targeted tests and authentic synthetic demonstrations. `PASS` means checked with evidence; `FAIL` means a required deliverable is absent here or a check failed; `UNVERIFIED` means evidence is insufficient. These labels do not predict an award.

## Repository baseline

| Item | Finding |
| --- | --- |
| Competition | Started clean on `main`, commit `4ba11c1781e51b6822a8bc329080fe903258fba4`, two commits, only README tracked. No tests or CI initially. |
| A1 branch | `codex-a/stage-a1-baseline`; local changes remain reviewable and uncommitted. |
| Core | Isolated clone at `.baseline/core`, clean `main`, `eda23d3ea646e8943287703c07a91e9a3b2909fb`, matching the README pin. Remote branches include profiling, safety assessment and perception/fusion experiments; A1 uses only the pinned mainline. |
| Core contents | Source, 46 test modules, pinned requirements, simulation and evaluation tools, profiling/CUDA experiments, PX4 shadow supervision, SAM backend and documentation. No core source edits. |
| Existing CI | Core workflow installs development extras, runs Ruff/pytest and a nominal demo, then uploads evidence. Its dev ranges are broader than the committed lock. |
| Remote CI result | UNVERIFIED. GitHub connector returned no PR-triggered runs for the pinned commit; that filtered result does not establish that all CI is absent or green. |
| New competition CI | Added local test/demo/artifact workflow; UNVERIFIED on GitHub until approved publication and execution. |

Exact local commit histories and working-tree output are in `evidence/a1/core-inspection.json`, `core-status.json`, `competition-baseline.json` and `core-final-tree.json`. No pre-existing local core checkout was found in the bounded home-directory search; this assessment covers the new clone, not another machine's worktree. No Amazon repository was modified.

Core documentation is useful but partly stale: `architecture.md` still describes motion compensation as future work even though the pinned source implements it. Its safety-precedence prose should be reconciled against current planner tests before reuse in the technical report. The core declares Apache-2.0 in package metadata, but a standalone license file was not found. The competition README reserves a licensing decision; confirm rights before distributing an archive or changing licenses.

## Official requirements and judging

Sources read October 21: [official Devpost overview](https://opencv26.devpost.com/) and [official rules](https://opencv26.devpost.com/rules). Recheck them before submission. The page header says **October 26, 11:45 PM PDT** while body text says 11:59 PM; use 11:45 PM as the hard deadline. Eligibility summaries also differ on age; the owner must confirm their applicable platform requirements.

Minimum package from the overview: substantive OpenCV 5 analysis; a meaningful AWS component; a technical report; judge-accessible source/archive; pinned dependencies and build/deploy/test instructions; an architecture diagram; a working endpoint or arranged live screen-share; a judge-accessible video of at most five minutes showing the team, running app, architecture and results; and evaluation with failures/limitations. Code may remain private. Agentic Vision adds a workflow diagram, evidence that visual output changes later behavior, and evaluation of effectiveness and human control. COOL is optional for the target awards.

The rules weight overall judging as technical execution 30%, innovation 20%, impact 20%, UX 10%, documentation/presentation 10%, cloud/reproducibility/responsible operation 10%. Agentic Vision weights integration 30%, orchestration/autonomy 25%, effectiveness/evaluation 20%, failure handling/observability/security/human control 15%, UX/documentation/demo 10%.

## Readiness gates

| Status | Gate | Evidence or missing work |
| --- | --- | --- |
| PASS | Substantive OpenCV 5 local execution | Actual package `5.0.0`, distribution `opencv-python==5.0.0.93`; build logs and video decode checks in final run directories. |
| PASS | Reusable, isolated entry point | `scripts/competition_demo.py`, full core pin, clean-tree guards, explicit local mode, exclusive output directories. |
| PASS | Perception influences subsequent behavior | Intrusion at frame 38 changes return-home to evasive hold. Low light begins at frame 30 and invokes active perception. See final traces; existing agent test checks the second observe call. |
| PASS | Targeted safety/approval/navigation/PX4/profiling regression | 56 tests passed. This is a targeted subset, not a full core-suite result. |
| PASS | Competition guard tests and lint | Five tests passed; Ruff passed. Raw outputs retained. |
| PASS | Authentic artifact generation | Three scenarios, 230 events and decoded video frames; trace identities/reasons present; all commands report no hardware transmission. |
| FAIL | AWS execution evidence available in submission package | Infrastructure exists, but no deployment identifier, successful signed request, storage receipt or cloud log was verified. |
| UNVERIFIED | Actual AWS deployment/account state | No AWS account or credential inspection, cloud calls, deployment or spend performed. |
| FAIL | Final technical report and polished judge presentation | A1 readiness/integration documents are preparation, not the final technical report. |
| FAIL | Judge-facing endpoint or arranged live demonstration | No arrangement or verified endpoint supplied. Local dashboard works. |
| FAIL | Final video | No public/unlisted judge-accessible video supplied. Generated MP4s are evidence clips, not the required team/architecture/results video. |
| UNVERIFIED | Registration, team eligibility, grant obligations, award selection and rights | Owner confirmation needed; existing functionality and competition additions must be disclosed. |
| UNVERIFIED | Reproduction on a second machine / GitHub runner | Local Linux run verified; new CI has not run remotely. |
| UNVERIFIED | Real-world utility and robust performance | Synthetic scenarios only in A1. No field-flight, production safety, COOL, GPU speedup or real-time claim established. |

## Measured local results

Authoritative final run artifacts live under `evidence/a1/final/`. Each contains actual core-generated video, trace, summary and dashboard, plus wrapper validation, stdout/stderr, build information and SHA-256 hashes. The earlier top-level scenario folders are retained preliminary runs from before wrapper guard/formatting revisions; use the final folders for review.

| Scenario | Frames | Recorded action counts | Active-perception / approval-required frames |
| --- | ---: | --- | ---: |
| nominal | 60 | continue mission 60 | 0 / 0 |
| low_battery_intrusion | 90 | return home 40; evade/hold 25; land 14; request approval 2; emergency land 9 | 0 / 5 |
| gps_loss_low_light | 80 | continue mission 20; return home 2; request approval 51; land 7 | 50 / 51 |

Approval-required counts can differ from the count of the `request_human_approval` action because stabilization preserves an action while approval state changes. These are frame counts in scripted videos, not counts of independent missions, successful physical landings or distinct operator requests. The low-light retry does not prove reliable recovery in arbitrary darkness. The videos are rendered at 15 FPS; that is not measured processing throughput. Runs were concurrent and un-warmed, so their wall time is smoke-test evidence only.

The intrusion trace records motion risk changing from 0 at frame 37 to 0.1825 at frame 38 while the action changes to evasive hold. The GPS-loss trace requests approval at frame 22; frame 30 records active perception after illumination drops. All approval-required behavior and critical-reserve exceptions must be explained with the planner's actual rules, not a claim that every risky landing always waits for a person.

## Commands, failures and provenance

See [integration instructions](INTEGRATION_PLAN.md) for reproduction. Every retained command JSON includes exact argv, cwd, output, timestamps and exit status. Runtime: Python 3.12.3, NumPy 2.5.2, OpenCV 5.0.0 on Linux x86_64. `pip-freeze.json` captures all installed package versions and `dependency-check.json` reports no broken requirements.

The initial editable install failed because sandbox DNS blocked the package index. After approved network access, the exact core lock installed successfully into `.venv`; the implementation uses source-path imports rather than an editable install. Initial targeted tests produced **54 passed, 2 failed** because subprocesses could not import `aegisland`. Re-running with an explicit inherited `PYTHONPATH` produced **56 passed** without source changes. Both logs are retained: `core-targeted-tests.json` and `core-targeted-tests-corrected.json`. `lint-final.json` records an intermediate failed lint check; `lint-verified.json` records the corrected pass. `tests-final.json` records the final five competition tests.

Final demo command logs deliberately supply a dummy localhost cloud endpoint in the parent environment. The wrapper removes it before invoking the core; the evidence remains local. This tests endpoint isolation without credential use. Provenance records the starting competition commit and dirty status because the new code has not been committed. A source-hash inventory accompanies A1; final submission should pin a reviewed competition commit as well as the core commit.

## AWS assessment

Static inspection at the pinned commit found SAM definitions for an IAM HTTP API, Python 3.12 Arm64 Lambda (256 MB, ten-second timeout, tracing), encrypted private S3 with 30-day expiry, and on-demand DynamoDB with encryption, TTL and point-in-time recovery. The deploy script invokes SAM validation/build and a confirmation-gated deployment. These are code properties, not verified deployed properties. SAM and AWS CLIs are absent from the local PATH; deployment validation was not run.

Readiness issues to address in a separate backend change:

| Finding | Implication / next check |
| --- | --- |
| `CloudTraceStore.write` ignores the HTTP response status | An HTTP 4xx/5xx can appear successful. Require explicit acknowledgement evidence and failure logging. |
| DynamoDB conditional write precedes S3 write | An S3 error followed by retry can return `duplicate_ignored` with no S3 trace. Test partial-failure recovery and completion semantics. |
| Cloud upload is synchronous inside the local event loop | Offline exception handling preserves events but network waits can still affect loop latency. Measure before claiming cloud independence for timing. |
| No backend handler tests found in the inspected test tree | Add local mocked request/storage/error tests before asking to deploy. |
| Lambda policy uses DynamoDB CRUD and S3 write templates | Review generated IAM least privilege and actual API authorization after an authorized deployment. |
| Bucket/table retained; tracing, API and backups may incur costs | Owner must explicitly authorize any deployment/spend and its budget/cleanup plan. |

A meaningful evidence/observability backend is the proposed AWS component. Whether that is persuasive for judging depends on demonstrating its actual contribution. An Arm64 Lambda alone does not establish COOL use, nor does infrastructure text establish a working cloud integration.

## Handoff

The highest-impact next task is a **local backend contract and partial-failure test patch**, prepared for owner review before any cloud action. Acceptance: non-2xx acknowledgements are visible, retries cannot leave a falsely complete event, and mocked tests cover authentication/validation boundaries, duplicates and storage failures. Keep the core safety policy unchanged. Then request explicit deployment/cost authorization against a concrete reviewed plan and verify end-to-end storage receipts.

In parallel planning, use existing trace/video evidence to outline the final report and five-minute video. Avoid expanding CUDA or COOL scope. Target an engineering freeze on October 25 and an early October 26 submission so the owner's October 27 midterm remains protected.
