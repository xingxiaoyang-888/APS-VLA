本次只审已提交的 Spatial 3044479 登记对账。a2 原源码 SHA 为 6cc0bce095f6f33bacd1fe6bd65ce2e3e1c8baa72ebaf0d27d96193c07e097cb。

独立执行原 a2 的精确只读前缀，物理删除 AST 中内存登记/文件发布/CAS 之后全部语句；未运行完整脚本。真实 266 行完整登记+已知作业对账通过，8 GPU，控制器 CPU0 与租约一致，原 ACK/token/argv、R/P invocation 和 173 R/S 源一致。3 个缺行、错 token、历史终态漂移负例由原 reconcile_submission 拒绝；原状态变更语句仅在内存模拟，真实 state 未改。

a1 存在队列路径返回 None 却访问 stdout 的问题，未执行，原件保留；a2 独立读取 scontrol 原文解决。实际返回为单条且各身份字段唯一。

root 可运行固定 a2，以其现场检查和 CAS 仅补登记原 job；不得再发 sbatch。此独审不代表对账已经提交，也不是训练成功或优化器/RNG恢复证明。全部原失败保持。

交付 archive_closure.json 所列顶层文件，以及独立 transport 日志；未修改生产 state、源码、Git、Slurm 或封存值。
