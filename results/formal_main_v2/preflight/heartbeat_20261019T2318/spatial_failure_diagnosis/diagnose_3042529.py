"""Server-only, read-only diagnosis of exact failed Spatial development3042529.
Only writes private diagnostic outputs beside this file. No retry or publication.
The virtual-publication CPU probe redirects one exact missing immutable JSON ref
in memory, labels that counterfactual explicitly, and never changes production.
"""
from pathlib import Path,PurePosixPath
from collections import Counter
from datetime import datetime,timezone
import hashlib,importlib.util,json,subprocess,sys,traceback,os,stat
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/spatial_failure_diagnosis_1518'
BASE='results/formal_main_v2/execution/action_spatial_resume_0943/'
RUN='results/formal_main_v2/libero_spatial/downstream/development/8c843c1d4ee8383c/attempt01'
INV='results/formal_main_v2/invocations/libero_spatial_development_8c843c1d4ee8383c_attempt02.json'
INV_SHA='6984d4dceeac9a88cb424fd986daef31595cae3e107581e9acfc4b7c96468261'
PRIOR='results/formal_main_v2/downstream_reviews/3022743.json'
PRIOR_SHA='9e14b86a1e556c53ef1cbd8c7bdc1733c3d5eb744f62ffee8df9395645816650'
WRAP='scripts/ops/formal_action_deployment_v1/wrapper.py'
WRAP_SHA='d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33'
CONTRACT='scripts/ops/formal_action_deployment_v1/contract.py'
CONTRACT_SHA='efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19'
refs={};observed={}
def need(v,m):
 if not v:raise ValueError(m)
def safe(rel):
 need(isinstance(rel,str) and str(PurePosixPath(rel))==rel and not rel.startswith('/') and '..' not in rel.split('/') and '\\' not in rel,'noncanonical diagnostic input')
 parts=rel.lower().split('/');q=Path(rel)
 need(not any('sealed' in x or x in ('test','weights','checkpoints','final') for x in parts),'protected evidence denied')
 need(q.suffix.lower() not in ('.pt','.ckpt','.bin','.safetensors','.pkl','.pickle','.init','.pruned_init'),'no tensor/state payload')
 if any(x in rel.lower() for x in ('init_state','initial_state','final_state','test_state')):
  need(q.suffix=='.py' or rel in {'configs/manifests/formal_main_v2/'+s+'/initial_states/development.json' for s in ('libero_10','libero_spatial','libero_object','libero_goal')},'no sealed state values')
 return rel
def digest(p):
 need(p.resolve()==p and not p.is_symlink(),'noncanonical file')
 with p.open('rb') as f:
  a=os.fstat(f.fileno());need(stat.S_ISREG(a.st_mode),'not regular')
  h=hashlib.sha256()
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
  z=os.fstat(f.fileno());need((a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns),'file changed')
 need((p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns),'path changed')
 refs[str(p)]=h.hexdigest()
 return {'path':str(p),'sha256':h.hexdigest(),'bytes':z.st_size}
def chk(base,rel,pin=None):
 safe(rel);p=base/rel
 if not p.exists():return {'path':str(p),'exists':False}
 x=digest(p);x['exists']=True
 need(pin is None or x['sha256']==pin,'SHA mismatch '+str(p))
 return x
def read(base,rel,pin=None):
 x=chk(base,rel,pin);need(x['exists'],'missing '+str(base/rel))
 return json.loads((base/rel).read_bytes())
