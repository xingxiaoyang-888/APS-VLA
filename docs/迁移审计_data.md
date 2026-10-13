# 数据迁移审计

日期：2026-10-14。范围：只读审计 `F:/DIWA`，迁入 `F:/CTI-VLA/src/cti_vla/data`；以下为代码及数据格式验证，不是 CTI-VLA 策略实验结果。

## 已迁入与修正

- `tfrecord.py`：保留 TFRecord 长度、CRC32C、截断与大小限制检查，统一为可流式复用的记录读取器。文件 SHA256 覆盖 framing 与 payload；空 shard 被拒绝。
- `sequence_example.py`：旧模块名沿用，但实际格式是 **flat `tf.train.Example`**，不是 `SequenceExample`。通过最小 protobuf 描述解析，无 TensorFlow/TFDS 依赖。新增字段类型检查与畸形 protobuf 错误；JPEG 保持压缩字节，数值为只读 NumPy。**动作/proprio 是原始数据，尚未应用 checkpoint 归一化；JPEG 头尾检查不等同完整解码。**
- 真实首 shard 证明 `episode_metadata/file_path` 只指向任务 HDF5：27 条轨迹仅有 7 个路径，不能作为 episode 唯一键。新键为所有必需 `steps/*` 字段的规范化内容 SHA256，保留原文件路径及 shard/record 溯源。换 shard、改变机器路径、重排 protobuf map 不改变键；相同轨迹内容重复出现会报错。此检查能识别完全相同的数据，不宣称检测语义上相近的轨迹。
- `libero.py`：新 schema v2 不兼容历史 pilot。按任务分层、按完整 episode 划分 train/validation/test；要求每个任务在各 split 都存在。采样覆盖轨迹时间早/中/晚三段并保留首末观测，记录真实长度、来源签名、随机种子。**时间三段不是接近/抓取/放置的语义标签。**
- 不再要求观测后有 8 个真实动作：当前标签来自教师预测，保留尾部观测是合法的，不沿用旧 pilot 的尾部排除。若后续训练需要真实 8 步动作监督，须另行定义尾部 mask，不能直接把当前 manifest 当成真实动作 chunk。
- `identity.py`：分隔符拼接改为带版本的规范 JSON 哈希；拒绝非法 step 和 NaN 签名。源文件签名使用文件名、大小、内容 SHA256，可跨本地/服务器复现，重复 basename 拒绝。

## 未迁入

`teacher_cache.py` 的历史 influence 强制非负、目标为 Huber，且没有完整保留集合 S；不能当成有符号的 L1 删除增量标签。`feature_cache.py` 只保存 pooled query、没有原始语言序列、未完整绑定 preprocessing/packing 版本，也不复用为新训练缓存。新删除标签缓存由 CTI-VLA 方法模块定义。

`contracts.py` 同时包含 latent/world-model、diffusion 等历史字段，并与新 packing 合约重复，因此不迁。RoboTwin、世界模型、旧缓存、120 个早期观测 manifest 和旧训练/评测结果均不导入新数据管线。

## 验证与待办

本地 Python 3.10 / NumPy 1.24.4 / protobuf 6.33.6：`python -m pytest tests/test_data_libero.py tests/test_data_sequence_example.py tests/test_data_tfrecord.py -q`，**22 项通过**。覆盖防泄漏、schema 拒绝、ID 防伪、重分片与同 HDF5 多 demo、早中晚/首末覆盖、CRC 标准向量/损坏/截断、错误字段类型和内容签名。

真实首 shard 已在新根目录的 `data/audit_source/` 复制审计，SHA256 与历史来源清单一致（118,202,941 bytes）。全部 27 条记录通过 CRC 和字段验证，得到 27 个不同内容 ID、7 个任务，长度 84–148；三阶段各采 27 个状态，共 81 个观测。**这些数字只是数据审计，未运行教师标注或模型评测。**详细证据：`results/migration/data_audit.json`。

首 shard 缺少完整 10 任务覆盖，且一个任务只有 1 条轨迹；新划分器正确拒绝据此建立所有任务齐全的三 split。

后续全量验证已完成：16 个 shard 全部通过 CRC/字段检查，共 432 条不同内容 ID 的轨迹、10 个任务，长度 75–193。实际文件集签名与下载 receipt 固定源哈希独立重建的签名一致。`configs/manifests/spatial_v1/` 已保存 seed=17 的 train/validation/test：分别 **302/64/66 episodes，906/192/198 observations**；各 split 均有全部 10 任务，三对 episode 交集均为 0，重新生成结果与落盘 manifest 一致。每轨迹取首/中/末 3 个观测，时间早中晚等量。完整证据：`results/migration/manifests_spatial_v1.json`。

这些 observation 尚未生成 CTI 删除标签；还需模型侧归一化/图像预处理联调及真实教师验证。正式测试 split 不能参与标注策略或超参数选型；闭环 simulator 初始状态须另建评测协议。

主调接口：`discover_episodes(paths)` → `split_episodes(..., seed=...)` → `build_stage_covered_manifest(..., source_signature=..., samples_per_episode=..., seed=...)` → `assert_episode_disjoint(...)` → `save_manifest(...)`。来源签名使用 `file_set_signature(paths, namespace="cti-vla:libero-source:v1")`。随机划分对相同 inventory/seed 可复现；新增数据会改变划分，因此必须保存 manifest。

## 原始源码 SHA256

以下均为 `F:/DIWA/` 下只读源文件；新代码已修改，哈希用于追溯来源，不代表新版本哈希。

| 源路径 | SHA256 | 处理 |
|---|---|---|
| `diwa/data/tfrecord.py` | `68540207fc2fae1d664f6ded028750f2d5db8ecf146b0566cb595e62519500c7` | 迁移并统一读取 |
| `diwa/data/sequence_example.py` | `3511df05d784b1b5e07894985b8d8c241b130106cd13cf449c4933bc77608b94` | 迁移并修正身份/校验 |
| `diwa/data/libero.py` | `efaf4efc3235cbb3dc0b5fe5e16e1d8655202930f39b1267a94c1e068ae3613a` | 重写 manifest/采样/划分 |
| `diwa/data/identity.py` | `2b81ee1fb021f9437c990ccb7ae0ebf4a4f93f0396bb671fe6c2c616ebe350b3` | 重写版本化标识 |
| `diwa/data/teacher_cache.py` | `1531a0874d26d3f374db042091ce860391ec895d035df4f3412b18b20051d162` | 审计，不迁 |
| `diwa/data/feature_cache.py` | `a63b90a9d7dabbfe5e5a44ff28d76979d3dc773090aeb946fc2a24c87bdedb56` | 审计，不迁 |
| `diwa/data/contracts.py` | `e2751aa5ca56829b7d7978ec55aff26686bf90742906ea9ee8b5b9d33a24ed39` | 审计，不迁 |
| `tests/test_sequence_example.py` | `f5f7880c11c217186e0f7e5485028bba542a8a5b8d01fe0890564f14ce39eb42` | 迁移并新增回归验证 |
| `tests/test_tfrecord.py` | `0cb0d9040711fed36eeaced9814c37998a87a85a6106eec627ec5b5b96e70524` | 迁移并新增损坏验证 |

原始数据 shard SHA256：`6d6360559a4b71df3bcabd9b55a75451f04375449ca5267616cbc1c21528eac5`。所有迁入模块均不依赖 `F:/DIWA` 或 `diwa` 包。
