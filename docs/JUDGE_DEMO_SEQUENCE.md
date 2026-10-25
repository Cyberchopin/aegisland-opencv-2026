# Judge demonstration sequence

Target a four-minute working demonstration with questions afterward. The operator uses existing A1 evidence and can rerun the pinned simulation locally. Any recorded playback must be labelled as playback; report rendering and synthetic video are not live flight.

Prepare all three `evidence/a1/final/<scenario>/report.html` dashboards and matching video/JSONL files. Use a loopback server if needed; never expose the development server publicly. Open the trace at the relevant frames before presenting. No cloud credentials, profile names or account identifiers should be visible.

| Time | Operator action | Judge-visible proof |
| --- | --- | --- |
| 0:00–0:25 | State problem and boundaries; show actual team introduction | A research prototype for observing and supervising simulated landing decisions; no physical drone control |
| 0:25–0:50 | Show nominal dashboard, play a brief labelled excerpt | 60 frames, continue mission throughout; OpenCV version/build and evidence ID available |
| 0:50–1:40 | Play intrusion excerpt; pause on frames 37 and 38; open their trace rows | Motion risk 0 → 0.1825; return home → evade/hold. Explain which evidence changed behavior. The simulated intruder is not proof of a semantic detector. |
| 1:40–2:25 | Show GPS/low-light timeline, frame 22 and frames 29–30 | GPS loss routes to pending human approval; light loss starts at 30 with active perception. Show the evidence/decision fields and local test for another observation call. |
| 2:25–2:55 | Show a low-confidence segment and approval status, then explain critical-reserve exceptions | Rescan does not guarantee recovery. Approval-required frame count and request-action count can differ; policy can permit emergency action under critical reserve. No hardware command was sent. |
| 2:55–3:30 | Show local artifact hashes and AWS reliability results | MP4/trace/summary consistency, five A1 guard tests plus 60 mocked cloud tests, failure rather than false success on bad ACKs |
| 3:30–4:00 | Use the AWS branch below, then close on known limitations | Accurate local/deployed distinction, reproducible source and clear remaining work |

AWS branch now: show the **local** 15-packet nominal plan and the proposed architecture. Say: “The backend has passed mocked failure tests and local packaging. AWS execution is not yet verified.” Do not call the uploader's live path during this offline presentation.

AWS branch after a separately authorized successful deployment: replace the plan-only segment with sanitized real receipts and readback comparison. Explain why remote evidence storage is useful and that it runs after simulation. Judge access to the local application or an arranged screen-share is still required; the ingestion API is not an application UI.

Fallbacks: if a live local rerun fails, show the retained artifact and its provenance as a prior run, preserve the failure output and explain it. If AWS is unavailable, show the local loop continuing and mark cloud delivery incomplete. Never substitute mocked receipts for deployed evidence.

Pre-recording checks: validate all 230 event/video-frame matches, rehearse pauses and trace row selection, hide sensitive desktop content, confirm sound and captions. Use exact scenario outputs rather than manually typed result slides. Freeze the sequence by October 25 to protect the owner's October 27 midterm.
