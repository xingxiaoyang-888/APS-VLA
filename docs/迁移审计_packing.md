# OpenVLA-OFT 与 packing 迁移审计

日期：2026-10-14。范围：冻结策略、视觉真实删除、原位置编号、动作读取边界与可执行冒烟入口。历史目录只读；当前代码不依赖旧项目。

## 已修复的问题

- **原位置丢失：**旧 adapter 传 `position_ids=None`，删除视觉 token 后会重新编号。新公共规则 `oft-original-positions-v1` 保持 BOS 为 0、视觉 token 为原索引 +1、proprio 为 N+1，语言及动作的原编号也不变。实际张量、attention mask 与动作读取下标仍按缩短长度构建。
- **注意力实现可能错载：**固定的 OFT Transformers fork 仅在 SDPA 分支实现非因果双向注意力。新 loader 显式选 SDPA，并验证锁定实现的函数源码 SHA256，拒绝同版本号的普通 Transformers 或未经审计的变体。动作读取保留官方偏移一位的约定；该偏移不能解释成整个 OFT 使用因果注意力。
- **校验过晚：**旧代码在大主干前向之后才发现 prompt/action span 不匹配。现在先校验；非二值 mask、padding、ragged 保留数量、乱序/重复/越界索引均拒绝。
- **训练状态未封闭：**新 token policy 构造时冻结源 VLA、动作头、proprio projector，保持 eval，动作前向使用 no-grad。条件选择器另行训练；不复用旧软门或旧教师。
- **条件及文本模板：**proprio 始终保留且使用 checkpoint 的 bounds_q99 归一化。新增输入模块采用官方问题模板；旧 pilot 的简化 `In: instruction` 文本不沿用。

## 当前公共接口

`src/cti_vla/models/abstraction/packing.py` 是唯一 packing 来源，含原序索引、固定数量 Top-k、实际 gather、`OFTPackedBatch` 与原位置编号。

优先使用 `OpenVLAOFTTokenPolicy.forward_from_full_tokens(visual, normalized_proprio, input_ids=..., attention_mask=..., retained_indices=...)`。索引是每行严格升序的原视觉坐标；省略表示完整集合。dense、标注和推理进入同一路径。底层 `forward_from_tokens` 接受已经 packed 的特征与完整 keep mask，但无法从特征值推断外部调用者是否打乱了行，因此不应作为新 teacher 的首选入口。

两张图按主视角、腕部视角顺序编码，各 256 个 token。语言、proprio、动作 token 均不是剪枝对象。物理前缀顺序为 BOS → 保留视觉 → proprio → 其余文本/动作/stop。动作读取从 `K+1+num_prompt_tokens` 开始，长度 56；`num_prompt_tokens` 不含 BOS，包含必要的 assistant empty token。

## 验证与限制

本地 Python 3.10 / Torch 2.0.1 CPU：39 项相关行为测试通过，覆盖原位置保持、dense 连续位置、原序真实删除、非法输入提前拒绝、动作偏移、冻结无梯度、条件输入传递、归一化、相机顺序及末帧输入。模拟 contextual backbone 仅证明接口行为，不能证明真实 VLA 的效果。

```powershell
$env:PYTHONPATH='F:/CTI-VLA/src'
python -m pytest tests/test_oft_adapter.py tests/test_openvla_oft_policy.py tests/test_openvla_oft_loader.py tests/test_openvla_oft_inputs.py -q
```

`scripts/smoke_openvla.py` 已提供真实 RLDS 单样本的服务器验证入口：先后校验全部 checkpoint 文件；比较官方原生 regression 与新 dense，最大绝对误差阈值不超过 0.002；检查 512/256/128/64 各预算输出有限 8×7 动作。默认单次计时只包含缓存视觉特征之后的 packing/策略校验/前向，记录独立视觉耗时、硬件与版本；不是 benchmark，也不报告加速结论。

```bash
python scripts/smoke_openvla.py "$CHECKPOINT" configs/assets/openvla_oft_libero_spatial.json --cache-directory .cache/huggingface --shard "$RLDS_SHARD" --record-index 0 --step-index 0 --output results/smoke/openvla.json
```