def load(p,name):
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def save(name,x):
 p=D/name
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2,ensure_ascii=False);f.write('\n')
 return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def main():
 receipt=read(P,'results/formal_main_v2/job_receipts/3042529.json','86676fe6e84440069e61f4609008c4e5a9a7c88e883444519479d45767bd011e')
 need(receipt['status']=='failed' and receipt['exit_code']==1 and receipt['error']=='Noncanonical or missing evidence' and receipt['invocation_sha256']==INV_SHA,'actual original failure')
 need(receipt['action_execution_artifacts']==receipt['adapter_artifacts']==receipt['adapter_receipts']==[] and receipt['original_scientific_wrapper_executed'] is False,'before child')
 invocation=read(P,INV,INV_SHA);chk(R,INV,INV_SHA)
 chk(P,WRAP,WRAP_SHA);chk(R,WRAP,WRAP_SHA);chk(P,CONTRACT,CONTRACT_SHA);chk(R,CONTRACT,CONTRACT_SHA)
 root_readiness=read(P,BASE+'runtime_readiness.json',invocation['runtime_readiness']['sha256'])
 original=read(P,BASE+'scientific_plan.json',invocation['scientific_plan']['sha256'])
 execution=read(P,BASE+'execution_contract.json',invocation['action_execution_contract']['sha256'])
 transition=read(P,execution['transition']['path'],execution['transition']['sha256'])
 prior=read(R,PRIOR,PRIOR_SHA)
 need(original['invocation']['prior_review']==PRIOR and original['invocation']['root_evidence_sha256'][PRIOR]==PRIOR_SHA,'exact inherited prior dependency')
 need(not (P/PRIOR).exists(),'missing dependency no longer reproduced')
 # Actual unmodified production parent verify, no main(), locks, child or GPU.
 parent=load(P/WRAP,'diagnostic_parent_3042529')
 ref_calls=[]
 original_load=parent.load
 def record_load(path,name):
  m=original_load(path,name)
  if Path(path)==P/CONTRACT:
   original_read=m.read_ref
   def traced(root,value):
    ref_calls.append({'root':str(root),'reference':value})
    return original_read(root,value)
   m.read_ref=traced
  return m
 parent.load=record_load
 try:
  parent.verify(invocation,project=P)
 except Exception as exc:
  actual={'error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'read_ref_calls':ref_calls,'after_the_fact_reproduction':True,'not_original_job_stdout':True}
 else:raise ValueError('original failure unexpectedly absent')
 need(actual['error_type']=='ValueError' and actual['error']=='Noncanonical or missing evidence' and ref_calls[-1]['reference']=={'path':PRIOR,'sha256':PRIOR_SHA},'exact reproduced missing prior')
 reproduction=save('actual_readonly_reproduction.json',actual)
 # Bounded counterfactual: replace exactly one read-only ref lookup in this
 # diagnostic process. This is not production preflight or authorization.
 redirects=[];virtual_calls=[]
 def projected_load(path,name):
  m=original_load(path,name)
  if Path(path)==P/CONTRACT:
   original_read=m.read_ref
   def projected(root,value):
    virtual_calls.append({'root':str(root),'reference':value})
    if Path(root)==P and value=={'path':PRIOR,'sha256':PRIOR_SHA}:
     redirects.append(value);return original_read(R,value)
    return original_read(root,value)
   m.read_ref=projected
  return m
 parent.load=projected_load
 try:
  result=parent.verify(invocation,project=P)
  virtual={'status':'passed_after_exact_one_missing_ref_redirect_in_memory_only','redirects':redirects,'read_ref_calls':virtual_calls,'actual_production_preflight_passed':False,'GPU_executed':False,'scientific_trials_added':0}
 except Exception as exc:
  virtual={'status':'additional_dependency_or_contract_failure','error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'redirects':redirects,'read_ref_calls':virtual_calls,'actual_production_preflight_passed':False}
 finally:parent.load=original_load
 need(redirects==[{'path':PRIOR,'sha256':PRIOR_SHA}],'exact one immutable reference only')
 counterfactual=save('virtual_publication_CPU_diagnostic.json',virtual)
 # Enumerate actual direct refs and all original/runtime watched dependencies.
 closure={}
 def require_dep(rel,pin,origin):
  safe(rel)
  if rel in closure:need(closure[rel]['sha256']==pin,'conflicting closure')
  else:closure[rel]={'sha256':pin,'origins':[],'R':chk(R,rel,pin),'P':chk(P,rel,pin)}
  closure[rel]['origins'].append(origin)
 for call in virtual_calls:
  require_dep(call['reference']['path'],call['reference']['sha256'],'production_contract.read_ref')
 for rel,pin in invocation['support_files'].items():require_dep(rel,pin,'prepared_invocation.support_files')
 for invlabel,inv in [('outer',invocation),('original',original['invocation'])]:
  for name,pin in inv['watched_files'].items():
   pp=Path(name);need(P in pp.parents,'watched root')
   require_dep(pp.relative_to(P).as_posix(),pin,invlabel+'.watched_files')
 for role,ref in root_readiness.get('component_reviews',{}).items():require_dep(ref['path'],ref['sha256'],'readiness.component_reviews.'+role)
 for rel,pin in root_readiness.get('runtime_publication_files',{}).items():require_dep(rel,pin,'readiness.runtime_publication_files')
 # The prior root review embeds a historical evidence map. Its own bytes bind
 # that map; current execution directly consumes only this JSON and files below.
 prior_raw={}
 for rel,pin in prior['files'].items():
  require_dep(rel,pin,'prior_review.files')
  prior_raw[rel]=closure[rel]
 need(transition['files'] and all(prior['files'].get(k)==v for k,v in transition['files'].items()),'transition raw binding')
 for rel,pin in transition['files'].items():require_dep(rel,pin,'transition.files')
 prefix_bytes=(P/RUN/'trials.jsonl').read_bytes()
 need(prefix_bytes.endswith(b'\n'),'truncated old ledger')
 rows=[json.loads(line) for line in prefix_bytes.splitlines()]
 terminal=[x for x in rows if x.get('status')=='completed']
 need(len(terminal)==12 and len(rows)==25 and prior['completed_trials']==12,'exact original12 prefix')
 need(hashlib.sha256(prefix_bytes).hexdigest()==prior['files'][RUN+'/trials.jsonl'],'old full prefix unchanged')
 # No action/old-adapter execution outputs were created for this failed job.
 action_dir=P/'results/formal_main_v2/action_execution_invocations/3042529'
 need(not action_dir.exists(),'unexpected action child output')
 need(not (P/RUN/'action_execution/3042529').exists(),'unexpected archived action output')
 for name in ['cti-formal-downstream_3042529.out','cti-formal-downstream_3042529.err']:chk(P,'results/slurm/'+name)
 inv173=read(R,'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 need(len(inv173['files'])==173,'original source count')
 for rel,pin in inv173['files'].items():chk(R,rel,pin);chk(S,rel,pin)
 scheduler_cmd=['sacct','-j','3042529','--noheader','--parsable2','--format=JobIDRaw,State,ExitCode,ElapsedRaw,AllocTRES,NodeList']
 p=subprocess.run(scheduler_cmd,capture_output=True,text=True,check=True,timeout=30)
 scheduler={'command':scheduler_cmd,'stdout':p.stdout,'stderr':p.stderr,'returncode':p.returncode,'read_only':True}
 row=next(line.split('|') for line in p.stdout.splitlines() if line.split('|')[0]=='3042529')
 need(row[1]=='FAILED' and row[2]=='1:0' and row[3]=='2' and 'gres/gpu=1' in row[4],'terminal Slurm bill')
 scheduler_ref=save('actual_scheduler_terminal.json',scheduler)
 missing=[{'path':k,'sha256':v['sha256'],'origins':v['origins'],'source':v['R']['path'],'destination':v['P']['path'],'bytes':v['R'].get('bytes')} for k,v in closure.items() if not v['P']['exists']]
 closure_ref=save('dependency_closure.json',{'schema':'formal_main_v2','kind':'read_only_dependency_closure_diagnosis','actual_read_refs':virtual_calls,'files':closure,'missing_P':missing,'prior_review_embedded_evidence_entries':len(prior['evidence_sha256']),'prior_review_historical_map_reinterpreted_as_current':False,'historical_evidence_rule':'The prior receipt whole SHA authenticates its embedded historical map. Runtime file references and original prefix files are individually checked; no recursive current-state rewrite of its historic SHA map.'})
 need(len(missing)==1 and missing[0]['path']==PRIOR,'more than minimal missing dependency')
 repair={'schema':'formal_main_v2','kind':'spatial_startup_dependency_repair_candidate','status':'candidate_only_not_authorized','failed_job_id':'3042529','failed_allocation_GPU_seconds':2,'old_authorization':'action_spatial_resume_0943','original_invocation':{'path':INV,'sha256':INV_SHA},'source_of_failure':'Production contract.read_ref(P, prior_review) rejected exactly missing prior root JSON before child execution.','minimal_publication_files':missing,'required_root_actions':['Preserve FAILED1:0 and2GPU seconds; reconcile pending using actual job identity, never resend consumed authorization.','Review this exact immutable R prior JSON and copy only matching bytes to its canonical P relative path, no overwrite of conflicting bytes.','Run the unchanged production wrapper.verify(original prepared invocation, project=P) as CPU-only validation against real published bytes and recheck the unchanged12-trial prefix.','Prepare a new exact single-attempt root authorization/invocation with current capacity and reservations under shared writer lock; do not reuse the consumed authorization or auto retry.'],'scientific_settings_change':False,'frozen173_change':False,'wrapper_change_required_for_this_failure':False,'new_trials_authorized':False,'counterfactual_is_not_actual_publication_proof':True}
 repair_ref=save('repair_candidate.json',repair)
 chk(R,Path(__file__).relative_to(R).as_posix())
 report={'schema':'formal_main_v2','kind':'independent_failed_spatial_startup_diagnosis','status':'confirmed_dependency_publication_failure_no_new_scientific_results','job_id':'3042529','error':'Noncanonical or missing evidence','failed_read_reference':{'path':PRIOR,'sha256':PRIOR_SHA},'failed_source_location':{'path':CONTRACT,'sha256':CONTRACT_SHA,'line':204},'receipt':{'path':'results/formal_main_v2/job_receipts/3042529.json','sha256':'86676fe6e84440069e61f4609008c4e5a9a7c88e883444519479d45767bd011e'},'original_terminal_trials':12,'new_terminal_trials':0,'journal_rows':25,'old_prefix_bytes':len(prefix_bytes),'old_prefix_sha256':hashlib.sha256(prefix_bytes).hexdigest(),'action_execution_artifacts':0,'adapter_artifacts':0,'child_started':False,'model_forward_calls':0,'GPU_engineering_cells':0,'actual_allocation_GPU_seconds':2,'nested_seconds_added_to_cost':False,'frozen173_R_S_unchanged':True,'actual_reproduction':reproduction,'virtual_publication_CPU_diagnostic':counterfactual,'closure':closure_ref,'scheduler':scheduler_ref,'repair_candidate':repair_ref,'actual_full_preflight_after_publication_passed':False,'state_written':False,'production_written':False,'retry_submitted':False,'weights_read':False,'sealed_state_values_read':False,'read_evidence_sha256':dict(sorted(refs.items())),'reviewed_utc':datetime.now(timezone.utc).isoformat()}
 ref=save('independent_diagnosis.json',report)
 print(json.dumps({'report':ref,'missing_P':missing,'virtual_status':virtual['status'],'original_trials':12,'new_trials':0,'GPU_seconds':2,'refs':len(refs)}))
if __name__=='__main__':main()
