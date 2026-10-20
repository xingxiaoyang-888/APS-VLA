from pathlib import Path
import hashlib,json,importlib.util,sys,os
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0225'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,v):
 assert not p.is_symlink();p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode());f.flush();os.fsync(f.fileno())
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';spec=importlib.util.spec_from_file_location('prefix58regctl',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read(sp);f=s['formal_main_progress'];assert s['pending_submission'] is None and not f['test_opened'] and f['completed_final_trials']==0
 auth='results/formal_main_v2/engineering/goal_prefix58_20261020T1825/root_authorization.json';assert h(R/auth)=='195e064794973fbc533dfc6c51afd7ec3fbb942734753c1d7f1a7b9c81687a75'
 d=R/'docs/正式Goal前58条工程诊断.md';assert d.relative_to(R).as_posix() not in read(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json')['files'] and not d.exists()
 d.write_text('# Goal 原前58条工程诊断登记\n\n2026-10-21：原 Goal256 seed17 作业3049679虽 Slurm 正常结束，但200条开发因配对初始观测不一致未接纳。短探针3050711未复现，原因未定；原200条与新增 Goal 科学开发继续 HOLD。\n\n本次只重走原清单前58条、29个开发初态，使用相同A/B checkpoint、原模型加载顺序、环境seed0、runtime seed17、等待10步、chunk8、最多300控制步。动作重新由策略计算，不强制回放历史动作。被动记录reset、set-init、等待和首次策略查询附近的观测、模拟器/RNG身份，检查原动作与观测是否一致；不能仅凭token相同认定输入相同。\n\n观察器AST钩子完整白名单、首个采样异常处理、落盘后模拟器/RNG复核均已修复并经独立CPU审计；root已在实际R/P路径复核原wrapper、选中checkpoint字节及固定58身份。CPU验证不作为真实GPU通过。冻结173源文件保持原字节。\n\n仅允许1次、1张L40、7CPU、64GiB、30分钟，计入8槽上限；不自动重试。先持共享writer锁登记pending与容量，再held提交，按真实token/作业ID/入口/资源核对并登记后才release。未知ACK保留pending，不重发。原训练72组已完成，不重启CPU训练控制器。\n\n完整Slurm分配、加载、异常和观察器I/O计入成本；观察器有额外开销，不提供正式延迟数据。结果新增科学trial为0，不解除任何Goal或最终评测HOLD。返回58条也不代表已解释原异常；真实产物须另行root和独审。\n\n配置与授权见[工程登记](../results/formal_main_v2/engineering/goal_prefix58_20261020T1825/root_authorization.json)，源码发布见[发布收据](../results/formal_main_v2/preflight/heartbeat_20261021T0225/Goal_prefix58_publication.json)。\n',encoding='utf-8')
 f['Goal_prefix58_engineering_registration']={'status':'registered_single_attempt_CPU_passed_pending_GPU_dispatch','authorization':{'path':auth,'sha256':h(R/auth)},'document':{'path':str(d.relative_to(R)),'sha256':h(d)},'scientific_release':False,'original200_HOLD':True,'new_Goal_science_HOLD':True,'maximum_attempts':1,'maximum_wall_seconds':1800,'GPU_jobs_submitted':0}
 c.atomic_json(sp,s,before);out=B/'Goal_prefix58_registration.json';put(out,{'schema':'formal_main_v2','status':'preregistered','state_before_sha256':before,'state_after_sha256':h(sp),'registration':f['Goal_prefix58_engineering_registration'],'utc':datetime.now(timezone.utc).isoformat()});print(json.dumps({'path':str(out.relative_to(R)),'sha256':h(out)}))
