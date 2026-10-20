# CPU author checks. No production I/O writes, Slurm, GPU, weights, sealed values.
import os,sys,json,hashlib,importlib.util,copy,time,traceback,ast,io,contextlib
from pathlib import Path
from types import SimpleNamespace
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent;OUT=D/'attempt03';K=D/'revision03/package';P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
CONTROL_SHA='09ae3486565e17bd2c41b09adbfaa7a6d99f38754d3e77071f77851c9ac54f6f';CHECKS=[];READS={}
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('CPU only: no process/network/Slurm')
 if event=='open':
  name,mode,flags=args
  if isinstance(name,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(name));p=p if p.is_absolute() else Path.cwd()/p
   assert not any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts),'sealed/weight access prohibited'
   assert p.suffix.lower() not in ('.pt','.pth','.bin','.safetensors','.pkl','.pickle','.ckpt','.init','.pruned_init'),'payload access prohibited'
   writing=isinstance(mode,str) and any(x in mode for x in 'wax+') or isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC))
   if writing:assert OUT in p.parents,'private outputs only:'+str(p)
sys.addaudithook(guard)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(name,ok,detail=None):
 CHECKS.append({'name':name,'passed':bool(ok),'detail':detail})
 if not ok:raise AssertionError(name)
def reject(name,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,RuntimeError) as e:check(name,True,str(e));return
 raise AssertionError('Unexpected admission:'+name)
