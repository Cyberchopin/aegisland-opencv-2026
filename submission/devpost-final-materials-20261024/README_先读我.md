# AegisLand — Devpost 最终提交资料包

本目录是独立的投稿资料，不是一次新的测试、推理、部署或比赛提交。冻结源码 ZIP 只是逐字节复制，没有重打包或改动。

建议顺序：
1. 阅读 `01_中文操作手册.md`，启动一个仅本机可访问的 8081 静态服务器。
2. 把 `02_英文口播稿.txt` 开头的 `[YOUR NAME]` 换成真实姓名，按 `03_分秒镜头表.md` 排练，目标 **2:55，成片必须少于 3:00**。
3. 录制并检查视频。使用 `youtube/` 的标题与描述；真实链接由你本人填写。
4. 按 `devpost/00_字段对应表.md` 选择实际网页存在的字段，再粘贴英文文案。
5. 完成 `05_最终提交检查表.md`。`06_已验证与未验证.md` 是能力声明的边界。

资料入口：`index.html`。技术报告在 `reports/`，真实帧截图和图在 `visuals/`。可供评委访问的代码附件是 `frozen-source/aegisland-judge-source-candidate.zip`；不要把本资料 ZIP 的 SHA 当成源码 SHA。

已确认：Core 215 passed、1 skipped；Competition 121 passed。源码 ZIP 为 9,181,179 bytes，SHA-256：
`8a03304e33ba80f9c19a2ca69022bfd9369674f899497ceda4db6a6a6bb0cfe4`。

最新真实云端结果为 **PASS_CLEANED**：34/34 bounded HTTP requests passed（unsigned 1/1、nominal 15/15、duplicate 15/15、negative 3/3），cloud readback passed，reconstructed files byte-matched 9/9；AWS 测试资源和精确 staging object 已清理，原有 staging bucket 保留。脱敏依据在 `verification/CLOUD_VERIFICATION_20261025.json`。首次 storage FAIL 503 仍作为历史失败保留，不能说成首次就成功。展示页不会调用 AWS。

本地记录能确认的规则来自 `docs/candidates/OFFICIAL_RULES_AUDIT_20261024.md`；未登录检查实际 Devpost 表单，也没有重新查询网页。所有无法从本地确认的规则、字段、字数、入口、分享选项均标注 **“需要我在网页上确认”**。姓名、队员、版权、联系方式、代码/视频/演示链接不能代填。

当前作者材料已加入后续真实云验证结果；现有资料 ZIP、源码 ZIP、MATERIALS_MANIFEST.json 与 verification/CONFIRMED_RESULTS.json 保持历史快照，不代表这些本地文案更新。PNG/原始 SVG 的 ASSET_PROVENANCE.json 仍描述原素材；新架构说明图另名为 architecture-cloud-verified.svg。
