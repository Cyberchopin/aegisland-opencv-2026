# Reproduce the local demonstration

Use Python 3.12. These instructions assume a copy of the competition source with Git metadata and an accessible core repository. Initial setup uses GitHub/PyPI; it was not rerun over the network during finalization. A prepared environment and the retained results can be used offline.

```bash
git clone https://github.com/Cyberchopin/aegisland-agentic-vision.git .baseline/core
git -C .baseline/core checkout --detach eda23d3ea646e8943287703c07a91e9a3b2909fb
python3.12 -m venv .venv
.venv/bin/python -m pip install -r .baseline/core/requirements-lock.txt
.venv/bin/python -m pip install -r requirements-aws-test.txt
```

If reviewing an extracted source ZIP without competition Git metadata, initialize a local snapshot before running the wrapper; it records competition provenance with Git. This creates only local archive-review metadata, not an upstream release or publication:

```bash
git init
git -c user.name='Archive reviewer' -c user.email='reviewer@example.invalid' \
  -c commit.gpgsign=false commit --allow-empty -m 'Local archive review baseline'
```

The archive's `PUBLIC_SOURCE_MANIFEST.json` pins the actual working-tree contents; an empty review commit does not contain those files. Preserve the manifest and original archive checksum. The core must remain at the exact pin and clean, including untracked files.

From the competition root, choose a fresh output directory:

```bash
.venv/bin/python scripts/competition_demo.py \
  --core .baseline/core --scenario gps_loss_low_light --output runs/judge-gps-final
.venv/bin/python -m pytest -q tests
.venv/bin/ruff check cloud scripts tests
```

Open `runs/judge-gps-final/report.html`, or serve retained dashboards locally:

```bash
.venv/bin/python -m http.server 8080 --bind 127.0.0.1 --directory evidence/a1/final
```

Use `http://127.0.0.1:8080/low_battery_intrusion/report.html` and `/gps_loss_low_light/report.html`. This loopback server is not a hosted judge endpoint; the owner must arrange screen sharing or separately approve another delivery method. Use a media player if the browser lacks MP4 support.

The wrapper checks the core pin, imported OpenCV 5, clean core, decoded video and trace counts, reasons and simulation-only commands. It removes the original core cloud endpoint and refuses to overwrite output. Leave uploader/deployment/quota scripts unused. All cloud operations need new owner approval; general uploader defaults are not the one-attempt supervised test plan.

For the complete core regression, export the core source for subprocesses and constrain test-only OpenCV threading for consistent resource use:

```bash
PYTHONPATH="$PWD/.baseline/core/src" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  .venv/bin/python -c 'import cv2,pytest; cv2.setNumThreads(1); raise SystemExit(pytest.main(["-c",".baseline/core/pyproject.toml",".baseline/core/tests","-o","addopts=","-q","-ra"]))'
```

Keep the optional native CUDA integration disabled unless its own hardware/executable prerequisites are intentionally supplied. GPU tests being skipped does not establish GPU parity or speedup. Fresh UUIDs, timing and encoded bytes may differ; compare decisions separately and retain each run's hashes.
