from pathlib import Path
from datetime import datetime,timezone
import os,sys,copy,json,hashlib,importlib.util
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');A=R/'.local/action_actual_plan_0943';D=R/'.local/action_actual_plan_independent_0943'
refs={}
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No process/network')
 if event=='open':
  p,mode,flags=args
  if isinstance(p,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(p));p=p if p.is_absolute() else Path.cwd()/p
   if 'sealed' in str(p).lower() or p.suffix.lower() in {'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'}:raise RuntimeError('Forbidden payload '+str(p))
   write=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
   if write and D not in p.parents:raise RuntimeError('No writes outside independent directory')
sys.addaudithook(guard)
def read(p,pin=None):
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest();assert pin is None or h==pin,(str(p),h,pin);refs[str(p)]=h;return b
def jread(p,pin=None):return json.loads(read(p,pin))
pins={'scientific_plan.json':'43a521e2b1c5b7f8ceff442ce655dde5cae73dfde0f9f7598f65fa57446b4a94','effective_plan.json':'a56ff9e12b6ddad13e3e6ee4b78f5181ffa3ead3f8df8c620370e00c95d2eb3b','execution_contract.json':'b63689d9f3fb3dece0c2fee8c219ad94cd8e1e694962afdb2cd66a40bf551bc0','runtime_readiness_draft.json':'3dbf2a4eac17d1f33766a2d8cbc5b89280bf223de8ec52293214e44afd805738'}
values={n:jread(A/n,h) for n,h in pins.items()};old=values['scientific_plan.json'];new=values['effective_plan.json'];action=values['execution_contract.json'];draft=values['runtime_readiness_draft.json'];inv=new['invocation']
p=R/'scripts/ops/formal_action_deployment_v1/contract.py';b=read(p,'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19');spec=importlib.util.spec_from_file_location('ind_actual_outer_contract',p);ct=importlib.util.module_from_spec(spec);exec(compile(b,str(p),'exec'),ct.__dict__)
kwargs=dict(scientific_plan_ref=inv['scientific_plan'],execution_contract_ref=inv['action_execution_contract'],execution_contract=action)
assert ct.validate_effective(old,new,**kwargs) is True
transition=jread(R/action['transition']['path'],action['transition']['sha256']);assert ct.validate_transition(transition,old,root=R,execution_contract=action) is True
assert action['runtime_contract']==jread(A/'runtime_contract.json','127b7f81407731126738a028c439a0d722474001ac945d1545da56f4f0678708')
assert inv['argv']==old['invocation']['argv'] and inv['source_provenance']==old['invocation']['source_provenance']
assert inv['stage']=='development' and inv['suite']=='libero_spatial' and inv['stop_after'] is None and inv['resume'] is True
assert draft['allowed_stages']==['development'] and draft['allowed_suite']=='libero_spatial'
assert set(draft['forbidden_stages'])=={'collect','full','components','global_freeze','final'}
assert all(draft[k] is False for k in ['O2A_enabled','global_freeze_enabled','final_evaluation_enabled','old_new_outcome_equivalence_established','active','production_chain_complete','raw_consumer_ready','scientific_settings_changed'])
assert draft['root_review'] is None and draft['independent_review'] is None and draft['status']=='draft_pending_plan_independent_and_root_readiness'
assert draft['effective_plan']['sha256']==pins['effective_plan.json'] and draft['scientific_plan']==inv['scientific_plan'] and draft['plan_sha256']==new['plan_sha256']
assert draft['support_files']==inv['support_files'] and draft['runtime_sources']==action['files'] and draft['action_execution_contract']==inv['action_execution_contract']
assert draft['maximum_new_trial_ids']==588 and draft['original_terminal_trials_preserved']==12
runtime_sources={}
for rel,pin in action['files'].items():read(R/rel,pin);read(P/rel,pin);runtime_sources[rel]=pin
for rel,pin in action['runtime_contract']['dependencies'].items():read(R/rel,pin);read(P/rel,pin)
for rel,pin in action['GPU_acceptance'].items():read(R/rel,pin);read(P/rel,pin)
publication=jread(R/'results/formal_main_v2/execution/action_spatial_resume_0943/runtime_publication.json','f86add8e6dc7fbbc2c2c8458ba97a70b42f71701c95009d4be324eee7badc8b0')
component={}
for role,ref in draft['component_reviews'].items():
 v=jread(R/ref['path'],ref['sha256']);assert v['status']=='passed_CPU_review' and v['component']==role and v['kind']=='formal_downstream_action_component_independent_CPU_review';component[role]=ref
 # Reuse the other author's runtime independent review; do not independently audit own implementation.
 for rel,pin in v['files'].items():read(R/rel,pin)
