# Object 唯一旧 policy_error：stage2 CPU 候选

状态：HOLD，尚未生产接纳、安装或提交。此包只有可执行CPU谓词、精确循环派生、分层结果视图和测试；不是新的GPU入口。Object599独审原包保持原字节。

固定目标为 Object/task8/source49/dense。原100开发初态、六方法清单、官方基座、A/B已选checkpoint、seed17/env0、等待10步、8动作块及280步horizon全部保留。原600与6713GPU秒保持不变；旧第8次被拒绝chunk没有保存，其具体值仍未知。

- fixed.py 逐SHA复核原600、失败start/result字节、599独审、原3个作业及173冻结源码；科学scope绑定完整原manifest，不将它改成1状态或1方法。
- iterator.py 只在原 evaluate_formal_trials 的 identity 构造之后插入一个精确trial_id白名单条件。原完整100状态和6方法校验、reset/reseed、动作执行、成功判据及错误记录保留。新ledger必须仅有一次实际新invocation，不伪填599 completion，不使用普通resume或stop_after=1。
- gate.py 是无IO的CPU准入谓词：逐角色root repair/599采用/独审/实际P readiness、所有模式最多8GPU、相同pair/cell互斥、pending/未知ACK、原token/comment和已尝试输出重复保护、controller终态、writer lock与CAS。它只返回不可提交的pending intent，绝不调用Slurm或修改state。
- terminal.py 只构造引用视图599 legacy-equivalent +1 linked-current。原600、旧policy_error与新结果分别保留；新负结果不触发再试。6713只按共享allocation计一次。原始raw不重写。
- test_cpu.py 有24项正例和74项拒绝。CPU假环境只重放旧失败记录已经保存的第一个chunk，不运行LIBERO、策略推理或GPU。伪造job9900001及100GPU秒仅是标明synthetic的测试输入，不能计入实际账。
- verify_saved.py 只读完整复跑CPU测试并逐项比较已保存输出。已通过；实际新增科学trial/GPU/Slurm提交均为0。

## 必须先补齐的生产门槛

本包的predicate成功不等于运行许可；inspect_candidate始终HOLD。未来确切新wrapper/entry/gateway/reviewer/consumer仍未实现或独审。当前source_map只覆盖四个候选模块和scope；未来完整生产闭包必须加入上述全部入口并重新独审，不得拿这个五文件CPU闭包冒称完整运行链。

原adapter会将当前函数代码记成 frozen_trial_loop_code_sha256。未来typed接线必须分别记录原冻结循环与实际派生循环，不能把派生函数代码放进旧字段冒称冻结原函数。不要修改原adapter或action wrapper文件，另建精确新typed入口；原完整模型、checkpoint、manifest、panel、数据和原始轨迹consumer检查仍必须运行。普通600条summary对新ledger只能报告partial，不能更名为completed；完成逻辑由独立typed引用视图表达。

terminal.py接收的两个terminal receipt对象只测试类型和绑定，尚不实现完整真实consumer重建。生产前必须让原轨迹/统计/动作runtime及adapter证据校验闭合，独审确认后再传真实canonical收据，不能用测试中的布尔断言代替真实检查。

root必须明确采用归档599独审，仅标599条legacy兼容；随后冻结唯一linked correction的完整production source闭包、真实P --verify、容量快照与原子提交门。新原子gateway只能一次记录pending→原ACK对账，未知结果停止，不清pending重发。任何失败、preempt或timeout都保留成本并停下。必须从初态完整reset，不从旧56步恢复，不推测query8，不以结果决定是否再试。

publication_map.json仅列候选将来的准确目标与当前SHA，actual_installed=false。未提供实际生产入口的任何SHA。所有新产物只在本私有服务器目录及已审transport指定journal；根状态、Git、P运行入口、173冻结源码、原独审均未写入。最终封存仍未开放。
