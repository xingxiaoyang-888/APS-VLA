# G1-F 数据与动作—未来对齐审计

2026-10-14。仅完成数据与 CPU 验证，不代表模型验收、训练或闭环收益。

冻结清单：[windows.json](../configs/manifests/spatial_future_v1/windows.json)；真实数据核验：[data_window_audit.json](../results/g1_future/data_window_audit.json)；源码与测试证据：[data_alignment_audit.json](../results/g1_future/data_alignment_audit.json)。

## 时间语义

采用 `obs[t] + actions[t:t+8] → obs[t+8]`，所有字段来自同一 episode。h=8 与 OFT 的 8 步 action chunk 对齐；合法起点为 `0 ≤ t ≤ N−9`，不复制末帧、不填充动作。

这不是仅凭 RLDS 字段名称推断。固定的 [OFT 再生成代码](https://github.com/moojink/openvla-oft/blob/e4287e94541f459edc4feabc4e181f537cd569a8/experiments/robot/libero/regenerate_libero_dataset.py#L135) 在执行前跳过 no-op，然后记录当前图像、proprio 和 action，最后才 `env.step(action)`。因此保留索引表示再生成轨迹中连续实际执行的控制步。初帧来自 10 步静置后的观测；RLDS 使用记录的 ee/gripper 观测，不使用复制的初始 `states/robot_states`。

作者的 [Spatial RLDS 转换](https://github.com/moojink/rlds_dataset_builder/blob/6174b0b6bb69df6361f1117944952bf14afb0cc3/LIBERO_Spatial/LIBERO_Spatial_dataset_builder.py#L43) 将同一索引的双相机、state、action 写入同一步，并将图像旋转 180°。最后一个 `is_terminal/is_last` 标记属于该步及其将执行的动作；最后保存的图像仍在最后动作之前。合法 late 窗口的未来可为最后保存帧，其动作区间截至倒数第二个动作，故不会越过 terminal。

边界：发布数据未提供原始示范时间戳或原始动作索引，也未记录生成时的精确代码 commit。当前结论有固定作者源码和实际 RLDS 长度/边界核验支持，但未独立重跑全部模拟器生成过程。不得将再生成 step 当作原始示范 timestamp，也不得将学生生成的不同动作配给这份示范未来。

## 真实示范动作目标

`normalize_demo_actions(raw_actions, checkpoint_action_stats)` 返回 `float32[8,7]`，复现原生 OFT LIBERO 的变换顺序：

1. 前 6 维保持原始动作语义；夹爪变为 `1−clip(g,0,1)`，即 1=open、0=closed。
2. 使用该冻结 checkpoint 的 `libero_spatial_no_noops/action` 统计，前 6 维按 `clip(2*(a−q01)/(q99−q01+1e−8)−1,−1,1)` 归一化；夹爪不按分位数缩放。
3. 与官方一致，`min==max` 的维度最终置零。要求显式 mask 为 `[true×6,false]`，不接受隐式默认、不在 validation 上拟合统计。

来源：[LIBERO transform](https://github.com/moojink/openvla-oft/blob/e4287e94541f459edc4feabc4e181f537cd569a8/prismatic/vla/datasets/rlds/oxe/transforms.py#L827)、[归一化及常数维处理](https://github.com/moojink/openvla-oft/blob/e4287e94541f459edc4feabc4e181f537cd569a8/prismatic/vla/datasets/rlds/utils/data_utils.py#L67)、[动作 mask](https://github.com/moojink/openvla-oft/blob/e4287e94541f459edc4feabc4e181f537cd569a8/prismatic/vla/datasets/rlds/oxe/materialize.py#L38)、[chunk 索引](https://github.com/moojink/openvla-oft/blob/e4287e94541f459edc4feabc4e181f537cd569a8/prismatic/vla/datasets/rlds/traj_transforms.py#L14)。CPU 测试从固定上游源码抽取原函数，以 NumPy 代替所用 TF 基础算子逐元素比对；这不等于运行完整 TensorFlow 数据管线。

## 固定窗口与隔离

| 划分 | 选中 episode | 固定窗口 | 每任务早/中/晚 | 所选轨迹全部合法起点 | 不足 h8 未来的末尾起点 |
|---|---:|---:|---|---:|---:|
| train | 30 | 90 | 3 / 3 / 3 | 3,442 | 240 |
| effective validation | 20 | 60 | 2 / 2 / 2 | 2,308 | 160 |

Train 继承原 diagnostic90 的 30 条训练轨迹。Validation 从原 effective validation 的每任务池选 2 条，seed=517；先按 episode ID 排序，任务名称与 seed 经固定 namespace 签名作为任务独立随机种子，再无放回抽样。排除工程曝光轨迹，test 不入池。没有剔除短轨迹：实际 N 为 79–182，所有 50 条均满足 3 个不同起点。

每条轨迹的窗口起点固定为 `0, floor((N−9)/2), N−9`。早/中/晚指**合法起点区间**，不是预先标注的语义阶段；late 的未来恰为末帧。所有合法起点统计用于说明可用范围，不代表已经抽取或训练了 5,750 个窗口。末尾 400 个不可用起点是按所有 step 起点统计；相对“仅需完整 8 动作”的原生 chunk 条件，本方案每条轨迹再少 1 个起点。

本次实际读取并校验 16 个 shard 的字节数/SHA256，对选中 50 条 episode 解码，验证内容 ID、存储定位、N、指令、双相机/动作/proprio 长度以及 first/last/terminal。顺序读取 TFRecord 时会经过其他记录的字节及 CRC，但没有解码 test 观测或将其作为模型输入。

窗口 manifest 文件 SHA256：`e63a30e4c0f63dd7008241f828cab794628be5268f38bd641ce75a12eb6ea66b`。内容签名：`sha256:70d12e3b90ebd5d43e1dac54856847acd5c9b403d918fb70ed9512d79725aa60`。

## 接入与验收边界

实现：[future_windows.py](../src/cti_vla/data/future_windows.py)；构建命令 `python scripts/data/build_future_windows.py`。`load_future_windows(path, protocol)` 验证清单签名、固定抽样规则、真实 episode 划分及已登记数据资产 hash；不沿用旧首/中/末 step 白名单。GPU 缓存前须再校验实际 shard bytes/SHA，再对每条解码记录调用 `validate_future_window(row, episode, protocol)`。

缓存应绑定 window、模型 revision/统计文件 hash、预处理/packing、未来 target 编码定义与实际 producer 源码。当前图像/语言/proprio 仅取 t；真实 GT 取 `[t,t+8)`；未来图像仅生成 detached 目标。该缓存审查不能替代 CUDA 梯度、原生全量动作一致性和部署不读取未来字段的实测。

专属 CPU 测试：`python -m pytest tests/test_data_future_windows.py -q --basetemp .local/test-artifacts/future-windows`，20 项通过。覆盖合法窗口、真实划分/隔离、边界异常、动作变换、重签名清单篡改、源字节变化和 150 窗口一致性。真实 RLDS 清单构建耗时 225.82 秒，GPU 调用为 0。
