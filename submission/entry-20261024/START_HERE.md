# AegisLand — final judge-review entry

**A traceable OpenCV perception → reconsideration → simulated action loop.**

Read the [current technical report](TECHNICAL_REPORT.md), watch the recorded scenario dashboards under `evidence/a1/final/`, and follow [REPRODUCE.md](REPRODUCE.md) for a fresh local run. Cloud source/build details and approval boundaries are in [CLOUD_STATUS.md](CLOUD_STATUS.md). The [current 2:55 recording plan](../devpost-final-materials-20261024/03_分秒镜头表.md), [visual asset index](VISUAL_ASSETS.md) and [current Devpost field copy](../devpost-final-materials-20261024/devpost/00_字段对应表.md) are ready for the owner's recording and submission work.

Current cloud result: **34/34 bounded HTTP requests passed**: unsigned 1/1, nominal 15/15, duplicate 15/15, negative 3/3. Cloud readback passed; reconstructed files byte-matched **9/9**. AWS test resources and the exact staging object were cleaned. The existing staging bucket was preserved; no live judge endpoint remains. See the [sanitized verification addendum](../../docs/AWS_PHASE_B_VERIFIED_20261025.md). The historical first attempt remains deployment PASS / storage FAIL 503 / teardown PASS; its original reports and archives are unchanged.

The source archive includes competition code, evidence and a file-hash inventory. The core is external and pinned in `core-pin.json`; initial source/dependency acquisition requires network and authorized access. Running the prepared demo needs neither AWS credentials nor an AWS endpoint. Code distribution, source/video access, eligibility and the actual submission remain owner decisions.
