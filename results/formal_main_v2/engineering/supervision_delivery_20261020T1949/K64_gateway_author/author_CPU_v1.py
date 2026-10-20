"""Bounded author CPU verification; no Gateway.run, publish, submit, or state mutation."""
from pathlib import Path
from types import SimpleNamespace
import ast,copy,fcntl,hashlib,importlib.util,json,sys,time,traceback
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/collect_terminal_20261020T1949/development_gateway';V=D/'revision01';O=D/'CPU_attempt01'
START=time.monotonic();CHECKS=[];NEG=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def record(name,value):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(value,f,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def ck(name,ok):
 if not ok:raise AssertionError(name)
 CHECKS.append(name)
def reject(name,fn):
 try:fn()
 except (ValueError,BlockingIOError) as e:NEG.append({'name':name,'error_type':type(e).__name__,'error':str(e)});return
 raise AssertionError('unexpected acceptance '+name)
def module(path,pin,name):
 ck('pin '+str(path),sha(path)==pin);spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
def main():
 O.mkdir(exist_ok=False)
 deriv=json.loads((V/'source_derivation.json').read_text());pin=deriv['new_source']['sha256'];m=module(V/'gateway.py',pin,'bounded_dev_gateway_author_CPU')
 ck('canonical inputs pin',sha(D/'canonical_inputs.json')==deriv['canonical_inputs']['sha256'])
 oldsrc=(R/deriv['baseline']['path']).read_text();newsrc=(V/'gateway.py').read_text();old={x.name:x for x in ast.parse(oldsrc).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))};new={x.name:x for x in ast.parse(newsrc).body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
 for name in ('Gateway','NativeIO','submission_argv','parse_ack','registered_comment','check_observed_identity','corroborate_new_job','Evidence','main'):
  ck('exact unchanged AST '+name,ast.dump(old[name])==ast.dump(new[name]))
 # Reverse only the helper name in the inherited common capacity function.
 projected=ast.parse(ast.unparse(new['capacity_gate']).replace('completed_training_development_gate','completed_training_collect_gate')).body[0]
 ck('common capacity unchanged after name mapping',ast.dump(projected)==ast.dump(old['capacity_gate']))
 closure=m.source_files(R);record('source_closure.json',closure)
 ck('both exact pair controls in closure',all(closure[x['control']['path']]==x['control']['sha256'] for x in m.SCOPED_DEVELOPMENT_PLANS.values()))
 snapshots={};plans={};auths={};proofs={};frozen={}
 for suite,q in m.SCOPED_DEVELOPMENT_PLANS.items():
  plan=json.loads((R/q['path']).read_text());science=json.loads((R/q['scientific_plan']['path']).read_text());ck('published plan SHA '+suite,sha(R/q['path'])==q['sha256'] and sha(R/q['scientific_plan']['path'])==q['scientific_plan']['sha256'])
  control=module(R/q['control']['path'],q['control']['sha256'],'author_bridge_'+suite)
  args=dict(stage='development',source_inventory=m.INVENTORY,execution_manifest=control.MANIFEST,output_relative=None,freeze_directory=None,profile_panel=None,prior_review=None,collection_review=None,repair_record=None,resume=False,stop_after=None)
  a=dict(controller_job_id='3034538',controller_activation=m.ACTIVATION,plan={k:q[k] for k in ('path','sha256')},scientific_plan=q['scientific_plan'],plan_arguments=args,root_reservation={'path':'.local/CPU_MEMORY_ONLY_NOT_AUTHORIZATION.json','sha256':'f'*64},runtime_readiness={'path':'.local/CPU_NOT_A_RUNTIME_READINESS.json','sha256':'0'*64})
  ck('exact plan/source scope '+suite,m._exact_development_plan(R,a,plan,science).descriptor()==control.descriptor())
  sp=R/f'.local/k64_seed23_bridges_20261020T1949/{suite.removeprefix("libero_")}/static_candidate/state_read_only_snapshot.json';ck('bridge immutable state '+suite,sha(sp)=='ac4dfa7989364ffad22799ec789442edad9164d0511f41deee9ade221292bb2f')
  snapshot=json.loads(sp.read_text());snapshots[suite]={'path':sp.relative_to(R).as_posix(),'sha256':sha(sp)}
  prepared={**plan['invocation'],'registered_utc':'2026-10-20T19:49:00+00:00','plan_sha256':plan['plan_sha256'],'runtime_readiness':a['runtime_readiness']}
  a['prepared_invocation']=record(suite+'/CPU_fixture_prepared.json',prepared)
  e=m.Evidence(R);bundle=m.FrozenPlan(R,a,e,plan,science,prepared).prepare(snapshot)
  ck('original FrozenPlan same-bridge reconstructs '+suite,bundle['plan']==plan and bundle['invocation']==prepared and bundle['prefix']=={})
  frozen[suite]=record(suite+'/FrozenPlan_CPU_reconstruction.json',{'status':'passed_CPU_fixture_only','scientific_plan':q['scientific_plan'],'effective_plan':a['plan'],'explicit_source_control':control.descriptor(),'read_evidence_sha256':e.hashes,'prepared_fixture':a['prepared_invocation'],'immutable_input_state':snapshots[suite],'actual_runtime_readiness':False,'root_authorization':False,'GPU_calls':0})
  plans[suite]=plan;auths[suite]=a
  for key,bad in [('stage','collect'),('stage','final'),('suite','libero_goal'),('method_ids',['A64_seed17','B64_seed17']),('method_ids',['A64_seed23']),('resume',True),('prior_job_ids',['1']),('stop_after',50)]:
   inv=copy.deepcopy(plan['invocation']);inv[key]=bad;reject(suite+' invocation '+key+str(bad),lambda inv=inv:m._exact_development_control(R,inv))
  bad=copy.deepcopy(a);bad['scientific_plan']=auths.get('libero_spatial',a)['plan'];reject(suite+' scientific ref mismatch',lambda:m._exact_development_authorization(bad))
  for field in ('path','sha256'):
   bad=copy.deepcopy(a);bad['plan'][field]='../forbidden.json' if field=='path' else '0'*64;reject(suite+' exact plan ref '+field,lambda bad=bad:m._exact_development_authorization(bad))
  bad=copy.deepcopy(plan);bad['invocation']['source_provenance']['explicit_source_control']['failed_job_id']='0';reject(suite+' source failure identity mutation',lambda bad=bad:m._exact_development_control(R,bad['invocation']))
 # Fresh registered-only observation. Never claim the immutable planning snapshot is a current dispatch permit.
 c=module(R/m.CONTROLLER,m.CONTROLLER_SHA,'bounded_dev_gateway_controller_CPU')
 statefile=R/m.STATE
 with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
  fcntl.flock(lock,fcntl.LOCK_SH)
  try:
   raw=statefile.read_bytes();state=json.loads(raw);snap=c.Slurm(timeout=45).observe(state['registered_jobs'])
   cpus=[str(j['job_id']) for j in state['registered_jobs'] if type(j.get('gpus')) is int and j['gpus']==0 and snap['rows'][str(j['job_id'])]['gpus']==0]
   for suite,p in plans.items():proofs[suite]=m.completed_training_development_gate(c,state,snap,auths[suite],p,cpus)
   ck('real normal-exit/owner/lease and source gate for both plans',all(x['lifecycle_lease_available_measured'] and x['root_arms']==72 for x in proofs.values()))
   ck('state exact bytes unchanged under shared lock',statefile.read_bytes()==raw)
   record('actual_state_read_only_snapshot.json',state);record('actual_registered_scheduler_snapshot.json',snap);record('actual_normal_exit_proofs.json',proofs)
  finally:fcntl.flock(lock,fcntl.LOCK_UN)
 cap=c.capacity(state['registered_jobs'],snap,'3034538');ck('actual registered capacity consistent',not cap['unknown'] and not cap['findings'])
 record('actual_capacity.json',cap)
 # Explicit in-memory reservation fixtures only; no authorization/reservation file exists.
 def fixture(suite):
  st=copy.deepcopy(state);st['autonomous_training_v1']['reserved_GPU_slots']=1;st['autonomous_training_v1']['reservation_root_record']=auths[suite]['root_reservation'];return st,copy.deepcopy(snap)
 for suite,p in plans.items():
  st,ss=fixture(suite);caps,_,_=m.capacity_gate(c,st,ss,auths[suite],p);ck('original all-mode capacity with memory reservation '+suite,len(caps['occupied'])<8)
 suite='libero_spatial';p=plans[suite];a=auths[suite]
 def fill(n):
  st,ss=fixture(suite);active=len(c.capacity(st['registered_jobs'],ss,'3034538')['occupied']);ck('fixture never removes actual jobs '+str(n),n>=active)
  for i in range(n-active):
   jid=str(9900000+i);st['registered_jobs'].append(dict(job_id=jid,name='CPU_FIXTURE_ONLY',experiment='formal_main_v2',mode='engineering',suite='libero_10',method_ids=[],gpus=1,status='RUNNING',stage_key='CPU'+jid,invocation='.local/CPU'+jid+'.json'))
   ss['rows'][jid]=dict(job_id=jid,status='RUNNING',exit_code='0:0',gpus=1,elapsed_seconds=0,allocation='gres/gpu=1',node='CPU',scheduler_name='CPU_FIXTURE_ONLY',scheduler_comment='');ss['queue'][jid]=dict(status='RUNNING',comment='')
  st['autonomous_training_v1']['occupied_job_ids']=c.capacity(st['registered_jobs'],ss,'3034538')['occupied'];return st,ss
 st,ss=fill(7);caps,_,_=m.capacity_gate(c,st,ss,a,p);ck('parallel seven other GPU jobs allowed',len(caps['occupied'])==7)
 st,ss=fill(8);reject('eight occupied slots rejected',lambda:m.capacity_gate(c,st,ss,a,p))
 def mutate(name,fn):
  st,ss=fixture(suite);aa=copy.deepcopy(a);pp=copy.deepcopy(p);fn(st,ss,aa,pp);reject(name,lambda:m.capacity_gate(c,st,ss,aa,pp))
 mutate('pending unknown rejected',lambda st,ss,a,p:st.update(pending_submission={'uncertain':True}))
 mutate('blocked pairs rejected',lambda st,ss,a,p:st['autonomous_training_v1'].update(blocked_pairs={'failure':{}}))
 mutate('duplicate registry rejected',lambda st,ss,a,p:st['registered_jobs'].append(copy.deepcopy(st['registered_jobs'][0])))
 mutate('unknown controller rejected',lambda st,ss,a,p:ss['rows']['3034538'].update(status='UNKNOWN'))
 mutate('incomplete root72 rejected',lambda st,ss,a,p:st['formal_main_progress'].update(root_and_independent_completed_arms=70))
 mutate('final opened rejected',lambda st,ss,a,p:st['formal_main_progress'].update(test_opened=True))
 mutate('unconfirmed exit rejected',lambda st,ss,a,p:st['autonomous_training_v1'].pop('root_confirmed_normal_training_exit'))
 mutate('wrong source scope rejected',lambda st,ss,a,p:p['invocation'].update(method_ids=['A128_seed23','B128_seed23']))
 mutate('changed published plan rejected',lambda st,ss,a,p:p.update(extra='CPU'))
 # Same source exact whitespace-independent old definitions; no mutations to originals.
 ck('old collect gateway unchanged',sha(R/deriv['baseline']['path'])==deriv['baseline']['sha256'])
 ck('173 source files R/S intact',all(sha(root/rel)==h for root in (R,m.S) for rel,h in json.loads((R/m.INVENTORY).read_text())['files'].items()))
 result={'schema':'formal_main_v2','kind':'bounded_completed_training_k64s23_development_gateway_author_CPU','status':'passed_CPU_checks','source':deriv['new_source'],'expected_canonical_path':deriv['expected_canonical_path'],'checks':CHECKS,'negative_cases':NEG,'passed':len(CHECKS),'negative_count':len(NEG),'source_files':closure,'scope':m.SCOPED_DEVELOPMENT_PLANS,'FrozenPlan_reconstructions':frozen,'real_registered_capacity':cap,'real_owner_lease_checked':True,'state_written':False,'Slurm_submitted':0,'runtime_GPU_calls':0,'actual_runtime_readiness':False,'root_authorization_created':False,'scientific_trials_added':0,'limits':'CPU source and exact immutable-plan reconstruction only; prepared and reservation fields are labeled in-memory/private fixtures. Root must use fresh state and real canonical runtime readiness/authorization/reservation before any GPU dispatch. All original lifecycle/NativeIO/ACK/CAS code preserved.','elapsed_wall_seconds':time.monotonic()-START}
 print(json.dumps({'report':record('CPU_report.json',result),'passed':len(CHECKS),'negative_count':len(NEG)}))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  if O.exists():record('failure.json',{'error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'checks':CHECKS,'negative_cases':NEG,'elapsed_wall_seconds':time.monotonic()-START})
  raise
