# 已完成 Spatial/Object 固定采集：root 回存与终验候选

仅作用于已登记的 3053503 (Spatial) 与 3053518 (Object)。作者没有运行 root helper，也没有改变 state/canonical 结果、Slurm 或 Git。原 `pull_formal_results.py` 根据自身路径推导服务器 R，不含需绕过的 F 盘断言；直接复用原文件，未新建传输适配。原 action-v1 reviewer/consumer 全部字节不变。

`root_collect_terminal_v1.py` 是给 root 的明确可审入口。须经已审 server_control_transport_v1，精确 bundle/入口 SHA，追加 `-- --root-execute-existing-collect-terminal`；不会默认执行。它在共享 writer.lock 内核两项登记和原私有输入清单；完整 terminal formal-job 快照仅供原 suite acceptance/来源链重新校验。原 pull 自身再次检查全登记作业的活动输出重叠与两次文件库存/Slurm 分配，只回存这两个输出、原 job receipt 和 stdout/err。

产物：`results/formal_main_v2/preflight/heartbeat_20261021T0349/collect_terminal/`，以及原规范路径 `results/formal_main_v2/downstream_reviews/3053503.json`、`3053518.json`。目录或 root review 已存在即拒绝重入，失败完整保留，没有自动重试。原 consumer 完整重建通过才写完成收据；若之后失败，已写的原审核结果与失败收据都保留，不能仅根据单一 passed 字段更新正式状态。所有 root 状态修改与独审整合仍是后续显式事务。

作者实际 P 只读核验：106 文件 / 27,522,013 字节；每套件10条预登记 Dense 轨迹，从原开发面板按每任务 source_state_index 最小值选择。环境seed0、runtime seed17、等待10、chunk8、Spatial220/Object280上限。固定首、floor((N-1)/2)、末，共60个原始NPZ /23,678,640字节；每个394,644字节，精确五数组，无对象/额外ZIP成员。全部原NPZ SHA、raw SHA、rollout SHA与任务收据/动作时间线一致；Spatial1007控制步/131查询，Object1319步/169查询。

20个针对性负例已在私有 CPU 检查通过：非法作业/阶段/套件/分配/重复恢复、原登记字节不一致、观测相位/步号/ID、NPZ目录越界、数组额外字段/错误类型/非有限值/错误形状。作者报告仅为原始字节预核，不冒称 root 或独立原consumer通过。`author_cpu_v1.py` 实际没有模型、GPU、网络或调度调用，明确拦截生产写入及权重/封存读取。

363/360 GPU秒已在 root 总账；helper只绑定原分配，不增加任何成本。新增scientific_trials=0；采集时长包括加载且不是O2A或分项计时；不发布成功率、不开放final、不更换科学面板。root 执行和独审仍待完成。

保留作者初次只读检查把 registered_jobs 误当dict的失败、输出过大被截断记录，以及 transport 首次拒绝 private audit 路径的原拒绝：该传输器仅接受原规范 control_transport JSONL，未改断言，改用规范新日志并在私有目录收存原件。
