# Goal 有界 CPU 诊断：可证明边界与固定后续方案

本包仅为服务器上的作者 CPU 分析与方案，等待另一代理独审。没有 Slurm 查询或提交、模型推理、环境步进、权重读取、state/Git/P 写入或科学结果接纳。旧 200 条与新增 Goal 科学闭环继续 HOLD；本包增加 0 GPU 秒、0 科学试验。3054127 的既有 840 GPU 秒不在此重复记账。

实际证据把 ordinal30（task1/source12/B256_seed17）限定为两次 58 条工程中唯一日志轨迹差异。前 72 条给 env.step 的数值命令相同，包括 canonical JSON 的符号零表示；前 9 个 chunk 的 post-policy 五分量观测 hash、动作与 metadata 相同。最后一个相同 post-policy 采样在 query8/step64，首次不同 post-policy 采样在 query9/step72。该区间是观测日志区间，不是已证明的隐藏模拟器分歧起点。

关键更正：冻结 run_episode 在 predict_chunk 返回之后才计算 ledger 的 observation_sha256。旧 3053440 仅 t0 有原始 pre/post 观察器数据，因此旧 step64 与 step72 的入策略前字节并未直接保存。新 3054127 全部 query 的 pre/post 原始字节一致，不能据此追溯证明旧尝试也一致。“旧输入在推理前已不同”与“旧推理期间观测发生改变”仍都与现有日志相容。相同 t0 的已记录 sim/RNG 和相同环境命令，也不证明中间隐藏 state、控制器、渲染器或 RNG 一致。

五分量 hash 覆盖两相机图像、末端位置、四元数、夹爪位置的名称、dtype、shape 和 C 顺序原字节；不包含 instruction、预处理 tensor、模型 activation、sim/RNG 或墙钟。两次 config 原字节相同，记录同 gpu4015、L40、软件与线程配置，原 accepted loop 及 trial code 身份相同。记录频率不同，会增加 I/O 与时间扰动；同节点/机型不证明同物理 GPU 或隐藏状态。

本次重算选定新 11 个 query 的原始输入，验证旧 t0 原件，读取 72 个去重的指定 blob；另从此前完整独审过的归档中只重建 q9 的 5 个真实输入成员。未再次全扫 10741 个 blob。预先固定的 3 个新整帧（q8/q9/q10）与 10 个单分量邻帧替换组合均不匹配旧 q9 posthash。这只能排除这 13 个精确候选，不能由不匹配推断差异通道或机制。

直接缺失的是旧 q9/step72 的五分量 pre/post 原始数组，以及中间 sim/controller/RNG/renderer 的对应观测。无法从整体 SHA 反推出原数组。因而仍不能把差异归因于图像、proprio、物理非确定性、RNG、policy mutation 或观察器时序；也没有证明旧 200 的 t0 问题已修复。旧 200 与两次工程的所有原尝试/成本必须保留。

## 明确下一步

prospective_full200_specification.json 将两个问题分开：旧 200 的历史兼容接纳继续全批 HOLD；未来新运行能否满足固定输入不变性协议可以独立检验，无需假装找回不存在的旧数组。

下一步是由不同代理独审本包，并由 root 明确选择是否采取完整 200 条替代协议。若选择，先实现并审查一个新版本、严格绑定原 100 开发初态 × 原 A/B256_seed17 顺序的全 200 门控入口，再由 root 按原容量/身份/单次 ACK 门槛另行授权一次新尝试。本包只生成方案与 CPU 拒绝测试，不发布入口、不分配新输出路径、不提交作业，不自动重跑 58 工程，也不把这份设计当 GPU 准入。

固定上限为 1 次新尝试、200 条、最多 60000 控制步及 7600 策略 query，均由原 Goal 每条 300 步与 chunk8 推导。所有选模 checkpoint、方法、预算、seed、预处理、控制器、初态、等待步数与 horizon 不变；不强制旧动作、不按旧成功率选择身份。

通过条件：全部 100 对 A/B 在 B 策略首次调用前五分量与 instruction 精确匹配；所有 query 入/出策略的输入身份、shape/dtype/bytes 与 instruction 不变；原 policy/env 调用与全部动作保持原样；200 条完整且真实 source/runtime/raw evidence 与 clean Slurm 终态齐全；原 consumer、不同代理终审和 root 验收均通过。仅届时可把这份新数据计为一次 200 条当前科学开发；正常任务失败必须照计。通过不证明旧原因、不接纳旧 200、不开放最终评测。

失败条件：初态不等在 B 推理前停；query 输入改变在下一 env action 前停；缺 blob/身份/源、损坏数据、异常、未知 ACK 或异常 Slurm 状态均 HOLD。保留部分结果和完整成本，不自动重试，不用普通 resume 跳过旧 terminal 行，不将通过的部分按结果挑选接纳。如固定协议下不能完成，Goal 继续阻塞，不修改科学设置来过关。

## 复核方式与范围

analyze.py 是固定源 SHA、有限输入与 13 候选的纯 CPU 分析；其 1235 项作者检查含原始 bytes、source 时序与 14 个逻辑分类器用例。build_prospective_specification.py 从原 panel、原 method identities 和注册环境生成完整 200 身份表，另有 1 个设计正例和 20 个拒绝例。合成用例只验证判定规则，不是 GPU 或科学证据。

两次脚本均已通过精确 SHA 的 server_control_transport_v1，完整 journal 已复制到本目录。脚本输出采用拒绝覆写语义；独审应在自己的独立目录复建，不能重跑覆盖本包。所有读入文件都带 SHA；只读 probe 的 schema/路径错误及输出截断另存 bootstrap_failures.json，不冒称试验失败。独审结果须由另一代理另行产生。
