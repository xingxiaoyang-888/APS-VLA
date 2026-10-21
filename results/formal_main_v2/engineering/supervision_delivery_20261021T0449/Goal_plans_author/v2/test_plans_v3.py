"""CPU replay of original five-pair planners and rejection boundaries; no inference."""
from pathlib import Path
from types import SimpleNamespace
import argparse,copy,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_remaining5_plans_20261021T0449/v2'
B_SHA='3d84ce954a5d6b3d74cbe430518b12bdba93fe25bc17631bf743cc75698b6ffa'
P_SHA='a633636dc4cdd64f75d32de72dda5dea34804b1253d7658c21dce97091aa7736'
def load(path,pin,name):
 raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==pin
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;exec(compile(raw,str(path),'exec'),m.__dict__);return m
b=load(D/'build_plans.py',B_SHA,'test_remaining5_builder');p=load(D/'prepare_after_reviews_v2.py',P_SHA,'test_remaining5_prepare')
def run(index_path,index_sha):
 checks=[]
 def ok(label,condition):
  b.require(condition,label);checks.append(dict(name=label,kind='positive',passed=True))
 def reject(label,fn):
  try:fn()
  except (ValueError,KeyError,TypeError,FileNotFoundError) as ex:checks.append(dict(name=label,kind='rejection',passed=True,error_type=type(ex).__name__,error=str(ex)));return
  raise AssertionError('NOT REJECTED: '+label)
 index=b.verify_index(index_path,index_sha)
 ok('all five original planner full replays exactly match frozen candidate',len(index['pairs'])==5)
 h=b.load('scripts/formal_execution_manifests.py');planner=b.load('scripts/ops/formal_downstream_supervisor.py');c=b.load('scripts/ops/formal_action_deployment_v1/contract.py')
 from cti_vla.evaluation import formal_trials
 panel=json.loads((R/b.PANEL).read_bytes());state=json.loads((R/index['state_snapshot']['path']).read_bytes())
 oldkeys=[]
 for key in b.KEYS:
  row=index['pairs'][key]
  def read(ref):return json.loads(b.publication(ref['path']).read_bytes())
  m=read(row['execution_manifest']);inner=read(row['scientific_plan']);outer=read(row['effective_plan']);action=read(row['execution_contract']);spec=read(row['specification'])
  ok(key+' original selected receipt scope',b.validate_scope(key,m)['pair_id']==row['pair_id'])
  ok(key+' own source provenance',inner['invocation']['source_provenance']==read(row['source_provenance']))
  ok(key+' no prior/no retry',inner['invocation']['prior_job_ids']==[] and inner['invocation']['resume'] is False and inner['invocation']['stop_after'] is None)
  ok(key+' independent standard invocation',row['planned_invocation_path'] not in oldkeys and row['planned_invocation_path']!='results/formal_main_v2/invocations/libero_goal_development_5185766bb353c8e6_attempt01.json');oldkeys.append(row['planned_invocation_path'])
  expected=[dict(ordinal=i+1,**formal_trials._identity(panel,s,mid)) for i,(s,mid) in enumerate((s,mid) for s in panel['states'] for mid in row['method_ids'])]
  ok(key+' all200 original identity order',spec['rows']==expected and spec['rows_signature_sha256']==b.sig(expected))
  formal_trials.validate_trial_identities(panel,row['method_ids'],SimpleNamespace(events=spec['rows']))
  ok(key+' original trial validator consumes all200 metadata',True)
  for field,value in [('split','final'),('suite','libero_object'),('development_panel','configs/manifests/formal_main_v2/libero_goal/initial_states/sealed_final.json'),('development_panel_sha256','0'*64),('registration_sha256','0'*64)]:
   bad=copy.deepcopy(m);bad[field]=value;reject(key+' manifest '+field,lambda bad=bad:b.validate_scope(key,bad))
  for field,value in [('runtime_seed',row['training_seed']+1),('environment_seed',1),('wait_steps',9),('action_chunk',4),('max_steps',301)]:
   bad=copy.deepcopy(m);bad['environment'][field]=value;reject(key+' environment '+field,lambda bad=bad:b.validate_scope(key,bad))
  for field,value in [('method_id','A256_seed17'),('pair_id','0'*64),('training_seed',99),('visual_tokens',32),('checkpoint_sha256','0'*64),('model_revision','different'),('source_sha256','0'*64),('config_sha256','0'*64),('deployment_receipt_sha256','0'*64),('f01_report_sha256','0'*64),('input_acceptance_sha256','0'*64),('future_head_deployed',True)]:
   bad=copy.deepcopy(m);bad['methods'][0]['identity'][field]=value;reject(key+' identity '+field,lambda bad=bad:b.validate_scope(key,bad))
  for field,value in [('receipt',m['methods'][1]['receipt']),('pair_config','configs/experiments/formal_main_v2/libero_goal_k256_seed17.json'),('checkpoint',m['methods'][1]['checkpoint']),('f01_report','results/formal_main_v2/libero_object/acceptance/attempt03/f01_k128.json')]:
   bad=copy.deepcopy(m);bad['methods'][0][field]=value;reject(key+' method source '+field,lambda bad=bad:b.validate_scope(key,bad))
  for mids in [[m['methods'][0]],[m['methods'][1],m['methods'][0]],m['methods']+[m['methods'][0]]]:
   bad=copy.deepcopy(m);bad['methods']=mids;reject(key+' missing/reversed/duplicate methods '+str(len(mids)),lambda bad=bad:b.validate_scope(key,bad))
  for field,value in [('runtime_seed',99),('environment_seed',1),('initial_state_sha256','0'*64),('source_state_index',99),('task_id',9),('method','dense'),('trial_id','forged')]:
   bad=copy.deepcopy(spec['rows']);bad[0][field]=value;reject(key+' original identity '+field,lambda bad=bad:formal_trials.validate_trial_identities(panel,row['method_ids'],SimpleNamespace(events=bad)))
  for field,value in [('method_ids',['dense']),('suite','libero_object'),('argv',['full']),('run_root','/tmp/foreign'),('source_sha256','0'*64),('source_provenance',{}),('stop_after',1),('resume',True)]:
   bad=copy.deepcopy(outer);bad['invocation'][field]=value;bad['plan_sha256']=c.signature({k:v for k,v in bad.items() if k!='plan_sha256'})
   reject(key+' effective scientific drift '+field,lambda bad=bad:c.validate_effective(inner,bad,scientific_plan_ref=row['scientific_plan'],execution_contract_ref=row['execution_contract'],execution_contract=action))
  e=h.Evidence(R);value=dict(evidence=e,suite='libero_goal',methods=row['method_ids']);args=b.args_for(key)
  actual=planner.prior_contract(args,state,value,R);ok(key+' original duplicate/output gate',actual[2]==[])
  prior=dict(job_id='99999901',experiment='formal_main_v2',mode='development',suite='libero_goal',stage_key=inner['invocation']['stage_key'],method_ids=row['method_ids'],run_root=inner['invocation']['run_root'],status='RUNNING')
  badstate=copy.deepcopy(state);badstate['registered_jobs'].append(prior);reject(key+' active same stage',lambda:planner.prior_contract(args,badstate,value,R))
  badstate=copy.deepcopy(state);badstate['registered_jobs'].append({**prior,'status':'UNKNOWN'});reject(key+' unknown stage',lambda:planner.prior_contract(args,badstate,value,R))
  badstate=copy.deepcopy(state);badstate['registered_jobs'].append({**prior,'status':'COMPLETED','exit_code':'0:0','elapsed_seconds':1,'gpus':1,'source_sha256':planner.FROZEN_SHA256,'adapter_sha256':planner.ADAPTER_SHA256});reject(key+' completed same instance cannot silently rerun',lambda:planner.prior_contract(args,badstate,value,R))
  badstate=copy.deepcopy(state);next(j for j in badstate['registered_jobs'] if j['job_id']=='3054717').pop('method_ids',None);reject(key+' retained missing methods prior block',lambda:planner.prior_contract(args,badstate,value,R))
  badstate=copy.deepcopy(state);badstate['pending_submission']={'request_token':'unknown'};reject(key+' root pending original planner',lambda:planner.plan(args,badstate,project=R,helper=h))
  for role in ('root','independent'):
   fake=p.expected_review(row,index,role);fake.update(runtime_sources=action['files'],blockers=[],review_evidence={})
   reject(key+' no synthetic receipt evidence '+role,lambda fake=fake,role=role:p.validate_review(fake,row,index,role,action['files']))
   for forbidden in ['results/formal_main_v2/checkpoints/model.pt','results/formal_main_v2/final/panel.json','results/formal_main_v2/initial_states/development.json']:
    wrong=copy.deepcopy(fake);wrong['review_evidence']={'forbidden':dict(path=forbidden,sha256='0'*64)};reject(key+' forbidden review metadata '+role+' '+forbidden,lambda wrong=wrong,role=role:p.validate_review(wrong,row,index,role,action['files']))
   for field,value in [('pair_id','0'*64),('status','candidate'),('original_builders',{}),('actual_new_runtime_P_verified',True),('production_chain_complete',False)]:
    wrong=copy.deepcopy(fake);wrong[field]=value;reject(key+' review binding '+role+' '+field,lambda wrong=wrong,role=role:p.validate_review(wrong,row,index,role,action['files']))
 for path in ['configs/manifests/formal_main_v2/libero_goal/initial_states/sealed_final.json','weights/forbidden.pt','../outside.json','results/formal_main_v2/final/panel.json']:
  reject('original evidence path forbidden '+path,lambda path=path:h.Evidence(R).path(path))
 reject('foreign pair blocked before plan',lambda:b.args_for('libero_goal_k256_seed17'))
 return dict(schema=b.ROUND,kind='Goal_remaining5_plans_author_CPU_tests',status='passed',source_files={'build_plans.py':B_SHA,'prepare_after_reviews_v2.py':P_SHA,'test_plans_v3.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},candidate_index_sha256=index_sha,positive=sum(x['kind']=='positive' for x in checks),rejections=sum(x['kind']=='rejection' for x in checks),checks=checks,real_original_rebuild_pair_count=5,actual_P_verified=False,production_admitted=False,new_trials=0,new_GPU_jobs=0,limitations=['trial rows are metadata-only CPU validation, not rollouts','no root or independent readiness fabricated','future canonical replay and actual-P/runtime/source/space/atomic gateway checks remain required'])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--index',type=Path,required=True);ap.add_argument('--index-sha256',required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=run(a.index,a.index_sha256);b.write(a.output,b.encoded(out));print(json.dumps({k:v for k,v in out.items() if k!='checks'},sort_keys=True))
if __name__=='__main__':main()