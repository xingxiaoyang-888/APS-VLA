"""Independent read-only canonical k64 seed23 source bridge audit. No submission."""
from pathlib import Path
from types import SimpleNamespace
import sys,os,json,hashlib,copy,ast,importlib.util,contextlib,io,traceback,time,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/k64_seed23_bridges_independent_20261020T1949/control_runtime_attempt01';A=R/'.local/k64_seed23_bridges_20261020T1949'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';INV_SHA='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
PUBLICATION='results/formal_main_v2/preflight/heartbeat_20261021T0349/k64_candidate_publication.json';PUB_SHA='1656f5c931545c0b0b2ae987202dbf1ae3281ccf2c71b900a30bf2f8a55f3949'
MAP_SHA='ec56fca197dcbb6de668761081852be973aba6ab61673edf4c961d29390973aa'
EXPECT={'spatial':{'control':'edab3f3917b57daf1867134bc8179a73673bfc4a1e61bfda5118d76fd64458f3','bridge':'678b6c57fbf6e188eced6d42bfa158862c1f185bced034027e535a4316804c87','total':42480,'failed':73,'selected':{'A':2500,'B':3500},'jobs':['3024716','3025205','3028522','3043399','3044479']},'object':{'control':'cf1058afd83073e0ef30c977e88c34f124f56adcfe9487b837ecaedaf6578767','bridge':'04c596f8b86569d7476f504fcf5519c205b0fc7eb2e0bd6de953fa47f5bc6735','total':52868,'failed':69,'selected':{'A':2500,'B':4500},'jobs':['3028468','3044017','3044844']}}
READS={};CHECKS=[];NEG=[];REPORTS=[]
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
def guard(event,args):
 if event.startswith(('subprocess.','socket.')) or event in ('os.system','os.posix_spawn','os.fork'):raise RuntimeError('audit forbids process/network/Slurm')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0])).absolute();mode=args[1];flags=args[2] or 0
  if p.suffix.lower() in {'.pt','.pth','.bin','.safetensors','.ckpt','.pkl','.pickle','.init','.pruned_init','.npz','.h5','.hdf5'} or any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts):raise RuntimeError('no weights/data/sealed access '+str(p))
  writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if writing and not p.is_relative_to(D):raise RuntimeError('private writes only '+str(p))
