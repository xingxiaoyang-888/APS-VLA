# Long G1-F 数据协议与时间对齐审计

本轮是独立的 LIBERO-Long 数据实验，套件为 `libero_10`，RLDS 与归一化键为 `libero_10_no_noops`。不使用 Spatial 选择器、清单或验证样本。这里只核验数据契约与构建工具；真实窗口审计以服务器生成并回存的收据为准，不预写 150 个真实窗口已验证。

## 固定来源与整轨迹隔离

- [资产清单](../configs/assets/libero_long_rlds.json)：`openvla/modified_libero_rlds` revision `6ce6aaaaabdbe590b1eef5cd29c0d33f14a08551`；32 个 `liber_o10-train.tfrecord-xxxxx-of-00032`，379 条轨迹，全部文件总计 3,656,815,424 字节。379 来自发布的 `dataset_info.json`，不是根据 Spatial 外推。
- [独立注册规则](../configs/experiments/g1_future_long_data_v1.json)：官方 LIBERO commit `8f1084e3132a39270c3a13ebe37270a43ece2a01` 的 `task_order_index=0`；任务名、语言与源码 SHA 固定。闭环任务预先取 0/3/5，不能按数据变化量或结果改选。
- 全部轨迹只做 protobuf 结构、长度、语言、边界标志与压缩字段内容 ID 清点。文件路径通常只标识任务 HDF5，不能充当轨迹 ID。沿用稳定内容 SHA 和每任务 `split_episodes(seed=17)` 的 70/15/15 整数分配，拆分不受目录顺序影响。
- 每任务在 train 中 seed117 抽 3 条，在 validation 中 seed517 抽 2 条；池先按 episode ID 排序，随机数种子还绑定 split 和官方任务名。若选中轨迹不足 3 个不同合法起点，拒绝构建，不能补抽或静默丢弃。
- 只对选中的 30 train + 20 validation 条轨迹执行完整数值解码和图像解码；test 的 protobuf 数据必须被读入和哈希以建立身份，但不解码其 RGB、不物化其 action/proprio NumPy 数组，不作为模型输入。Long 尚无工程曝光隔离条目；任何新曝光需单独登记，不能把 Spatial 隔离项机械套用。

## 时间对齐与真实动作 GT

固定 OFT 源 commit `e4287e94541f459edc4feabc4e181f537cd569a8` 的 [regenerate_libero_dataset.py](../external/openvla-oft/experiments/robot/libero/regenerate_libero_dataset.py:136) 先判断并跳过 no-op，再记录当前观测和实际动作，最后执行 `env.step(action)`。因此过滤后的索引是重新执行的控制步；不是删掉帧后仍沿用原始时间戳。

作者 RLDS builder commit `6174b0b6bb69df6361f1117944952bf14afb0cc3` 的 [LIBERO_10_dataset_builder.py](../external/rlds_dataset_builder_future/LIBERO_10/LIBERO_10_dataset_builder.py:43) 把同一索引的图像、EEF 状态、夹爪状态和 action 写入同一步；双相机已旋转 180°。最后保存的图像是最后一个动作之前的图像，没有保存最后动作执行后的新图像。

所以每窗固定 `obs[t]`、真实 `actions[t:t+8]`、`obs[t+8]`，动作末项是 `action[t+7]`。长度 N 的起点必须满足 `0 ≤ t ≤ N−9`；取 `0, floor((N−9)/2), N−9`，要求三点不同，禁止 padding。早/中/晚指合法起点区间，不是语义子任务阶段。末窗的未来图像可为第 N−1 帧，其 outgoing action 的 terminal 标志不意味着窗口跨终止边界。

GT 直接复用经过核验的纯算子 `normalize_demo_actions`：先按 [官方 LIBERO transform](../external/openvla-oft/prismatic/vla/datasets/rlds/oxe/transforms.py:827) 令夹爪为 `1−clip(raw,0,1)`，再以当前 **Long** checkpoint 的 `libero_10_no_noops` 统计量做 BOUNDS_Q99。前六维按 q01/q99 归一化并裁剪，夹爪不缩放，min=max 的维度设零。不能重拟合统计量或拿 Spatial checkpoint 的统计量。训练 runner 负责绑定 Long 模型 revision 与统计文件 SHA。

上述时间语义是固定源码审计与 RLDS 结构交叉核验；发布的 RLDS 没有原始示范时间戳、逐条 demo ID 或可验证的生成 commit，因此不能声称已独立重新生成整个数据集。

## h8 变化量与验收

固定 150 窗后再计算下列描述指标，指标不反过来影响样本选择：

