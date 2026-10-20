from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/k64_terminal_independent_20261020T2054'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':h(p)}
def save(name,data):
 p=D/name
 with p.open('x') as f:json.dump(data,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 return ref(p)
assert os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R)
refs={'3053875':('v2_3053875_independent_review.json','ba1191c8f03bef87ba97608e4d2f6048f1a282776864b0e16ff0d4f68d71d1f7'),'3053894':('v3_3053894_independent_review.json','592eeefe20ceef41e444479aded178e042596d261ca8598cb62d3ef7e81a98e5')}
jobs={}
for jid,(name,pin) in refs.items():
 p=D/name;assert h(p)==pin;r=json.loads(p.read_text());assert r['status']=='passed' and r['job_id']==jid and r['trials']==200 and r['full_original_consumer_reconstruction_passed'] is True and r['new_GPU_jobs']==0
 jobs[jid]=r
transports=[]
for jid in ['3053875','3053894']:
 for attempt in ['01','02']:
  name='independent_k64_'+jid+'_20261020T2054_attempt'+attempt+'.jsonl';p=R/'results/formal_main_v2/control_transport'/name;blob=p.read_bytes();rows=[json.loads(x) for x in blob.splitlines()]
  assert rows[-1]['event']=='control_end' and rows[-1]['source173_and_entrypoint_unchanged'] is True and rows[-1]['returncode']==(0 if attempt=='02' else 1)
  target=D/('transport_'+jid+'_attempt'+attempt+'.jsonl')
  with target.open('xb') as f:f.write(blob)
  transports.append({'original':ref(p),'copy':ref(target),'returncode':rows[-1]['returncode']})
checks={jid:{'review':{'path':(D/n).relative_to(R).as_posix(),'sha256':pin}} for jid,(n,pin) in refs.items()}
aggregate={'schema':'formal_main_v2','kind':'independent_development_terminal_pair_batch','status':'passed','review_role':'independent','reviewed_utc':datetime.now(timezone.utc).isoformat(),'totals':{'allocated_gpu_seconds':sum(j['allocated_gpu_seconds'] for j in jobs.values()),'chunks':sum(j['full_action_chunks'] for j in jobs.values()),'executed_actions':sum(j['executed_control_actions'] for j in jobs.values()),'trials':400,'unique_initial_states_in_this_two_suite_batch':200,'new_distinct_development_states_claimed':0},'jobs':jobs,'source_reviews':checks,'transport_runs':transports,'notes':['Each completed allocation is counted once:3053875=2283seconds;3053894=2175seconds. Training costs are provenance only, not added again.','The two CPU audit failures were extra independent-check assumptions (demonstration macro aggregation and sign(0) gripper); original scientific evidence was not changed. All failures, corrected source and partial diagnostics retained.','Full consumer reconstruction is source-specific for each pair; no other-pair bridge or Long compatibility conclusion was reused.','Recorded current t0 hashes are after original policy calls; their equality does not prove before-call immutability. Later diverged trajectory observations are not treated as paired.','These two development jobs are new current-action results. They do not admit Object historical600, Spatial historical600, or Goal historical200.','No new GPU jobs, mutable state writes, Git changes, final release or sealed state access. Root controls admission and integration.'],'new_GPU_jobs':0,'final_release':False,'sealed_final_values_read':False,'checkpoint_bytes_copied':False,'state_written':False}
assert aggregate['totals']['allocated_gpu_seconds']==4458 and aggregate['totals']['chunks']==6289 and aggregate['totals']['executed_actions']==48847
aggregate_ref=save('independent_review.json',aggregate)
text="# Independent terminal audit: Spatial and Object 64-token seed23\n\nBoth existing jobs pass independent whole-consumer reconstruction and all raw trial checks. Spatial3053875 and Object3053894 each contain200 trials on the fixed100 development initial states, A96/B97, paired A-only1/B-only2. All6289 chunks and48847 recorded control commands were checked. Both original controller clipping checks are byte-inactive for these records.2283+2175=4458GPU seconds are each counted once.\n\nThe retained CPU audit corrections fix the independent verifier only: demonstration error uses task-macro aggregation, and the unchanged original -np.sign gripper mapping permits signed zero at its exact midpoint. No actions, outcomes, model selection, scientific configuration or source bridge was altered. All failed CPU checks and partial outputs are retained.\n\nindependent_review.json contains the requested jobs/totals structure, per-task paired outcomes, selected-checkpoint offline teacher/demonstration L1, and validation/t0 token diagnostics. Per-window and per-state records are linked and fully retained. The existing original raw ledgers remain in canonical results under the hashes recorded in each report.\n\nThis is not a new GPU run or authorization. No state/Git changes, final release or sealed-value access occurred. The report does not adopt any historical held Object, Spatial or Goal batch. Current t0 equality applies to original recorded post-policy hashes, not a before-policy mutation proof.\n"
with (D/'README.md').open('x') as f:f.write(text)
files=[]
for p in sorted(D.iterdir()):
 if not p.is_file():raise ValueError('unexpected nested private output')
 if p.suffix.lower() in {'.pt','.pth','.safetensors','.ckpt','.npz'}:raise ValueError('forbidden weight/raw-array output')
 files.append({'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':h(p)})
manifest=save('delivery_manifest.json',{'schema':'formal_main_v2','kind':'independent_k64_terminal_delivery','status':'passed','root':str(R),'source_directory':D.relative_to(R).as_posix(),'entrypoint':ref(Path(__file__).resolve()),'independent_review':aggregate_ref,'files':files,'file_count':len(files),'bytes':sum(x['bytes'] for x in files),'new_GPU_jobs':0,'final_release':False,'all_CPU_attempts_retained':True})
print(json.dumps({'manifest':manifest,'independent_review':aggregate_ref,'file_count':len(files),'bytes':sum(x['bytes'] for x in files),'totals':aggregate['totals']},sort_keys=True))