sys.addaudithook(guard)
def sha(b):return hashlib.sha256(b).hexdigest()
def check(ok,label):
 CHECKS.append({'name':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)
def read(path,pin=None):
 p=Path(path);p=p if p.is_absolute() else R/p;b=p.read_bytes();h=sha(b)
 check(pin is None or pin==h,'exact byte SHA '+str(p));check(str(p) not in READS or READS[str(p)]==h,'stable input '+str(p));READS[str(p)]=h;return b
def rd(path,pin=None):return json.loads(read(path,pin))
def write(path,val):
 p=D/path;p.parent.mkdir(parents=True,exist_ok=True);b=val if isinstance(val,bytes) else (json.dumps(val,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(b)}
def load(path,pin=None,name=None):
 p=Path(path);p=p if p.is_absolute() else R/p;b=read(p,pin);n=name or 'k64ind_'+p.stem+'_'+sha(str(p).encode())[:12];spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;exec(compile(b,str(p),'exec'),m.__dict__);return m
class Evidence:
 def __init__(self):self.project=self.root=R;self.files={};self.hashes=self.files;self.forbidden_paths=set()
 def path(self,n):
  p=Path(n);p=p if p.is_absolute() else R/p;check('..' not in p.parts and p.resolve()==p.absolute() and p.is_relative_to(R),'safe R evidence '+str(n));return p
 def watch(self,n):
  p=self.path(n);b=read(p);self.files[p.relative_to(R).as_posix()]=sha(b);return sha(b)
 def read(self,n):p=self.path(n);self.watch(p);return json.loads(p.read_bytes())
 def relative(self,n):return self.path(n).relative_to(R).as_posix()
 def unchanged(self):
  for n,pin in self.files.items():check(sha((R/n).read_bytes())==pin,'unchanged evidence '+n)
def neg(label,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,AssertionError) as e:NEG.append({'name':label,'type':type(e).__name__,'message':str(e),'passed':True});return
 raise AssertionError(label+' accepted invalid input')
def capture(path,fn):
 buff=io.StringIO()
 with contextlib.redirect_stdout(buff),contextlib.redirect_stderr(buff):result=fn()
 write(path,buff.getvalue().encode());return result


GATEWAY_CAN='scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py'
GATEWAY_CAND='.local/collect_terminal_20261020T1949/development_gateway/revision01/gateway.py'
GW_SHA='873d0145f8d3ed51e916f39e1e36cb0251d10777a6f98429621f526d37a2c7bb'
BASE='scripts/ops/formal_action_deployment_posttraining_v1/gateway.py';BASE_SHA='4a11a62e817cd96523cd8f06aa0c3c71e12208f1b3a6b487799160915e59ec83'
PRE='scripts/ops/formal_action_deployment_v1/'
def sem(x):
 if not hasattr(x,'co_code'):return x
 return(x.co_argcount,x.co_posonlyargcount,x.co_kwonlyargcount,x.co_nlocals,x.co_stacksize,x.co_flags,x.co_code,x.co_names,x.co_varnames,x.co_freevars,x.co_cellvars,tuple(sem(t) for t in x.co_consts),x.co_exceptiontable)
def main():
 t=time.monotonic();prior=rd('.local/k64_seed23_bridges_independent_20261020T1949/attempt04/independent_index.json','0b7b0e4c04a402582b795c2d1162e6a02875ccb08a5ea813a7afa2e93280a524');check(prior['status']=='passed_CPU_source_and_metadata_review','prior actual source CPU review')
 rootpub=rd('results/formal_main_v2/preflight/heartbeat_20261021T0349/k64_static_plan_publication.json','2d4d5c57f0c47bf7ab98c4984f39be2e54e6a939a75de9b084cea25fdb3ed724');mapping=rd(A/'static_plan_publication_candidate.json','d447aebff71f88bea0f568def97a5106936a7c107062062e7386758f8d6a30ca')
 for pair in mapping['pairs']:
  for row in pair['files']:
   raw=read(row['path'],row['sha256']);check(raw==read(row['source'],row['sha256']) and len(raw)==row['bytes'],'static exact published file '+row['path'])
   if row['publish_P']:read(P/row['path'],row['sha256'])
 gpath=GATEWAY_CAN if (R/GATEWAY_CAN).exists() else GATEWAY_CAND
 g=load(gpath,GW_SHA);src=read(gpath,GW_SHA).decode();old=read(BASE,BASE_SHA).decode()
 defs=lambda s:{n.name:n for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};aa=defs(old);bb=defs(src)
 for name in ['Gateway','NativeIO','submission_argv','parse_ack','registered_comment','check_observed_identity','corroborate_new_job','reconcile_submission','error_capture','Evidence','main','intent_sha']:
  check(ast.dump(aa[name],include_attributes=False)==ast.dump(bb[name],include_attributes=False),'inherited AST exact '+name)
 mapped=ast.parse(ast.unparse(bb['capacity_gate']).replace('completed_training_development_gate','completed_training_collect_gate')).body[0];check(ast.dump(mapped)==ast.dump(aa['capacity_gate']),'full common capacity exact except completed helper name')
 closure=g.source_files(R);check(len(closure)==15,'full union source closure15');write('source_closure.json',closure)
 for n,pin in closure.items():read(n,pin)
 with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
  fcntl.flock(lock,fcntl.LOCK_SH);raw=(R/g.STATE).read_bytes();fcntl.flock(lock,fcntl.LOCK_UN)
 state=json.loads(raw);state_ref=write('state_read_only_snapshot.json',raw)
 snap=rd('.local/collect_terminal_20261020T1949/development_gateway/CPU_attempt01/actual_registered_scheduler_snapshot.json','42b157918905a7749fd58c6f226481f895e77b0df9932748f3a6b7af7beb6030')
 check(set(snap['rows'])=={str(j['job_id']) for j in state['registered_jobs']},'immutable scheduler exact registered IDs, no requery')
 controller=load(g.CONTROLLER,g.CONTROLLER_SHA);plans={};auths={};typed={};runtime=load(PRE+'runtime_scope.py','6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53');contractmod=load(PRE+'contract.py','efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19');newwrap=load(P/(PRE+'wrapper.py'),'d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33')
 for suite,q in g.SCOPED_DEVELOPMENT_PLANS.items():
  short=suite.removeprefix('libero_');pair=next(v for v in mapping['pairs'] if v['suite']==suite);plan=rd(q['path'],q['sha256']);science=rd(q['scientific_plan']['path'],q['scientific_plan']['sha256']);check(science==rd('.local/k64_seed23_bridges_independent_20261020T1949/attempt04/'+short+'/canonical_scientific_plan.json'),'canonical science matches independent rebuild '+suite)
  c=load(q['control']['path'],q['control']['sha256']);args=rd(Path(q['path']).parent/'plan_arguments.json');actionref=plan['invocation']['action_execution_contract'];action=rd(actionref['path'],actionref['sha256']);read(P/actionref['path'],actionref['sha256'])
  contractmod.validate_effective(science,plan,scientific_plan_ref=q['scientific_plan'],execution_contract_ref=actionref,execution_contract=action)
  check(runtime.make_contract(project_root=R,source_root=S,suite=suite,stage='development')==action['runtime_contract']==runtime.make_contract(project_root=P,source_root=S,suite=suite,stage='development'),'actual R/P runtime context exact '+suite)
  for n,pin in plan['invocation']['support_files'].items():read(P/n,pin);read(R/n,pin)
  for n,pin in plan['invocation']['watched_files'].items():read(n,pin)
  for n,pin in action['files'].items():read(P/n,pin);read(R/n,pin)
  fixture={'controller_job_id':'3034538','controller_activation':g.ACTIVATION,'plan':{'path':q['path'],'sha256':q['sha256']},'scientific_plan':q['scientific_plan'],'plan_arguments':args,'root_reservation':{'path':'.local/CPU_FIXTURE_NOT_RESERVATION.json','sha256':'f'*64},'runtime_readiness':None}
  prepared={**plan['invocation'],'registered_utc':'2026-10-20T19:49:00+00:00','plan_sha256':plan['plan_sha256'],'runtime_readiness':None};fixture['prepared_invocation']=write(short+'/CPU_prepared_fixture_not_authorized.json',prepared)
  ge=g.Evidence(R);frozen=g.FrozenPlan(R,fixture,ge,plan,science,prepared).prepare(state);check(frozen['plan']==plan and frozen['invocation']==prepared and frozen['prefix']=={},'actual FrozenPlan exact source-bound reconstruction '+suite)
  neg(suite+' real P action wrapper rejects absent root readiness',lambda:newwrap.verify(plan['invocation'],project=P))
  rv=c.reviewer_module(Evidence());oldrv=load(c.REVIEWER,c.ORIGINAL[c.REVIEWER])
  for name in ['validate_envelope','verify_pull','actual_runtime','trajectory_validator','science_context','validate_transition_after','checked_asset_identities']:check(sem(getattr(rv,name).__code__)==sem(getattr(oldrv,name).__code__),'original terminal primitive unchanged '+suite+'/'+name)
  se=rv.Evidence(R);reviewold=rv.load(se,rv.OLD_REVIEW,rv.PINNED[rv.OLD_REVIEW]);helper,scheduler=c.control_modules(se);iv=plan['invocation'];job={k:iv[k] for k in ['stage_key','suite','method_ids','run_root','source_sha256','adapter_sha256','execution_manifest_sha256']};job.update(mode='development',source_provenance_sha256=scheduler.signature(iv['source_provenance']),job_id='CPU_ONLY_NOT_SLURM',status='NOT_RUN',gpus=0)
  def no_downstream(*a,**kw):raise RuntimeError('unexpected prior downstream read')
  result,_=rv.science_context(se,reviewold,scheduler,helper,job,iv,state['registered_jobs'],science,action,no_downstream);check(result['source_provenance']==science['invocation']['source_provenance'],'real terminal source chain reconstructs same proof '+suite);se.unchanged();ge.unchanged()
  for label,delta in [('final',{'stage':'final'}),('collect',{'stage':'collect'}),('Goal',{'suite':'libero_goal'}),('seed17',{'method_ids':['A64_seed17','B64_seed17']}),('onlyA',{'method_ids':['A64_seed23']}),('resume',{'resume':True}),('prior',{'prior_job_ids':['1']}),('prefix',{'stop_after':1})]:
   x=copy.deepcopy(iv);x.update(delta);neg(suite+' exact gateway '+label,lambda x=x:g._exact_development_control(R,x))
  for field in ['path','sha256']:
   x=copy.deepcopy(fixture);x['plan'][field]='../outside.json' if field=='path' else '0'*64;neg(suite+' immutable authorization '+field,lambda x=x:g._exact_development_authorization(x))
  plans[suite]=plan;auths[suite]=fixture
  proof=write(short+'/plan_metadata_evidence.json',{'kind':'independent_real_metadata_chain_only','gateway_entry':{'path':gpath,'sha256':GW_SHA},'canonical_science':q['scientific_plan'],'effective':fixture['plan'],'terminal_source_evidence':se.files,'FrozenPlan_evidence':ge.hashes,'fixture_not_runtime_authorization':fixture['prepared_invocation'],'actual_GPU_runtime_chain_verified':False})
  typed[suite]=write(short+'/independent_plan_review.json',{'schema':'formal_main_v2','kind':'formal_action_plan_independent_CPU_review','status':'passed','reviewed_by':'independent','suite':suite,'stage':'development','allowed_stages':['development'],'execution_version':'formal-downstream-action-v1','method_ids':c.METHODS,'methods':c.METHODS,'scientific_plan':q['scientific_plan'],'effective_plan':fixture['plan'],'action_execution_contract':actionref,'plan_sha256':plan['plan_sha256'],'runtime_sources':action['files'],'explicit_source_control':c.descriptor(),'production_chain_complete':True,'production_chain_scope':'canonical source / original planner / actual P metadata wrapper / action contract / original terminal consumer source reconstruction only','actual_GPU_runtime_chain_verified':False,'real_GPU_development':False,'scientific_trials_added':0,'scientific_settings_changed':False,'final_evaluation_enabled':False,'prior_job_ids':[],'resume':False,'detailed_evidence':proof,'source_independent_index':{'path':'.local/k64_seed23_bridges_independent_20261020T1949/attempt04/independent_index.json','sha256':'0b7b0e4c04a402582b795c2d1162e6a02875ccb08a5ea813a7afa2e93280a524'},'blockers':[]})
 # All normal-exit gates are measured without querying Slurm or changing owner/state.
 cpus=[str(j['job_id']) for j in state['registered_jobs'] if type(j.get('gpus')) is int and j['gpus']==0 and snap['rows'][str(j['job_id'])]['gpus']==0]
 normal={s:g.completed_training_development_gate(controller,state,snap,auths[s],p,cpus) for s,p in plans.items()};write('normal_exit_lease_proofs.json',normal)
 def fixture(suite):
  st=copy.deepcopy(state);st['autonomous_training_v1']['reserved_GPU_slots']=1;st['autonomous_training_v1']['reservation_root_record']=auths[suite]['root_reservation'];return st,copy.deepcopy(snap)
 for suite,p in plans.items():
  st,ss=fixture(suite);caps,_,proj=g.capacity_gate(controller,st,ss,auths[suite],p);check(not caps['findings'] and not caps['unknown'] and len(caps['occupied'])<8,'actual recorded all-mode capacity with synthetic own reservation '+suite)
 suite='libero_spatial';p=plans[suite];auth=auths[suite]
 def fill(n):
  st,ss=fixture(suite);active=len(controller.capacity(st['registered_jobs'],ss,'3034538')['occupied']);check(n>=active,'fixture does not remove actual allocations')
  for i in range(n-active):
   jid=str(9900000+i);st['registered_jobs'].append(dict(job_id=jid,name='CPU_FIXTURE_ONLY',experiment='formal_main_v2',mode='engineering',suite='libero_10',method_ids=[],gpus=1,status='RUNNING',stage_key='CPU'+jid,invocation='.local/CPU'+jid+'.json'));ss['rows'][jid]=dict(job_id=jid,status='RUNNING',exit_code='0:0',gpus=1,elapsed_seconds=0,allocation='gres/gpu=1',node='CPU',scheduler_name='CPU_FIXTURE_ONLY',scheduler_comment='');ss['queue'][jid]=dict(status='RUNNING',comment='')
  st['autonomous_training_v1']['occupied_job_ids']=controller.capacity(st['registered_jobs'],ss,'3034538')['occupied'];return st,ss
 st,ss=fill(7);caps,_,_=g.capacity_gate(controller,st,ss,auth,p);check(len(caps['occupied'])==7,'seven occupied allows one exact slot')
 st,ss=fill(8);neg('eight occupied rejects new request',lambda:g.capacity_gate(controller,st,ss,auth,p))
 def mutate(name,fn):
  st,ss=fixture(suite);aa=copy.deepcopy(auth);pp=copy.deepcopy(p);fn(st,ss,aa,pp);neg(name,lambda:g.capacity_gate(controller,st,ss,aa,pp))
 mutate('unknown submission pending',lambda st,ss,a,p:st.update(pending_submission={'unknown':True}))
 mutate('blocked training pair',lambda st,ss,a,p:st['autonomous_training_v1'].update(blocked_pairs={'failure':{}}))
 mutate('duplicate registry',lambda st,ss,a,p:st['registered_jobs'].append(copy.deepcopy(st['registered_jobs'][0])))
 mutate('unknown controller',lambda st,ss,a,p:ss['rows']['3034538'].update(status='UNKNOWN'))
 mutate('controller TIMEOUT',lambda st,ss,a,p:ss['rows']['3034538'].update(status='TIMEOUT'))
 mutate('incomplete root72',lambda st,ss,a,p:st['formal_main_progress'].update(root_and_independent_completed_arms=70))
 mutate('wrong updates',lambda st,ss,a,p:st['formal_main_progress'].update(root_and_independent_reviewed_arm_updates=359999))
 mutate('test opened',lambda st,ss,a,p:st['formal_main_progress'].update(test_opened=True))
 mutate('unconfirmed exit',lambda st,ss,a,p:st['autonomous_training_v1'].pop('root_confirmed_normal_training_exit'))
 mutate('no slot reservation',lambda st,ss,a,p:st['autonomous_training_v1'].update(reserved_GPU_slots=0))
 mutate('foreign reservation',lambda st,ss,a,p:st['autonomous_training_v1'].update(reservation_root_record={'path':'elsewhere','sha256':'0'*64}))
 mutate('root submission hold',lambda st,ss,a,p:st['autonomous_training_v1'].update(root_submission_hold={'reason':'hold'}))
 mutate('wrong seed method scope',lambda st,ss,a,p:p['invocation'].update(method_ids=['A64_seed41','B64_seed41']))
 mutate('published plan content changed',lambda st,ss,a,p:p.update(extra='invalid'))
 inventory=rd(INV,INV_SHA)
 for root in (R,S):
  for n,h in inventory['files'].items():check(sha((root/n).read_bytes())==h,'173 exact after supplemental '+str(root/n))
 writes={'reads':write('read_inputs.json',READS),'checks':write('checks.json',CHECKS),'expected_rejections':write('expected_rejections.json',NEG)}
 report={'schema':'formal_main_v2','kind':'formal_downstream_server_gateway_independent_CPU_review','status':'passed_CPU_review','reviewed_by':'independent','files':closure,'entrypoint':{'path':gpath,'sha256':GW_SHA},'canonical_source_verified':gpath==GATEWAY_CAN,'pair_plan_reviews':typed,'checks':len(CHECKS),'negative_cases':len(NEG),'preserved_original_AST':['Gateway','NativeIO','reconcile_submission','submission_argv','parse_ack','intent_sha'],'new_controller_restart':False,'only_two_exact_development_pairs':True,'actual_GPU_runtime_chain_verified':False,'root_authorization_created':False,'state_writes':False,'new_GPU_runs':0,'scientific_trials_added':0,'all_modes_maximum_GPU_jobs':8,'root_runtime_post_review_required':True,'observed_scheduler_source':{'path':'.local/collect_terminal_20261020T1949/development_gateway/CPU_attempt01/actual_registered_scheduler_snapshot.json','sha256':'42b157918905a7749fd58c6f226481f895e77b0df9932748f3a6b7af7beb6030'},'state_read_only_snapshot':state_ref,'evidence':writes,'blockers':[],'wall_seconds':time.monotonic()-t}
 print(json.dumps(write('independent_gateway_CPU_review.json',report),sort_keys=True));print(json.dumps({'plan_reviews':typed,'checks':len(CHECKS),'negative_cases':len(NEG)},sort_keys=True))
try:main()
except BaseException as e:write('failure.json',{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc(),'checks':CHECKS,'expected_rejections':NEG,'read_inputs':READS});raise
