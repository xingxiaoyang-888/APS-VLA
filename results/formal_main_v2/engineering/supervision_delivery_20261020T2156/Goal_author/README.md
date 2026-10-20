# Goal 被动配对门控：生产 outer 集成候选

这里只交付单次 58 条、29 个配对开发初态的工程候选。没有提交 GPU，没有写 state、Git 或正式 P 入口；旧 Goal 200 与新增科学开发仍 HOLD。

8 个包文件保持固定 SHA，原 observer_v3、ast_observer_v2、prefix58 逐字节沿用。新 entry 保留原 prepare_original、validate_config/authorization/review_ref/prefix 以及原 scientific_runner 调用和 source/action/loading context；dispatch 仅换精确新 token 前缀。配对 gate/AST 来自上轮双审版本，仅将依赖收敛为包内固定文件、更新真实工程标签与输出字段，算法和 AST 投影不变。

真实入口只可从精确 P 路径、已登记 Slurm job、全新 root 授权、不同 root/independent 收据、held ACK 与一槽 reservation 启动。硬编码 allow_cpu_fixture=False 且 sink=None。它不提供 sbatch、retry 或科学结果准入。

输入在 B 首次调用策略前与该初态 A 的原始五组件 dtype/shape/bytes 和指令比较；每次策略前后检查同一输入对象、数组字节与指令。原策略抛出的普通 Exception 仍先按原 run_episode 写 policy_error，formal_trials 在原 ledger 写入后经 BaseException 门控停止，不继续下一条。先前实际执行动作、原 ledger、前后组件、query 返回值和外层错误收据全部保留；不伪造 policy 结果或动作。

CPU 证据分三层：迁移后原 66 断言；真实 P prepare_original/checkpoint/prefix 与 173×3 源闭包；精确生产 execute 函数在显式私有文件根和 synthetic policy/model-loader 下运行实际冻结 loops/native MjData。CPU outer 测试不能代替真实模型加载、GPU、完整 LIBERO 环境或工程终验。原 outer 测试第一次仅因检查 error_type 而非 ledger 的 termination 字段失败，修正只在审核脚本 v2；首轮证据原样保留。

另有实际 MuJoCo 2.3.7 CPU MjData 被动读取验证，allow_cpu_fixture=False、输入/RNG/native fields 不变。wrapper 与图像为合成，没有调用 LIBERO reset/render，没有 GPU；服务器无 OSMesa，未冒称完整 CPU LIBERO 验收。

磁盘按原 256×256×3 双图、58×38 次最大 query、所有前后捕获不计去重，含原始 journal 与额外文本预算，估计上界 3,289,879,290 字节，另留 1 GiB 共需 4,363,621,114 字节。预验时 P 空闲 8,628,740,096 字节；这不是跨进程磁盘预留，root 提交前必须重查。没有改变 P 输出路径或压低记录门槛。

3053440 的动作历史在27/30/33/46/57/58与旧200不同；旧第57条只留下 postquery hash，不能据此定位原因。新工程是同身份前缀的新诊断，不是精确历史重放；即使全部通过，也不采纳旧200、不自动开放科学开发、测速或最终。