def write(name,value):
 p=OUT/name;raw=value if isinstance(value,bytes) else (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
 with p.open('xb') as f:f.write(raw)
 return {'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(raw).hexdigest()}
def load(p,pin=None):
 p=Path(p);raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();assert pin is None or h==pin;READS[str(p)]=h
 spec=importlib.util.spec_from_file_location('object23_author_'+p.stem,p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;exec(compile(raw,str(p),'exec'),m.__dict__);return m
class E:
 def __init__(self):self.project=self.root=R;self.files={}
 def path(self,p):p=Path(p);return p if p.is_absolute() else R/p
 def watch(self,p):q=self.path(p);h=digest(q);k=q.relative_to(R).as_posix();assert k not in self.files or self.files[k]==h;self.files[k]=h;return h
 def read(self,p):self.watch(p);return json.loads(self.path(p).read_text())
 def unchanged(self):
  for k,h in self.files.items():assert digest(R/k)==h

def main():
 OUT.mkdir(exist_ok=False);t=time.monotonic();c=load(K/'control.py',CONTROL_SHA);ev=E();closure=c.closure();write('control_closure.json',closure)
 inv=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text())
 for root in [R,S]:
  for path,pin in inv['files'].items():check('173-before:'+str(root)+':'+path,digest(root/path)==pin)
 state_path=R/'.local/object256s23_consumer_candidate_20261020T1530/runtime_check01/author_state_snapshot.json';check('snapshot exact',digest(state_path)=='303d0e953ef966fa53787f46b19152f697c2d211640a7f3f8813754776d05430');state=json.loads(state_path.read_text());state_before=copy.deepcopy(state)
 write('snapshot_reference.json',{'path':state_path.relative_to(R).as_posix(),'sha256':digest(state_path),'author_CPU_only_not_fresh_root_lock_or_CAS_authorization':True})
 args=json.loads((R/'.local/object256s23_consumer_candidate_20261020T1530/runtime_check01/plan_arguments.json').read_text());write('plan_arguments.json',args)
 f,pl=c.control_modules(ev);science=pl.plan(SimpleNamespace(**args),state,project=R);check('no state mutation',state==state_before);sciref=write('scientific_plan.json',science)
 check('explicit full source proof',science['invocation']['source_provenance']['explicit_source_control']==c.descriptor());check('three allocations retained',set(science['invocation']['source_provenance']['method_bindings']['A256_seed23']['registered_training_job_ids'])=={'3028460','3039258','3042627'})
 check('fresh planner deterministic',c.control_modules(E())[1].plan(SimpleNamespace(**args),copy.deepcopy(state),project=R)==science)
 factory_argv=['--project-root',str(R),'development','--suite','libero_object','--methods',*c.METHODS,'--source-inventory',args['source_inventory'],'--output',(OUT/'factory_manifest.json').relative_to(R).as_posix()]
 with contextlib.redirect_stdout(io.StringIO()) as factory_text:factory_rc=f.main(factory_argv)
 check('bounded factory valid paired manifest',factory_rc==0 and json.loads((OUT/'factory_manifest.json').read_text())==json.loads((R/c.MANIFEST).read_text()))
 check('bounded factory explicit source proof',json.loads((OUT/'factory_manifest.json.evidence.json').read_text())['source_provenance']['explicit_source_control']==c.descriptor())
 for bad in [None,[],['--project-root',str(R),'freeze'],factory_argv[:4]+['libero_goal']+factory_argv[5:],factory_argv[:-1]+['results/experiment_supervisor/state.json'],factory_argv+['--release']]:
  reject('reject bounded factory argv '+str(bad),lambda bad=bad:f.main(bad))
 for key,new in [('stage','final'),('stage','collect'),('stage','full'),('stage','components'),('stop_after',1),('resume',True),('execution_manifest','other.json'),('output_relative','results/other'),('prior_review','results/old.json')]:
  bad=dict(args);bad[key]=new;reject('reject arguments '+key+'='+str(new),lambda bad=bad:c.scope_args(SimpleNamespace(**bad)))
 for key,new in [('suite','libero_goal'),('method_ids',['A256_seed23']),('method_ids',['A256_seed41','B256_seed41']),('execution_manifest_sha256','0'*64),('resume',True),('prior_job_ids',['3028460']),('stop_after',1)]:
  bad=copy.deepcopy(science['invocation']);bad[key]=new;reject('reject invocation '+key+'='+str(new),lambda bad=bad:c.scope_invocation(bad))
 bad=copy.deepcopy(science['invocation']);bad['source_provenance'].pop('explicit_source_control');reject('reject missing explicit proof',lambda:c.scope_invocation(bad))
 g=c.gateway_module();gb=load(R/c.GATEWAY,c.ORIGINAL[c.GATEWAY]);check('gateway source closure includes control',g.source_files(R)==closure)
 # Original lock/CAS/capacity/submission/reconciliation implementations are unchanged code.
 def semantic_code(fn):
  import types
  def sem(co):return (co.co_code,co.co_names,co.co_varnames,co.co_argcount,co.co_kwonlyargcount,tuple(sem(x) if isinstance(x,types.CodeType) else x for x in co.co_consts))
  return sem(fn.__code__)
 for name in ['capacity_gate','parse_ack','registered_comment','check_observed_identity','corroborate_new_job','submission_argv','reconcile_submission','intent_sha']:
  check('original gateway function:'+name,semantic_code(getattr(g,name))==semantic_code(getattr(gb,name)))
 for cl,names in [('Gateway',['run','_cas','_job']),('NativeIO',['_watch','_inputs','preflight','publish'])]:
  for name in names:check('original class method:'+cl+'.'+name,semantic_code(getattr(getattr(g,cl),name))==semantic_code(getattr(getattr(gb,cl),name)))
 reject('gateway missing root bridge authorization',lambda:g.validate_authorization(R,{'path':sciref['path'],'sha256':sciref['sha256']}))
 # Root readiness intentionally absent; this only exercises actual FrozenPlan rebuild path.
 pre='scripts/ops/formal_action_deployment_v1/';ct=load(R/(pre+'contract.py'),'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19')
 rt=load(R/(pre+'runtime_scope.py'),'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53');runtime=rt.make_contract(project_root=R,source_root=S,suite='libero_object',stage='development')
 files={p:digest(R/p) for p in ct.EXPECTED_NEW_FILES};files[ct.ACTION_ADAPTER]=ct.ACTION_SHA
 action={'schema':ct.SCHEMA,'kind':'formal_action_execution_contract','version':ct.VERSION,'status':'candidate_pending_root_readiness','scientific_settings_changed':False,'final_evaluation_enabled':False,'files':files,'runtime_contract':runtime,'GPU_acceptance':ct.GPU_REFS,'source_inventory':{'path':ct.INVENTORY,'sha256':ct.INVENTORY_SHA},'transition':None};aref=write('execution_contract.json',action)
 effective=ct.effective_plan(science,scientific_plan_ref=sciref,execution_contract_ref=aref,execution_contract=action);eref=write('effective_plan_private_preview.json',effective)
 auth={'scientific_plan':sciref,'plan_arguments':args,'runtime_readiness':None};prepared={**effective['invocation'],'registered_utc':'2026-10-20T16:44:00+00:00','plan_sha256':effective['plan_sha256'],'runtime_readiness':None};auth['prepared_invocation']=write('CPU_prepared_shape_not_invocation_or_authorization.json',prepared)
 bundle=g.FrozenPlan(R,auth,g.Evidence(R),effective,science,prepared).prepare(copy.deepcopy(state));check('actual FrozenPlan rebuild matches explicit science',bundle['plan']==effective and bundle['invocation']==prepared)
 reject('baseline gateway rejects unbridged metadata',lambda:gb.FrozenPlan(R,auth,gb.Evidence(R),effective,science,prepared).prepare(copy.deepcopy(state)))
 wrapper=load(P/(pre+'wrapper.py'),'d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33');reject('actual P wrapper missing true readiness',lambda:wrapper.verify(effective['invocation'],project=P))
 oldwrapper=load(P/'scripts/server/run_formal_downstream.py','f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24');check('original P metadata verify',oldwrapper.verify(science['invocation']).mode=='evaluate')
 reviewer=c.reviewer_module(E());rb=load(R/c.REVIEWER,c.ORIGINAL[c.REVIEWER])
 for name in ['validate_envelope','verify_pull','actual_runtime','trajectory_validator','science_context','validate_transition_after','checked_asset_identities']:
  check('original raw-review primitive:'+name,semantic_code(getattr(reviewer,name))==semantic_code(getattr(rb,name)))
 # Actual source reconstruction path called by terminal review, without claiming any runtime trial evidence.
 se=reviewer.Evidence(R);old=reviewer.load(se,reviewer.OLD_REVIEW,reviewer.PINNED[reviewer.OLD_REVIEW]);h,sch=c.control_modules(se)
 pi=effective['invocation'];job={k:pi[k] for k in ['stage_key','suite','method_ids','run_root','source_sha256','adapter_sha256','execution_manifest_sha256']};job.update(mode='development',source_provenance_sha256=sch.signature(pi['source_provenance']),job_id='CPU_ONLY_NOT_SLURM',status='NOT_RUN',gpus=0)
 value,_=reviewer.science_context(se,old,sch,h,job,pi,state['registered_jobs'],science,action,lambda *a,**k:(_ for _ in ()).throw(AssertionError('No downstream reference allowed')))
 check('terminal actual science_context reconstructs same proof',value['source_provenance']==science['invocation']['source_provenance'])
 for mode in ['final','collect','full','components']:
  reject('terminal rejects mode '+mode,lambda mode=mode:reviewer.review(R,job={'mode':mode,'suite':'libero_object','method_ids':c.METHODS}))
 consumer=c.consumer_module(E())
 for stage,suite,complete in [('final','libero_object',True),('development','libero_goal',True),('development','libero_object',False)]:
  reject('consumer rejects scope '+str((stage,suite,complete)),lambda stage=stage,suite=suite,complete=complete:consumer.review_downstream_output(E(),{},expected_stage=stage,suite=suite,require_complete=complete))
 # Invalid consumer references must fail before the requested artifact is read/watched.
 class ReferenceGuard(E):
  def watch(self,p):
   if str(p).startswith('results/formal_main_v2/downstream_reviews/') or str(p).startswith('probe_forbidden'):raise AssertionError('invalid reference reached artifact I/O')
   return super().watch(p)
  def read(self,p):raise AssertionError('invalid reference reached artifact read')
 for ref in [{},{'path':'../forbidden.json','sha256':'0'*64},{'path':'probe_forbidden.json','sha256':'0'*64},{'path':'results/formal_main_v2/downstream_reviews/nonexistent.json','sha256':'bad'},{'path':'/absolute/forbidden.json','sha256':'0'*64}]:
  reject('consumer rejects reference before I/O '+str(ref),lambda ref=ref:consumer.review_downstream_output(ReferenceGuard(),ref,expected_stage='development',suite='libero_object'))
 check('source modules originals unchanged',all(digest(R/p)==h for p,h in c.ORIGINAL.items()))
 for root in [R,S]:
  for path,pin in inv['files'].items():check('173-after:'+str(root)+':'+path,digest(root/path)==pin)
 ev.unchanged();se.unchanged();write('read_evidence.json',{'control':ev.files,'terminal_source_chain':se.files,'loaded_sources':READS})
 report={'status':'passed_CPU_control_candidate_only','checks':len(CHECKS),'negative_cases':sum(x['name'].startswith(('reject','gateway missing','baseline gateway rejects','actual P wrapper missing','terminal rejects','consumer rejects')) for x in CHECKS),'results':CHECKS,'CPU_wall_seconds':time.monotonic()-t,'source_control':c.descriptor(),'scientific_manifest_byte_identical':True,'actual_FrozenPlan_rebuild':True,'actual_terminal_science_context_rebuild':True,'original_adapter_runtime_trajectory_cost_primitives_unchanged':True,'GPU_runs':0,'scientific_trials':0,'Slurm_calls':0,'state_Git_canonical_writes':False,'production_path_published':False,'root_and_independent_runtime_readiness':False,'actual_final_checkpoint_bytes_checked':False,'terminal_GPU_receipt_verified':False,'all_original_readiness_gates_required':True,'unrun200_not_admitted':True,'failed_GPU_seconds_retained':84,'all_pair_GPU_seconds':58917}
 write('cpu_report.json',report);print(json.dumps({k:report[k] for k in ['status','checks','negative_cases','actual_FrozenPlan_rebuild','actual_terminal_science_context_rebuild','production_path_published','root_and_independent_runtime_readiness']}))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  if OUT.exists():write('failure.json',{'error':str(e),'traceback':traceback.format_exc(),'checks':CHECKS,'GPU_runs':0,'Slurm_calls':0})
  raise
