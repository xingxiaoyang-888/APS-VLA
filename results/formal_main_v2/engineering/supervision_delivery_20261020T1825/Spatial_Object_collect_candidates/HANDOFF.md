# Spatial/Object 固定观测采集 CPU 候选

两套候选均通过原冻结 planner、实际 P wrapper.verify、新进程原 prepare-only 和原 11 项负向检查。每套只采 Dense10条固定开发轨迹的首/中/后共30观测，Spatial220、Object280、等待10、chunk8；没有真实 GPU 采集或新增成功率样本。所有计划、diff、原检查和状态快照原样保留。

原控制器3034538已正常退出，旧gateway要求RUNNING，故旧draft授权不可实际提交。root另行准备仅绑定这两份exact effective计划的阶段兼容分支；仍需独立计划审计、root最终readiness及真实容量检查。Goal全套HOLD、Long已完成的30观测、全局冻结后的完整/组件测速、final封存均不改变。

compact_handoff.json提供精确计划路径、SHA及publication map。delivery_manifest.json覆盖本目录所有文件；各CPU执行的闭合transport也单独绑定。候选作者未做自我独审，未改canonical/state/Git/Slurm。
