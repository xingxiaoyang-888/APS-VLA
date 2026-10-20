"""Independent CPU/source audit. No gateway.run, publish, submit, or production mutation."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,difflib,fcntl,hashlib,importlib.util,json,os,subprocess,sys,time
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/completed_training_gateway_independent_20261020T1825/attempt02'
D.mkdir(exist_ok=False)
NEW='.local/completed_training_gateway_20261020T1825/revision02/gateway.py'
NEW_SHA='4a11a62e817cd96523cd8f06aa0c3c71e12208f1b3a6b487799160915e59ec83'
TARGET='scripts/ops/formal_action_deployment_posttraining_v1/gateway.py'
OLD='scripts/ops/formal_action_deployment_v1/gateway.py'
OLD_SHA='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a'
CONTROLLER='scripts/ops/formal_autonomous_training_v1/controller.py'
CONTROLLER_SHA='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
START=time.monotonic();CHECKS=[];NEG=[];SUBPROCESSES=[];WRITES=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
def ref(p):
 p=Path(p);return dict(path=p.relative_to(R).as_posix(),sha256=sha(p.read_bytes()),bytes=p.stat().st_size)
def record(name,value):
 p=D/name
 with p.open('xb') as f:f.write(canonical(value)+b'\n')
 return ref(p)
def check(name,ok,detail=None):
 if not ok:raise AssertionError(name)
 CHECKS.append(dict(name=name,status='passed',detail=detail))
def negative(name,fn,contains=None):
 try:fn()
 except (ValueError,BlockingIOError,KeyError) as e:
  if contains is not None and contains not in str(e):raise AssertionError(name+': unexpected error '+str(e))
  NEG.append(dict(name=name,status='rejected_as_required',error_type=type(e).__name__,message=str(e)))
 else:raise AssertionError(name+': unexpectedly accepted')
def guard(event,args):
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes)):
   p=Path(os.fsdecode(path)).absolute()
   if p.suffix.lower() in {'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'}:raise RuntimeError('weight/state payload read forbidden')
   if isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
    if not p.is_relative_to(D):raise RuntimeError('production write forbidden: '+str(p))
    WRITES.append(str(p))
 if event=='subprocess.Popen':
  argv=args[1]
  if not isinstance(argv,list) or argv[0] not in {'sacct','squeue'}:raise RuntimeError('non-observation subprocess forbidden')
  SUBPROCESSES.append(argv)
 if event.startswith('socket.') or event in {'os.system','os.remove','os.rename','os.rmdir','os.unlink'}:raise RuntimeError('forbidden side effect: '+event)
sys.addaudithook(guard)
def load(rel,pin,name):
 raw=(R/rel).read_bytes();check('pin:'+rel,sha(raw)==pin)
 spec=importlib.util.spec_from_file_location(name,R/rel);m=importlib.util.module_from_spec(spec);sys.modules[name]=m
 exec(compile(raw,str(R/rel),'exec'),m.__dict__);return m
old=load(OLD,OLD_SHA,'independent_old_gateway1825')
new=load(NEW,NEW_SHA,'independent_new_gateway1825')
c=load(CONTROLLER,CONTROLLER_SHA,'independent_controller1825')
oast=ast.parse((R/OLD).read_text());nast=ast.parse((R/NEW).read_text())
odefs={n.name:n for n in oast.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
ndefs={n.name:n for n in nast.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
check('only_one_additional_function',set(ndefs)-set(odefs)=={'completed_training_collect_gate'})
for name,node in odefs.items():
 if name!='capacity_gate':check('unchanged_AST:'+name,ast.dump(node)==ast.dump(ndefs[name]))
ocap=copy.deepcopy(odefs['capacity_gate']);ncap=copy.deepcopy(ndefs['capacity_gate'])
changed=[i for i,(x,y) in enumerate(zip(ocap.body,ncap.body)) if ast.dump(x)!=ast.dump(y)]
check('capacity_one_statement_change',len(ocap.body)==len(ncap.body) and len(changed)==1,changed)
i=changed[0];oldstatement=ocap.body[i];newstatement=ncap.body[i]
check('capacity_change_is_running_fallback',isinstance(oldstatement,ast.Expr) and isinstance(newstatement,ast.If) and len(newstatement.body)==1 and not newstatement.orelse and 'completed_training_collect_gate' in ast.unparse(newstatement))
ncap.body[i]=copy.deepcopy(oldstatement)
check('capacity_reverse_projection_exact_original',ast.dump(ncap)==ast.dump(ocap))
allowed_added={'COMPLETED_COLLECTION_PLANS','COMPLETED_EXIT_OBSERVATION','COMPLETED_ROOT_INTEGRATION','COMPLETED_WORK','COMPLETED_OWNER_SHA','COMPLETED_OWNER_ID','COMPLETED_CONTROLLER_ID'}
def assign_names(n):return {t.id for t in n.targets if isinstance(t,ast.Name)} if isinstance(n,ast.Assign) else set()
projected=[]
for n in copy.deepcopy(nast).body:
 if isinstance(n,ast.FunctionDef) and n.name=='completed_training_collect_gate':continue
 if assign_names(n)&allowed_added:continue
 if isinstance(n,ast.FunctionDef) and n.name=='capacity_gate':n=copy.deepcopy(ocap)
 if isinstance(n,ast.Import):n.names=[a for a in n.names if a.name!='fcntl']
 if 'VERSION' in assign_names(n):n=next(copy.deepcopy(x) for x in oast.body if 'VERSION' in assign_names(x))
 projected.append(n)
check('whole_module_reverse_projection_exact_original',ast.dump(ast.Module(body=projected,type_ignores=[]))==ast.dump(oast))
diff=''.join(difflib.unified_diff((R/OLD).read_text().splitlines(True),(R/NEW).read_text().splitlines(True),fromfile=OLD,tofile=TARGET))
with (D/'original_to_revision02.diff').open('x') as f:f.write(diff)
plans={suite:json.loads((R/p['path']).read_bytes()) for suite,p in new.COMPLETED_COLLECTION_PLANS.items()}
check('exact_two_collect_allowlist',set(plans)=={'libero_spatial','libero_object'})
for suite,p in plans.items():
 allowed=new.COMPLETED_COLLECTION_PLANS[suite]
 check('published_exact_plan:'+suite,sha((R/allowed['path']).read_bytes())==allowed['sha256'] and p['plan_sha256']==allowed['plan_sha256'])
 check('plan_identity_content:'+suite,sha(new.canonical({k:v for k,v in p.items() if k!='plan_sha256'}))==p['plan_sha256'])
 check('collect_dense_only:'+suite,p['invocation']['stage']=='collect' and p['invocation']['method_ids']==['dense'])
 check('old_runtime_gateway_remains_pinned:'+suite,p['invocation']['support_files'][OLD]==OLD_SHA)
SP=plans['libero_spatial'];OP=plans['libero_object']
def auth(plan):
 allowed=new.COMPLETED_COLLECTION_PLANS[plan['invocation']['suite']]
 return dict(controller_job_id='3034538',controller_activation=new.ACTIVATION,plan={k:allowed[k] for k in ('path','sha256')},root_reservation={'path':'.local/CPU_MEMORY_ONLY_RESERVATION_NOT_AUTHORIZATION.json','sha256':'f'*64})
A=auth(SP)
lock=R/'results/experiment_supervisor/.writer.lock';statepath=R/new.STATE
with lock.open('rb') as f:
 fcntl.flock(f,fcntl.LOCK_SH)
 try:
  raw=statepath.read_bytes();state=json.loads(raw)
  snapshot=c.Slurm(timeout=45).observe(state['registered_jobs'])
  check('registered_only_live_observation',set(snapshot['rows'])=={str(j['job_id']) for j in state['registered_jobs']})
  capacity=c.capacity(state['registered_jobs'],snapshot,'3034538')
  check('live_capacity_known_consistent',not capacity['unknown'] and not capacity['findings'],capacity)
  cpus=[str(j['job_id']) for j in state['registered_jobs'] if type(j.get('gpus'))is int and j['gpus']==0 and snapshot['rows'][str(j['job_id'])]['gpus']==0]
  actual_proofs={}
  for suite,p in plans.items():actual_proofs[suite]=new.completed_training_collect_gate(c,state,snapshot,auth(p),p,cpus)
  check('actual_completed_helper_two_plans',all(x['lifecycle_lease_available_measured'] and x['root_arms']==72 and not x['final_release'] for x in actual_proofs.values()),actual_proofs)
  lease=new.COMPLETED_WORK/'controller.lease.lock';before=lease.stat();owner_before=sha((new.COMPLETED_WORK/'owner.json').read_bytes())
  with lease.open('rb') as q:
   fcntl.flock(q,fcntl.LOCK_EX|fcntl.LOCK_NB)
   try:negative('actual_held_lifecycle_lease_blocks',lambda:new.completed_training_collect_gate(c,state,snapshot,A,SP,cpus))
   finally:fcntl.flock(q,fcntl.LOCK_UN)
  after=lease.stat()
  check('actual_owner_lease_not_recreated_or_modified',(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns) and owner_before==sha((new.COMPLETED_WORK/'owner.json').read_bytes()))
  check('state_exact_bytes_unchanged_under_read_lock',statepath.read_bytes()==raw)
  with (D/'state_at_audit.json').open('xb') as q:q.write(raw)
  record('actual_registered_scheduler_snapshot.json',snapshot)
  record('actual_helper_proofs.json',actual_proofs)
 finally:fcntl.flock(f,fcntl.LOCK_UN)
check('actual_no_pending_no_root_hold',state['pending_submission'] is None and state['autonomous_training_v1']['root_submission_hold'] is None)
check('actual_reserved_slots_zero',state['autonomous_training_v1']['reserved_GPU_slots']==0)
negative('actual_outer_gate_requires_real_reservation',lambda:new.capacity_gate(c,state,snapshot,A,SP),'own dedicated reservation missing')
# Below are explicit in-memory CPU fixtures. They are never authorizations/state writes.
base=copy.deepcopy(state);base['autonomous_training_v1']['reserved_GPU_slots']=1;base['autonomous_training_v1']['reservation_root_record']=A['root_reservation']
basesnap=copy.deepcopy(snapshot)
fixtureproofs={}
for suite,p in plans.items():
 caps,_,projection=new.capacity_gate(c,base,basesnap,auth(p),p)
 fixtureproofs[suite]=caps
 check('fixture_reservation_original_capacity_accepts:'+suite,len(caps['occupied'])<8)
check('capacity_fixtures_leave_actual_state_unchanged',sha(canonical(state))==sha(canonical(json.loads(raw))))
# Do not erase real active jobs in fixtures. Fill free slots with labeled synthetic non-training allocations.
def filled(count,first_collect=False):
 st=copy.deepcopy(base);sn=copy.deepcopy(basesnap)
 n=len(c.capacity(st['registered_jobs'],sn,'3034538')['occupied'])
 if count<n:raise AssertionError('requested CPU fixture cannot remove actual live allocation')
 for k in range(count-n):
  jid=str(9900000+k);collect=first_collect and k==0;inv=SP['invocation']
  job=dict(job_id=jid,name='cpu-fixture-only',experiment='formal_main_v2',mode='collect' if collect else 'engineering',suite='libero_spatial' if collect else 'libero_10',method_ids=['dense'] if collect else [],stage_key=inv['stage_key'] if collect else 'cpu_fixture_'+jid,status='RUNNING',exit_code='0:0',gpus=1,invocation=SP['invocation_relative'] if collect else '.local/cpu_fixture_'+jid+'.json')
  st['registered_jobs'].append(job);sn['rows'][jid]=dict(job_id=jid,status='RUNNING',exit_code='0:0',gpus=1,elapsed_seconds=0,allocation='gres/gpu=1',node='CPU_FIXTURE',scheduler_name='cpu-fixture-only',scheduler_comment='')
  sn['queue'][jid]=dict(status='RUNNING',comment='')
 st['autonomous_training_v1']['occupied_job_ids']=c.capacity(st['registered_jobs'],sn,'3034538')['occupied']
 return st,sn
actual_n=len(capacity['occupied'])
check('live_at_most_seven_slots',actual_n<=7,actual_n)
for count in sorted(set([max(actual_n,1),7])):
 st,sn=filled(count)
 caps,_,_=new.capacity_gate(c,st,sn,A,SP)
 check('fixture_parallel_nontrain_'+str(count)+'_slots',len(caps['occupied'])==count)
st,sn=filled(max(actual_n+1,2),True)
caps,_,_=new.capacity_gate(c,st,sn,auth(OP),OP)
check('fixture_second_collect_with_first_collect_active',len(caps['occupied'])==max(actual_n+1,2))
negative('fixture_duplicate_active_collect',lambda:new.capacity_gate(c,st,sn,A,SP),'duplicate active/unresolved stage')
st8,sn8=filled(8)
negative('fixture_eight_slots_blocks',lambda:new.capacity_gate(c,st8,sn8,A,SP),'eight GPU slots occupied')
# Normal RUNNING branch remains exactly usable, without ever calling the new helper.
running=copy.deepcopy(base);rs=copy.deepcopy(basesnap)
for j in running['registered_jobs']:
 if str(j['job_id'])=='3034538':j.update(status='RUNNING',exit_code='0:0')
rs['rows']['3034538'].update(status='RUNNING',exit_code='0:0');rs['queue']['3034538']=dict(status='RUNNING',comment=rs['rows']['3034538'].get('scheduler_comment',''))
legacy=old.capacity_gate(c,running,rs,A,SP);updated=new.capacity_gate(c,running,rs,A,SP)
check('fixture_original_RUNNING_capacity_exact_result',legacy==updated and 'completed_training_collect_gate' not in updated[0])
# Bounded input corruption tests, all in memory; no source/evidence modifications.
def reject_state(name,mutator,expected=None):
 st=copy.deepcopy(base);sn=copy.deepcopy(basesnap);a=copy.deepcopy(A);p=copy.deepcopy(SP);mutator(st,sn,a,p)
 negative(name,lambda:new.capacity_gate(c,st,sn,a,p),expected)
reject_state('pending_rejected',lambda s,n,a,p:s.update(pending_submission={'request_token':'fixture'}),'unresolved pending')
reject_state('root_hold_rejected',lambda s,n,a,p:s['autonomous_training_v1'].update(root_submission_hold={'reason':'fixture'}),'root hold')
reject_state('wrong_reservation_rejected',lambda s,n,a,p:s['autonomous_training_v1'].update(reserved_GPU_slots=0),'own dedicated reservation')
reject_state('missing_accounting_rejected',lambda s,n,a,p:n['rows'].pop(next(k for k in n['rows'] if k!='3034538')),'all registered accounting')
reject_state('unknown_status_rejected',lambda s,n,a,p:n['rows']['3034538'].update(status='UNKNOWN'),'unknown/inconsistent')
reject_state('duplicate_registry_rejected',lambda s,n,a,p:s['registered_jobs'].append(copy.deepcopy(s['registered_jobs'][0])),'registry duplicate')
reject_state('controller_failed_rejected',lambda s,n,a,p:n['rows']['3034538'].update(status='FAILED'),'unknown/inconsistent')
reject_state('wrong_controller_identity_rejected',lambda s,n,a,p:a.update(controller_job_id='9999999'),'controller state identity')
reject_state('controller_gpu_rejected',lambda s,n,a,p:n['rows']['3034538'].update(gpus=1),'original successful COMPLETED CPU0')
reject_state('controller_queue_disagreement_rejected',lambda s,n,a,p:n['queue'].update({'3034538':{'status':'RUNNING','comment':''}}),'unknown/inconsistent')
reject_state('training_blocked_pairs_rejected',lambda s,n,a,p:s['autonomous_training_v1'].update(blocked_pairs={'fixture':{}}),'blocked/pending')
reject_state('training_incomplete_root_count_rejected',lambda s,n,a,p:s['formal_main_progress'].update(root_and_independent_completed_arms=70),'root72/360000')
reject_state('training_incomplete_update_rejected',lambda s,n,a,p:s['formal_main_progress'].update(root_and_independent_reviewed_arm_updates=359999),'root72/360000')
reject_state('missing_completed_pair_rejected',lambda s,n,a,p:s['autonomous_training_v1']['completed_pairs'].pop(next(iter(s['autonomous_training_v1']['completed_pairs']))),'exact completed36')
reject_state('unverified_checkpoint_outcome_rejected',lambda s,n,a,p:next(iter(s['autonomous_training_v1']['completed_pairs'].values())).update(selected_checkpoints_verified=False),'incomplete controller pair')
reject_state('missing_normal_exit_rejected',lambda s,n,a,p:s['autonomous_training_v1'].pop('root_confirmed_normal_training_exit'),'normal exit identity')
reject_state('wrong_owner_rejected',lambda s,n,a,p:s['autonomous_training_v1'].update(owner_id='wrong'),'owner/activation')
reject_state('wrong_activation_rejected',lambda s,n,a,p:s['autonomous_training_v1'].update(activation_sha256='0'*64),'controller state identity')
reject_state('final_open_rejected',lambda s,n,a,p:s['formal_main_progress'].update(test_opened=True),'cannot authorize final')
reject_state('global_release_rejected',lambda s,n,a,p:s['formal_main_progress'].update(global_release_created=True),'cannot authorize final')
reject_state('noncollect_rejected',lambda s,n,a,p:p['invocation'].update(stage='development'),'two exact')
reject_state('Goal_collect_rejected',lambda s,n,a,p:p['invocation'].update(suite='libero_goal'),'two exact')
reject_state('wrong_plan_ref_rejected',lambda s,n,a,p:a['plan'].update(sha256='0'*64),'exact collect plan')
reject_state('wrong_plan_content_rejected',lambda s,n,a,p:p.update(CPU_ONLY_MUTATION=True),'published exact collect plan')
reject_state('changed_controller_accounting_rejected',lambda s,n,a,p:n['rows']['3034538'].update(elapsed_seconds=n['rows']['3034538']['elapsed_seconds']+1),'terminal accounting differs')
def active_training(s,n,a,p):
 j=next(j for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2' and j.get('mode')=='train');jid=str(j['job_id']);j.update(status='RUNNING',exit_code='0:0');n['rows'][jid].update(status='RUNNING',exit_code='0:0');n['queue'][jid]=dict(status='RUNNING',comment=n['rows'][jid].get('scheduler_comment',''))
reject_state('active_training_allocation_rejected',active_training,'training allocation still active')
def repeat_invocation(s,n,a,p):
 j=next(j for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2' and j.get('mode')!='train' and str(j['job_id'])!='3034538');j['invocation']=p['invocation_relative']
reject_state('invocation_repeat_rejected',repeat_invocation,'invocation already registered')
inventory=json.loads((R/new.INVENTORY).read_bytes());check('source_inventory_pin',sha((R/new.INVENTORY).read_bytes())==new.INVENTORY_SHA)
for location in (R,new.S):
 for rel,pin in inventory['files'].items():
  if sha((location/rel).read_bytes())!=pin:raise AssertionError('173 source drift '+str(location/rel))
check('all173_frozen_R_and_S_unchanged',len(inventory['files'])==173)
check('only_registered_sacct_squeue_commands',all(a[0] in {'sacct','squeue'} for a in SUBPROCESSES),SUBPROCESSES)
record('independent_CPU_checks.json',dict(checks=CHECKS,negative_cases=NEG,passed=len(CHECKS),negative_count=len(NEG),actual_capacity=capacity,fixture_reservation_warning='CPU-only in-memory; never a real authorization or reservation',fixture_proofs=fixtureproofs))
source_refs={x:ref(R/x) for x in [NEW,OLD,CONTROLLER]}
record('code_review.json',dict(schema='formal_main_v2',kind='formal_downstream_server_gateway_independent_CPU_review',status='passed_CPU_review',reviewer='/root/devterminal_20261020_1418',created_utc=datetime.now(timezone.utc).isoformat(),version=new.VERSION,files={TARGET:NEW_SHA,OLD:OLD_SHA},candidate_sources=source_refs,blockers=[],actual_registered_jobs=len(state['registered_jobs']),actual_occupied_GPU_jobs=capacity['occupied'],actual_controller=snapshot['rows']['3034538'],actual_state_sha256=sha(raw),actual_owner_sha256=new.COMPLETED_OWNER_SHA,actual_owner_lease_probe=True,shared_writer_lock_open_mode='rb/LOCK_SH',source_projection='All original definitions/classes/module statements exact after reversing the explicitly scoped fallback/additions/version/import',original_RUNNING_branch_retained=True,all_modes_capacity_limit=8,two_exact_plans_only=new.COMPLETED_COLLECTION_PLANS,new_helper_checks=len(CHECKS),negative_checks=len(NEG),original_runtime_gateway_bound=True,original_runtime_plan_bytes_unchanged=True,scientific_settings_changed=False,scientific_plan_independently_approved_here=False,plan_author_is_this_agent=True,plan_independent_review_required_from_other_agent=True,actual_GPU_probe=False,Slurm_submissions=0,production_state_writes=0,production_publications=0,weights_loaded=False,final_values_read=False,final_release_authorized=False,per_plan_readiness_approved=False,real_reservation_approved=False,scope='Independent source/capacity CPU review of gateway revision02 only; no real submission or collect outcome claim',proofs=[ref(D/x) for x in ['actual_registered_scheduler_snapshot.json','actual_helper_proofs.json','independent_CPU_checks.json','original_to_revision02.diff']],elapsed_CPU_wall_seconds=time.monotonic()-START))
record('manifest.json',dict(schema='formal_main_v2',kind='independent_gateway_CPU_delivery_manifest',created_utc=datetime.now(timezone.utc).isoformat(),files=[ref(p) for p in sorted(D.iterdir()) if p.is_file() and p.name!='manifest.json'],new_GPU_seconds=0,no_production_mutation=True))
print(json.dumps({'code_review':ref(D/'code_review.json'),'manifest':ref(D/'manifest.json'),'checks':len(CHECKS),'negative':len(NEG),'actual_capacity':capacity},ensure_ascii=False))
