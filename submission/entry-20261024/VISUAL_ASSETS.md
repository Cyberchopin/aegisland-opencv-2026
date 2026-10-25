# Recording assets and screenshot priorities

All scene captures are decoded from retained OpenCV output, with no generated pixels or extra overlays. Their source-video, trace and PNG hashes are in [the capture manifest](../candidate-20261023/screenshots/MANIFEST.json).

1. **Hero transition:** [intrusion37](../candidate-20261023/screenshots/low_battery_intrusion-sequence-037.png) beside [intrusion38](../candidate-20261023/screenshots/low_battery_intrusion-sequence-038.png). Show matching trace action/risk/evidence fields, not merely a dramatic image.
2. **Human control:** [GPS22](../candidate-20261023/screenshots/gps_loss_low_light-sequence-022.png), accompanied by the pending-approval trace row.
3. **Agentic tool use:** [low-light30](../candidate-20261023/screenshots/gps_loss_low_light-sequence-030.png), with29→30 active-perception comparison. Explain the enhancement/re-observation and retained uncertainty.
4. **Architecture:** [current SVG](../candidate-20261023/ARCHITECTURE.svg). It labels the historical503 and pending correction; older diagrams marked “not deployed” are historical.
5. **Engineering evidence:** final validation table, source manifest and sanitized cloud result (`evidence/aws-phase-b/result.json`). Show deployment PASS/storage FAIL/teardown PASS together. Keep actual private AWS logs and identifiers off screen.

The useful dashboard paths from repository root are `evidence/a1/final/low_battery_intrusion/report.html` and `evidence/a1/final/gps_loss_low_light/report.html`. Narrated retained playback is acceptable evidence when labelled honestly. Do not imply that opening a recorded dashboard constitutes a new run.
