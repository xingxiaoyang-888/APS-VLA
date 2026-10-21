# Goal 剩余五 pair：CPU 证据矩阵与下一轮最小集成门槛

这是设计和身份核对，不是提交授权。已冻结归档包和已有 runtime/dispatch 均未修改。

状态快照 SHA：bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa。已验收 Goal128 三 seed 共 1,000 条，其中 A/B 为 600、四参考为 400。3054717 新256seed17 200条虽已有已保存 COMPLETED 0:0 / 2205 GPU秒，仍由 root 与独审另行准入；旧3049679 200条不转为已接纳。

|剩余 pair|A选中更新|B选中更新|原开发提交|待执行数|
|---|---:|---:|---|---:|
|Goal 256 / seed23|4500|4500|登记与 R/P 精确发布目录均未发现|200|
|Goal 256 / seed41|3000|4500|登记与 R/P 精确发布目录均未发现|200|
|Goal 64 / seed17|4500|2000|登记与 R/P 精确发布目录均未发现|200|
|Goal 64 / seed23|4000|4500|登记与 R/P 精确发布目录均未发现|200|
|Goal 64 / seed41|3500|3000|登记与 R/P 精确发布目录均未发现|200|

五 pair 的冻结 pair config、5000训练双终验、部署收据、全部11验证节点与原最早平分选模均核对；10份 best.pt 在服务器流式复算 SHA，与原 root/独审登记及 receipt 一致，不复制权重。R/S 的173份冻结源逐字节通过。完整开发100初态的原文件、顺序、10任务每任务10初态身份一致；不读 final 值。

## 缺少的计划，不补造
第二次CPU检查保留了跨套件同名method_id引起的误拒记录；v3限定suite=libero_goal或完整pair_id后再查重复，不以Object/Spatial的同名A256_seed23冒充Goal提交。
首次检查发现待执行pair的部分 P/configs 路径未发布，原失败保留；v2 对已存在的 P 文件继续逐SHA核对，对缺失项在每pair missing_P_publication_files 明列并保持生产HOLD。R/S 冻结配置和服务器checkpoint身份均独立验证，不能以此替代P发布。
目前 R/P 正式 execution/invocations 下只有 Goal128 三个开发计划及 Goal256seed17 旧计划，其他五 pair 尚没有独立 execution manifest / scientific plan / invocation / ACK。design.json 里的 planned_scientific_matrix_source 指向原冻结训练科学配置，不冒充已发布的下游计划。下一轮应先用原已审 planner、原 deployment identity builder 为每个固定 A/B pair + 同100初态构建各200条明确清单，再冻结其原始字节与执行身份。

## 操作性绑定须新增，原入口保持专用
现 formal_goal_full200_gate_v1 和 dispatch_v1 专属 3054717。entry/config/specification/paired_input_gate/consumer/storage/run.slurm、dispatch scope/prepare admission 各自包含 stage、method IDs、seed、budget、pair_id、原 invocation、checkpoint、raw/output 路径、授权/审计/容量收据和唯一 comment/token 绑定。必须在新受审包逐项绑定五个精确目标，不能运行时替换全局常量或改旧包。原五 pair 没有历史开发 invocation，不能复用 c07489c5... 伪作各 pair 的原调用。
两个 AST 转换器当前无 seed/budget 字符串，仅可在源码/代码对象/回调闭包独审后原字节继承；observer 与 five-component gate 的方法映射、全输入采集和相应限额也须测试新 pair，不能因为函数名相同就继承 GPU 验收结论。原控制循环、动作/clip、预处理、packing、action slice、环境/RNG调用规则及300步/chunk8保持不变。

## 每 pair 最小门槛
1. 根与独立终验先结束3054717原200的准入；为剩余五 pair 明确新受审 scope 和保留所有既往失败/成本，不据结果改 checkpoint、初态、方法或预算。
2. 科学输入：固定本 pair A/B100状态各一次；原开发面板 SHA、官方Goal基座、原 selected checkpoint SHA、F01、训练/数据/来源桥完整核对；没有 source bridge 就 HOLD，不能套别 pair。source173原字节不改。
3. 执行：保留完整原执行 manifest 与原 parser/scientific guard；每 pair 独立 fresh reset / ledger，不普通恢复3054717或58工程。每 pair 最大200 trial、60000控制步、7600 query、一次尝试；新结果不能触发重试。历史动作不注入，异常立即停止并保留。
4. AST/运行期闭包：核 original / derived loop、adapter.run、policy 方法、回调函数与 source code SHA。强制预调用与调用后五组件完整输入、sim/RNG记录及t0跨A/B门控；非t0空数组、缺一组件、错类型/shape、错内容地址、synthetic标志、额外/漏事件一律拒绝。
5. 终态：原 consumer 完整执行模型/config/checkpoint/data/轨迹和ledger核验，再typed observer/gate逐条重建。新增消费者实际接受 mode=development、run_root=<attempt>/original_run 的真实登记；必须做 registration→consumer.validate_job 跨入口CPU测试，不能终验临时修改 job 或信布尔通过。
6. 发布：完整新 source closure、root/独审源码CPU收据、精确 R/P 安装映射、实际P --verify、不可变 readiness 和 root authorization 齐全后才能提交；旧已通过 receipt 只证明其旧范围。
7. 容量：提交与计算节点两次实际检查 R 五组件与 P 元数据/被动blob空间；每pair独占内容地址 claim，无未来去重信用。按5个新attempt的并行 worst-case 预算核全量容量，不能按3054717短轨迹实测放宽每pair上限。
8. 提交：共享 writer.lock + CAS，root pending 与 autonomous pending 双拒绝；控制器生命周期lease、全部模式GPU合计最多8及Goal pair占用校验。新唯一token/output、held sbatch→持久原ACK→精确sacct/comment/name/account/output/原argv核验→同锁登记→唯一release；不确定提交/release只能精确原ACK对账，不能清pending重发。不同pair不共享ACK或授权。
9. 验收与成本：每pair完整原始P→R allowlist、五组件/被动blob内容地址可恢复归档、root+不同agent终验齐后仅新增200。保存每个失败/工程/加载与全部Slurm分配并且只计一次；未完成/失败或缺证据不得记成功率分母。
10. 最终和测速：五pair完成也不自动开放 final 或 O2A。仍需72checkpoint、16参考、四套件开发收据和最终清单全局冻结与root release；本设计不读取封存值、不泛化到其他套件/预算/种子/方法。

精确源、路径、原始SHA、checkpoint SHA、pair_id、已验收收据和缺失项见 design.json。verification_checks.json 只证明此次CPU身份核验。fresh Slurm查询、实际P的新入口验证和任何GPU运行均未执行。
