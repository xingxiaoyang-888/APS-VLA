from pathlib import Path
import json,hashlib,sys,importlib.util,copy,io,contextlib,traceback
from unittest.mock import patch
from types import SimpleNamespace
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/downstream_runtime_independent_20261021T0110/Object_gateway';A=R/'.local/object_single_error_gateway_20261021T0110'
positive=[];negative=[]
def need(v,label):
 if not v:raise AssertionError(label)
 positive.append(label)
def reject(fn,label):
 try:fn()
 except (ValueError,AssertionError,RuntimeError) as e:negative.append({'check':label,'error_type':type(e).__name__,'error':str(e)});return
 raise AssertionError('UNEXPECTED ACCEPT '+label)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,x):
 p=D/name
 with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False);f.write('\n')
 return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p)}
def load(p,name,pin):
 need(sha(p)==pin,'exact import '+str(p.relative_to(R)))
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m

def main():
 before=sha(R/'results/experiment_supervisor/state.json')
 need(sha(A/'delivery_manifest.json')=='7b0aa2781ca22773b2bfe624a51a42a19d0878638d4bf4d4e1c4c6b02fa2d95d','frozen author manifest')
 manifest=json.loads((A/'delivery_manifest.json').read_text());need(manifest['file_count']==len(manifest['files'])==28,'exact28 author files')
 for row in manifest['files']:
  p=R/row['path'];need(p.is_relative_to(A) and not p.is_symlink(),'author package containment '+row['path']);need(sha(p)==row['sha256'] and p.stat().st_size==row['bytes'],'author exact member '+row['path'])
 harness=load(A/'verify_cpu.py','_independent_object_gateway_replay','21149d9e50067520598de510c7f1e2c4b225279cec2e7ad7f7e86b3c1f120340')
 g=harness.g;c=g.controller();closure=json.loads((A/'source_closure.json').read_text())
 need(closure['gateway_files'][g.BASE+'/gateway.py']==sha(A/'gateway.py'),'gateway exact source closure')
 for rel,pin in closure['old_production_sources'].items():
  for base in (R,P):need(sha(base/rel)==pin,'actual original10 R/P '+str(base/rel))
 stdout=io.StringIO();argv=sys.argv[:]
 with patch('subprocess.run',side_effect=AssertionError('No external command permitted in independent CPU replay')),contextlib.redirect_stdout(stdout):
  sys.argv=[str(A/'verify_cpu.py'),'--verify-saved']
  try:harness.main()
  finally:sys.argv=argv
 need(len(harness.positive)==63 and len(harness.negative)==100,'independent replay63 positive100 negative exact saved report')
 replay=save('author_replay.json',{'status':'passed','stdout':stdout.getvalue(),'positive':harness.positive,'negative':harness.negative,'subprocess_calls_permitted':False,'new_GPU_jobs':[]})
 live=json.loads((A/'live_inputs.json').read_text());base_state=live['state_for_projection'];base_obs=live['result']['observation']
 need(len(base_state['registered_jobs'])==301,'all301 saved registered jobs retained')
 need(c.parse_sacct(base_obs['raw_sacct'],set(base_obs['rows']))==base_obs['rows'],'independent saved raw all301 accounting reconstruction')
 # These fabricated capacity rows exist only in this private CPU fixture, never Slurm/state.
 def capacity_case(n,pending=False):
  state=copy.deepcopy(base_state);obs=copy.deepcopy(base_obs);detail={}
  for index in range(n):
   jid=str(9911000+index);name='cti-cpu-fixture-slot-'+str(index);comment='CPU_ONLY_CAPACITY_'+str(index);status='PENDING' if pending else 'RUNNING'
   argv=['sbatch','--job-name='+name,'--comment='+comment,'--account=p_p15016','--partition=L40','--output=/cpu_fixture/'+name+'_%j.out']
   job={'job_id':jid,'name':name,'job_name':name,'mode':['engineering','development','collect','profile','latency','training_probe','other'][index%7],'experiment':'formal_main_v2','suite':'libero_goal','gpus':1,'status':status,'actual_sbatch_argv':argv,'CPU_fixture':True}
   state['registered_jobs'].append(job)
   obs['rows'][jid]={'job_id':jid,'status':status,'exit_code':'0:0','elapsed_seconds':7,'gpus':0 if pending else 1,'allocation':'cpu=7,gres/gpu=1','node':'CPU_FIXTURE','scheduler_name':name,'scheduler_comment':comment}
   obs['queue'][jid]={'status':status,'comment':comment}
   f=g.expected_live(job);f.update(TresPerNode='gres:gpu:l40:1',JobState=status);detail[jid]=f
  return state,obs,detail
 for n in (0,1,7):
  state,obs,detail=capacity_case(n);r=g.normalized_projection(c,state,obs,detail);need(len(r['occupied'])==n,'all-mode requested count permits new slot after '+str(n))
 state,obs,detail=capacity_case(8);reject(lambda:g.normalized_projection(c,state,obs,detail),'eight existing all-mode jobs reject ninth')
 state,obs,detail=capacity_case(9);reject(lambda:g.normalized_projection(c,state,obs,detail),'nine preexisting jobs refuse')
 state,obs,detail=capacity_case(7,True);need(len(g.normalized_projection(c,state,obs,detail)['occupied'])==7,'pending allocation gpus0 still counts requested slot')
 for reserved in (1,2):
  state,obs,detail=capacity_case(7);state['autonomous_training_v1']['reserved_GPU_slots']=reserved
  reject(lambda:g.normalized_projection(c,state,obs,detail),'all-mode7+reservation'+str(reserved)+'+new refuses')
 state,obs,detail=capacity_case(1);jid='9911000'
 for field in ('Comment','JobName','Account','Partition','StdOut','TresPerNode','JobState'):
  bad=copy.deepcopy(detail);bad[jid][field]='WRONG'
  reject(lambda bad=bad:g.normalized_projection(c,state,obs,bad),'independent occupied identity '+field)
 for field,value in [('suite','libero_object'),('pair_id',g.PAIR),('stage_key','object-other-budget'),('run_root','/runtime/libero_object/other'),('name','cti-object-other')]:
  bad=copy.deepcopy(state);bad['registered_jobs'][-1][field]=value
  reject(lambda bad=bad:g.normalized_projection(c,bad,obs,detail),'active Object/samepair allmode '+field)
 bad=copy.deepcopy(obs);bad['rows'][jid]['status']='UNKNOWN';reject(lambda:g.normalized_projection(c,state,bad,detail),'unknown accounting refuses')
 bad=copy.deepcopy(obs);bad['rows'][jid]['gpus']=2;reject(lambda:g.normalized_projection(c,state,bad,detail),'multiGPU refuses')
 bad=copy.deepcopy(obs);bad['rows'].pop(jid);reject(lambda:g.normalized_projection(c,state,bad,detail),'missing live accounting refuses')
 bad=copy.deepcopy(detail);bad.pop(jid);reject(lambda:g.normalized_projection(c,state,obs,bad),'missing exact scontrol projection refuses')
 # Strict exact self exception after held ACK registration, and no generic pending clear.
 state,obs,detail=capacity_case(7);b=harness.bundle();newid='9900001';job=g.job_record(newid,b,g.sbatch_argv(b));state['registered_jobs'].append(job)
 obs['rows'][newid]={'job_id':newid,'status':'PENDING','exit_code':'0:0','elapsed_seconds':0,'gpus':0,'allocation':'cpu=7','node':'None','scheduler_name':g.NAME,'scheduler_comment':b['comment']}
 obs['queue'][newid]={'status':'PENDING','comment':b['comment']};detail[newid]={**g.expected_live(job),'JobState':'PENDING','TresPerNode':'gres:gpu:l40:1'}
 state['pending_submission']={'kind':'Object_single_error_durable_pending','stage_key':g.STAGE,'logical_trial_id':g.CELL,'known_job_id':newid}
 need(len(g.normalized_projection(c,state,obs,detail,allow_job=newid)['occupied'])==8,'exact own held eighth row with original pending permitted')
 for field in ['kind','stage_key','logical_trial_id','known_job_id']:
  bad=copy.deepcopy(state);bad['pending_submission'][field]='WRONG'
  reject(lambda bad=bad:g.normalized_projection(c,bad,obs,detail,allow_job=newid),'only exact own rootpending '+field)
 bad=copy.deepcopy(state);bad['autonomous_training_v1']['pending_submission']={'known_job_id':newid}
 reject(lambda:g.normalized_projection(c,bad,obs,detail,allow_job=newid),'nested pending refuses even exact self exception')
 fixtures=save('CPU_capacity_fixture.json',{'schema':'CPU_SYNTHETIC_NOT_SCHEDULER','purpose':'independent exact8 slot/ownheld example; not actual receipt','state':state,'observation':obs,'details':detail})
 # More crash windows use original transaction implementation with memory-only IO.
 for phase in ('cas_before_0','fact_preflight.json','fact_pending.json','fact_held_capacity_before_registration.json','fact_committed.json'):
  fake=harness.Fake(phase)
  try:g.Transaction(fake,harness.bundle()).run(submit=True)
  except harness.Interruption:pass
  else:raise AssertionError('missing BaseException injection '+phase)
  need(fake.sbatch_calls<=1 and fake.release_calls<=1,'BaseException once-only '+phase)
  old_calls=fake.sbatch_calls
  reject(lambda:g.Transaction(fake,harness.bundle()).run(submit=True),'postexception repeat refused '+phase)
  need(fake.sbatch_calls==old_calls,'postexception no resubmit '+phase)
 # Control-plane review does not change original/derived scientific-loop sources.
 oldreview=json.loads((R/g.PROD_REVIEW).read_text());need(oldreview['production_admitted'] is False and oldreview['production_source_closure']==closure['old_production_sources'],'prior independent source proof inherited with its CPU-only scope')
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text());need(len(inventory['files'])==173,'original inventory173')
 for rel,pin in inventory['files'].items():
  for root in (R,Path(inventory['source_root_server'])):need(sha(root/rel)==pin,'source173 '+str(root/rel))
 for row in manifest['files']:need(sha(R/row['path'])==row['sha256'],'author source unchanged '+row['path'])
 review=dict(schema='formal_main_v2',kind='Object_single_error_gateway_independent_review',status='passed',reviewed_by='independent',review_scope='source_and_CPU_only',scope_sha256=g.SCOPE,blockers=[],production_sources=closure['old_production_sources'],gateway_files=closure['gateway_files'],gateway_source={'path':g.BASE+'/gateway.py','bytes':(A/'gateway.py').stat().st_size,'sha256':sha(A/'gateway.py')},
  author_manifest_sha256=sha(A/'delivery_manifest.json'),author_replay=replay,independent_positive_count=len(positive),independent_negative_count=len(negative),positive=positive,negative=negative,CPU_fixture=fixtures,
  held_submit_durable_ACK_register_release_order_verified=True,unknown_ACK_no_resubmit_verified=True,uncertain_release_no_repeat_verified=True,all_modes_eight_GPU_and_same_pair_verified=True,nested_pending_failclosed_verified=True,BaseException_failclosed_verified=True,raw_scheduler_not_boolean_verified=True,original599_evidence_reconstructed=True,original_GPU_seconds_retained=6713,source173_verified=True,
  original_scientific_loop_and_derived_loop_roles_preserved=True,prior_10_source_review_inherited={'path':g.PROD_REVIEW,'sha256':g.PROD_REVIEW_SHA,'not_new_GPU_terminal_review':True},
  GPU_execution_authorized=False,actual_P_verified=False,production_ready=False,production_admitted=False,remaining_production_gates=['Root exact new3 canonical R/P installation','Root exact plan/repair and actual P new entry --verify with full original evidence','Archived independent report, root readiness/exact authorization and fresh actual owner/lease/pending/allmode capacity before held submission','Unique saved original ACK registration before single release; uncertain outcomes remain HOLD','Future actual one-trial raw original/derived-loop/consumer and all allocation terminal review'],
  state_written=False,state_sha256_before=before,state_sha256_after=sha(R/'results/experiment_supervisor/state.json'),Slurm_queries=0,new_GPU_jobs=[],scientific_trials_added=0,final_sealed=True,
  limitations=['The synthetic capacity and crash fixtures are CPU-only, never actual Slurm evidence.','Historical raw all301 accounting/lease evidence is replayed; fresh dispatch facts must be remeasured by root gateway.','No new single-trial GPU result exists or is preaccepted. Ordinary failure is terminal and cannot authorize another attempt.'])
 print(json.dumps(save('independent_review.json',review),sort_keys=True))
try:main()
except BaseException as e:
 save('failure.json',{'type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'positive':positive,'negative':negative,'Slurm_queries':0,'new_GPU_jobs':[]});raise
