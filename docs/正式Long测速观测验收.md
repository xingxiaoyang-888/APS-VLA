# Long 固定测速观测验收

2026-10-20 17:50 CST：训练 **62/72组通过root与独立复核**（Long18、Spatial16、Object16、Goal12），314000已审臂更新；本轮无新增训练或成功率结果。当前5卡运行，累计 **511.257 GPU小时**（全部登记分配，包含失败与运行中作业，非最终）。正常训练交自动控制器。

Long采集3047982完成双审：原10任务各一条预登记Dense开发轨迹，按实际首、中、末保留30观测，共11,839,320字节，没有按成功率筛换。两路图像和当前机器人状态按精确路径、SHA和数组格式放行到GitHub。369次动作chunk、2917控制步，完整分配472GPU秒（0.131小时，含加载）；已计入总账，不重复累加，不是O2A延迟。

采集不增加成功率分母：当前动作语义仍1600条开发试验、100唯一初态，历史1212另列。完整测速及分项计时未运行，遵守原88身份与四套件开发冻结。旧Long600复用映射仅归档作者候选，生产准入仍需root及独审；历史安装/工厂来源不冒称当时实例哈希测量，不新增旧完整RNG dump门槛。旧600未复用或重跑，最终0/35200封存，173科学文件不变。

[本轮证据](../results/formal_main_v2/preflight/heartbeat_20261020T1727/summary.json)，[观测验收](正式Long测速观测验收.md)。

## 固定来源与实际轨迹覆盖

每任务取原开发面板最小source_state_index。环境seed0、运行seed17、等待10步、chunk8、上限520控制步。等待后、执行动作前采集；middle=floor((N−1)/2)，无补帧或结果筛选。

| task | 开发初态索引 | 实际控制步N | 首 | 中 | 末 |
|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 380 | 0 | 189 | 379 |
| 1 | 4 | 249 | 0 | 124 | 248 |
| 2 | 7 | 242 | 0 | 120 | 241 |
| 3 | 3 | 220 | 0 | 109 | 219 |
| 4 | 6 | 260 | 0 | 129 | 259 |
| 5 | 2 | 148 | 0 | 73 | 147 |
| 6 | 3 | 200 | 0 | 99 | 199 |
| 7 | 6 | 269 | 0 | 134 | 268 |
| 8 | 8 | 429 | 0 | 214 | 428 |
| 9 | 2 | 520 | 0 | 259 | 519 |

## 内容与复查

每个NPZ恰含两路256×256×3 uint8图像，float64当前位置(3)、姿态四元数(4)、夹爪状态(2)，各394,644字节；allow_pickle=False，无object数组、额外ZIP成员或封存模拟器初态。官方Long基座revision 95220f9a3421a7ff12d4218e73d09ade830fa9a3，Dense512，无未来头。panel签名0287609dd3154b0aa86b9bd0325d1d702e793b7842af03a8c0cfb8c836b68392。

[原panel](../results/formal_main_v2/libero_10/downstream/collect/648ce4233e78353e/attempt01/panel.json)、[root审核](../results/formal_main_v2/downstream_reviews/3047982.json)、[独立审核](../results/formal_main_v2/downstream_reviews/3047982_independent.json)、[精确文件清单](../results/formal_main_v2/preflight/heartbeat_20261020T1727/observation_npz_delivery_allowlist.json)、[NPZ内容独审](../results/formal_main_v2/engineering/supervision_delivery_0927/Long_observation_delivery_independent/typed_allowlist_review.json)。

472GPU秒包括整个Slurm分配，不是策略调用均值延迟。正式O2A仍需同checkpoint、每实例50次预热、面板20轮、随机平衡顺序和共同计时边界。此次不产生加速比或成功率—延迟结论。审计脚本一次元数据字段名修正及失败原件保留，采集内容不变。
