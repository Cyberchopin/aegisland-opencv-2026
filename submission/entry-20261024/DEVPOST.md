# Devpost copy — owner review before posting

**Project name:** AegisLand

**Tagline:** OpenCV evidence that changes the next simulated landing action—and preserves why.

## Inspiration

A landing supervisor needs to reconsider when a scene changes. We wanted an inspectable prototype that connects a visual observation to the next action, records uncertainty and exposes where human review is required.

## What it does

AegisLand uses OpenCV 5 in a deterministic perception–decision loop over synthetic video and telemetry. It can request enhanced observation, change a simulated flight intent or route a decision to review. Three retained scenarios contain 230 matching frames/events with annotated video, decision reasons, dashboards and provenance hashes. No aircraft commands are sent.

At intrusion frame 38, motion risk changes from 0 to 0.1825 and return-home becomes evasive hold. In GPS loss/low light, the trace shows pending human review and a subsequent enhancement/rescan. A retry can still leave uncertainty; critical reserve can require emergency action without waiting for approval.

## How we built it

We reuse a clean, pinned AegisLand core for perception, policy and simulation. Competition additions isolate the launcher, validate artifacts and add a post-run evidence protocol with deterministic failure tests. OpenCV performs grayscale/edge/texture analysis, optical flow, camera compensation, zone scoring, CLAHE and real video encoding/decoding. The runtime agent does not depend on an LLM; coding agents assisted implementation, testing and documentation.

The cloud design uses an IAM-authenticated HTTP API, Arm64 Lambda, private S3 and DynamoDB. Conditional writes, body hashes and consistent index reads must pass before an acknowledgement is accepted. Cloud responses never change simulation safety decisions.

## Challenges and actual results

Our real AWS deployment passed, but the first signed packet returned **503 storage_unverified**. We stopped after two HTTP requests with no retry, preserved one matching S3 packet with no index item, and completed teardown. We received no successful storage acknowledgement and did not verify a complete cloud bundle.

Offline investigation found an unaliased DynamoDB reserved-word condition and hardened completion/acknowledgement types. The current correction passes regression tests and preserves the same resources, policies and encryption. The original log retained only ClientError, so its exact historical AWS error code is unknown. **The corrected pipeline is not yet cloud-verified.**

## Accomplishments and lessons

The strongest demonstrated result is the causal link from an OpenCV measurement to another tool call or simulated action, with inspectable human-control states. Adversarial tests exposed cases ordinary mocks missed; failures are now retained rather than inferred as success. The source package includes reproduction instructions, hashes and transparent failure evidence.

## Limits and next steps

These are fixed synthetic scenes and heuristic perception, not field validation or flight certification. We claim no real-time behavior, GPU speedup, integrated CUDA/COOL workload or end-to-end cloud-storage success. The immediate next step is a separately authorized, bounded cloud verification—not architecture expansion.

**Built with:** Python, OpenCV 5, NumPy, pytest, Boto3/Botocore, AWS Lambda, API Gateway, S3, DynamoDB, IAM and CloudWatch Logs.

## Owner-only completion checklist — do not paste this section as the story

- Confirm team/representative details, registration, eligibility and code/media distribution rights.
- Select the Agentic Vision path; do not claim COOL eligibility.
- Provide judge-accessible source/archive, report and under-three-minute video URLs (current target 2:55). Verify them signed out.
- Arrange a working live screen-share or provide a separately authorized working endpoint; a private ingestion API is not a judge UI.
- Resolve or explicitly discuss the incomplete meaningful-cloud requirement; do not change the story to claim success without new proof.
- Review the current rules, preview every field and press Submit before October 26, 11:45 PM PDT. No source/video URL or owner identity has been invented here.
