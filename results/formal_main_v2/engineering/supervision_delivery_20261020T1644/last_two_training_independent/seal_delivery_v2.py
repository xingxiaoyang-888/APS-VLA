from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/last_two_training_independent_20261020T1644'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin):
 p=R/rel;assert sha(p)==pin,rel;return json.loads(p.read_text())
def write(p,x):
 with p.open('x') as f:json.dump(x,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
refs={
'Goal_review':{'path':str((D/'goal/3043813_independent_review.json').relative_to(R)),'sha256':'d23ddb4a0636c3da92293ea766a099bbf62dabff6b8379c17d07af73dfb1d670'},
'Object_review':{'path':str((D/'object/independent_review.json').relative_to(R)),'sha256':'9d357b032ae9c8c3d1aa4f901875eec4ef4fca7c2912805c52e114813e3b2150'},
'Goal_CPU':{'path':str((D/'goal/cpu_selfcheck_v1.json').relative_to(R)),'sha256':'b668da411c331d699b439d3a2cabbf0fcb00c1aa5e89e80fa35507a1f00d1685'},
'Object_CPU':{'path':str((D/'object/cpu_selfcheck_v2.json').relative_to(R)),'sha256':'35ffcdb2fc3727e89590fa3e1d4553a47ae36505e8a73015d74f61c94478ecab'}}
v={k:load(x['path'],x['sha256']) for k,x in refs.items()}
assert v['Goal_CPU']['passed']==29 and v['Object_CPU']['passed']==33 and not v['Goal_CPU']['failed'] and not v['Object_CPU']['failed']
assert all(v[k]['status']=='passed_complete_training_only' and v[k]['completed_by_arm']=={'A':5000,'B':5000} for k in ['Goal_review','Object_review'])
rel='results/formal_main_v2/control_transport/review_last_two_20261020T1644.jsonl';pin='212f28e85a9b436618f12bc03b4d78b29a1faf67b3ede30db2146a628e40f39d';p=R/rel;assert sha(p)==pin
rows=[json.loads(x) for x in p.read_text().splitlines()];assert rows[-1]['event']=='control_end' and rows[-1]['returncode']==1 and rows[-1]['source173_and_entrypoint_unchanged']
helper='.local/review_last_two_20261020T1644.py';helperpin='11212cd651c48c34592d085ce7542ad0ee758c5a732109702fe7622d6f6a00f2';assert sha(R/helper)==helperpin
normal='scripts/review_formal_segment.py';normalpin='566408f7f72bd3d878204175573a9c08b01db67be69358ed4a8ac2d0e0603790';assert sha(R/normal)==normalpin
reason='Failed compatibility allocations require explicit raw runtime reconstruction before continuation review';assert reason in (R/normal).read_text()
write(D/'object/normal_reviewer_refusal_preserved.json',{'normal_root_reviewer_refusal_retained':True,'transport':{'path':rel,'sha256':pin},'root_helper':{'path':helper,'sha256':helperpin},'original_reviewer':{'path':normal,'sha256':normalpin},'observed_transport_returncode':1,'transport_contains_stderr_text':False,'root_reported_error':reason,'source_guard_text_verified':True,'interpretation':'Root reported exact line510 guard failure. Transport proves nonzero completion and unchanged source but does not capture stderr. Registered startup reviewer and this independent audit reconstruct the original failure, never suppress it.','subsequent_root_review':v['Object_review']['root_review'],'startup_failure_independently_reconstructed':True,'failed_job_id':'3028468','failed_GPU_seconds':69,'automatic_retry_authorized':False})
td=D/'transport_logs';td.mkdir();tr=[]
for name in ['last_two_independent_prepare_20261020T1644.jsonl','last_two_independent_prepare_v3_20261020T1644.jsonl','last_two_Goal23_audit_v1_20261020T1644.jsonl','last_two_Goal23_audit_v2_20261020T1644.jsonl','last_two_Object23_audit_v2_20261020T1644.jsonl','last_two_Goal23_cpu_v1_20261020T1644.jsonl','last_two_Object23_cpu_v2_20261020T1644.jsonl','review_last_two_20261020T1644.jsonl']:
 src=R/'results/formal_main_v2/control_transport'/name;data=src.read_bytes();j=[json.loads(x) for x in data.splitlines()];assert j[-1]['event']=='control_end'
 dest=td/name
 with dest.open('xb') as f:f.write(data)
 tr.append({'source':str(src.relative_to(R)),'private_copy':str(dest.relative_to(R)),'sha256':sha(src),'returncode':j[-1]['returncode']})
write(D/'transport_index.json',{'entries':tr,'all_closed':True,'raw_stderr_capture_claimed':False})
s={'schema':'formal_main_v2','kind':'last_two_training_independent_handoff','status':'two_pairs_passed_training_only','created_utc':datetime.now(timezone.utc).isoformat(),'evidence':refs,'pairs':{},'root_integration_candidate_delta':{'completed_arms':4,'reviewed_arm_updates':19000,'prior_root_completed_arms_expected':68,'after_if_root_integrates_all_completed_arms':72,'prior_root_reviewed_arm_updates_expected':341000,'after_if_root_integrates_reviewed_arm_updates':360000,'canonical_state_written_by_this_agent':False},'CPU':{'passed':62,'failed':0,'GPU_seconds':0},'cost_accounting':'Existing unique Slurm allocations only; no audit GPU allocation and no second addition to the global ledger.','Goal_development_HOLD_lifted':False,'Object_deployment_consumer_admission_granted':False,'final_states_opened':False,'scientific_release_authorized':False,'weights_copied_or_tensor_deserialized':False,'canonical_state_Git_Slurm_mutated':False,'nonweight_archive_publication_claimed':False,'limitations':['Goal23 has one fresh attempt per arm; original actual Goal F03, unchanged source and rehashed probe checkpoints supply shared restoration qualification.','Object23 exact observed500-step checkpoint and original optimizer/RNG restore code bind its real continuation; no checkpoint tensors independently deserialized.','Lossless Git raw-log archive publication is separate root work.','All selected metrics are offline teacher L1 diagnostics, not closed-loop success or latency claims.']}
for key,suite,jid,delta in [('Goal_review','libero_goal','3043813',10000),('Object_review','libero_object','3044844',9000)]:
 q=v[key];s['pairs'][jid]={'suite':suite,'seed':23,'visual_tokens':64,'completed_by_arm':q['completed_by_arm'],'new_reviewed_arm_updates':delta,'all_pair_allocated_GPU_seconds':q['cost']['all_pair_allocated_GPU_seconds'],'arms':{a:{k:x[k] for k in ['completed_updates','sample_uses','unique_windows','earliest_selected_update','selected_teacher_l1','selected_expert_l1','best_sha256','gradient_range','window_pool_coverage','window_pool_equivalent_traversals']} for a,x in q['arms'].items()}}
write(D/'handoff_summary.json',s)
text='# Final two training audits\n\nGoal64 seed23 and Object64 seed23 passed independent training-only acceptance. CPU fault injection:62 passed,0 failed. See handoff_summary.json for compact outcomes and exact evidence references.\n\nOriginal preparation failures and corrected versions are retained. Goal audit v1 failed at a wrong retrospective template citation; v2 corrected only that exact historical source path. Object authorization filename was corrected before execution. All original CUDA failure evidence and69GPU seconds remain. No canonical state, Git, Slurm, GPU, scientific-trial or final-release action was performed.\n\nRebuild using exact entrypoints/bindings from closed transport logs. Original raw journals stay on the server; root performs separate lossless Git archiving. Optimizer/RNG evidence limitations are explicit in the reports. Goal scientific development remains HOLD and no Object consumer admission is granted. The directory is immutable after delivery_manifest.json.\n'
with (D/'README.md').open('x') as f:f.write(text)
files=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  assert p.resolve().is_relative_to(D.resolve()) and not p.is_symlink() and p.suffix not in ['.pt','.ckpt','.bin','.safetensors','.pkl','.pickle','.pyc']
  files.append({'relative':p.relative_to(D).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
manifest={'schema':'cti_private_nonweight_delivery_v1','root':str(D),'kind':'last_two_training_independent_audit','files':files,'file_count':len(files),'bytes':sum(x['bytes'] for x in files),'summary':{'path':'handoff_summary.json','sha256':sha(D/'handoff_summary.json')},'weights':False,'mutable_after_manifest':False,'manifest_self_excluded':True}
write(D/'delivery_manifest.json',manifest)
print(json.dumps({'manifest':str((D/'delivery_manifest.json').relative_to(R)),'manifest_sha256':sha(D/'delivery_manifest.json'),'summary_sha256':sha(D/'handoff_summary.json'),'files':len(files),'bytes':manifest['bytes'],'CPU':s['CPU'],'status':s['status']}))
