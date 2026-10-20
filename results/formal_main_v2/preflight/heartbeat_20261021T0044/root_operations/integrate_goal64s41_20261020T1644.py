from pathlib import Path
from datetime import datetime,timezone,timedelta
import argparse,copy,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1644';PAIR='libero_goal_k64_seed41'
ROOT_REF=dict(path='results/formal_main_v2/libero_goal/k64/seed41/training/segment_reviews/3043877.json',sha256='121ea7c85950ee7b162b642e2e14880f2ec1eb4a1ffcfe3cf34a9ab2b19f6c60')
SELECTED_REF=dict(path=B+'/3043877_selected_server.json',sha256='2731875fc1c0b0a9ef9c57e433fa682969ebf2f172c903dbde89aafb02a73e8c')
OBS_REF=dict(path=B+'/initial_observation.json',sha256='f310180f7c00bc61dbd7ad3610b1016d0f4273ac9a03dd10682ec630105b907e')
CANONICAL_IND='results/formal_main_v2/libero_goal/k64/seed41/training/segment_reviews/3043877_independent.json'
DOCS=['docs/实验进度.md','docs/完整实验计划.md','docs/正式主实验规划.md','docs/正式主实验阶段结论.md','docs/正式自动连续训练执行登记.md']
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=h(p),bytes=p.stat().st_size)
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+chr(10)).encode()
def rd(rr):
 p=R/rr['path'];assert h(p)==rr['sha256'];return json.loads(p.read_bytes())
def put(p,raw):
 assert p.is_relative_to(R) and not any(x.is_symlink() for x in [p,*p.parents])
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw
 else:
  with p.open('xb') as f:f.write(raw)
 return ref(p)
def module(name,rel,pin):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument('--independent',required=True);ap.add_argument('--independent-sha256',required=True);ap.add_argument('--apply',action='store_true');a=ap.parse_args()
ir=dict(path=a.independent,sha256=a.independent_sha256);ind=rd(ir);root=rd(ROOT_REF);selected=rd(SELECTED_REF);obs=rd(OBS_REF)
assert root['status']=='passed' and root['completed_by_arm']=={'A':5000,'B':5000} and root['job_id']=='3043877'
assert root['suite']=='libero_goal' and root['seed']==41 and root['visual_tokens']==64
assert root['pair_allocated_gpu_seconds']==59575 and root['continuation']=='formal_training_complete_no_extension' and not root['sealed_states_opened']
assert ind['status']=='passed_complete_training_only' and ind['job_id']=='3043877' and ind['completed_by_arm']=={'A':5000,'B':5000}
assert ind['suite']=='libero_goal' and ind['seed']==41 and ind['visual_tokens']==64 and not ind['resume_required'] and ind['allowed_next_segment_end'] is None
assert ind['parallel_root_reconstruction']['path']==ROOT_REF['path'] and ind['parallel_root_reconstruction']['sha256']==ROOT_REF['sha256']
assert ind['cost']['all_pair_allocated_GPU_seconds']==59575 and ind['cost']['allocations']==[dict(GPU_seconds=59575,job_id='3043877')]
assert ind['parallel_root_reconstruction']['new_reviewed_arm_updates']==10000 and ind['parallel_root_reconstruction']['prior_reviewed_updates_per_arm']==0
assert selected['root_review']==ROOT_REF and selected['status']=='verified_actual_server_bytes' and not selected['weights_copied']
checks=[]
for row in selected['checks']:
 arm=row['arm'];p=Path(row['path']);assert p.is_relative_to(Path('/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_goal/k64/seed41'))
 st=p.stat();assert h(p)==row['sha256'] and st==p.stat();receipt_rel='results/formal_main_v2/libero_goal/k64/seed41/training/'+arm+'/deployment_receipt.json'
 rec=rd(dict(path=receipt_rel,sha256=root['files'][receipt_rel]));assert rec['training_complete'] and rec['completed_updates']==5000 and rec['checkpoint_sha256']==row['sha256']
 assert [v['update'] for v in rec['evaluations']]==list(range(0,5001,500))
 assert rec['metadata']['update']==row['selected_update'] and rec['metadata']['validation_metric']==row['validation_metric']
 checks.append(dict(arm=arm,path=str(p),expected_sha256=row['sha256'],selected_update=row['selected_update'],validation_metric=row['validation_metric']))
