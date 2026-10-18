# 动作 v3 与自动训练共存的受限提交桥接

仅替换冻结 supervisor 的 read/write/lock/refresh 接口；原 execute_submit、科学 probe、launcher、wrapper、manifest 与 node_exclusion 不变。兼容模块的 __file__ 是原 supervisor 身份锚，实际 facade 身份由 entry 显式 SHA 绑定；不把替换函数称为冻结函数。

- 查询全部登记作业，原始 sacct/squeue 和 CPU0 证据完整保留；仅容量投影排除登记与当前 AllocTRES 均为 0GPU 的作业。未知、重复、非本项目活动作业或身份漂移均拒绝。
- 只使用既有共享 writer 锁，缺锁拒绝；CAS 与三次原 pending 状态转换强制完整字段白名单。历史 registry、controller 完成收据和 next_actions 不被 legacy refresh 覆写。
- 最终 current_round_cost.registered_jobs 保持原正式轮次语义：sum(experiment == formal_main_v2)，不误用 GPU 投影数量；全 registry 保留历史实验。
- 只有新 v3 job 已持久入册的同一最终 CAS 才把专用 reserved_GPU_slots 从 1 改为 0，并记录消费 job。原 reservation_root_record 保留。未知 ack/上传/收据失败保留 pending 和预留；不自动重试或清理。
- 默认 check-only：无 state、invocation、publication、Slurm 提交或审计文件写入，仅 stdout。root 可另行把 stdout 保存在服务器。
- 实际提交必须显式 --submit --root-reviewed-submit，精确 entry SHA，且位于既有受审 transport 范围。原 node exclusion 保留 --exclude=gpu4020。

作者 CPU：34/34；覆盖原 execute_submit 的真实三阶段流程与真实 node adapter，远端上传、ack 和科学合同闭包在这组测试中为明确 synthetic fixture。另以真实全合同与全登记 Slurm 只读检查验收：245 作业，7GPU，unknown/findings 空；无新 GPU/模型/封存初态读取。原 a1=33/33 及缺锁修正历史均保留。

检查（默认即 check-only）：

```sh
/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B /share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/action_v3_autonomous_dispatch_1808/entry.py --entry-sha256 1cb2e30fbde96376183f77b5fb863e823500e2601f2157af00f93ff5ee703788
```

root 完成独立审查后的一次实际命令（本候选未执行）：

```sh
/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B /share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/scripts/ops/server_control_transport_v1/run_server_control.py --bundle-manifest-sha256 3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149 --entrypoint .local/action_v3_autonomous_dispatch_1808/entry.py --entrypoint-sha256 1cb2e30fbde96376183f77b5fb863e823500e2601f2157af00f93ff5ee703788 --audit-relative results/formal_main_v2/control_transport/action_v3_autonomous_dispatch_1808.jsonl -- --entry-sha256 1cb2e30fbde96376183f77b5fb863e823500e2601f2157af00f93ff5ee703788 --submit --root-reviewed-submit --audit-relative results/formal_main_v2/preflight/heartbeat_20261019T0208/action_v3_dispatch_01
```

候选固定只适用当前 reservation、controller3034538 和该 v3 一次登记。后续工程实验不自动获授权；真实 GPU 动作验收尚待 root 提交并检查。最终闭环继续封存。
