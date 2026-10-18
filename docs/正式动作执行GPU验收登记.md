# 正式动作执行 GPU 验收登记

2026-10-19 00:57：v3八份GPU候选源码及固定16格面板已按原审核字节发布，服务器控制入口通过14项作者、16项独立CPU检查，root重核533条输入；实际服务器check-only返回0，173个冻结源未变。新登记仅允许一次有界GPU尝试，当前8槽均用于健康训练，尚未提交v3 GPU作业。CPU通过不等于GPU验收；新增科学闭环、旧结果复用与最终release仍暂停。[v3配置](../configs/experiments/formal_main_v2_action_execution_compat_gpu_v3.json)；[实际check-only](../results/formal_main_v2/preflight/action_execution_gpu_v3_server_check_only_v1.json)；[服务器入口根复核](../results/formal_main_v2/preflight/heartbeat_20261019T0037/v3_server_entry_root_acceptance.json)。

2026-10-18：v2作业3030159在构造身份检查处失败（85 GPU秒，0/16工程格），原结果保留。差异来自Python3.11整模块与截取class的编译上下文。最小候选在本地3.10/3.12及服务器3.11分别通过14/16/16项CPU检查，并经独审；尚未集成或通过GPU验收。新的16格版本正在准备，新增科学闭环仍暂停，训练并行继续。


本轮只验收统一动作执行修正。训练方法、checkpoint 选择、任务面板和173个冻结源码文件保持原身份。CPU完整回归53项、独立检查26项通过；真实GPU及控制器验收尚未完成，新增正式开发闭环和历史结果复用仍须等待验收。

范围固定为 Long → Spatial → Object → Goal。每套件使用自己的官方基座和已完成5000步的128-token seed17选择器，依次检查 Dense、uniform128、A128、B128，共16格；没有成功率比较或测速。每格独立重置同一开发初态，runtime seed17、env seed0，等待10步，预测一次8步动作chunk，最多执行8个控制动作。提前终止时保留未执行尾部，不继续生成动作。

| 套件 | 已有开发任务编号 | 该任务最小开发初态编号 | A/B所选更新 |
|---|---:|---:|---|
| Long | 0 | 0 | 4500 / 5000 |
| Spatial | 0 | 3 | 4000 / 5000 |
| Object | 0 | 5 | 2500 / 4500 |
| Goal | 0 | 7 | 2000 / 4500 |

任务名、初态行哈希、基座版本、checkpoint哈希及来源收据在候选清单中固定。仅使用已公开的开发面板，不读取官方全50初态文件或封存集。检查实际控制器类型、`use_delta`、输入输出限值及绑定的`scale_action`、`set_goal`源码；环境收到的动作必须与原`PolicyChunk`队列逐字节一致，不增加clip或重标定。记录实际一次视觉编码、packing、VLA和动作头；A/B另有一次DIE和Top-k，未来头不部署。

Object使用已验收的元数据适配，Goal同时使用其组件适配。所有适配层必须记录完整退出和恢复证据。任何身份、调用次数、动作、有限值、环境或来源检查失败，整次工程尝试立即停止；保留失败和已消耗GPU时间，不自动重试，不计算论文成功率或延迟。

提交上限为一个L40、3600秒、一次尝试，计入最多8个活动GPU请求。root在提交前核验登记作业、现有产物与全部输入哈希；固定输出根目录，运行时由Slurm job ID生成唯一子目录。配置及源码不在提交后改写。原Object失败trial不随本工程验收自动重跑。

验收产物必须回存原始事件、动作、控制器证据、模型调用计数、退出状态和全部Slurm成本，并经root与独立审计。通过后仍需逐条历史动作等价审计，才能声明原正常trial可复用。原1212条开发记录及其中1条policy_error保留。最终评测仍需72选择器、16参考、四套件开发及全局release，当前未开放。

提交前发现的日志重复字段和未知Slurm job ID输出登记问题均已修正，旧版源码与CPU复现保留；这些是工程问题，未产生GPU试验结果。

root已登记[单次GPU配置](../configs/experiments/formal_main_v2_action_execution_compat_gpu_v1.json)，[CPU验收](../results/formal_main_v2/preflight/action_execution_gpu_candidate_root_0626.json)及实际293项本地提交依赖检查通过。2026-10-18 15:40的容量核对确认8个训练请求占满，因此未提交第9个请求；待首个空闲槽按同一登记提交，见[就绪记录](../results/formal_main_v2/preflight/action_execution_gpu_ready_0626.json)。提交器另经作者32项、独立22项CPU检查；服务器发布和真实GPU结果尚未取得。


2026-10-18 16时更新：v1首次提交在传输清单前触发Windows命令长度限制，无上传、pending或GPU作业；实际服务器缺省路径复核已留证。v2改用stdin传输并使用独立工程命名空间，CPU作者与独立检查通过；新typed CPU登记链及真实GPU验收仍待完成。原v1与全部科学配置保留，训练继续。