assert {x['arm'] for x in checks}=={'A','B'} and len(checks)==2
c=module('integrateGoal41_1644','scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';state_before=sp.read_bytes();before_sha=h(sp);s=json.loads(state_before);old=copy.deepcopy(s);f=s['formal_main_progress']
 assert f['root_and_independent_completed_arms']==66 and f['root_and_independent_reviewed_arm_updates']==331000
 assert f['current_action_development_trial_count']==4400 and f['completed_development_trials']==5612 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0 and s['autonomous_training_v1']['root_submission_hold'] is None
 pair=f['completed_training_pairs'][PAIR];assert pair['completed_by_arm']=={'A':5000,'B':5000} and not pair.get('root_review') and not pair.get('independent_review')
 registered=[j for j in s['registered_jobs'] if str(j['job_id'])=='3043877'];assert len(registered)==1
 j=registered[0];assert j['status']=='COMPLETED' and j['exit_code']=='0:0' and j['elapsed_seconds']==59575 and j['gpus']==1
 targetref=dict(path=CANONICAL_IND,sha256=ir['sha256'])
 pair.update(job_id='3043877',suite='libero_goal',visual_tokens=64,seed=41,root_review=ROOT_REF['path'],root_review_sha256=ROOT_REF['sha256'],independent_review=CANONICAL_IND,independent_review_sha256=ir['sha256'],selected_checkpoints=checks,selected_server_review=SELECTED_REF['path'],selected_server_review_sha256=SELECTED_REF['sha256'],root_and_independent_verification_kind='completed_original_root_and_independent_training_review')
 f['root_and_independent_completed_arms']=68;f['root_and_independent_reviewed_arm_updates']=341000
 now=datetime.now(timezone.utc);summary=dict(schema='formal_main_v2',kind='Goal64seed41_original_root_independent_terminal_integration',utc=now.isoformat(),state_before_sha256=before_sha,root_review=ROOT_REF,independent_review=targetref,selected_server=SELECTED_REF,selected=checks,new_completed_arms=2,root_independent_complete=68,expected_arms=72,new_reviewed_arm_updates=10000,root_independent_updates=341000,training_pair_GPU_seconds=59575,training_pair_cost_already_in_global_ledger=True,observation=OBS_REF,observation_utc=obs['utc'],GPU_hours_at_observation=obs['allocated_GPU_hours'],occupied_jobs_at_observation=obs['active_jobs'],new_GPU_jobs=0,new_development_trials_accepted=0,current_action_development_trials=4400,compatible_legacy_Long_trials=600,compatible_development_trials=5000,unique_development_initial_states=400,held_Goal_trials=200,Goal_original_t0_cause='undetermined',Object256s23_bridge_admission=False,final_trials=0,final_sealed=True,global_release=False,post_integration_independent_review_pending=True)
 sr=dict(path=B+'/summary.json',sha256=hashlib.sha256(enc(summary)).hexdigest());f['integration_20261020T1644_accepted']=sr
 f['supervision_integrity_review_20261020T1644']=dict(status='pending_post_integration_crosscheck',summary=sr,training_independent_review=targetref,scientific_gate_changed=False)
 s['last_root_supervision_snapshot']=sr;s['last_supervision_utc']=now.isoformat();s['updated_utc']=now.isoformat()
 s['current_work']='68/72 training arms root+independent accepted;341000 reviewed updates. Goal64seed41 newly accepted, no new development acceptance (current4400 + compatible Long600,400 unique initials). 6 GPU jobs at initial observation,548.415 GPU hours. Goal original200 remain HOLD;Object source bridge integration pending;final0/35200 sealed.'
 s['next_actions']=['Leave healthy training and four registered64 development jobs to automatic controller; review terminal originals on scheduled supervision, no duplicate submission.','Remaining training pairs Goal64seed23 and Object64seed23 require original root+independent terminal review when complete.','Object256seed23 source bridge remains unadmitted until explicit factory/planner/gateway/terminal-consumer integration and independent actual-entry checks pass.','Goal256seed17 original200 remain HOLD; the bounded probe did not reproduce the t0 discrepancy. Preserve all originals and identify the cause before scientific re-run.','All72 checkpoint identities plus16references and all4suite development/final manifests must be frozen before global final release; no sealed state values read.']
 # No controller, job registry, previous result, completion machine evidence, release, or pending mutation.
 for k in old:
  if k not in ['formal_main_progress','last_root_supervision_snapshot','last_supervision_utc','updated_utc','current_work','next_actions']:assert old[k]==s[k],k
 allowed={'root_and_independent_completed_arms','root_and_independent_reviewed_arm_updates','completed_training_pairs','integration_20261020T1644_accepted','supervision_integrity_review_20261020T1644'}
 for k in old['formal_main_progress']:
  if k not in allowed:assert old['formal_main_progress'][k]==f[k],k
 for key,row in old['formal_main_progress']['completed_training_pairs'].items():
  if key!=PAIR:assert f['completed_training_pairs'][key]==row
  else:
   for k,v in row.items():assert pair[k]==v
 docs_before={rel:(R/rel).read_bytes() for rel in DOCS};stamp=now.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 paragraph=stamp+'：Goal64 seed41 A/B各5000步通过原root与独立终审，正式训练68/72组、341000已审更新；A选3500、B选3000，均完成11次完整验证。59575 GPU秒已在总账内，仅记录本次验收，不重复加账。本轮未新增已验收开发结果：当前动作4400条，加显式兼容Long600为5000条、400唯一初态。初次核对6个GPU作业正常、累计548.415GPU小时；健康作业交由自动控制器。Goal原200条继续HOLD，Object来源兼容桥尚未准入；最终0/35200封存。见[本轮验收](../'+B+'/summary.json)。'
 docs={}
 for rel,raw in docs_before.items():
  head,sep,body=raw.decode('utf-8').partition(chr(10));assert sep and head.startswith('# ');docs[rel]=(head+chr(10)*2+paragraph+chr(10)*2+body).encode('utf-8')
 intent=dict(status='prepared_exact_training_increment_only',code=ref(Path(__file__)),independent_private=ir,summary=sr,before_sha256=before_sha,after_sha256=hashlib.sha256(enc(s)).hexdigest(),doc_before={k:hashlib.sha256(v).hexdigest() for k,v in docs_before.items()},doc_after={k:hashlib.sha256(v).hexdigest() for k,v in docs.items()},registry_controller_scientific_results_preserved=True)
 if not a.apply:
  dst=R/'.local/Goal64s41_integration_preview_20261020T1644';put(dst/'state_before.json',state_before);put(dst/'state_after.json',enc(s));put(dst/'summary.json',enc(summary));put(dst/'intent.json',enc(intent))
  for rel,raw in docs_before.items():put(dst/'documents_before'/Path(rel).name,raw)
  for rel,raw in docs.items():put(dst/'documents_after'/Path(rel).name,raw)
  assert h(sp)==before_sha;print(json.dumps(dict(status='preview_only',preview=str(dst),summary=sr,intent=ref(dst/'intent.json'))),flush=True)
 else:
  put(R/B/'integration_state_before.json',state_before);put(R/B/'integration_intent.json',enc(intent));put(R/CANONICAL_IND,(R/ir['path']).read_bytes());put(R/B/'summary.json',enc(summary))
  for rel,raw in docs_before.items():assert (R/rel).read_bytes()==raw
  assert h(sp)==before_sha
  for rel,raw in docs.items():(R/rel).write_bytes(raw)
  c.atomic_json(sp,s,before_sha)
  out=R/B/'integration_completion.json';put(out,enc(dict(status='root_applied_pending_post_independent_crosscheck',summary=sr,state_before_sha256=before_sha,state_after_sha256=h(sp),documents={k:ref(R/k) for k in DOCS},independent=targetref,new_completed_arms=2,new_reviewed_updates=10000,new_GPU_jobs=0,new_development_accepted=0,final_sealed=True)))
  print(json.dumps(dict(status='applied_68_of72',completion=ref(out),summary=sr)),flush=True)
