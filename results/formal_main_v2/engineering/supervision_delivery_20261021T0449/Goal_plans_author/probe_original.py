from pathlib import Path
import importlib.util,sys,json,hashlib,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_remaining5_plans_20261021T0449'
sys.dont_write_bytecode=True
sys.path.insert(0,str(R/'src'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(rel,v):
 p=D/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
def load(rel,pin):
 p=R/rel;assert sha(p)==pin
 s=importlib.util.spec_from_file_location('original_manifest',p);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
h=load('scripts/formal_execution_manifests.py','614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89')
state=(R/'results/experiment_supervisor/state.json').read_bytes();save('probe_state_snapshot.json',json.loads(state))
results=[]
for budget,seed in [(256,23),(256,41),(64,17),(64,23),(64,41)]:
 key=f'libero_goal_k{budget}_seed{seed}'
 e=h.Evidence(R)
 try:
  src=h.source_contract(e,h.SOURCE_INVENTORY);reg=h.registration_contract(e,h.REGISTRATION)
  rows=h.suite_rows(e,reg,'libero_goal',src,[f'A{budget}_seed{seed}',f'B{budget}_seed{seed}'])
  manifest=h.make_execution(reg,'libero_goal',rows,split='development')
  spec=reg['suites']['libero_goal'];panel=spec['initial_states_root']+'/development.json'
  manifest.update(development_panel=panel,development_panel_sha256=e.watch(panel))
  e.unchanged();save('original_probe/'+key+'/execution_manifest.json',manifest);save('original_probe/'+key+'/source_provenance.json',e.source_provenance['libero_goal'])
  results.append(dict(pair_key=key,status='passed_original_manifest_builder',files=e.files))
 except Exception as ex:
  results.append(dict(pair_key=key,status='blocked_original_guard',error_type=type(ex).__name__,error=str(ex),traceback=traceback.format_exc(),files=e.files))
  print(key,type(ex).__name__,str(ex),flush=True)
 save('original_probe/'+key+'/result.json',results[-1])
save('probe_results.json',dict(schema='formal_main_v2',kind='Goal_remaining5_original_builder_probe',state_source_sha256=hashlib.sha256(state).hexdigest(),results=results,new_trials=0,new_jobs=0,production_admitted=False))
print(json.dumps([{k:r[k] for k in ('pair_key','status')} for r in results]))