- EEF 位置端点 L2 与 8 步路径长度，单位米。
- EEF 轴角转旋转矩阵后的 SO(3) 端点夹角与逐步角度和，单位弧度；不直接相减轴角向量，避免 ±π 环绕错误。
- 两维夹爪 qpos 的端点 L2 与路径长度，保持原始物理量单位。
- 两相机的原始 256×256 RGB 端点 MAE、RMSE（0–1）和任一通道变化超过 8/255 的像素比例。无模型特征、无图像保存或展示。

端点/路径不同可识别“移动后返回”这一数值现象；图像差异也包含相机运动和外观变化。所有指标都不能证明物体任务进度或语义子任务切换。报告提供逐窗值及 split/task/phase 的均值、中位数、p95；同轨迹窗口并非独立样本。

CPU 测试 `tests/test_data_long_future_windows.py` 25 项通过，原 `tests/test_data_future_windows.py` 20 项保持通过（合计45）。覆盖同内容身份、379 轨迹结构、固定选样、禁止 test 冒用、重新签名不能绕过权威配置、终止边界、GT 共用、只解码选定记录、角度环绕和运动返回。测试数据是合成 protobuf，不替代真实数据验收。

## 构建接口与产物

在主项目运行环境执行，无 GPU/模型依赖；需要 NumPy、protobuf、Pillow：

```text
python scripts/data/build_long_future_protocol.py --project-root PROJECT_ROOT
python scripts/data/build_long_future_windows.py --project-root PROJECT_ROOT
```

代码从不可变 snapshot 执行时，同样显式指向主项目 `--project-root`；输出不得落入 snapshot。两步依次生成：

| 产物 | 含义 |
|---|---|
| `configs/manifests/long_future_v1/protocol.json` | 所有轨迹的元数据整轨迹划分、任务映射、原始 shard SHA 与计数 |
| `configs/manifests/long_future_v1/windows.json` | 固定90 train / 60 validation 窗、真实定位、h8动作区间及来源 |
| `results/g1_future_long/data/protocol_audit.json` | 完整源文件与元数据核验收据 |
| `results/g1_future_long/data/window_audit.json` | 仅选定50轨迹解码核验收据 |
| `results/g1_future_long/data/h8_endpoint_changes.json` | 不影响选样的逐窗变化量与汇总 |

这些文件使用冻结写入，不能覆盖不同内容。运行耗时每次不同；再次审计应使用新的 `--audit-output` 路径。

公共模块 `cti_vla.data.long_future_windows` 提供 `load_long_future_protocol(path, asset_manifest=None, registration_path=None)`、`load_future_windows(path, protocol)`、`validate_future_window(row, episode, protocol)`、`normalize_demo_actions`。显式别名为 `load_long_protocol`、`load_long_future_windows`。此处 asset 参数专指 RLDS 清单。默认 protocol 位于项目标准 `configs/manifests/long_future_v1`，loader 由此定位资产和注册文件；也支持显式传入。

`protocol.payload.task_catalog` 是 `{task_id, task_name, instruction}` 列表；window 的 `task_name` 延续 Spatial 接口，表示语言 instruction。window 行与 Spatial 字段相同，但 dataset、window ID、版本和签名相互独立。cache 前必须调用 runtime validator，并再次核验实际 shard 字节数/SHA；validator 检查内容 ID、长度、存储位置、真实 split/固定面板、语言、首末/终止标志及完整 action8/proprio。

本轮仅新增 Long 数据模块、两条构建脚本、注册规则、专属测试与本文；没有改动 Spatial 数据代码、模型权重或 GPU 作业。

源码 SHA256：

| 文件 | SHA256 |
|---|---|
| OFT regenerate_libero_dataset.py | `165fd2c08a6d29306de53b3ea9a0fbaf4a7e3d533d82464f21a38f2909ac0dd8` |
| Long RLDS builder | `f7fe4df4a6d88e7449e246d57356b4be0f418707a3c20b4299d0a678f48d2c74` |
| OFT oxe/transforms.py | `7644f1b4fa0badab70f9924de68eeb9d94b41c82bf6d8dbc776e58677adae485` |
| OFT utils/data_utils.py | `4f7a36c6713e6c28a7237ec7ae1325abd47a1f0c921164fc5548ce4c81340d44` |
| Long RLDS asset manifest | `ff033c44aeabb41cae06524be4d3db76a2514b25428e8562dd8ceb1adc746b5a` |
| Long data registration | `9c682603bc9bc32d6bb1f3c19f7144cb09879aa6bb7320b68f1d30d74076ac97` |
