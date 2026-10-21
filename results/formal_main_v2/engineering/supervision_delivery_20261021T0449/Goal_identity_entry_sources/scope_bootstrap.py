from pathlib import Path
import json,hashlib,os,math,datetime
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=R/'.local/goal_remaining5_independent_20261021T0449'
checks=[]
def require(value,label):
 checks.append({'check':label,'passed':bool(value)})
 if not value:raise AssertionError(label)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def ref(p):
 p=Path(p);return {'path':str(p.relative_to(R)) if p.is_relative_to(R) else str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def readref(d):
 p=Path(d['path']);p=p if p.is_absolute() else R/p
 require(sha(p)==d['sha256'],'reference SHA '+str(p))
 if 'bytes' in d:require(p.stat().st_size==d['bytes'],'reference size '+str(p))
 return json.loads(p.read_bytes())
def dump(name,v):
 with (D/name).open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
DP=R/'.local/goal_remaining5_design_20261021T0334/design.json'
require(sha(DP)=='5c813e3a6e9429cc46ed9ab52a5543d0cf6302c5e5c1819efd11a501a2fb4e8e','original five-pair design pin')
d=json.loads(DP.read_bytes());targets=[('libero_goal_k256_seed23',256,23),('libero_goal_k256_seed41',256,41),('libero_goal_k64_seed17',64,17),('libero_goal_k64_seed23',64,23),('libero_goal_k64_seed41',64,41)]
require([(x['pair_key'],x['budget'],x['seed']) for x in d['remaining_pairs']]==targets,'five exact pairs only')
invp=R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';require(sha(invp)=='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926','source inventory pin');inv=json.loads(invp.read_bytes());require(len(inv['files'])==173,'173 fixed sources')
for base in (R,S):
 for rel,pin in inv['files'].items():require(sha(base/rel)==pin,'source '+str(base)+'/'+rel)
pairs=[]
for x in d['remaining_pairs']:
 cfg=readref(x['planned_scientific_matrix_source']);summary=readref(x['training_summary']);require(summary['status']=='completed' and summary['pair_complete'] is True,'training pair completed '+x['pair_key'])
 for k,r in x['training_terminal_evidence'].items():readref(r)
 armrows=[]
 for a in x['arms']:
  dep=readref(a['deployment_receipt']);md=dep['metadata'];es=dep['evaluations']
  require(dep['completed_updates']==dep['planned_updates']==5000 and dep['training_complete'] is True,'5000 completed '+a['method_id'])
  require(dep['pair_config']==cfg,'registered pair config '+a['method_id'])
  require([e['update'] for e in es]==list(range(0,5001,500)),'all eleven validation nodes '+a['method_id'])
  require(all(type(e['validation_metric']) in (int,float) and math.isfinite(e['validation_metric']) and e['validation_metric']>=0 for e in es),'finite original selection metrics '+a['method_id'])
  chosen=min(es,key=lambda e:(e['validation_metric'],e['update']))
  require(chosen['update']==md['update']==a['selected_update'],'earlier-tie task macro best selection '+a['method_id'])
  require(chosen['candidate_sha256']==dep['checkpoint_sha256']==a['checkpoint']['sha256'],'selected candidate equals best file '+a['method_id'])
  cp=Path(a['checkpoint']['path']);st=cp.stat();require(st.st_size==a['checkpoint']['bytes'] and sha(cp)==a['checkpoint']['sha256'] and st==cp.stat(),'actual immutable checkpoint bytes '+a['method_id'])
  require(md['seed']==x['seed'] and md['visual_tokens']==x['budget'] and md['pair_id']==x['pair_id'] and md['arm']==a['arm'],'per-pair arm identity '+a['method_id'])
  require(md['selection_metric']=='task_macro_hard_validation_teacher_l1' and md['selection_protocol_sha256']=='893e208ba12f74cb5759f914425d40497c5f62a94d3a4b3346f9eaf0b438fbd3','selection rule unchanged '+a['method_id'])
  require(md['training_source_sha256']=='36b4654ba1479a040c5415258f5e043abfff41fc4ed4200f81dd5bc4638d7662','original training source '+a['method_id'])
  for rel,pin in md['training_source_files'].items():require(sha(S/rel)==pin,'training source closure '+a['method_id']+' '+rel)
  armrows.append({'method_id':a['method_id'],'checkpoint':a['checkpoint'],'selected_update':chosen['update'],'selected_validation_metric':chosen['validation_metric'],'validation_nodes':11,'deployment_receipt':a['deployment_receipt'],'training_seed':md['seed']})
 pairs.append({'pair_key':x['pair_key'],'pair_id':x['pair_id'],'budget':x['budget'],'training_seed':x['seed'],'runtime_seed':17,'environment_seed':0,'wait_steps':10,'chunk':8,'horizon':300,'trials':200,'unique_states':100,'arms':armrows})
state=R/'results/experiment_supervisor/state.json';state_ref=ref(state);st=json.loads(state.read_bytes());latest=st['last_root_supervision_snapshot'];summary=readref(latest)
capacity={}
for label,p in [('R',R),('P',P)]:
 s=os.statvfs(p);capacity[label]={'path':str(p),'free_bytes':s.f_bavail*s.f_frsize,'st_dev':p.stat().st_dev,'quota_checked':False}
report={'schema':'formal_main_v2','kind':'goal_remaining5_independent_scope_and_identity_baseline','status':'passed_readonly_identity_baseline_production_HOLD','reviewed_by':'independent','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'five existing Goal pairs; source/config/checkpoint/selection identity only; no scientific execution','design':ref(DP),'state_snapshot':state_ref,'last_root_snapshot':latest,'source173_inventory':ref(invp),'source173_R_S_verified':True,'pairs':pairs,'capacity_snapshot':capacity,'production_admitted':False,'GPU_execution_authorized':False,'new_trials':0,'sealed_final_values_read':False,'original_Goal200_HOLD':True,'checks':checks,'check_count':len(checks),'remaining_gates':['Frozen exact original five manifests and planner-produced invocations with real independent/root readiness','New runtime and exact dual-root passive/raw mapping independent source and CPU review','New five-instance dispatcher isolated scopes and aggregate storage/8GPU/per-pair admission','Root exact R/P publication and actual-P metadata/source verification','Root unique held ACK/CAS/release per pair, no automatic re-submit','New actual raw terminal review before any scientific acceptance']}
dump('identity_baseline.json',report);print(json.dumps({'status':report['status'],'check_count':len(checks),'report':ref(D/'identity_baseline.json'),'capacity':capacity},sort_keys=True))
