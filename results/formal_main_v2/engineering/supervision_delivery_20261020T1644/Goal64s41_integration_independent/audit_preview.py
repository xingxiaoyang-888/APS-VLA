"""Independent preview audit; no import/execution of the integration mutation entrypoint."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/Goal64s41_integration_independent_20261020T1644';V=R/'.local/Goal64s41_integration_preview_20261020T1644'
B='results/formal_main_v2/preflight/heartbeat_20261021T0044';PAIR='libero_goal_k64_seed41'
CODE='.local/integrate_goal64s41_20261020T1644.py';CODE_SHA='1e34811cf8bc84543f48d411b3b741fa51375b04d9f65b96d343e038b43e9293'
INTENT_SHA='4ae1472a843e194e5e8fc8d940361ef5d3af391d789573669c9776d8eccb9636'
IND='.local/Goal64s41_independent_20261020T1644/3043877_independent_review.json';IND_SHA='1b1dd348efcc5b0857bcefde44d4f9b97243952d4bc15ee5383f46b1aea3d064'
readmap={};checks=[]
def hbytes(b):return hashlib.sha256(b).hexdigest()
def check(ok,name):
 if not ok:raise ValueError(name)
 checks.append(name)
def raw(p,sha=None):
 p=R/p if isinstance(p,str) else p;check(p.is_relative_to(R) and p.resolve()==p,'canonical read '+str(p.relative_to(R)))
 b=p.read_bytes();h=hbytes(b);check(sha is None or h==sha,'SHA '+str(p.relative_to(R)))
 q=str(p.relative_to(R));check(q not in readmap or readmap[q]==h,'stable '+q);readmap[q]=h;return b
def rd(p,sha=None):return json.loads(raw(p,sha))
def rr(v):return rd(v['path'],v['sha256'])
def snapshot_hash(p):
 with p.open('rb') as f:
  hh=hashlib.sha256()
  for block in iter(lambda:f.read(8<<20),b''):hh.update(block)
 return hh.hexdigest()
def validate_core(old,new,summary,intent,ind,root,selected,obs):
 check(set(old)==set(new),'no top-level field creation/removal')
 top_allow={'formal_main_progress','last_root_supervision_snapshot','last_supervision_utc','updated_utc','current_work','next_actions'}
 for key in old:
  if key not in top_allow:check(old[key]==new[key],'unchanged top '+key)
 f=old['formal_main_progress'];g=new['formal_main_progress'];check(f['root_and_independent_completed_arms']==66 and g['root_and_independent_completed_arms']==68,'exact completed66to68')
 check(f['root_and_independent_reviewed_arm_updates']==331000 and g['root_and_independent_reviewed_arm_updates']==341000,'exact reviewed331000to341000')
 check(f['current_action_development_trial_count']==g['current_action_development_trial_count']==4400,'current dev4400 unchanged')
 check(f['completed_development_trials']==g['completed_development_trials']==5612,'raw dev5612 unchanged')
 check(f['current_action_development_unique_initial_states']==g['current_action_development_unique_initial_states']==400,'unique400 unchanged')
 check(g['completed_final_trials']==0 and g['test_opened'] is False and g['global_release_created'] is False,'final0 sealed release closed')
 check(old['pending_submission'] is None and new['pending_submission'] is None,'pending remainsNone')
 check(old['autonomous_training_v1']['reserved_GPU_slots']==0 and old['autonomous_training_v1']['root_submission_hold'] is None,'no engineering reservation held')
 check(new['autonomous_training_v1']==old['autonomous_training_v1'],'controller all lease owner actions immutable')
 check(new['registered_jobs']==old['registered_jobs'],'whole registry immutable')
 ids=[str(j['job_id']) for j in old['registered_jobs']];check(len(ids)==len(set(ids)),'no duplicate registeredjobs')
 bill=sum((j.get('elapsed_seconds') or 0)*(j.get('gpus') or 0) for j in old['registered_jobs'])
 check(bill==old['current_round_cost']['allocated_gpu_seconds']==new['current_round_cost']['allocated_gpu_seconds'],'allocated total recomputed no double count')
 job=[j for j in old['registered_jobs'] if str(j['job_id'])=='3043877'];check(len(job)==1,'pair allocation registered once');job=job[0]
 check(job['elapsed_seconds']==59575 and job['gpus']==1 and job['status']=='COMPLETED' and job['exit_code']=='0:0','59575 already in summed allocation')
 selected_checks=[]
 for arm in ['A','B']:
  x=next(x for x in selected['checks'] if x['arm']==arm);a=ind['arms'][arm]
  check(x['selected_update']==a['earliest_selected_update'] and x['validation_metric']==a['selected_teacher_l1'] and x['sha256']==a['best_sha256'],'actual independently selected '+arm)
  selected_checks.append({'arm':arm,'path':x['path'],'expected_sha256':x['sha256'],'selected_update':x['selected_update'],'validation_metric':x['validation_metric']})
 target={'path':'results/formal_main_v2/libero_goal/k64/seed41/training/segment_reviews/3043877_independent.json','sha256':IND_SHA}
 pair_expected=copy.deepcopy(f['completed_training_pairs'][PAIR]);check(not pair_expected.get('root_review') and not pair_expected.get('independent_review'),'new original independent acceptance absent before')
 check(pair_expected['completed_by_arm']=={'A':5000,'B':5000},'machine completion retained not claimedindependent')
 pair_expected.update(job_id='3043877',suite='libero_goal',visual_tokens=64,seed=41,root_review=summary['root_review']['path'],root_review_sha256=summary['root_review']['sha256'],independent_review=target['path'],independent_review_sha256=target['sha256'],selected_checkpoints=selected_checks,selected_server_review=summary['selected_server']['path'],selected_server_review_sha256=summary['selected_server']['sha256'],root_and_independent_verification_kind='completed_original_root_and_independent_training_review')
 expected=copy.deepcopy(f);expected['completed_training_pairs'][PAIR]=pair_expected;expected['root_and_independent_completed_arms']=68;expected['root_and_independent_reviewed_arm_updates']=341000
 expected['integration_20261020T1644_accepted']=intent['summary'];expected['supervision_integrity_review_20261020T1644']={'status':'pending_post_integration_crosscheck','summary':intent['summary'],'training_independent_review':target,'scientific_gate_changed':False}
 check(g==expected,'exact full formal transform only targetpair and2counters andauditrefs')
 check(g['completed_training_pairs'][PAIR]['machine_verification']==f['completed_training_pairs'][PAIR]['machine_verification'],'complete machine evidence retained')
 check(summary['held_Goal_trials']==200 and summary['Object256s23_bridge_admission'] is False and summary['Goal_original_t0_cause']=='undetermined','hold200 and Object unadmitted unchanged')
 check(g['downstream_blockers_20261020T1418']==f['downstream_blockers_20261020T1418'],'original blocker receipts retained')
 for key,value in {'new_completed_arms':2,'root_independent_complete':68,'expected_arms':72,'new_reviewed_arm_updates':10000,'root_independent_updates':341000,'training_pair_GPU_seconds':59575,'training_pair_cost_already_in_global_ledger':True,'new_GPU_jobs':0,'new_development_trials_accepted':0,'current_action_development_trials':4400,'compatible_legacy_Long_trials':600,'compatible_development_trials':5000,'unique_development_initial_states':400,'final_trials':0,'final_sealed':True,'global_release':False,'post_integration_independent_review_pending':True}.items():check(summary[key]==value,'summary '+key)
 check(summary['independent_review']==target and summary['selected']==selected_checks,'summary original receipt checkpoint binding')
 check(summary['observation_utc']==obs['utc'] and summary['GPU_hours_at_observation']==obs['allocated_GPU_hours'] and summary['occupied_jobs_at_observation']==obs['active_jobs'],'all snapshot costs/capacity explicitly original observation')
 check(new['last_root_supervision_snapshot']==intent['summary'] and new['last_supervision_utc']==new['updated_utc']==summary['utc'],'new root summary clock exact')
 check('68/72' in new['current_work'] and '341000' in new['current_work'] and '548.415' in new['current_work'] and 'Goal original200 remain HOLD' in new['current_work'] and 'final0/35200 sealed' in new['current_work'],'narrative accurate limited to datedsnapshot')
 check(len(new['next_actions'])==5 and all(isinstance(v,str) for v in new['next_actions']),'new nextactions are advisory only')
 return {'allocated_GPU_seconds_preserved':bill,'Goal64seed41_GPU_seconds_already_counted':59575,'selected':selected_checks,'completed_arms':68,'reviewed_updates':341000,'dev_current':4400,'dev_compatible':5000,'dev_unique':400,'held_Goal_trials':200,'final_trials':0}
def main():
 code=raw(CODE,CODE_SHA);compile(code,CODE,'exec')
 intent=rd(V/'intent.json',INTENT_SHA);check(intent['code']['path']==CODE and intent['code']['sha256']==CODE_SHA,'exact reviewed codebound')
 before=raw(V/'state_before.json',intent['before_sha256']);after=raw(V/'state_after.json',intent['after_sha256']);old=json.loads(before);new=json.loads(after)
 summary=rd(V/'summary.json',intent['summary']['sha256']);check(summary['state_before_sha256']==intent['before_sha256'],'summary exact before')
 ind=rd(IND,IND_SHA);check(ind['status']=='passed_complete_training_only' and ind['job_id']=='3043877' and ind['completed_by_arm']=={'A':5000,'B':5000},'original independent actual terminal passed')
 root=rr(summary['root_review']);selected=rr(summary['selected_server']);obs=rr(summary['observation'])
 check(root['status']=='passed' and root['pair_allocated_gpu_seconds']==59575 and root['completed_by_arm']==ind['completed_by_arm'],'original root matches independent')
 check(ind['parallel_root_reconstruction']['path']==summary['root_review']['path'] and ind['parallel_root_reconstruction']['sha256']==summary['root_review']['sha256'],'exact original independent root proof')
 result=validate_core(old,new,summary,intent,ind,root,selected,obs)
 docs=[]
 for rel,sha in intent['doc_before'].items():
  before_doc=raw(V/'documents_before'/Path(rel).name,sha);after_doc=raw(V/'documents_after'/Path(rel).name,intent['doc_after'][rel])
  head,sep,body=before_doc.decode().partition('\n');h2,sep2,body2=after_doc.decode().partition('\n');check(head==h2 and sep==sep2=='\n','document heading preserved '+rel)
  check(after_doc.endswith(body.encode()) and len(after_doc)>len(before_doc),'old entire doc body preserved '+rel)
  prefix=body2[:-len(body)] if body else body2
  check(prefix.startswith('\n') and prefix.endswith('\n\n') and prefix.count('Goal64 seed41')==1,'single appended current paragraph '+rel)
  for term in ['68/72','341000','A选3500','B选3000','11次完整验证','59575','不重复加账','4400','5000','400唯一初态','HOLD','尚未准入','0/35200封存']:check(term in prefix,'doc current fact '+rel+' '+term)
  docs.append({'path':rel,'before_sha256':sha,'after_sha256':intent['doc_after'][rel],'history_preserved':True})
 inventory=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');check(len(inventory['files'])==173,'173 source entries')
 for rel,sha in inventory['files'].items():raw(rel,sha);check(snapshot_hash(S/rel)==sha,'snapshot source unchanged '+rel)
 raw(Path(__file__))
 for rel,sha in readmap.items():check(hbytes((R/rel).read_bytes())==sha,'evidence stable afteraudit '+rel)
 output={'schema':'formal_main_v2','kind':'independent_Goal64s41_integration_preview_review','status':'passed','reviewed_utc':datetime.now(timezone.utc).isoformat(),'code':intent['code'],'preview_intent':{'path':str((V/'intent.json').relative_to(R)),'sha256':INTENT_SHA},'state_before_sha256':intent['before_sha256'],'state_after_sha256':intent['after_sha256'],'summary':intent['summary'],'result':result,'documents':docs,'all173_R_S_unchanged':True,'canonical_writes_performed':False,'state_Git_Slurm_mutated':False,'post_apply_verification_performed':False,'checks':checks,'check_count':len(checks),'read_evidence_sha256':dict(sorted(readmap.items()))}
 p=D/'preview_independent_review.json'
 with p.open('x') as f:json.dump(output,f,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
 print(json.dumps({'path':str(p.relative_to(R)),'sha256':hbytes(p.read_bytes()),'status':'passed','checks':len(checks),'summary':result}))
if __name__=='__main__':main()
