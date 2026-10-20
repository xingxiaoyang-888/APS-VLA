from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1644'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(n):return dict(path=n,sha256=h(R/n))
def checked(x):assert h(R/x['path'])==x['sha256'];return json.loads((R/x['path']).read_bytes())
def put(n,x):
 p=R/n;assert p.is_relative_to(R) and not any(q.is_symlink() for q in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as stream:json.dump(x,stream,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);stream.write(chr(10))
p=argparse.ArgumentParser();p.add_argument('--post-sha256',required=True);p.add_argument('--archive-sha256',required=True);args=p.parse_args()
postref=dict(path=E+'/last_terminals_integration_independent/post_attempt02/postapply_review.json',sha256=args.post_sha256)
post=checked(postref);archive=checked(dict(path=B+'/last_terminal_integration_independent_delivery.json',sha256=args.archive_sha256))
assert post['status']=='passed_actual_transaction_and_publication' and not post['production_state_written'] and post['Git_or_Slurm_calls']==0 and post['new_GPU_jobs']==0
assert all(x['passed'] for x in post['checks']) and any(x['name']=='173 frozen unchanged R and S' for x in post['checks'])
assert (post['training_arms'],post['reviewed_updates'],post['current_development'],post['compatible_development'],post['historical_development'],post['unique_initial_states'],post['final_trials'])==(72,360000,5200,5800,6412,400,0)
assert post['Goal_original200_HOLD'] and post['new_Goal_science_HOLD'] and post['existing_3052166_single_registration']
assert post['controller_training_complete_is_normal'] and post['no_controller_restart_performed']
assert post['summary']==dict(path=B+'/last_terminals_integration.json',sha256='90c214ae6a1e28356823ed26585dd869c8edca1568c54452679ae9a251229422')
summary=checked(post['summary']);completion=checked(post['root_completion']);checked(post['intent'])
assert post['actual_after_compact_sha256']==completion['state_after_sha256'] and summary['global_cost_unchanged']
assert archive['status']=='exact_complete_nonweight_packages_archived' and archive['root_state_unchanged']
for x in archive['copies']:
 assert h(R/x['archive']['path'])==x['archive']['sha256']==x['source']['sha256'] and h(R/x['source']['path'])==x['source']['sha256']
for x in post['publications']:assert h(R/x['path'])==x['sha256']
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('lastTerminalPost1644',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sn='results/experiment_supervisor/state.json';before=h(R/sn);s=json.loads((R/sn).read_bytes());old=copy.deepcopy(s);f=s['formal_main_progress'];a=s['autonomous_training_v1'];key='last_terminals_integrity_review_20261020T1644'
 assert key not in f and f['last_terminals_integration_20261020T1644']==post['summary']
 assert (f['root_and_independent_completed_arms'],f['root_and_independent_reviewed_arm_updates'],f['current_action_development_trial_count'],f['completed_development_trials'])==(72,360000,5200,6412)
 assert len(a['completed_pairs'])==36 and not a['blocked_pairs'] and not f['test_opened'] and not f['global_release_created'] and f['completed_final_trials']==0 and '3049679' not in f['new_action_development_verified_by_job']
 assert s['pending_submission'] is None and a['reserved_GPU_slots']==0 and a['root_submission_hold'] is None
 assert sum(str(x['job_id'])=='3052166' for x in s['registered_jobs'])==1
 receipt=dict(status='passed',summary=post['summary'],independent_review=postref,archival=ref(B+'/last_terminal_integration_independent_delivery.json'),root_completion=post['root_completion'],root_completed_arms=72,reviewed_updates=360000,development_current=5200,development_compatible=5800,development_historical=6412,unique_initial_states=400,Goal_original200_HOLD=True,all_new_Goal_scientific_HOLD=True,final_sealed=True,final_trials=0,global_release=False,new_GPU_jobs=0,science_registry_controller_cost_preserved=True,controller_admissions_inherited_not_new_machine_review=True,controller_training_completion_is_normal=True,utc=datetime.now(timezone.utc).isoformat())
 rp=B+'/last_terminals_root_post_acceptance.json';put(rp,receipt);f[key]=dict(status='passed',summary=post['summary'],independent_review=postref,root_acceptance=ref(rp),scientific_gate_changed=False)
 s['updated_utc']=receipt['utc']
 for k in old:
  if k not in ('formal_main_progress','updated_utc'):assert old[k]==s[k],k
 for k,v in old['formal_main_progress'].items():assert f[k]==v,k
 c.atomic_json(R/sn,s,before)
 print(json.dumps(dict(status='root_accepted_exact72_training_and800_development_integration',receipt=ref(rp),independent_review=postref)))
