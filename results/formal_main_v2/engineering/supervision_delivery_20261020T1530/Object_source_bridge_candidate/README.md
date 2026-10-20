# Object256 seed23 来源兼容桥候选

仅处理 `libero_object / 256 / seed23` 的 A/B 已选 checkpoint。候选没有提交GPU，没有改变训练或开发科学设置，也没有获得 root 科学准入。

- 保留 3028460 原 CUDA 启动失败、原错误日志及0步边界；成功 metadata 只属于3039258、3042627。三个分配完整计账58,917 GPU秒，其中失败84秒；不重新训练。
- `bridge_v2.py` 是当前候选；`bridge_v1.py` 及两轮CPU记录全部保留。版本化私有副本严格绑定原 consumer SHA，以四处精确替换实现三个操作差异：成功/失败来源分开；失败走原 raw verifier；原 pull 的三个失败外部文件保留失败作业所有权。全部成功训练、173源、F00/F01/F03、选模与部署收据检查仍走原函数。没有伪造普通metadata或改变原consumer。
- `policy_v1.json` 硬绑定唯一pair、三job、原失败、恢复root/独审、连续准入、终验root/独审、selected-server证明和两个checkpoint SHA。任一改变即拒绝。
- `attempt02/cpu_checks.json`：41/41 CPU通过；原factory仍按旧metadata错误拒绝；新factory完整科学门槛通过；终态消费者能重建完全相同的显式版本proof。负例覆盖遗漏失败、篡改费用/种子/checkpoint、伪装成功、漏独审等。
- `runtime_check01/P_check_only.json`：root精确发布两个静态JSON后，真实P原wrapper.verify与action runtime metadata检查通过。它们未加载模型/环境、未读取权重或封存值。新action wrapper因缺真实root readiness正确拒绝。四项P准备检查是CPU元数据证据，不能称GPU通过。

## 后续集成门槛

1. 独立审核此候选与原失败来源链，root决定版本化准入；当前不可提交。
2. 生产factory、planner、gateway独立重建和终态来源consumer必须明确使用同一桥。`control_modules()`仅创建私有工厂/planner实例；`auditor().review_invocation()`提供开发期终态接口。原生产gateway仍使用旧consumer，不能直接通过当前生产gateway提交。不得静默替换全局helper或按异常放行。
3. 科学manifest已按原字节在R/P发布；桥源码、调用、state、Slurm、root readiness均未发布。有效计划预览引用私有路径，仅用于审阅，不能直接用于部署。
4. root整合后必须重建精确计划、验证生产gateway和终态consumer的来源proof一致，并执行真实root/独立readiness、当时锁内CAS/重复提交/8槽检查。当前checkpoint原字节仍需部署前由原运行入口核验。
5. 只允许既定100个开发初态×A/B=200条，保持测试封存。不授权其他pair、预算、最终评测或自动重试。

`author_state_snapshot.json`明确为作者只读原子文件快照，不是root writer-lock/CAS授权；root最初观察与发布收据另有精确SHA。所有已有失败和版本均保留。最终seal自身的闭合transport位于候选外，将由root按返回SHA单独归档，避免递归自哈希。
