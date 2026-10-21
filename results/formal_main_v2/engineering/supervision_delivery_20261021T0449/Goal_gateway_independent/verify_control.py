from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import ast,copy,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
A=R/'.local/goal_remaining5_dispatch_20261021T0449'
D=R/'.local/goal_remaining5_gateway_independent_20261021T0449'
PINS={'gateway.py':'7de77ebb179dfe465e490290ab33ff280109cd28225dcbfe6a9b859a0d5207b3','verify_cpu_v2.py':'909bcf3886936f9f0bcee162a829263bb97376f34876006acf5773465756a454','CPU_report_v2.json':'686f8f1bde8283259f190b63ad48ab1b24ceb14374a73d3b1a5731765b488385'}
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,v):
 p=D/name
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True,ensure_ascii=False);f.write('\n')
 return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
for name,pin in PINS.items():assert sha((A/name).read_bytes())==pin,name
# Execute the original author's checks with exactly one AST change: final report
# destination is private to this independent audit. Gateway and all assertions stay byte-identical.
script=(A/'verify_cpu_v2.py').read_bytes();tree=ast.parse(script,str(A/'verify_cpu_v2.py'))
count=0
for node in ast.walk(tree):
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='out':
  assert isinstance(node.value,ast.BinOp) and isinstance(node.value.left,ast.Name) and node.value.left.id=='D' and isinstance(node.value.right,ast.Constant) and node.value.right.value=='CPU_report_v2.json'
  node.value=ast.Call(func=ast.Name(id='Path',ctx=ast.Load()),args=[ast.Constant(str(D/'author_replay.json'))],keywords=[]);count+=1
assert count==1
ast.fix_missing_locations(tree)
def forbidden(*a,**k):raise AssertionError('real subprocess or scheduler is forbidden in independent CPU audit')
ns={'__name__':'_independent_author_replay','__file__':str(A/'verify_cpu_v2.py')}
with patch('subprocess.run',forbidden),patch('subprocess.Popen',forbidden):
 exec(compile(tree,str(A/'verify_cpu_v2.py'),'exec',dont_inherit=True),ns)
expected=json.loads((A/'CPU_report_v2.json').read_bytes());rebuilt=json.loads((D/'author_replay.json').read_bytes())
assert rebuilt==expected,'full author CPU result differs'
m=ns['m'];ds=ns['dispatchers'];Fake=ns['Fake'];bundle=ns['bundle'];Interrupt=ns['Interrupt'];ctl=m.controller()
positive=[];negative=[];findings=[]
def ok(v,label):
 if not v:raise AssertionError(label)
 positive.append(label)
def no(fn,label):
 try:fn()
 except Exception as e:negative.append({'check':label,'type':type(e).__name__,'error':str(e)});return
 except Interrupt as e:negative.append({'check':label,'type':type(e).__name__,'error':str(e)});return
 raise AssertionError('accepted forbidden: '+label)
# Every single retained terminal/partial identity is enough to prevent a second attempt.
for key,d in ds.items():
 b=bundle(d);j=d.job_record('9960001',b,d.sbatch_argv(b))
 identities=[{'stage_key':j['stage_key']},{'logical_trial_id':j['logical_trial_id']},{'invocation':j['invocation']},{'run_root':j['run_root']},{'run_root':j['attempt_root']},{'run_root':d.output},{'name':j['name']},{'job_name':j['job_name']},{'slurm_comment':j['slurm_comment']},{'pair_id':j['pair_id'],'mode':'development'}]
 for i,row in enumerate(identities):
  for status in ('FAILED','COMPLETED','UNKNOWN'):
   row=copy.deepcopy(row);row['status']=status
   ok(d.duplicate(row),key+' fragment duplicate '+str(i)+' '+status)
 ok(d.goal_overlap({'pair_id':d.pair_id,'mode':'profile'}),key+' same pair cross mode blocks')
 ok(d.goal_overlap({'suite':'libero_goal','pair_id':'unknown'}),key+' unknown Goal pair blocks')
 no(lambda:m.fields('JobId=7 JobId=8'),key+' duplicate scheduler fields')
 # No existing or uncertain record may be treated as permission to submit.
 f=Fake(d);f.state['pending_submission']={'unknown':True};no(lambda:d.Transaction(f,b).run(submit=True),key+' root pending blocks');ok(f.sbatch_calls==0,key+' pending has no allocation')
 f=Fake(d);f.state['autonomous_training_v1']['reserved_GPU_slots']=1;no(lambda:d.Transaction(f,b).run(submit=True),key+' existing reservation blocks');ok(f.sbatch_calls==0,key+' reservation has no allocation')
 bb=copy.deepcopy(b);bb['reconcile_existing']=True;f=Fake(d);no(lambda:d.Transaction(f,bb).run(submit=True),key+' reconcile-only metadata cannot submit')
 # More pre-submit and post-pending BaseException windows than the original test.
 for phase in ('fact_preflight.json','fact_pending.json','cas_before_0'):
  f=Fake(d,phase);no(lambda:d.Transaction(f,b).run(submit=True),key+' boundary '+phase)
  ok(f.sbatch_calls==0,key+' failed initial persistence no sbatch '+phase)
  no(lambda:d.Transaction(f,b).run(submit=True),key+' preserved failed fact blocks retry '+phase)
 # Exact own pending and ACK cannot be transplanted across instances.
 f=Fake(d,'actual_held');no(lambda:d.Transaction(f,b).run(submit=True),key+' save unique ACK')
 for otherkey,other in ds.items():
  if otherkey==key:continue
  no(lambda other=other:d.Transaction(f,bundle(other)).run(reconcile=True),key+' ACK cannot reconcile '+otherkey)
 for field,value in [('submission_token','wrong'),('invocation_sha256','f'*64),('known_job_id','9961234'),('authorization',{'path':'wrong'}),('actual_sbatch_argv',['sbatch','wrong'])]:
  g=copy.deepcopy(f);g.state['pending_submission'][field]=value;no(lambda g=g:d.Transaction(g,b).run(reconcile=True),key+' pending tamper '+field)
 # After the release intent is durable, uncertain release is never reissued.
 f=Fake(d,'release_before_effect');no(lambda:d.Transaction(f,b).run(submit=True),key+' before release effect');count0=f.release_calls
 no(lambda:d.Transaction(f,b).run(reconcile=True),key+' still-held after release intent remains HOLD')
 ok(f.release_calls==count0==1 and f.sbatch_calls==1,key+' neither release nor submit repeated')
