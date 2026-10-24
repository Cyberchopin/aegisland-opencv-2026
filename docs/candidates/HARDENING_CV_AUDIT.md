# Offline computer-vision and performance audit candidate

This is an additive engineering review of the pinned core at `eda23d3ea646e8943287703c07a91e9a3b2909fb`. No core source, safety policy, CUDA kernel, historical report or evidence was changed. No network, AWS, deployment, dependency download or GPU benchmark was performed for this audit. External competition rules were not revalidated offline.

## Verified scope

The production path is CPU OpenCV 5: resize; BGR-to-gray; retry-only CLAHE; blur; Canny and morphology; Laplacian texture; raw Farneback flow; ORB/matching/homography camera compensation; residual Farneback flow; quality/self-diagnosis; grid-based appearance, structure, motion and clearance scores; evidence construction and annotation. This is a measurable heuristic pipeline, not semantic person identification, calibrated probability estimation or a flight-safety proof.

The low-light retry changes the observation/tool sequence and retains the pre-frame reference. It reuses the visual pose rather than integrating the same physical frame twice. The confidence heuristic includes an explicit retry bonus; increased confidence is not independently validated hazard-detection improvement. Agentic evidence should show actual tool calls, perception values, decisions and human-approval status, rather than equating confidence with real-world accuracy.

The competition recordings remain three scripted synthetic scenarios and 230 frames/events, not independent missions or real aircraft trials. The MP4 playback rate of 15 FPS is not measured processing throughput. Simulated command intents and PX4 shadow behavior must remain distinct from physical flight execution.

## Offline checks run in this audit

The selected CV/profiling/CUDA unit suite collected **63 tests: 62 passed and one expected opt-in GPU integration test skipped**, exit 0. The skipped test requires an existing native GPU executable through `AEGISLAND_GRAY_EXE`; it was not enabled or replaced with mocked GPU results.

Executed from `.baseline/core` using the competition environment's Python, with `PYTHONPATH` set to the pinned `src` and `PYTHONDONTWRITEBYTECODE=1`:

```bash
/home/shiyue1128/aegisland-opencv-2026/.venv/bin/python -m pytest -c pyproject.toml \
  tests/test_profiling.py tests/test_cuda_gray.py tests/test_motion_compensation.py \
  tests/test_perception_quality.py tests/test_perception_trust.py tests/test_gps_denied.py \
  tests/test_tracking.py tests/test_ttc.py tests/test_fusion.py \
  -q -o cache_dir=/tmp/aegisland-hardening-cv-pytest-cache

/home/shiyue1128/aegisland-opencv-2026/.venv/bin/python -m aegisland.profiling \
  --output /tmp/aegisland-hardening-cv-cpu-base --warmup 1 --runs 3 --threads 1

/home/shiyue1128/aegisland-opencv-2026/.venv/bin/python -m aegisland.profiling \
  --input /tmp/aegisland-hardening-cv-cpu-base/inputs.npz \
  --output /tmp/aegisland-hardening-cv-cpu-active --warmup 1 --runs 2 --threads 1 --active
```

The runs used Python 3.12.3, OpenCV 5.0.0, NumPy 2.5.2, one OpenCV thread, OpenCL disabled, and fourteen 320×240 BGR frames from the existing synthetic scene corpus. CPU reference replay and instrumented-stage replay both passed exact array/evidence comparison in both runs. The base run produced 42 uninstrumented samples, 3,606 stage rows and 93 stage labels. The active run produced 56 uninstrumented samples: 28 base observations and 28 forced retries.

The base-run smoke distribution over its 42 mixed-frame samples was p50 **25.8394105 ms**, p95 **42.4921468 ms**. These are actual observations from this run, not a performance guarantee. The host was not isolated; another CV test process ran concurrently. Three observations per frame do not support tail-latency conclusions. First frames, discontinuous scene transitions and later frames are heterogeneous; aggregate percentiles must not be advertised as operational latency or converted into real-time flight claims.

Full temporary artifacts, including `samples.csv`, named-stage samples, correctness results, profiles, environment, replay inputs and `SHA256SUMS`, are under the two output directories above. Compact summaries are `/tmp/aegisland-hardening-cv-audit-summary.json` and `/tmp/aegisland-hardening-cv-active-summary.json`. Preserve them in the new hardening evidence package if these smoke values are quoted; temporary paths alone are not durable submission provenance.

## Timing and parity methodology

The existing harness correctly separates three independent rounds: uninstrumented wall-clock baseline, named-stage instrumentation and cProfile. Each round has separate warmup sequences, state/RNG reset per sequence and temporal state within the sequence. Timed `invoke` includes annotation, allocations/state updates and explicit retry enhancement. Input loading, correctness snapshots and serialization are outside the timing boundary. Production `processing_ms` ends before annotation and some evidence construction, so it is not interchangeable with `invoke` latency.

