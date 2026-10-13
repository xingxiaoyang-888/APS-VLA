# 条件选择器与删除教师迁移审计

审计日期：2026-10-14。来源为只读历史项目 `F:/DIWA`；本文件及新增实现均属于 `F:/CTI-VLA`。这里记录代码语义及工程验证，不记录闭环成功率或实测加速收益。

补充真实验收：L40作业2987244通过单观测条件链路：7次教师调用、4个signed标签（包含负值）、缓存往返、用2个标签进行1次临时scorer更新，选择后1次策略前向；大策略无梯度。没有保存训练模型，也不构成选择质量结论。见 [原始结果](../results/smoke/openvla_2987244.json) 的 `conditional_integration`。

## 结论

旧方法核心不能直接沿用作为 CTI-VLA。保留其“冻结教师、顺序调用、轻量网络单独训练”的工程边界，按本项目研究方案重新实现 `selection/conditional.py`、`labeling/deletion.py`、`labeling/cache.py`、`training/conditional.py`。这些模块没有对 `diwa` 或旧目录的运行时依赖；旧 checkpoint 和旧 teacher label 不自动兼容。

| 历史实现 | 与当前方法不一致之处 | 本次处理 |
|---|---|---|
| `models/influence/teacher.py` | 对保留全长的替换前后动作计算非负 Huber 距离；不是相对完整教师的误差增量 | 顺序执行真实 `S`、`S-i` 的保留索引回调；`y=mean(abs(a_S-i-a_full))-mean(abs(a_S-a_full))` |
| `models/influence/die.py` | softplus 限制非负；没有独立归一化 proprio 编码和原 patch 编码；集合摘要跨相机混合 | 线性 signed 输出；冻结词嵌入+轻量位置编码、proprio MLP、相机/原 patch 编码、分相机 mean/max |
| `models/stage_b_selector.py` | 单轮全局 Top-k，且输出为分数顺序；未保证原视觉顺序和每相机预算 | 多轮显式预算，每轮重算集合条件；同分优先原序号；最终原序输出 |
| `losses/influence_loss.py`、`influence_targets.py` | 非负 log1p；hybrid 含逐样本 max-normalization | 统一训练集 RMS 正尺度，不平移标签，保留负值；Huber 为默认，集合内 ranking 默认关闭 |
| `training/stage_a.py`、`pipeline.py` | detach/optimizer 隔离可借鉴，但其 batch/teacher 假设仍属于旧标签 | 新 trainer 只消费校验过的 detached 新缓存；optimizer 必须恰好包含 scorer/条件编码参数 |
| `data/teacher_cache.py` | 非负约束；记录删除数量不能确定具体 S | 保存完整 S、候选原索引、full action、两项误差和 signed 标签；绑定内容摘要与版本 |
| `models/influence/sampling.py` | 历史候选方案围绕旧替换标签与归因覆盖率设计 | 未直接迁入；新 teacher 接受显式候选，后续按实验配置加入随机/均匀/selector 集合采样 |

## 新接口与统一边界

`ConditionalTokenBatch` 包含完整原序视觉特征、冻结 instruction token embeddings、指令 mask、已归一化 proprio、camera ID、原 camera-local patch ID、valid mask。拒绝携带梯度图的输入；对 `inference_mode()` 产生的张量（含 bool mask/整数索引）转为普通 detached 拷贝，避免它们不能被小网络 backward 保存。proprio 的归一化统计由对应 checkpoint 决定，不能重新用当前小样本拟合。

`ConditionalInfluenceEstimator` 默认投影维度 256，语言 token 加位置编码后先经非线性网络再池化，避免单纯相加再均值导致顺序信息消失。每相机分别统计当前 S 的均值与最大值，并读取 `|S|/N`。输出为可正可负的删除增量。训练后输出单位是统一 RMS 归一化单位，乘 checkpoint 中的 `TrainingLabelScale.value` 可恢复原动作误差单位；Top-k 次序不受正尺度影响。

`staged_topk(estimator.eval(), batch, ((128,128),(64,64),(32,32)))` 对双 256-patch 视角得到 `512→256→128→64`。阶段内保留分数较大的 token；这仍是批量删除近似，不是精确组合搜索。

`DeletionTeacher(policy, callback)` 要求 policy 的全部子模块 frozen/eval。callback 签名是 `(batch, retained_indices[B,K]) -> normalized_actions[B,8,7]`，必须调用共享 `OpenVLAOFTTokenPolicy.forward_from_full_tokens`。例如：

```python
def callback(batch, indices):
    return policy.forward_from_full_tokens(
        batch.visual,
        batch.normalized_proprio.to(batch.visual.dtype),
        input_ids=input_ids,
        attention_mask=attention_mask,
        retained_indices=indices,
    )
```

teacher、selector 与 policy 都直接复用 `models.abstraction.packing.retained_indices`。其版本为 `oft-original-positions-v1`，按原坐标升序排列真实删除后的 token。policy 内部统一重建原 position IDs、attention mask 与 action slice。当前 batch 必须按 prompt 长度、full visual 数量和 S 大小分桶；不同 observation 可有不同具体 S。

