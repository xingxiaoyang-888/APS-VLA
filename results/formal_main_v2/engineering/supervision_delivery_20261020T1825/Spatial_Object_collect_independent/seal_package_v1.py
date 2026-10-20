from pathlib import Path
from types import SimpleNamespace
import ast,copy,difflib,hashlib,json,os,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent;sys.dont_write_bytecode=True
PINS={'prepare_collect_authorization_20261020T1825_v2.py':'7510c461b4502c0baaa5473dbdd0bee2f5379f83f84a07d8ef307442bae64aad','prepare_collect_authorization_20261020T1825_v4.py':'e4c33873093bb5ab6bbfd69c63ec7d935c1e50cb50f07c4c67f3a8b0374ff099'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def put(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2,allow_nan=False);f.write(chr(10))
 return ref(p)
def copy_exact(src,dest,pin=None):
 raw=src.read_bytes();assert pin is None or hashlib.sha256(raw).hexdigest()==pin;dest.parent.mkdir(parents=True,exist_ok=True)
 with dest.open('xb') as f:f.write(raw)
 assert dest.read_bytes()==src.read_bytes();return ref(dest)
helper=D/'helper_review';helper.mkdir();texts={}
for name,pin in PINS.items():
 src=R/'.local'/name;assert sha(src)==pin;texts[name]=src.read_text();copy_exact(src,helper/name,pin)
old,new=list(PINS)
(helper/'v2_to_v4.diff').write_text(''.join(difflib.unified_diff(texts[old].splitlines(True),texts[new].splitlines(True),fromfile=old,tofile=new)))
# Execute only the exact candidate's assertions referring to pr, in an isolated in-memory context.
def binding_code(text):
 nodes=[n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.Assert) and any(isinstance(x,ast.Name) and x.id=='pr' for x in ast.walk(n))];nodes.sort(key=lambda n:n.lineno);assert nodes
 return compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<original helper assertions only>','exec')
codeold=binding_code(texts[old]);codenew=binding_code(texts[new]);tests=[]
def ctx(label):
 out=R/('results/formal_main_v2/execution/'+label.lower()+'_collect_action_v1_20261020T1825');plan=json.loads((out/'effective_plan.json').read_text());action=json.loads((out/'execution_contract.json').read_text());ready=json.loads((out/'runtime_readiness.json').read_text());pr=json.loads((D/label/'independent_readiness.json').read_text())
 return {'pr':pr,'out':out,'plan':plan,'inv':plan['invocation'],'action':action,'ready':ready,'h':sha,'ref':lambda p:{'path':p.relative_to(R).as_posix(),'sha256':sha(p)},'g':SimpleNamespace(COMPLETED_COLLECTION_PLANS={plan['invocation']['suite']:{'sha256':sha(out/'effective_plan.json')}})}
for label,other in [('Spatial','Object'),('Object','Spatial')]:
 env=ctx(label);exec(codenew,env);tests.append({'name':label+'_real_matching_plan','expected':'pass','observed':'pass'})
 wrong=ctx(label);wrong['pr']=ctx(other)['pr'];exec(codeold,wrong);tests.append({'name':label+'_old_v2_cross_suite_gap','expected':'old_guard_accepts','observed':'accepted_by_exact_original_v2_pr_assertions','finding':'Scoped review-binding defect corrected in v4; no production helper executed here.'})
 try:exec(codenew,wrong)
 except AssertionError:tests.append({'name':label+'_v4_cross_suite_rejected','expected':'reject','observed':'AssertionError'})
 else:raise AssertionError('cross-suite review accepted')
 for key,value in [('suite','libero_goal'),('stage','full'),('allowed_stages',['collect','full']),('plan_sha256','0'*64),('scientific_plan',{'path':'wrong.json','sha256':'0'*64}),('effective_plan',{'path':'wrong.json','sha256':'0'*64}),('action_execution_contract',{'path':'wrong.json','sha256':'0'*64})]:
  bad=ctx(label);bad['pr'][key]=value
  try:exec(codenew,bad)
  except AssertionError:tests.append({'name':label+'_v4_reject_'+key,'expected':'reject','observed':'AssertionError'})
  else:raise AssertionError('typed binding fault accepted '+label+key)
