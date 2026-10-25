# Technical report outline

Working title: **AegisLand: OpenCV evidence that changes the next simulated landing action**.

The report should lead with one traceable result: synthetic intrusion changes the plan at frame 38; darkness triggers another OpenCV observation. The engineering contribution is a reproducible, observable perception–decision–action prototype. Real flight safety, detection accuracy and field benefit remain unproved.

The [official overview](https://opencv26.devpost.com/) calls for a technical report, architecture, reproducible source/instructions, working demonstration, evaluation and a video of no more than five minutes. The [rules](https://opencv26.devpost.com/rules) put the largest overall weight on technical execution and substantial weight on innovation and impact. Readiness and operational truth belong in the main report, not only an appendix.

| Section | Content and evidence to include |
| --- | --- |
| 1. Problem, intended users and limits | Emergency landing decisions when battery, navigation or visual confidence degrade. Intended beneficiaries: robotics researchers/operators assessing decision supervision. Explain why choosing to rescan or ask a person matters. Mark user benefit as a hypothesis pending field/user validation. |
| 2. What was reused and what was added | Core pin `eda23d3ea646e8943287703c07a91e9a3b2909fb`; unchanged policy and simulated command adapter. Competition additions: pinned launch wrapper, artifact checks/provenance, evidence delivery protocol, failure tests and judge materials. Record the final competition commit after owner review. |
| 3. Architecture and trust boundaries | Frame/telemetry → OpenCV → deterministic agent/planner → approval gate/simulated command → local evidence. Separate post-run uploader → IAM HTTP API → Arm64 Lambda → S3 and DynamoDB. Solid lines for locally demonstrated paths; label AWS execution UNVERIFIED until receipts exist. Use `INTEGRATION_PLAN.md` diagram. |
| 4. OpenCV 5 implementation | Actual version/build log; Canny, Laplacian, morphology, Farneback flow, zone scores, confidence, motion compensation and CLAHE retry. Explain which outputs influence which tool/action. No semantic person-detection claim from a rendered shape. |
| 5. Agent loop and human control | Trace at intrusion frames 37–38 and low-light frames 29–30. Explain the pending approval route and critical-reserve exceptions from source/tests. Distinguish policy intent, stabilized decision, approval state and simulated execution. |
| 6. Evaluation method | Three fixed synthetic scenarios, 230 events/decoded frames; exact commands, package versions, source/artifact hashes. Report frame counts separately from independent trials. A2's fresh 80-frame decision comparison is a regression check, not an independent efficacy trial. |
| 7. Results and failures | Source action counts from A1 summaries. Report active-perception/approval counts and an unresolved low-confidence/failure segment. Include 65 competition and 56 targeted core tests with scope. Do not infer general success rates or real-time performance from rendered video FPS. |
| 8. AWS contribution | Why off-device evidence storage and auditable receipt verification are useful; packet inventory, actual-byte readback, conditional writes, matching acknowledgements and replay. Separate the 60 mocked reliability tests/local build from any later deployed results. Insert real cloud evidence only after authorized verification. |
| 9. Responsible operation | No hardware command sent, heuristic limits, synthetic imagery, IAM/private storage, finite retries, cloud outside safety decisions, retention and deletion costs. State who controls approvals. Explain why budgets are alerts rather than hard caps. |
| 10. Reproduction and availability | Core/competition pins, Python and runtime/tool locks, fresh output directories, local commands, judge access arrangement, exact cloud configuration if deployed. Confirm licensing and data rights with owner. |
| Appendix | Provenance inventory, scenario/metric definitions, full failure list, backend protocol, cost assumptions and owner-approved deployment/cleanup receipts. Redact account IDs, ARNs, credentials and recipient details. |

Evidence anchors: `evidence/a1/final/`, `evidence/a2/aws-tests.xml`, `evidence/a2/core-regression.json`, `evidence/a2/integrity-and-decision-audit.json`, final SAM/package records, and `docs/AWS_RELIABILITY.md`.

Outstanding author inputs: team introduction, verified eligibility/rights, judge access, intended user feedback, final source commit, and optional authorized AWS receipts. Keep these explicit TODOs. Do not fill them with invented users, interviews, deployment success or field trials. Finish writing around existing evidence before October 25; reserve October 26 for checks and submission ahead of 11:45 PM PDT.
