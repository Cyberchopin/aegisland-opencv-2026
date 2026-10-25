# 截图清单、建议顺序与英文 caption

PNG 是已保存 MP4 的原始解码帧副本，没有生成新画面。使用 `visuals/ASSET_PROVENANCE.json` 对照源文件和 SHA。架构图及结果展示卡是说明性资料，不是一次新的运行截图。

| 顺序 | 文件/页面 | 可粘贴英文 caption |
| --- | --- | --- |
| 1 | `visuals/architecture.svg` | AegisLand's OpenCV perception–decision loop and separate evidence path. The first cloud storage verification failed; the corrected path remains unverified in AWS. |
| 2 | `visuals/02_intrusion_sequence_037.png` | Recorded synthetic scene before the decision transition. No aircraft hardware commands are sent. |
| 3 | `visuals/03_intrusion_sequence_038.png` | The next recorded observation changes simulated intent from return-home to evasive hold. This is not a real-world person-detection benchmark. |
| 4 | `visuals/04_gps_sequence_022.png` | GPS-loss simulation with the corresponding saved trace showing pending human review. No live approval-button interaction is implied. |
| 5 | `visuals/05_lowlight_sequence_030.png` | Low-light observation associated with enhancement and another OpenCV tool call. Retry does not guarantee recovery. |
| 6 | `VERIFIED_RESULTS.html` 的测试卡 | Saved validation: 215 core tests passed, one optional native CUDA integration skipped, and 121 competition tests passed. These are not newly executed results. |
| 7 | 同页 AWS 卡 | Historical AWS result: deployment PASS, signed storage verification FAIL 503, teardown PASS. No successful storage acknowledgement was received. |

截图尺寸、数量限制、封面比例和实际 Devpost 上传字段：**需要我在网页上确认**。选取画面时不要裁掉 simulation、skip 或 cloud-unverified 说明。没有素材支持真实飞行、云端成功、GPU 加速或性能提升的额外截图。
