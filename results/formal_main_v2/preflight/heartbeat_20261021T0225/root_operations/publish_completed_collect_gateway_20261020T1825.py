from pathlib import Path
import fcntl,hashlib,json,os
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0225'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,raw):
 assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw;return
 with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
m=R/'.local/completed_training_gateway_20261020T1825/publication_manifest_v2.json';assert h(m)=='7f814ac48cb9a252463385204f8e08e33c4c8eed9bc41c004879cc6796e01130';mapping=json.loads(m.read_bytes());review=R/'.local/completed_training_gateway_independent_20261020T1825/attempt02/code_review.json';assert h(review)=='0cfcb9d8da5712c4e4561243043d5cd251a635091dbb7e35a63ea29482d3a1e3';v=json.loads(review.read_bytes());assert v['status']=='passed_CPU_review' and not v['blockers']
with (R/'results/experiment_supervisor/.writer.lock').open('a+b') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);state=R/'results/experiment_supervisor/state.json';before=h(state);s=json.loads(state.read_bytes());assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0
 for row in mapping['files']:
  p=R/row['source'];assert h(p)==row['sha256']==v['files'][row['destination']] and p.stat().st_size==row['bytes']
  for root in [R,P]:put(root/row['destination'],p.read_bytes());assert h(root/row['destination'])==row['sha256']
 assert h(R/'scripts/ops/formal_action_deployment_v1/gateway.py')=='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a'
 d=R/'docs/正式训练后采集执行登记.md';put(d,('# 训练完成后的固定测速观测采集\n\n2026-10-21登记：72组已完成5000步并经root＋独立验收。原CPU控制器3034538正常退出且lease已释放，不重启。旧gateway仅允许控制器RUNNING；新增独立版本只为本次Spatial/Object两个确切collect计划增加COMPLETED0:0准入。原RUNNING分支、pending/ACK/CAS、一次提交、原8槽全GPU容量与重复保护保持；工程与采集可并行。\n\n各套件从原100个开发初态中按任务选source_state_index最小者，共10条Dense轨迹，seed17/环境seed0，等待10步、chunk8、Spatial最多220/Object280控制步。每条固定取first/floor((N-1)/2)/last原始观测，共30个；不足3个合法观测即失败，不按成功率换轨迹或补填。仅固定测速输入，新增成功率trial=0；采集成本单列并加入全部GPU成本。\n\n本次不做完整O2A、分项计时、global freeze或final；它们仍等全部部署身份和开发收据齐全后按原门槛执行。新gateway严格绑定两个effective plan文件及内容SHA，不给其它任务或更换面板授权。每次申请1张L40，连同Goal工程等所有登记GPU不超过8。失败或不确定ACK停该请求，不自动重试。所有历史异常保留。\n\n证据见[源与CPU审计发布](../results/formal_main_v2/preflight/heartbeat_20261021T0225/completed_training_collect_gateway_publication.json)、[固定输入](../results/formal_main_v2/preflight/heartbeat_20261021T0225/Spatial_Object_collect_input_publication.json)、[静态计划](../results/formal_main_v2/preflight/heartbeat_20261021T0225/Spatial_Object_collect_plan_publication.json)。\n').encode())
 assert h(state)==before
 out=B/'completed_training_collect_gateway_publication.json';value={'schema':'formal_main_v2','status':'exact_source_published_after_root_and_independent_CPU_review','files':mapping['files'],'independent_review':{'path':str(review.relative_to(R)),'sha256':h(review)},'root_review':'Source diff limited to explicit normal-completion collect gate and version; corrected over-strict no-active-GPU predicate before admission. Original transactional gates and runtime scientific closure unchanged.','new_GPU_jobs':0,'state_unchanged':True,'state_sha256':before,'final_release':False,'utc':datetime.now(timezone.utc).isoformat()};put(out,(json.dumps(value,sort_keys=True,indent=2)+'\n').encode());print(json.dumps({'path':str(out.relative_to(R)),'sha256':h(out)}))