2026-10-14 补充验收：真实 L40 单观测冒烟已通过，官方 dense 最大绝对误差0，512/256/128/64输出均有效，checkpoint前后哈希不变；见 [原始输出](../results/smoke/openvla_2987244.json)。图像输入目前是 RLDS JPEG 经 checkpoint processor；没有加入评测 center crop，不能当作已验证的 LIBERO rollout 预处理。内部严密校验可能引入 GPU 同步，正式计时必须记录这些开销。闭环和正式测速未完成。

## 固定上游依据

- [OFT 原生模型边界](https://github.com/moojink/openvla-oft/blob/e4287e94541f459edc4feabc4e181f537cd569a8/prismatic/extern/hf/modeling_prismatic.py)：视觉/proprio 拼接、动作占位与回归 span。
- [固定 Transformers fork](https://github.com/moojink/transformers-openvla-oft/blob/bc339d9ad707454c0c115970db43c260067c61ab/src/transformers/models/llama/modeling_llama.py)：SDPA 的双向注意力及显式 RoPE 位置输入。`LlamaSdpaAttention.forward` 经 dedent/strip/LF 规范化后的 SHA256：`46e487c53cd67d3ffbbf9f0274d6c855c214b03e8169bb4b9258dd1e2d7948e1`。这是代码身份门槛，不替代真实数值对齐。
- [官方输入辅助代码](https://github.com/moojink/openvla-oft/blob/e4287e94541f459edc4feabc4e181f537cd569a8/experiments/robot/openvla_utils.py)：问题模板、proprio 归一化和评测图像预处理约定。

## 历史来源登记

以下路径是迁移来源记录，不是运行时依赖。旧测试中属于旧均值替换 teacher 的集成用例未迁入。

| 旧源文件（根目录 `F:/DIWA`） | 源文件 SHA256 | 迁入/用途 |
|---|---|---|
| `diwa/models/abstraction/packing.py` | `a4adfced362b985efabd73e17298776044c0dd29af02af8cd1ae4719da5bd7a3` | 重写并统一公共 packing |
| `diwa/data/contracts.py` | `e2751aa5ca56829b7d7978ec55aff26686bf90742906ea9ee8b5b9d33a24ed39` | 只取 OFT prefix 约束；不迁世界模型 TokenBatch |
| `diwa/models/oft_adapter.py` | `2f5a52a9ba5244554fe77b338b29e95759a42675dc668ce9a0eb454665bbf693` | 新 namespace，显式位置与前置校验 |
| `diwa/models/openvla_oft_policy.py` | `04309097cb8a7fae06a9c12bca939f6d4af60c99c2c318d454e9d94602b46471` | 冻结/no-grad、完整特征统一入口 |
| `diwa/models/openvla_oft_loader.py` | `2b3089e4a4de381e880076c2b18ec01164df1a18b0bf488315176c68b5b5688c` | SDPA 实现身份及 512 视觉边界检查 |
| `diwa/models/openvla_oft_runtime_compat.py` | `bfa9494bea598cb668fa4a31cceda52f463172f5b6c2785fda01e64621b7da1c` | 最小 Prismatic LIBERO 常量兼容 |
| `diwa/evaluation/forward_smoke_openvla_oft.py` | `bdd7ac5fc73214128659e138e536a92523224e6ffcbc845638ec001873b0133e` | 原生 normalized 对照流程参考 |
| `diwa/evaluation/teacher_pilot_openvla_oft.py` | `5f4c587c3a709d5938d2e7c8178004fbef4380fcef3c72c974790ede44e2ea18` | 仅参考 RLDS 双图解码；不迁旧 teacher |
| `diwa/evaluation/smoke_openvla_oft.py` | `9e97a22b2804477323a201b6fb79b183cbd2d74cb3de2daee34d9271e0ca0ac1` | 离线隔离 HF cache 参考 |
| `tests/test_oft_adapter.py` | `0c0c6dd5101144c50d74579f7112466dd76a381633b8fd68ef29fc889935cb18` | 原行为用例及新位置/非法输入测试 |
| `tests/test_openvla_oft_policy.py` | `a8c6dfd354d5d13970f9a193cf01a17cf682cd75d0e4c0083eee6acfb112d626` | 去除旧 teacher 用例，新增冻结与统一入口测试 |
| `tests/test_openvla_oft_loader.py` | `c3a1123a6630183f4ee98c9011752bddf72112e34856c7d469c25cac202ce80b` | 组件行为及拒绝错误 SDPA 实现测试 |