helper_report=put(helper/'binding_review.json',{'status':'passed_scoped_binding_review','reviewed_by':'independent','candidate_sources':PINS,'scope':'Only typed per-suite binding and read-only verification of resulting canonical readiness; this is not a full independent review of the root publication helper.','exact_assertion_tests':tests,'production_helper_executions':0,'real_GPU_calls':0,'findings':[{'status':'fixed_in_v4','original_v2_missing_suite_plan_binding':True,'v4_added_exact_suite_stage_allowedstages_semantic_planhash_three_refs':True}],'root_v4_extra_changes':'Existing root-review utc and prepared registered_utc are preserved only for idempotent write; all other bytes still checked by exclusive save.'})
transport_records=[]
for name in ['spatial_object_collect_independent_20261020T1825_v1.jsonl','spatial_object_collect_independent_20261020T1825_post_v1.jsonl']:
 src=R/'results/formal_main_v2/control_transport'/name;events=[json.loads(x) for x in src.read_text().splitlines()];assert events[0]['event']=='control_start' and events[-1]['event']=='control_end' and events[-1]['returncode']==0 and events[-1]['source173_and_entrypoint_unchanged'] is True;transport_records.append(copy_exact(src,D/'closed_transport'/name))
for label,pin in [('Spatial','8c14a975a6b79cf1f5fdbc497560cafd77455a22af307712465468aecb27cfc3'),('Object','e278f9ec7db15810e580dffbb886c4853a4838aeac3f287c48c83b569c244330')]:assert sha(D/label/'independent_readiness.json')==pin
post=json.loads((D/'post_readiness/independent_index.json').read_text());assert post['status']=='passed' and post['actual_full_P_wrapper_verifications']==2 and post['actual_GPU_collect_completed'] is False
handoff=put(D/'handoff.json',{'status':'passed_exact_two_collect_plans_and_actual_P_readiness','reviewed_by':'independent','independent_plan_index':ref(D/'independent_index.json'),'post_readiness_index':ref(D/'post_readiness/independent_index.json'),'helper_binding_review':helper_report,'CPU_checks':7558,'expected_negative_cases':28,'post_readiness_checks':2130,'planned_observations_per_suite':30,'planned_suites':['libero_spatial','libero_object'],'observations_produced_here':0,'scientific_success_trials_added':0,'new_GPU_jobs':0,'new_Slurm_queries':0,'production_state_or_Git_modified':False,'sealed_values_read':False,'closed_audit_transport_copies':transport_records,'author_delivery_manifest':{'path':'.local/spatial_object_collect_20261020T1825/delivery_manifest.json','sha256':'bc95cc4708b91e36dd76799f2b6556ca3a7329f9a2547f113b1844bcdeac2a1f'},'sealing_transport_external':'results/formal_main_v2/control_transport/spatial_object_collect_independent_20261020T1825_seal_v1.jsonl','limits':['CPU metadata/source/selection and actual P wrapper verified. No real GPU collect outcome claimed.','The separately audited completed-controller gateway and root dispatch still must enforce live capacity, duplicate and pending/ACK state.','Goal science and final evaluation remain HOLD/sealed.','Any actual submitted collections require original terminal/raw consumer and independent result audit.']})
files=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  assert not p.is_symlink() and p.suffix.lower() not in ('.pt','.pth','.bin','.safetensors','.ckpt','.npz','.npy','.pickle','.pkl') and p.stat().st_size<100*1024*1024;files.append({'path':p.relative_to(D).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
manifest=put(D/'delivery_manifest.json',{'schema':'formal_main_v2','kind':'independent_collect_plan_and_post_readiness_delivery','status':'sealed','root':str(D),'files':files,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'failure_preservation':'All28expected negative cases plus original v2 binding-gap demonstration retained; no failed independent plan or post-readiness execution occurred. Author failures remain byte-verified in author package.','contains_weights_or_final_values':False,'new_GPU_jobs':0,'handoff':handoff,'external_sealing_transport_excluded_while_open':True})
for row in files:assert sha(D/row['path'])==row['sha256'] and (D/row['path']).stat().st_size==row['bytes']
print(json.dumps({'manifest':manifest,'handoff':handoff,'file_count':len(files),'bytes':sum(x['bytes'] for x in files),'helper_test_count':len(tests)}))
