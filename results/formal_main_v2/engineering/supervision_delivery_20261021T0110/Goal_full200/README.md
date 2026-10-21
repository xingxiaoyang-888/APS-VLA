# Goal full200 前瞻执行候选（仅服务器）

本包是作者候选，不是 root GPU 授权或已通过的实际生产终态。固定设计来自 06911f2ba90ffa9e7df233e0793c0989e0d15edf260b18a2fa2fb963ef0912d7，规格原字节 ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad。存储选择来自 7542920320810275798d8fa7ebf2cd85d7b8b4f60ead315638a261b6ecef44de。

旧 Goal 200 全批继续 HOLD；新尝试不能解释旧差异的原因，不能把未复现当修复，也不是两次旧58的精确重放。训练/checkpoint/初态/方法/动作/预处理/随机规则不变。实际结果须新 full200 原始 consumer、独立终审及 root 单独采用，当前科学结果增量为0。

## 路径与接口

生产候选目录 scripts/ops/formal_goal_full200_gate_v1，version goal-full200-prospective-single-attempt-v1。install_files.json 给出11个文件的精确源/目标/sha256/bytes（10闭包成员+package_manifest）。

STAGE=goal_full200_20261021T0110；BASE=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/results/formal_main_v2/engineering/STAGE；OUTPUT=BASE/attempt01；原runner输出=OUTPUT/original_run。P保留 outer、observer 事件及本地 sim/RNG blob。只有5个原始开发观测组件写入唯一绝对 RAW=/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/results/formal_main_v2/raw_runtime/goal_full200_20261021T0110/attempt01，不使用symlink，不写别的raw根。

entry.prepare_original() 完整执行原 action wrapper.verify，原科学invocation c07489c5e56cc3255b60f5eb6df34146e37e4b60fa7151cc97f8008f402b8803；验证原两checkpoint、原60s watchdog与开发模式。validate_prefix 按原 formal_trials._identity 重建全部200顺序和100状态。仅 a.output 与 a.stop_after=200改变，其余原运行参数逐字段保持；原入口、173源及已有科学状态不写。

发布后实际P验证命令：

    PY -B P/scripts/ops/formal_goal_full200_gate_v1/entry.py --verify --package-manifest-sha256 <精确package_manifest_SHA>

该命令只核源/元数据/容量，不申请GPU、不创建RAW/OUTPUT。私有目录的entry拒绝冒充已发布入口。

执行命令只由新 held Slurm 作业调用：

    PY -B P/scripts/ops/formal_goal_full200_gate_v1/entry.py --authorization BASE/root_authorization.json --authorization-sha256 <SHA>

run.slurm 使用 CTI_GOAL_FULL200_AUTH_SHA256，cti-goal-full200，1 L40 /7CPU/64G/7200秒/no-requeue/exclude gpu4020。不自动重试。新 token 为 cti-goal-full200-v1:<authorization SHA>。本包没有原生 sbatch/状态提交API；root 的独立审计薄封装负责共享writer-lock/CAS、所有模式8槽和同pair唯一活动作业、held submit、精确原ACK/pending对账、登记后release。禁止复用旧58授权或不确定重发。

validate_authorization、validate_dispatch、check_review 给出严格新schema；root/independent readiness 必须绑定当前完整10文件闭包与配置，角色和精确路径不同。root_admission不能仅从测试布尔自产生。原CPU控制器终态、旧3053440/3054127关闭与全成本由root实际证据核查。新native thin wrapper不在本包内，其独审是后续门槛。

## 科学循环与被动门控

AST只在原已接受的 action-v1 runtime/scoped trial函数中插入观察调用；去掉观察后原AST、调用顺序、policy计时语句完全一致。原已审动作幅度分支处理继承，不添加动作裁剪/排序/预处理，不改变方法顺序。GateAbort继承BaseException，因此原run_episode普通Exception分支不能吞掉完整性异常而继续下一trial。

每个query前后复制5组件并记录dtype/shape/strides/bytes/hash、指令UTF8字节、mapping/array id和pointer。post检查必须与pre相同，首个B query之前还核同状态A的5组件与指令完全相同。每个原返回动作chunk和每个已执行动作都有无修改原字节记录。全局RNG、环境直接RNG与可被动读取的MuJoCo现有字段在观察前后比较；不调用step/render/reset/get_observation等额外环境方法。对无法直接读取的隐藏状态仍明确missing；不能据此宣称证明所有隐藏模拟器状态。

普通完整horizon失败保持原status=completed、success=False，不据结果挑选。policy_error、环境/cleanup错误、输入变异、不可写、容量/次数/字节超界保留已有前缀后停。原policy普通异常先由原函数保存真实policy_error，然后外层gate停止；不伪造terminal或动作。验证、复制和I/O会扰动墙钟，本尝试不是O2A测速。

