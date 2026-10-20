from pathlib import Path
from types import SimpleNamespace
import ast,copy,fcntl,hashlib,importlib.util,json,sys,time,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/completed_training_gateway_20261020T1825';V=D/'revision02';O=D/'CPU_attempt02';O.mkdir(exist_ok=False);start=time.process_time();checks=[];neg=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wr(n,v):p=O/n;p.write_text(json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False)+'\n');return dict(path=str(p.relative_to(R)),sha256=h(p))
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def reject(n,fn):
 try:fn()
 except (ValueError,BlockingIOError) as e:neg.append(dict(name=n,error_type=type(e).__name__,error=str(e)));return
 raise AssertionError('unexpected acceptance: '+n)
def main():
 pin='4a11a62e817cd96523cd8f06aa0c3c71e12208f1b3a6b487799160915e59ec83';ck('candidate pin',h(V/'gateway.py')==pin);sp=importlib.util.spec_from_file_location('completed_gateway_author_CPU',V/'gateway.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
 a0=ast.parse((D/'inputs/original_gateway.py').read_text());a1=ast.parse((V/'gateway.py').read_text());old={n.name:n for n in a0.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};new={n.name:n for n in a1.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};ck('only one added helper',set(new)-set(old)=={'completed_training_collect_gate'} and not set(old)-set(new));ck('all original classes and other functions exact AST',all(ast.dump(old[k],include_attributes=False)==ast.dump(new[k],include_attributes=False) for k in old if k!='capacity_gate'))
 projected=copy.deepcopy(new['capacity_gate']);candidates=[(i,x) for i,x in enumerate(projected.body) if isinstance(x,ast.If) and any(isinstance(t,ast.Call) and isinstance(t.func,ast.Name) and t.func.id=='completed_training_collect_gate' for t in ast.walk(x))];ck('one completed branch only',len(candidates)==1)
 i,_=candidates[0];original_gate="require(a['controller_job_id'] in cpus and snap['rows'][a['controller_job_id']]['status']=='RUNNING','controller not confirmed RUNNING CPU0')";projected.body[i]=ast.parse(original_gate).body[0];ck('capacity original projection exact',ast.dump(projected,include_attributes=False)==ast.dump(old['capacity_gate'],include_attributes=False))
 state=json.loads((D/'inputs/author_observed_state.json').read_text());obs=json.loads((D/'inputs/root_normal_exit_observation.json').read_text());snap=copy.deepcopy(obs['observation']);ctl=state['autonomous_training_v1'];jid='3034538';controller=SimpleNamespace(TERMINAL={'COMPLETED','FAILED','TIMEOUT','PREEMPTED','CANCELLED','OUT_OF_MEMORY','NODE_FAIL'})
 # All registered allocation records already existed at the author's observed
 # snapshot. For direct helper negatives only the exact controller and train
 # terminal fields are used; this is not a live scheduler capacity claim.
 for j in state['registered_jobs']:
  jn=str(j['job_id'])
  if jn not in snap['rows']:snap['rows'][jn]=dict(status=j['status'],exit_code=j.get('exit_code','0:0'),gpus=j.get('gpus',1),elapsed_seconds=j.get('elapsed_seconds',0),node=j.get('node',''),job_id=jn)
 # Remap only absent exact plan metadata into its immutable author candidate.
 # This is scoped to this private module instance, never baseline/global source.
 base=m.Evidence;private={}
 for suite,label in [('libero_spatial','Spatial'),('libero_object','Object')]:
  rel=m.COMPLETED_COLLECTION_PLANS[suite]['path'];p=R/f'.local/spatial_object_collect_20261020T1825/{label}/plan_v1/effective_plan.json';private[rel]=p;ck('exact candidate plan '+suite,h(p)==m.COMPLETED_COLLECTION_PLANS[suite]['sha256'])
 class PlanEvidence(base):
  def watch(self,rel,pin=None):
   if rel not in private or (R/rel).exists():return super().watch(rel,pin)
   got=h(private[rel]);m.require(pin is None or pin==got,'candidate plan SHA differs');m.require(rel not in self.hashes or self.hashes[rel]==got,'candidate drift');self.hashes[rel]=got;return got
  def read(self,rel,pin=None):
   if rel not in private or (R/rel).exists():return super().read(rel,pin)
   self.watch(rel,pin);v=json.loads(private[rel].read_bytes());self.watch(rel,self.hashes[rel]);return v
 m.Evidence=PlanEvidence;reports={};lease=m.COMPLETED_WORK/'controller.lease.lock';lease_before=lease.stat()
 for suite in ('libero_spatial','libero_object'):
  q=m.COMPLETED_COLLECTION_PLANS[suite];plan=json.loads(private[q['path']].read_text());auth=dict(controller_job_id=jid,plan={k:q[k] for k in ('path','sha256')});before=copy.deepcopy(state);proof=m.completed_training_collect_gate(controller,state,snap,auth,plan,[jid]);ck('completed exact collect accepted '+suite,proof['lifecycle_lease_available_measured'] and state==before);reports[suite]=proof
 q=m.COMPLETED_COLLECTION_PLANS['libero_spatial'];plan=json.loads(private[q['path']].read_text());auth=dict(controller_job_id=jid,plan={k:q[k] for k in ('path','sha256')})
 # A completed training controller does not require all GPU work to be idle.
 # These are explicitly in-memory nontraining fixtures; the unchanged common
 # capacity gate, independently audited, still enforces its all-mode8 limit.
 for n in (1,7):
  st=copy.deepcopy(state);ss=copy.deepcopy(snap);active=[]
  for i in range(n):
   jn=str(99000000+i);active.append(jn);st['registered_jobs'].append(dict(job_id=jn,experiment='formal_main_v2',mode='engineering',gpus=1,status='RUNNING'));ss['rows'][jn]=dict(job_id=jn,status='RUNNING',exit_code='0:0',gpus=1);ss['queue'][jn]=dict(status='RUNNING')
  st['autonomous_training_v1']['occupied_job_ids']=active
  pr=m.completed_training_collect_gate(controller,st,ss,auth,plan,[jid]);ck('parallel nontraining jobs allowed '+str(n),pr['lifecycle_lease_available_measured'])

 for field,bad in [('stage','development'),('suite','libero_goal'),('stage','full')]:
  p=copy.deepcopy(plan);p['invocation'][field]=bad;reject('scope '+field+' '+bad,lambda p=p:m.completed_training_collect_gate(controller,state,snap,auth,p,[jid]))
 p=copy.deepcopy(plan);p['plan_sha256']='0'*64;reject('exact plan changed',lambda:m.completed_training_collect_gate(controller,state,snap,auth,p,[jid]))
 for status,exitcode in [('FAILED','1:0'),('TIMEOUT','0:0'),('RUNNING','0:0'),('COMPLETED','1:0'),('UNKNOWN','0:0')]:
  ss=copy.deepcopy(snap);ss['rows'][jid].update(status=status,exit_code=exitcode);reject('abnormal controller '+status+exitcode,lambda ss=ss:m.completed_training_collect_gate(controller,state,ss,auth,plan,[jid]))
 for location,key,bad in [('formal_main_progress','root_and_independent_completed_arms',70),('formal_main_progress','root_and_independent_reviewed_arm_updates',359999),('formal_main_progress','global_release_created',True),('autonomous_training_v1','owner_id','different'),('autonomous_training_v1','blocked_pairs',{'old_failure':{}}),('autonomous_training_v1','last_result',{'status':'failed'})]:
  st=copy.deepcopy(state);st[location][key]=bad;reject('state '+key,lambda st=st:m.completed_training_collect_gate(controller,st,snap,auth,plan,[jid]))
 st=copy.deepcopy(state);st['pending_submission']={'uncertain':True};reject('pending unknown',lambda:m.completed_training_collect_gate(controller,st,snap,auth,plan,[jid]))
 st=copy.deepcopy(state);st['autonomous_training_v1']['completed_pairs'].pop(next(iter(st['autonomous_training_v1']['completed_pairs'])));reject('missing36pair',lambda:m.completed_training_collect_gate(controller,st,snap,auth,plan,[jid]))
 st=copy.deepcopy(state);next(iter(st['autonomous_training_v1']['completed_pairs'].values()))['completed_by_arm']['A']=4999;reject('incomplete arm',lambda:m.completed_training_collect_gate(controller,st,snap,auth,plan,[jid]))
 st=copy.deepcopy(state);st['autonomous_training_v1']['root_confirmed_normal_training_exit']['lease_released']=False;reject('root exit unconfirmed lease',lambda:m.completed_training_collect_gate(controller,st,snap,auth,plan,[jid]))
 # Existing inode only: nonblocking flock never creates/rebinds the lifecycle lock.
 with lease.open('rb') as held:
  fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:reject('actual held lifecycle lease',lambda:m.completed_training_collect_gate(controller,state,snap,auth,plan,[jid]))
  finally:fcntl.flock(held,fcntl.LOCK_UN)
 ck('lifecycle lock inode retained',(lease.stat().st_dev,lease.stat().st_ino)==(lease_before.st_dev,lease_before.st_ino));m.Evidence=base
 # Assert the unchanged RUNNING branch never calls the added helper. A tiny
 # ordinary registry fixture exercises original capacity/projection without I/O.
 code=ast.Module(body=[new['capacity_gate']],type_ignores=[]);calls=[]
 def forbidden(*args):calls.append(args);raise AssertionError('normal running touched completed helper')
 ns=dict(require=m.require,re=m.re,json=json,copy=copy,ROUND=m.ROUND,check_observed_identity=m.check_observed_identity,completed_training_collect_gate=forbidden);exec(compile(code,'<exact_capacity_CPU>','exec'),ns)
 j=dict(job_id=jid,gpus=0,experiment='formal_main_v2',name='cti-auto-controller',mode='controller',status='RUNNING');row=dict(job_id=jid,gpus=0,status='RUNNING',exit_code='0:0',elapsed_seconds=1,allocation='cpu=1',node='cpui135',scheduler_name='cti-auto-controller',scheduler_comment='');queue=dict(status='RUNNING',comment='')
 aa=dict(controller_job_id=jid,controller_activation=m.ACTIVATION,root_reservation={'path':'CPU-only','sha256':'0'*64});ss=dict(pending_submission=None,registered_jobs=[j],autonomous_training_v1=dict(activation=m.ACTIVATION,activation_sha256=m.ACTIVATION['sha256'],controller_job_id=jid,root_submission_hold=None,reserved_GPU_slots=1,reservation_root_record=aa['root_reservation']));sn=dict(rows={jid:row},queue={jid:queue});cc=SimpleNamespace(TERMINAL=controller.TERMINAL,capacity=lambda *args:dict(unknown=[],findings=[],occupied=[]));pp=dict(invocation=dict(suite='libero_goal',stage='development',method_ids=['CPU'],stage_key='CPU',prior_job_ids=[],prior_review=None,resume=False),invocation_relative='CPU-only')
 ns['capacity_gate'](cc,ss,sn,aa,pp);ck('RUNNING original branch unchanged even other original stage',not calls)
 ck('original gateway unchanged',h(R/'scripts/ops/formal_action_deployment_v1/gateway.py')=='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a');wr('positive_helper_proofs.json',reports)
 report=dict(schema='formal_main_v2',kind='completed_training_collect_gateway_author_CPU',status='passed_CPU_checks',source_sha256=pin,checks=checks,negative_cases=neg,passed=len(checks),negative_count=len(neg),canonical_collect_plan_files_present={k:(R/k).exists() for k in private},private_plan_only_mapping_explicit=True,all_other_original_AST_unchanged=True,RUNNING_branch_preserved=True,actual_owner_and_lease_probe=True,production_state_written=False,Slurm_submissions=0,GPU_calls=0,CPU_seconds=time.process_time()-start,limits='Direct new helper with author snapshot, actual pinned root exit evidence/owner and actual lease; absent exact plan files may be read through explicitly private mapping. No live all-job capacity claim or dispatch; root must perform original full gateway check with new authorization and actual canonical plans.')
 print(json.dumps(dict(report=wr('CPU_review.json',report),passed=len(checks),negative_count=len(neg))))
if __name__=='__main__':
 try:main()
 except BaseException as e:print(json.dumps(wr('failure.json',dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),checks=checks,negative_cases=neg,CPU_seconds=time.process_time()-start))));raise
