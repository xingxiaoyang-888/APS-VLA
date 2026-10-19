# Spatial64 seed23 CUDA 恢复预约独审

结论：PASS_reservation_preparation_only。精确单次授权 3028522 尚未消费；可由 root 按共享 writer 锁/CAS 激活原 1 槽预约，等待真实 GPU 空槽。此报告不是提交许可的替代，也不是 GPU 恢复成功证明。

- 原 gateway.validate_authorization 通过，精确授权 7411a2e5…、预约 0aabce41…、controller3034538/activation/源码匹配。
- 真实查询全部259个登记作业，8个GPU活动、controller为运行中的0GPU作业；无未知状态、身份漂移或目标pair活动作业。
- Spatial64 seed23 保持原3024716→3025205→3028522历史，末次FAILED及73 GPU秒保留，blocked未清。未见相同授权消费、pending或attempt04发布。
- 原冻结 require_saved 对三份canonical failure proof从归档原始证据完整重建。Spatial A/B仍为1000更新、cursor8000，本次失败没有新增初始化或更新。
- 原 NativeIO.preflight 只读验证真实R/S173源、原输出清单/字节、wrapper和两份resume。A为ed121a0c4804865b109edbaded37d9e96f43ed17536e7bbf9ba066f064852550，B为47bc5895459c4e30b6a4e83184e695d919ea420683c1b2f75eda0a359a42f741；只做流式SHA，没有tensor反序列化或optimizer/RNG恢复。
- 计划仍为原5000步调度内1000→1500、batch8、h8、lambda0.1、每视角32token；4小时原恢复时限、排除gpu4020、至多新增1次。

当前8GPU满，未调用含容量门的RecoveryScience.prepare，也未改作业投影伪造空槽。NativeIO输入仅是从旧invocation与原proof抽取的只读I/O字段，没有构造或发布新生产invocation。root实际提交前须重新执行完整gateway授权、fresh全登记Slurm、容量、Science.prepare、NativeIO、pending/CAS与一次性提交事务；任何变化/歧义仍停。

作者代码及收据只写本审计目录；无state、P、Git、Slurm修改，无GPU调用或封存值读取。正常训练未干预。

本次命令：

```text
/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B /share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/spatial_cuda_reservation_audit_1621/audit.py
```

审计代码只允许新建本目录证据文件；不要原地重复运行覆盖原证据。完整Slurm原始输出、状态身份快照、NativeIO检查与856项精确引用分别在本目录JSON中。
