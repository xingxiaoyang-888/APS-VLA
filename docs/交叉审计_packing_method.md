# 方法侧对 packing、输入与成本的独立审计

日期：2026-10-14。范围是方法实现代理独立审阅 packing 代理代码及锁定上游源；未修改 packing/loader/inputs 模块。

**结论：当前审阅及独立回归未发现阻断性位置、action slice 或归一化错误。真实 checkpoint 的 dense parity 仍须由服务器报告确认。**

## 位置与 action readout

设完整视觉数 N，保留数 K，prompt 不含 BOS 的长度 P。原语义位置为 BOS=0、visual=i+1、proprio=N+1，随后 prompt/action/stop 按完整序列继续编号。删除后物理 tensor 缩短，原语义位置不压缩。proprio 的物理位置为 K+1，但语义位置仍是 N+1。

OFT 官方 action readout 起点是 `NUM_PATCHES + NUM_PROMPT_TOKENS`；其中 NUM_PATCHES 包括 proprio。这实际从最后一个 prompt hidden 开始读取，保持 next-token shift，而不是从第一个 action placeholder hidden 开始。项目实现的物理起点 `K+1+P` 与之相符。[锁定 OFT 实现](https://github.com/moojink/openvla-oft/blob/e4287e94541f459edc4feabc4e181f537cd569a8/prismatic/extern/hf/modeling_prismatic.py)

独立测试使用“backbone 直接输出 semantic position ID”的确定 oracle：N=6、两个样本保留不同原索引，dense/sparse 均读取位置10、11、12、13；额外核对 proprio/text/action/stop 位置、placeholder 清零、stop 非零、attention mask 缩短与 cache 禁用。代码见 `tests/test_conditional_crossaudit.py`。这不是实际大模型数值等价证明。

## 非因果 SDPA

锁定 fork 的 SDPA forward 明确关闭 causal，并把上游 mask 的末行复制为各 query 的 mask；无 padding 时所有 token 双向互相可见。项目 loader 强制 SDPA 并核对 forward 方法源码 SHA256，普通 transformers 的相同版本号不足以满足这一条件。[锁定 fork 源码](https://github.com/moojink/transformers-openvla-oft/blob/bc339d9ad707454c0c115970db43c260067c61ab/src/transformers/models/llama/modeling_llama.py)

独立从该 commit 读取源码得到同一 SHA256 `46e487c53cd67d3ffbbf9f0274d6c855c214b03e8169bb4b9258dd1e2d7948e1`；提取原 forward，以零 Q/K、恒等 V/O、三角输入 mask 验证每个 query 都返回全部3个 value 的平均值，最大绝对误差0。输出为 `results/migration/independent_sdpa_audit.json`。该 probe 校验锁定方法语义，不替代安装后 runtime hash 或 GPU 验收。

## 输入与统计

`normalize_proprio` 的 q01/q99、mask 和最终 clip 规则与官方相符；processor-only 图像路径已明确不等同正式 LIBERO rollout 的 crop/resize/旋转/动作后处理。两分支共用输入的 tensor parity 不足以单独证明 rollout preprocessing 正确。[官方输入路径](https://github.com/moojink/openvla-oft/blob/e4287e94541f459edc4feabc4e181f537cd569a8/experiments/robot/openvla_utils.py)

方法缓存与 scorer 发现并修复了独立边界问题：`inference_mode()` 张量即使 detached，也不能直接被可训练小网络的 backward 保存。现在构造 batch/labels 时，在关闭 inference_mode 的局部作用域中复制为普通 detached 张量，包含 mask 与 index；真实 smoke 的优化阶段在外层 inference_mode 之外执行。

## 成本计数

- B 个 observation、每状态两个非完整集合、每集合2个候选：reference 1 + 2×(base 1 + deletion 2) = **7 个 batched policy 调用**。
- 每个 observation 参与7次教师调用；总样本前向数为 **7B**。随后最终选择执行1个 batched deployment调用，即 B 次样本前向。
- 标签总数为4B，拟合尺度所含 retained-set 行数2B，独立 observation 数B（按sample ID去重），episode 数另按episode ID去重。
- 工程 smoke 的单次优化仅消费第一个集合的2B标签，另一个集合只参与统一尺度拟合与缓存检查；输出明确记录这一点，不能描述为完成4B标签训练。
- 合成 B=2 smoke 中一个集合就是 full，省掉其 base 重复前向，因此 teacher 为6个batched调用、每observation6次、总样本前向12；与两个非完整集合的7次不矛盾。

这些计数不包含 dense parity 与各预算单独 tensor smoke 的前向，它们分别在报告的其他阶段；`engineering_seconds` 含校验/哈希/缓存开销，不是正式 observation-to-action 测速。
