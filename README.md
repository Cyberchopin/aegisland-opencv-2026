# AegisLand — OpenCV AI Competition 2026

AegisLand turns OpenCV observations into inspectable simulated landing decisions: reconsider the scene, request another observation, change the next intent, or route a decision to human review. The runtime planner is deterministic. No aircraft hardware commands are sent.

**Current judge-review entry:** [final demonstration and submission assets](submission/entry-20261024/START_HERE.md). Start with [FINAL_SUBMISSION_HANDOFF.md](FINAL_SUBMISSION_HANDOFF.md) for results, owner actions and approvals. Earlier reports and archives are dated historical snapshots.

## Verified behavior and limits

- Three retained OpenCV 5 synthetic scenarios contain 230 trace events and matching decoded frames, annotated video, decision reasons and provenance hashes.
- The corrected nine-resource AWS evidence path passed **34/34 bounded HTTP requests**: unsigned 1/1, nominal 15/15, duplicate 15/15 and negative 3/3. Cloud readback passed and reconstructed files byte-matched **9/9**. The test resources and exact staging object were cleaned; the existing staging bucket was preserved. See the [sanitized live result](docs/AWS_PHASE_B_VERIFIED_20261025.md).
- The first live attempt remains deployment PASS / storage FAIL 503 / teardown PASS. Its exact historical AWS error code remains unknown. The [original failure report](docs/AWS_PHASE_B_RESULT.md) and historical evaluations are preserved; the later successful test does not rewrite that failure.
- CPU profiling and exact replay checks are available. Historical standalone CUDA results are separate from the CPU demonstration; no GPU speedup, real-time capability, field success rate or production-flight safety is claimed.

## Reproduce locally

The pinned core is [Cyberchopin/aegisland-agentic-vision](https://github.com/Cyberchopin/aegisland-agentic-vision), commit `eda23d3ea646e8943287703c07a91e9a3b2909fb`, recorded in [core-pin.json](core-pin.json). Core source is not copied into this repository. Initial source/dependency acquisition needs network; subsequent simulations and tests run offline. See the [integration plan](docs/INTEGRATION_PLAN.md) for setup.

With a clean pinned `.baseline/core` and the prepared `.venv`, run from this repository root into a new directory:

```bash
.venv/bin/python scripts/competition_demo.py \
  --core .baseline/core --scenario gps_loss_low_light --output runs/judge-gps
.venv/bin/python -m pytest -q tests
.venv/bin/ruff check cloud scripts tests
```

The wrapper checks OpenCV 5, the core pin and clean tree, disables the original cloud endpoint, validates decoded video/trace counts and refuses to overwrite outputs. Recorded evidence is under [evidence/a1/final](evidence/a1/final/). Playback at 15 FPS is not processing throughput.

Prepare an evidence packet plan without constructing a cloud transport:

```bash
.venv/bin/python scripts/evidence_cloud.py \
  --evidence evidence/a1/final/nominal --output runs/cloud-plan-nominal
```

Do not use `--upload`, deployment or quota scripts without new authorization. The reviewed live procedure uses one uploader and attempts=1; the general uploader's three-attempt default is not that procedure.

## Submission and release gates

The [current submission checklist](submission/devpost-final-materials-20261024/05_最终提交检查表.md), [2:55 recording plan](submission/devpost-final-materials-20261024/03_分秒镜头表.md) and [current technical report](submission/entry-20261024/TECHNICAL_REPORT.md) distinguish the completed cloud test from the historical failure. Eligibility/rights checks, judge/source access, real team/video capture and owner submission remain open. The test API has been deleted.

The core retains its policy, GPS-denied behavior and PX4 shadow supervision. Commands do not drive a flight-dynamics model; the demo uses fixed synthetic scenes. Core reuse, team contribution and distribution rights need owner confirmation. This README grants no new license.

Historical build/review scripts require separately retained approval attachments; a reduced clone cannot regenerate every historical ZIP. See [artifact boundaries](submission/entry-20261024/CLOUD_STATUS.md#repository-and-attachment-boundaries). The PR tree is not the frozen source ZIP, and that ZIP's SHA-256 is not a PR or commit hash.

No AWS call, deployment, merge or Devpost submission is authorized by these instructions or candidate files.