200×300=60000只统计原策略控制步；原warmup10×200=2000独立计数，不占60000、不删改warmup。原chunk8、控制步0..299给每条query步0,8,...296，共38，故总7600。reset/set-init观测不算控制步。每trial capture上限推导为4个trial/reseed/factory marker+4 reset/set-init marker+20 warmup前后+76 query前后=104；200条20800，加加载/完成/异常余量，硬界21032。gate事件最大200配对+7600query+60000动作+open/finish，硬界68032。还有每条trial_end及异常记录，其存储在余量内。

## 容量与所有原始值

实际固定schema：双256×256×3 uint8，加float64 pos3/quat4/grip2，共393288B/capture。不依赖去重节省，RAW payload上界8271633216B，另1GiB余量，readiness需9345375040B。P capture各RNG最多65536B、sim聚合8192B、事件最多16384B；gate每事件16384B；其他固定原ledger、outer、报告预留1GiB；再1GiB余量，总需5157355520B。保留原blob，无截断、降采样或丢失败。

写入本身逐类字节/次数硬限，超限fail closed；原chunk metadata额外限制32768B防原ledger无界增长，正常metadata不变。文件系统块碎片及trial_end/abort小记录使用余量，不把statvfs当无限quota承诺。登录节点readiness已真实只读通过，但实际计算节点仍要核路径、ownership、无symlink、write/execute权限、statvfs余量，然后以exclusive mkdir和claim.json一次认领RAW。磁盘/配额在运行中改变时写失败即停，不删历史或退化记录。实际compute-node可写和真实GPU门控本轮尚未证明。

所有CPU原始目录均封入 archives/*.tar.gz 和对应 members.json，包含每条原始测试输出/断言/失败/合成blob的SHA/bytes。它们不是模型权重；不把松散.bin加入普通Git。真实RAW将来只按root精确allowlist分卷归档。私人原件仍在，不删除。

## Typed终验与原consumer

entry实际写 outer/completion.json 和 outer/typed_parent.json，后者绑定真实completion SHA及原adapter归档，绝不把新parent称为旧wrapper。旧完整original adapters仅在私有函数命名空间把一个parent读取位置显式改为新typed_parent，其他guard保留；runtime_inputs、完整rollout、真实action-v1 trajectory与summarize全部原函数。固定新output是显式scientific view，没有伪造旧invocation/ledger。

consumer.review_terminal(R, reference) 仅接受已发布canonical consumer与新 goal_full200_typed_terminal_manifest：执行version、实际终态COMPLETED0:0单GPU job、原ACK/授权/预约/双readiness、精确P→R非权重artifact清单、全部metadata/source、原runner200记录、所有query/动作/blob/100pair前后记录必须匹配。检查原5000选模身份不变。全原consumer须scientific_complete、200/200、唯一job marker、零unknown-cost；独立重建raw门控，不凭成功率取舍。consume(R,ref)从原材料再重建已保存typedreview，不能拿CPU收据替换。

终态manifest的authorization/dispatch/reservation/terminal引用均为R下相对路径+SHA；payload中原P绝对身份保持。artifacts列表为新OUTPUT所有精确非权重相对路径/sha256/bytes（含observer本地content-addressed .bin/.rng.json；它们有专门typed guard，不走通用权重文件放行）。原始5组件仍在已批准RAW绝对路径，按claim、每项SHA/bytes与唯一attempt核验并在收尾重新hash。权重/封存值不复制不读。

CPU原始consumer测试有明确局限：新200原始门控算法用原循环生成的合成CPU轨迹；内存中只把生产标签/双图尺寸guard改为必须匹配CPU标签和3×4×3，再保留其余完整重建，原生产函数明确拒绝该fixture。真实原58的runtime_inputs、全adapters与完整rollout已重建为58/200 incomplete；CPU parent/elapsed envelope明确不是Slurm记账。不声称本轮存在真实新200 terminal。

## CPU证据、失败与继续条件

最终原循环cpu_full200_v3.py：86检查；200/100配对、600query/3400控制步与原调用/动作/ledger/RNG逐项一致；另执行完整horizon pair 76query/600控制+20wait，负结果保留。拒绝预B错配/原地或identity变更/普通policy错误后继续/写盘/超界/symlink。
cpu_outer_v3.py：872检查、275拒绝、7正例，包含实际原wrapper/full200身份/容量与R、R镜像、S各173原字节。
cpu_consumer_v2.py：22检查、15拒绝；合成200门控全部原始重建、真实58的原完整consumer不预记完成。
这些是作者测试，不是独立审计。

保留cpu_outer_v1在P工作树误作S的失败；v2/v3改为存储登记的R、R/snapshots、P/snapshots，不改源。保留cpu_consumer_v1漏传trajectory identity的失败；v2按原函数签名修正并保留完整原58 incomplete结论。旧设计包计数勘误/9项漏检原件由根既有归档保留，本包不重写旧证据。

继续必须依次：独立候选审计→root canonical R/P逐字节安装→实际P --verify与完整闭包核验→新的root/independent readiness与native单次held/ACK/CAS封装验收→root明确单次授权→真正一次新200→原consumer+独立终审→root新结果采用。任一异常HOLD；本作者无state/Git/canonical/P/Slurm修改或GPU提交权限，本轮没有新GPU或科学结果。最终封存初态仍保持关闭。