negative=[]
def reject(name,mutate,transition_only=False):
 v=copy.deepcopy(transition if transition_only else new);mutate(v)
 if not transition_only:v['plan_sha256']=ct.signature({k:x for k,x in v.items() if k!='plan_sha256'})
 try:
  if transition_only:ct.validate_transition(v,old,root=R,execution_contract=action)
  else:ct.validate_effective(old,v,**kwargs)
 except Exception as e:negative.append({'case':name,'rejected':True,'exception_type':type(e).__name__,'error':str(e)});return
 raise AssertionError('Mutation accepted: '+name)
reject('final_stage',lambda x:x['invocation'].__setitem__('stage','final'))
reject('changed_method_panel',lambda x:x['invocation'].__setitem__('method_ids',['dense']))
reject('changed_checkpoint_argument',lambda x:x['invocation']['argv'].__setitem__(x['invocation']['argv'].index('--checkpoint')+1,'/tmp/other-checkpoint'))
reject('changed_prefix_prior_jobs',lambda x:x['invocation'].__setitem__('prior_job_ids',[]))
config_watch=str(P/new['output_relative']/'config.json')
reject('extra_mutable_watch_exemption',lambda x:x['invocation']['watched_files'].pop(config_watch))
reject('repeated_old_trial_permission',lambda x:x.__setitem__('terminal_trials_repeated',True),True)
reject('altered_prior_outcomes_permission',lambda x:x.__setitem__('prior_outcomes_replaced',True),True)
# Verify every additional runtime watch against P; the exact unpublished plans are reported, never manufactured.
new_watches={p:h for p,h in inv['watched_files'].items() if old['invocation']['watched_files'].get(p)!=h};P_status=[]
for absolute,pin in new_watches.items():
 p=Path(absolute)
 if p.exists():read(p,pin);status='already_exact'
 else:status='pending_root_publication'
 P_status.append({'path':absolute,'sha256':pin,'status':status})
report={'schema':'formal_main_v2','kind':'independent_exact_development_outer_plan_check','status':'passed_readonly_plan_and_runtime_publication','created_utc':datetime.now(timezone.utc).isoformat(),'scientific_inputs_synthetic':False,'scientific_plan':draft['scientific_plan'],'effective_plan':draft['effective_plan'],'action_execution_contract':inv['action_execution_contract'],'effective_plan_content_sha256':new['plan_sha256'],'runtime_sources':runtime_sources,'component_reviews':component,'runtime_and_GPU_acceptance_R_P_bytes_equal':True,'new_watch_publication_status':P_status,'negative_actual_plan_tests':negative,'scientific_argv_resources_source_method_and_panel_unchanged':True,'mutable_prefix_exception_exact_files':ct.resume_prefix_inputs(old['invocation']),'allowed_stages':['development'],'forbidden_stages':['collect','full','components','global_freeze','final'],'old_new_outcome_equivalence_established':False,'GPU_full_chain_run_observed':False,'GPU_jobs_submitted':0,'state_written':False,'final_values_read':False,'production_readiness_signed':False,'evidence_sha256':refs}
raw=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();out=D/'exact_outer_plan_readonly_check.json';assert not out.exists();out.write_bytes(raw);print(json.dumps({'status':report['status'],'sha256':hashlib.sha256(raw).hexdigest(),'refs':len(refs),'negative_cases':len(negative),'pending_P_publication':[x['path'] for x in P_status if x['status']!='already_exact']}))