# Rebuild the real complete accounting snapshot from saved raw text only.
state=ns['state'];obs=ns['obs']
ok(ctl.parse_sacct(obs['raw_sacct'],set(obs['rows']))==obs['rows'],'saved real sacct rows reconstruct')
ok(len(state['registered_jobs'])==303 and sum(j.get('experiment')=='formal_main_v2' for j in state['registered_jobs'])==273,'all 303 allocation rows / 273 formal')
for key,d in ds.items():
 clean=d.normalized_projection(ctl,state,obs,{})
 ok(clean['allocated_formal_GPU_seconds']==1994468,key+' all-mode saved cost exact')
 for field,mut in [('missing',lambda o:o['rows'].pop(next(iter(o['rows'])))),('extra',lambda o:o['rows'].update({'9999999':copy.deepcopy(next(iter(o['rows'].values())))})),('unknown',lambda o:o['rows']['3053440'].update(status='UNKNOWN')),('oldcost',lambda o:o['rows']['3053440'].update(elapsed_seconds=802)),('oldexit',lambda o:o['rows']['3054127'].update(exit_code='1:0')),('oldGPU',lambda o:o['rows']['3054127'].update(gpus=0))]:
  bad=copy.deepcopy(obs);mut(bad);no(lambda bad=bad:d.normalized_projection(ctl,state,bad,{}),key+' reject accounting '+field)
 bad=copy.deepcopy(state);bad['registered_jobs'].append(copy.deepcopy(bad['registered_jobs'][0]));no(lambda:d.normalized_projection(ctl,bad,obs,{}),key+' duplicate registered ID')
# Read-only observation state machine: two complete snapshots for stale registry
# terminal rows, complete queue for live rows, no interpretation of errors as empty.
class Scheduler:
 def __init__(self,answers):self.answers=list(answers);self.calls=[]
 def run(self,argv):
  self.calls.append(argv)
  if not self.answers:raise AssertionError('unplanned scheduler call')
  return SimpleNamespace(**self.answers.pop(0))
def answer(text,rc=0):return {'returncode':rc,'stdout':text,'stderr':'fixture-error' if rc else ''}
job={'job_id':'9981001','status':'RUNNING','gpus':1}
terminal='9981001|COMPLETED|0:0|15|gres/gpu=1|gpu4010|cti-fixture|token\n'
running='9981001|RUNNING|0:0|15|gres/gpu=1|gpu4010|cti-fixture|token\n'
s=Scheduler([answer(terminal),answer(terminal)]);o=m.actual_observation(ctl,s,[job])
ok(len(s.calls)==2 and o['terminal_confirmation']['stale_registry_terminal_ids']==['9981001'],'stale status requires two complete consistent snapshots')
for answers,label in [([answer(terminal),answer(terminal.replace('|15|','|16|'))],'changed terminal duration'),([answer(terminal),answer('')],'missing second allocation'),([answer(terminal),answer('',1)],'failed confirmation'),([answer(running),answer('',1)],'Invalid job id is not empty queue'),([answer(running),answer('')],'live accounting absent queue'),([answer(running),answer('9981001|RUNNING|token\n9981001|RUNNING|token\n')],'duplicate queue row'),([answer(running.replace('|RUNNING|','|UNKNOWN|'))],'unknown scheduler state')]:
 no(lambda answers=answers:m.actual_observation(ctl,Scheduler(answers),[job]),'observe rejects '+label)
s=Scheduler([answer(running),answer('9981001|RUNNING|token\n')]);o=m.actual_observation(ctl,s,[job]);ok(len(s.calls)==2 and o['queue']['9981001']['comment']=='token','live exact queue retained')
# Exact source lifecycle scope remains pending final runtime manifest binding.
for name,pin in PINS.items():ok(sha((A/name).read_bytes())==pin,'source unchanged '+name)
report={'schema':'formal_main_v2','kind':'Goal_remaining5_atomic_dispatch_independent_control_CPU_preliminary','status':'passed_control_transaction_CPU_pending_runtime_binding','reviewed_by':'spatial588_recovery_author_2054_independent_gateway_only','source_sha256':PINS['gateway.py'],'author_test_sha256':PINS['verify_cpu_v2.py'],'author_replay':{'positive':302,'rejections':383,'report_sha256':sha((D/'author_replay.json').read_bytes())},'independent_positive_count':len(positive),'independent_negative_count':len(negative),'positive':positive,'negative':negative,'scope':list(ds),'findings':findings,'blockers':['final exact five-pair runtime manifest/scope not yet supplied','actual admission/entry/consumer cross-interface with final runtime not yet independently rebuilt','canonical actual-P publication/verification and production root readiness remain future work'],'scope_fixture_not_production':True,'actual_scheduler_queries':0,'new_GPU_submissions':0,'GPU_execution_authorized':False,'production_admitted':False}
print(json.dumps(save('control_CPU_preliminary_review.json',report),sort_keys=True))
