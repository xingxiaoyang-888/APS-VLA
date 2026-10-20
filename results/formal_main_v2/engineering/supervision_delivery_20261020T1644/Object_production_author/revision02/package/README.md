# Object256 seed23 显式来源控制桥（待发布、待真实路径验收）

仅修复该 pair 的下游来源消费者：3028460 为 84 GPU 秒的真实 CUDA 启动失败，正常 metadata_history 只有恢复 3039258 与连续 3042627。三项分配总计 58917 GPU 秒全部保留；不生成不存在的正常 metadata。仅准入 Object、总256 tokens、seed23、A/B 两方法、固定100开发初态各一次，共200条。训练和科学设置不变，最终集不开放。

本包 control.py 精确加载已独审的 bridge_v2.py / policy_v1.json，以及原 factory、planner、gateway、reviewer、consumer。每次在新的私有模块命名空间显式注入相同 source proof；没有修改 canonical 原模块文件或其全局缓存。gateway 的真实 FrozenPlan.prepare 与 terminal reviewer 的实际重建调用链均使用同一桥。原 Gateway.run、锁、CAS、八卡容量、同 pair 唯一、pending 原 ACK 对账及异常停止保持原代码。原 runtime、动作 wrapper、adapter、轨迹核验与成本消费者不变。

## 修订与验收状态

revision02 是首个拟发布源码版本；package/ 与 attempt01 保留精确缩进替换失败。attempt02 作者 CPU 检查通过 759 项、33 个负例，真实 FrozenPlan 源重建与 terminal science_context 同源重建通过，173 冻结文件在 R/S 前后字节一致。该结果不等于 canonical 发布、root/独立 readiness 或任何 GPU/科学完成。新增 GPU、trial、Slurm 操作均为0。

## root 发布后的必要步骤

1. root 在共享 writer 锁下按 source_publication_manifest.json 将本目录四项逐字节复制到 R/scripts/ops/formal_object256s23_source_bridge_v1/。此步骤仅源码发布，不修改 state、不配置准入、不提交作业。该控制层只在 R 执行；P 端仍用既有动作 wrapper 与原 runtime。
2. 从 canonical control.py 重新读取 closure()/descriptor()。不能沿用 private 路径的 proof、科学/effective plan、CPU fixture 或 readiness；proof 包含精确实际源码位置。
3. 用 fresh root 锁快照和固定 plan_arguments，经 canonical control_modules(evidence)[1].plan 重建科学计划；manifest 仍为已登记 Object256s23 原字节。原 contract.effective_plan 生成正式 envelope。对 R、P 实际文件检查完整来源/metadata，确保对应 selected checkpoint 身份仍原值。root 与独审员分别完成真实 canonical gateway/FrozenPlan 重建、实际 P wrapper readiness 和 terminal consumer 同桥路径审计。
4. 原 gateway authorization 的全部类型、证据、component review、reservation 与容量要求仍须满足。authorization 额外绑定 explicit_source_control=canonical descriptor()；gateway_files 为 canonical closure()。独审 CPU 报告 files 必须覆盖全 closure；root 和 independent runtime readiness 子收据都绑定同一 explicit_source_control。不得用作者 CPU_prepared_shape fixture 或空 runtime_readiness 充当生产授权。
5. root 以固定 transport+入口 SHA 调用 canonical control.py 的 main，传 --control-sha256、--authorization、--authorization-sha256；真正提交还需同时传 --submit --root-reviewed-submit。先原 gateway check-only；原共享锁/CAS/精确 reservation/pending 生命周期维持。private candidate 的 main 始终拒绝生产 gateway 操作。禁止直接调用旧 gateway 代替此显式入口。
6. 作业终态后 root 必须通过 canonical reviewer_module(evidence).review 执行完整原始 receipts / adapters / runtime / rollout / allocation cost 核验。后续消费用 canonical consumer_module(evidence).review_downstream_output，不能只复用 source proof；保存的完整原 action-v1 root review 必须原样重建且带 canonical control closure。此桥不适用于其它 stage/pair、续跑或其它历史失败。

## API（只读计划/核验由 root 调用）

- control_modules(ev) 返回私有 factory/planner，planner.plan 只接受固定 development 参数；factory.main 仅接受明确 Object256s23 A/B development 命令。
- gateway_module() 返回保留原生命周期逻辑的私有 gateway，真实 FrozenPlan 内重新调用显式 planner。
- reviewer_module(ev)、consumer_module(ev) 仅接受完整200条 Object256s23 开发消费，保留原所有原始证据核验。
- closure()/descriptor() 提供实际发布位置与内容 SHA，root/独立验收必须重新生成，不能复制 private 预览身份。

没有新增正常 metadata、改变原失败记录、放行原 Goal200 HOLD 或读取封存值。原 bridge 源码独审不替代本控制层独审；本控制层 CPU 检查不替代尚未完成的 canonical root/独立 readiness。