`teacher.reference(batch, provenance)` 用一次完整前向产生可复用 reference；随后 `label(..., full_reference=reference)` 只执行需要的 base 与 candidate 前向。两个非完整集合、每集合 8 个候选，共 `1 + 2×(1+8)=19` 个 batched policy 调用。reference 的模型/数据/条件摘要不匹配时拒绝复用。`teacher_calls` 记录当次 label 新发生的 batched 调用数；`teacher_calls_per_observation` 数值相同，`teacher_sample_forwards=B×teacher_calls`。复用 reference 时须另计最初 1 次 batched 调用和 B 次样本前向。训练标签数为 B×集合数×候选数，不能用它当作独立 observation 或 episode 数。

## 缓存与训练约束

新缓存 `save_deletion_labels`/`load_deletion_labels` 为独立 schema，CPU detached 张量写入 `.pt`；读取使用 `weights_only=True`。缓存绑定 sample/episode/split、模型 revision、数据/preprocess/packing/condition/action/label 版本，并对完整视觉特征、指令特征/mask、proprio、camera/patch/valid 内容作 SHA256。训练前校验具体 S 与候选，以及 `y=E_deleted-E_base`。不能把历史缓存重命名后直接训练。

统一尺度仅接受 train split，记录参与拟合的 episode IDs；验证/测试 episode 与拟合 episode 重叠会报错。调用方仍需使用数据模块的 episode split manifest，版本字符串应填写已登记的真实 revision/hash。内容 hash 校验为离线正确性检查，会产生 CPU 拷贝，不属于最终优化过的计时路径。缓存重排/切分时必须重新构造对齐的 batch 与记录，当前实现不会自动对齐任意 sample 顺序。

## 已验证与未完成

- `python -m pytest -q tests/test_conditional_method.py tests/test_conditional_cross_audit.py tests/test_conditional_crossaudit.py`：23 项通过，torch `2.0.1+cpu`；含独立代理的 B=2 非线性标签手算、相对条件分数/空相机梯度检查、本次 inference tensor 回归，以及真实 policy 接口上的 512-token 合成联调。17 项主方法测试覆盖负标签、真实删除长度、reference 复用、条件编码、detached 边界、bfloat16、相机预算/原序/同分、统一尺度、缓存与 optimizer 隔离。
- `python scripts/smoke_conditional_pipeline.py --output results/smoke/conditional_synthetic_2026-10-14.json`：合成 B=2 通过实际共享 OFT policy/packing 接口；6 次 batched 教师调用、12 次样本前向；缓存往返、仅 scorer 更新，最终选择后仅 1 次 policy 调用。backbone/action head 为合成小模块，结果不是预训练 VLA 或 LIBERO 成果。
- `evaluation/conditional_smoke.py` 已接入 `scripts/smoke_openvla.py`，位于大 `inference_mode` 作用域之外。真实运行将执行两个 S（均匀256/随机128）、各2候选，完整 reference 1次加每集合3次，共7次 batched teacher调用；缓存往返，临时 scorer 优化一步，分阶段选择后再执行1次 policy。不保存 scorer checkpoint。当前记录仅确认其 mock policy 回归通过；实际 GPU 验收以服务器回存结果为准。
- 尚未完成正式集合采样策略、训练作业/恢复 checkpoint、正式 episode 覆盖实验与闭环评测。不能由上述测试推断成功率、真实标签收益或 observation-to-action 加速。

## 来源 SHA256

以下 SHA256 为本次读取的历史文件内容，不表示这些旧文件已满足新方法；旧项目未写入修改。路径均相对 `F:/DIWA`。

| 来源 | SHA256 |
|---|---|
| `diwa/models/influence/die.py` | `421aa13152703f3a920f73091f54b1908cb89caed4072aa8afb765355dd0c17e` |
| `diwa/models/influence/teacher.py` | `9689695491d1a03596d386ea5e9f5b2770b19e5b5f33e3f23d9b1c12f80c8280` |
| `diwa/models/influence/sampling.py` | `a3d99bda425dd31f814d34a9d3524aa35265eeab08da11fb58c13b0710b4e207` |
| `diwa/losses/influence_loss.py` | `ac19e6e4f67f02f3d051ed4fd744cabeb4c31e85b645eab92d7d012a72436f43` |
| `diwa/losses/influence_targets.py` | `e7fec8b5d5e547772a033b337c42e4b9c540b45ba422adcb695f426fc92b93f8` |
| `diwa/losses/action_distance.py` | `a3310c2c23e514e0978d5585d0f6ba7efb85c617d57f962fede4569c04a22a3b` |
| `diwa/models/stage_b_selector.py` | `b4222eaf0bb5cb0e502a195e1f2bcbeb2a6bb7472ea17ee8babfdfbe6bc6b941` |
| `diwa/training/stage_a.py` | `330fbc2520712b00269be1a27672ca01cd19a396256d19bf9281f3b762759496` |
| `diwa/training/pipeline.py` | `b8df6c6b8822cc6f2e4388a472b825f07885d66e8b493910c5f828e1f208893d` |
| `diwa/data/teacher_cache.py` | `1531a0874d26d3f374db042091ce860391ec895d035df4f3412b18b20051d162` |
