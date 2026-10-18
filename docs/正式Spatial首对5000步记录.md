# Spatial 首对正式 5000 步验收

2026-10-18，北京时间。`formal_main_v2` 的 Spatial、总 128 tokens（每视角 64）、seed17，A/B 均完成 5000 更新；十段原始训练、全部验证、根审计、独立审计及服务器选中权重 SHA 核验通过。此时正式累计完成 **6/72 组**。本记录确认训练与选模完成，L1 诊断不能推出闭环成功率或加速收益。

| 方法 | 选中更新 | 任务等权硬 teacher L1 | best.pt SHA256 |
|---|---:|---:|---|
| A | 4000 | 0.022592171768524818 | `68953d2b4f0325b54df698b3ed7aadb19ac1d53b2b53bb9e0b8ff7abb0c84a40` |
| B | 5000 | 0.023319684344949944 | `ea56dea4fd9f67c99c2b149b123a2112ae7e5971249fe86f697128000d7d1b7e` |

每臂有效 batch8，实际使用 40000 次窗口，覆盖全部 34703 个合法训练窗口；另有 5297 次预定第二轮采样，属于合法重复，并非恢复重放。A/B 共用初始化和完整样本顺序，终态游标均为 40000；无训练失败或恢复重放。每臂完成 **11×189** 窗口验证（0、500、…、5000），在固定面板上以任务等权硬 teacher L1 选模，平分取更早更新。基座全程冻结，原 5000 步退火、动作损失和 B 的 h8、λ=0.1 保持不变。

十个训练 Slurm 分配合计 **36092 GPU 秒（10.025556 小时）**，包含模型加载、缓存、前反向、验证和保存。最后一段 `3021362` 的 3255 秒已计入总数，内部阶段耗时不重复相加；共享工程验收成本另记。173 个冻结文件原字节一致。

权重仅保留在服务器，实际选中路径为：

- A：`/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_spatial/k128/seed17/A/best.pt`。
- B：`/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_spatial/k128/seed17/B/best.pt`。

以下收据完整绑定方法/预算/seed、选中更新、checkpoint、模型 revision、归一化统计键、输入与 packing 版本、配置与数据划分、F00/F01、冻结基座、训练源码及选模协议。其全部字段与原始训练、验证和服务器证明交叉一致；部署协议为一次硬 Top-k、统一 packing、一次 VLA 前向，移除未来头及实际执行动作输入。

| 完整部署身份 | 收据 SHA256 | metadata SHA256 |
|---|---|---|
| [A 部署收据](../results/formal_main_v2/libero_spatial/k128/seed17/training/A/deployment_receipt.json) | `b7c2828291366358c4c24685e36631084eceb200fe969cb7df6d9d912e5a1ac3` | `d6b3b50c36ccfd42363e01aa70576dd239f701913820daaef67e2be13977cfa5` |
| [B 部署收据](../results/formal_main_v2/libero_spatial/k128/seed17/training/B/deployment_receipt.json) | `d11087f91e648b5737ed13b298faa8783ebde2a5fe893094f347c5083635be0e` | `6ab9fcdf36aae82488ab7d658e54a12e553eab6947d6878a4776f541375cb46f` |

基座 revision 为 `6d0231af0e48c5985f1ff86908f4674b84bc049b`，统计键为 `libero_spatial_no_noops`；冻结源码总身份为 `dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e`。上述部署收据可供后续加载核验，**Spatial 正式开发闭环与完整 observation-to-action（O2A）测速尚未进行**，不能据此宣称未来监督有效。

证据：[根审计](../results/formal_main_v2/libero_spatial/k128/seed17/training/segment_reviews/3021362.json)、[独立审计](../results/formal_main_v2/libero_spatial/k128/seed17/training/segment_reviews/3021362_independent.json)、[实际服务器 best SHA](../results/formal_main_v2/libero_spatial/k128/seed17/training/segment_reviews/3021362_selected_server.json)、[稳定回存](../results/formal_main_v2/pulls/20261018T001956Z_0e685a6ebf63/receipt.json)。独立审计 SHA 为 `dcac42df8b98bdf5c2ee4496396442f1444fdc5027cb8ffc523d29232d976c60`；服务器哈希由 root 实际探针取得，独审只核对非权重证据，未读取权重或封存初态。

本对不再续训至 5500；不自动扩大方法、预算或任务。当前不是全局最终放行：全部最终初态继续封存，须完成 72 个选择器、16 个参考身份、四套件开发门槛及 root 显式 release 后，才可开放最终评测。
