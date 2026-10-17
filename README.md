# AegisLand — OpenCV AI Competition 2026

Competition-specific delivery repository for AegisLand.

## Core project

Long-term research and development:
https://github.com/Cyberchopin/aegisland-agentic-vision

Pinned development baseline:
eda23d3

The core contains the perception pipeline, safety policies, simulation,
PX4 shadow supervision, evaluation tools, and CPU profiling.

## Scope of this repository

- OpenCV 5 and AWS integration instructions
- Competition-specific configuration and demo entry points
- Evaluation evidence, failure cases, and limitations
- Architecture, technical report, and submission materials

These deliverables are planned; this repository does not yet contain
a complete runnable competition submission.

## Reuse and provenance

This entry builds on the existing AegisLand project.
Existing functionality and competition-specific additions will be
documented separately.

Core code is not copied into this repository. Reuse and distribution
will follow an explicit licensing decision. No open-source license
is granted by this README.

## Current limitations

- Research prototype, not flight-certified
- PX4 integration is read-only shadow supervision
- The standalone CUDA grayscale kernel is not an integrated GPU pipeline
- No speedup or real-time claim is made
- AWS deployment evidence remains to be verified for the final submission
