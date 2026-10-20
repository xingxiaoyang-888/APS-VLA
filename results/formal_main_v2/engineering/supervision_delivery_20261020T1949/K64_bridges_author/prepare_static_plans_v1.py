import sys,json,hashlib,importlib.util,fcntl,copy,datetime
from pathlib import Path
from types import SimpleNamespace
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=Path(__file__).resolve().parent;sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
PINS={'spatial':'edab3f3917b57daf1867134bc8179a73673bfc4a1e61bfda5118d76fd64458f3','object':'cf1058afd83073e0ef30c977e88c34f124f56adcfe9487b837ecaedaf6578767'}
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(rel,pin):
 p=R/rel;assert h(p)==pin;spec=importlib.util.spec_from_file_location('_k64_static_'+p.parent.name+'_'+p.stem,p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
class E:
 def __init__(self):self.project=self.root=R;self.files={}
 def path(self,p):p=Path(p);return p if p.is_absolute() else R/p
 def watch(self,p):q=self.path(p);x=h(q);k=q.relative_to(R).as_posix();assert k not in self.files or self.files[k]==x;self.files[k]=x;return x
 def read(self,p):self.watch(p);return json.loads(self.path(p).read_text())
 def unchanged(self):
  for k,v in self.files.items():assert h(R/k)==v
rows=[]
for suite,cpin in PINS.items():
 out=D/suite/'static_candidate';out.mkdir(exist_ok=False);base='results/formal_main_v2/execution/'+suite+'64seed23_source_control_v1_20261020T1949';items=[]
 def put(name,value):
  p=out/name;raw=(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode();p.write_bytes(raw);ref={'path':base+'/'+name,'sha256':h(p)};items.append({'source':p.relative_to(R).as_posix(),**ref,'bytes':len(raw),'publish_R':True,'publish_P':name in ('execution_contract.json',)});return ref
 c=load('scripts/ops/formal_'+suite+'64s23_source_bridge_v1/control.py',cpin)
 with (R/'results/experiment_supervisor/.writer.lock').open('rb') as f:
  fcntl.flock(f,fcntl.LOCK_SH);raw=(R/'results/experiment_supervisor/state.json').read_bytes();fcntl.flock(f,fcntl.LOCK_UN)
 state=json.loads(raw);before=copy.deepcopy(state);(out/'state_read_only_snapshot.json').write_bytes(raw)
 args={'stage':'development','source_inventory':'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','execution_manifest':c.MANIFEST,'output_relative':None,'freeze_directory':None,'profile_panel':None,'prior_review':None,'collection_review':None,'repair_record':None,'resume':False,'stop_after':None}
 ev=E();factory,planner=c.control_modules(ev);science=planner.plan(SimpleNamespace(**args),state,project=R);assert state==before;sciref=put('scientific_plan.json',science);argref=put('plan_arguments.json',args)
 ct=load('scripts/ops/formal_action_deployment_v1/contract.py','efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19');rt=load('scripts/ops/formal_action_deployment_v1/runtime_scope.py','6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53')
 runtime=rt.make_contract(project_root=R,source_root=S,suite='libero_'+suite,stage='development');files={p:h(R/p) for p in ct.EXPECTED_NEW_FILES};files[ct.ACTION_ADAPTER]=ct.ACTION_SHA
 action={'schema':ct.SCHEMA,'kind':'formal_action_execution_contract','version':ct.VERSION,'status':'candidate_pending_root_readiness','scientific_settings_changed':False,'final_evaluation_enabled':False,'files':files,'runtime_contract':runtime,'GPU_acceptance':ct.GPU_REFS,'source_inventory':{'path':ct.INVENTORY,'sha256':ct.INVENTORY_SHA},'transition':None};aref=put('execution_contract.json',action)
 effective=ct.effective_plan(science,scientific_plan_ref=sciref,execution_contract_ref=aref,execution_contract=action);eref=put('effective_plan.json',effective);ev.unchanged()
 put('source_provenance.json',science['invocation']['source_provenance']);(out/'read_evidence.json').write_text(json.dumps(ev.files,sort_keys=True,indent=2)+'\n')
 rows.append({'suite':'libero_'+suite,'methods':c.METHODS,'source_control':c.descriptor(),'scientific_plan':sciref,'effective_plan':eref,'plan_sha256':effective['plan_sha256'],'invocation_relative':effective['invocation_relative'],'output_relative':effective['output_relative'],'stage_key':effective['invocation']['stage_key'],'files':items,'state_snapshot':{'path':(out/'state_read_only_snapshot.json').relative_to(R).as_posix(),'sha256':hashlib.sha256(raw).hexdigest()},'completed_development_trials_added':0,'not_an_authorization':True})
p=D/'static_plan_publication_candidate.json';p.write_text(json.dumps({'kind':'k64_seed23_exact_two_development_plans_CPU_candidate','pairs':rows,'all_methods_new_development_no_overlap':True,'not_submitted':True,'runtime_readiness_and_root_authorization_pending':True,'GPU_runs':0,'Slurm_calls':0,'canonical_state_Git_writes':False},sort_keys=True,indent=2)+'\n');print(json.dumps({'path':p.relative_to(R).as_posix(),'sha256':h(p),'pairs':[{k:x[k] for k in ('suite','effective_plan','scientific_plan','plan_sha256','invocation_relative')} for x in rows]}))
