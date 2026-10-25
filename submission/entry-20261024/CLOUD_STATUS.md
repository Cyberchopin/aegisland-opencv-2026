# Cloud evidence and build/deployment boundary

Historical result: deployment PASS, first signed packet 503/storage FAIL, teardown PASS. Current source and the `final-hardening-20261023-r2` Lambda artifact are corrected offline candidates, not new live results. The old Change Set was executed once and removed; it must not be reused.

The source package includes the full template, source, dependency locks and manifest, but omits SDK-containing deployment ZIPs and all private account configuration/logs. The owner has the separately reviewed Lambda ZIP locally. Its required SHA-256 is `52e37629b1434e9a898448ddd5f63aa94ce367b1f552fdb5c082c92ea816aa39`; no new artifact may be substituted without review.

For an independent local SAM build, first install the locked tool environment; this may require network for dependencies but does not authorize AWS access:

```bash
python3.12 -m venv runs/sam-tools
runs/sam-tools/bin/python -m pip install -r requirements-sam-lock.txt
SAM_CLI_TELEMETRY=0 AWS_EC2_METADATA_DISABLED=true AWS_DEFAULT_REGION=us-east-1 \
  AWS_ACCESS_KEY_ID=local-build-only AWS_SECRET_ACCESS_KEY=local-build-only \
  runs/sam-tools/bin/sam build --template-file infra/template.unreserved-review.yaml \
  --build-dir runs/sam-local --cache-dir runs/sam-cache
```

Use new output directories. A fresh SAM build is separate provenance and need not have the same ZIP bytes as the approved deterministic package. Inspect local build output; do not invoke `sam deploy`, `sam sync`, packaging uploads or cloud tests under these instructions.

The existing owner-review manifest and security/cost checks are in `approval/final-hardening-20261023-r2/`. [Phase A](../../approval/final-hardening-20261023-r2/PHASE_A_PLAN.md) requires new approval for one exact upload and one unexecuted Change Set. [Phase B](../../approval/final-hardening-20261023-r2/PHASE_B_PLAN.md) then requires separate approval naming its new UUID, nine resources, one role/inline policy, bounded 34-request verification (ceiling 40, attempts=1) and teardown.

No policy, encryption or quota relaxation is proposed. The $0.921067 full-run allowance and aggregate $5 target are planning values, not actual charges or enforced caps. Stop on the first unexpected response, preserve private evidence outside temporary storage and Git, and never claim success without all receipts and complete readback.

## Repository and attachment boundaries

This PR tracks an explicitly reviewed source/documentation subset and small canonical regression fixtures. It excludes final source/material ZIPs, duplicate frozen-source contents, generated materials manifests, historical approval ZIPs, SDK-containing Lambda ZIPs, raw private AWS records, environments, caches and operator recordings. Three small synthetic MP4 fixtures remain because the current tests read their exact bytes; they are not personal screen recordings.

A reduced clone can run the competition tests/local demo after obtaining the pinned core and locked dependencies. It cannot regenerate every historical approval/review/submission attachment. In particular, `build_unreserved_approval.py`, `build_storage_remediation.py build`, `reproduce_cloud_candidate.py` and `verify_hardening_candidate.py` require separately retained original approval ZIPs, previous manifests or validated build artifacts omitted from this PR. `verify_submission_archive.py` additionally needs the separate frozen archive and owner-private configuration. Do not retrieve substitutes, widen permissions or treat a missing historical artifact as permission to rebuild/overwrite it. The render path for the current r2 manifest also needs the exact separately retained Lambda ZIP.

Attachment publication/download locations remain an owner decision; this PR creates no Release and uploads no ZIP. The frozen source SHA-256 identifies that immutable artifact, not this PR's tree or commit. Old manifests and source checksums describe their dated attachment snapshots, not all files in a fresh clone. The self-contained operator materials ZIP remains unchanged; its tracked authoring files do not imply the excluded frozen-source copy is present in the repository.

The current recording target is 2:55; use the materials narration and shot list. Retained 3:45/2:45 plans are historical/superseded. Playback is recorded synthetic evidence, not new inference. Corrected live cloud storage remains unverified. No new AWS Phase A/Phase B is created or authorized by this PR.