Named stages are compiled from trusted production methods and restored after the instrumented round. Exact baseline/stage replays guard against instrumentation-induced output changes. Inclusive parent/child timings overlap. Exclusive timing includes instrumentation/condition overhead and is not pure native compute. Never sum parent and child durations, or use stage/cProfile time to claim an uninstrumented speedup.

The current smoke's raw/residual Farneback stage times together represented about **65.17%** of instrumented end-to-end inclusive time. This is diagnostic attribution only. The source executes two dense-flow passes on valid references, plus ORB/matching/homography and quality analysis. Those are credible areas to investigate on representative data after submission; grayscale conversion alone is not established as the dominant bottleneck. No optimization or new kernel is warranted for this deadline.

The strict backend-equivalence gate requires equal field/schema/order, shapes/dtypes and all array pixels, boxes, candidates/safe flags/localization/evidence identifiers; only nondeterministic `processing_ms` is excluded. Binary masks additionally report IoU with two empty masks treated as 1. Exact correctness is appropriately stricter than a generic epsilon near policy thresholds. Preserve failures and use threshold-boundary data before reviewing any future relaxed tolerance.

## CUDA evidence classification

The core contains a historical measured-result summary at `benchmarks/results/first_cuda_gray/summary.json` and an explanatory `docs/first-cuda-kernel.md`. Source SHA-256 fingerprints for the CUDA file and Python driver match the pinned files. The current checkout does **not** contain the original raw CSVs, `.ncu-rep`, GPU output images or native executable needed to independently reproduce those historical measurements. Therefore these numbers are **historical recorded measurements, not newly verified results in this audit**:

| Historical record | Value / boundary |
| --- | --- |
| Hardware/tooling | RTX 4060 Ti, CC 8.9, CUDA 12.8, driver 595.95, Nsight Compute 2025.1.0 |
| Correctness summary | 18 cases / 17,929,593 pixels, including all 16,777,216 BGR8 triplets; recorded zero mismatch/error and downstream gate pass |
| Isolated frame-000 primitive | 320×240; kernel-event p50 4.096 µs; pageable H2D/kernel/sync/D2H wall p50 74.850 µs; CPU gray wall p50 17.400 µs |
| Profiled launch | One selected launch, eight profiler replay passes; Nsight duration 2.592 µs; achieved occupancy 72.792803%; DRAM throughput percentage 32.368608% |

These timing boundaries differ. CUDA events around a resident-input kernel are not a whole perception measurement, and profiler replay duration is not ordinary unprofiled timing. GPU allocations/context/file I/O are excluded; CPU gray uses ordinary allocation. Cached historical GPU gray outputs were substituted into CPU downstream replay for correctness, not integrated GPU latency. Desktop activity and clocks were not controlled in the historical normal run. Occupancy and a tool's estimated speedup do not establish a measured improvement.

The standalone driver uses exact integer gray conversion, bounds/strides and destination-padding checks, plus the recorded exhaustive-color/odd-width cases. Those are strong arithmetic and memory-layout checks for that primitive. They do not establish a GPU-accelerated landing agent, active-perception acceleration, general CUDA pipeline correctness, real-time performance, a COOL claim or production safety. Do not describe the historical plan-only sections as measurements; `first-cuda-kernel.md` explicitly supersedes those sections with a bounded experiment.

## Confirmed input edge case, kept outside deadline scope

A separate local diagnostic passed a uint8 frame shaped 12×10,000×3 directly to the pinned perception class. Its resize cap produces a one-row image; quality analysis raises `cv2.error` in OpenCV `resize`. The profiling loader accepts the source dimensions because both are at least twelve, so that source-shape check does not guarantee valid post-resize geometry. The ordinary 240×320 control completed with finite JSON and no warnings. The diagnostic result is saved at `/tmp/aegisland-hardening-cv-input-edge.json`.

This is a concrete unsupported-input boundary, not a failure of the recorded synthetic runs. No core patch was made. Keep demonstration inputs at the verified dimensions and do not imply arbitrary image support. A later separately reviewed input-contract change should validate post-resize geometry before invoking perception; it should reject unsupported shapes clearly rather than silently alter score thresholds or safety policy.

## Judge-facing screenshot priorities

1. Reproducible entry-point output: pinned core/OpenCV version, provenance hash and actual decoded-frame count.
2. Intrusion frames 37/38: annotated video next to trace rows, motion-risk change and changed simulated action; caption the rendered intrusion and avoid semantic identity claims.
3. GPS/low-light sequence: frame-22 pending approval and frame-30 active-perception tool transition; show human-control fields and that no hardware command was dispatched.
4. Actual AWS result panel: deployment PASS, first signed storage verification FAIL/503, teardown PASS. The proposed alias correction is offline-tested and not cloud-verified. Redact identifiers and private logs.

No CV rewrite, GPU kernel, fabricated performance chart or real-flight demonstration is needed to strengthen the submission. The strongest defensible story is visual measurements changing a later simulated decision, preserved provenance, explicit approval boundaries and transparent failure reporting.
