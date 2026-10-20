from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=Path(__file__).parent;S=P/'snapshots/formal_main_v2_run_564be0995e';PKG='scripts/ops/formal_goal_prefix58_observer_v2';BASE='results/formal_main_v2/engineering/goal_prefix58_20261020T1825';O=D/'post_publication';O.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def put(n,x):
 with (O/n).open('x') as f:json.dump(x,f,sort_keys=True,indent=2);f.write(chr(10))
pub=R/'results/formal_main_v2/preflight/heartbeat_20261021T0225/Goal_prefix58_publication.json';assert sha(pub)=='03bec8d979c721a7866e8ac72cbe4b443b2a8c060c90426b592af27ca3f610cb';receipt=read(pub);assert receipt['GPU_jobs_submitted']==0 and not receipt['real_GPU_acceptance'] and not receipt['scientific_release']
assert len(receipt['files'])==7;verified=[]
for row in receipt['files']:
 assert sha(R/row['source'])==sha(R/row['destination'])==sha(P/row['destination'])==row['sha256'];assert (R/row['source']).stat().st_size==(R/row['destination']).stat().st_size==(P/row['destination']).stat().st_size==row['bytes'];verified.append(row)
authpath=R/BASE/'root_authorization.json';authsha='195e064794973fbc533dfc6c51afd7ec3fbb942734753c1d7f1a7b9c81687a75';assert sha(authpath)==sha(P/BASE/'root_authorization.json')==authsha
epath=R/PKG/'entry.py';assert sha(epath)=='da3e094a98104d08735d6da6a180b326f79ae077e710880aa9117b39b911e31f';sp=importlib.util.spec_from_file_location('g58_actual_published_gate',epath);e=importlib.util.module_from_spec(sp);sys.modules[sp.name]=e;sp.loader.exec_module(e)
config=read(P/PKG/'config.json');auth=read(authpath);mh=sha(P/PKG/'package_manifest.json');ch=sha(P/PKG/'config.json');e.validate_config(config);e.validate_authorization(auth,ch,mh,sha(epath));reviews={}
for role in ['root','independent']:
 x=auth[role+'_review'];assert x=={'path':str(P/BASE/(role+'_readiness.json')),'sha256':sha(P/BASE/(role+'_readiness.json'))};assert sha(R/BASE/(role+'_readiness.json'))==x['sha256'];e.check_review(read(P/BASE/(role+'_readiness.json')),role,mh,ch);reviews[role]=x
assert reviews['independent']['sha256']=='660a2f543e7f64ce0105e50dcd908d55bf9db4ee7b73aedb7994738b424ae057'
inv=R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';assert sha(inv)=='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926';frozen=read(inv)['files'];assert len(frozen)==173
for n,pin in frozen.items():assert sha(R/n)==sha(S/n)==pin,n
s=read(R/'results/experiment_supervisor/state.json');assert s['pending_submission'] is None and not any(j.get('stage_key')=='goal_prefix58_20261020T1825' or j.get('name')=='cti-goal-prefix58' for j in s['registered_jobs']);assert s['autonomous_training_v1']['reserved_GPU_slots']==0;assert not (P/BASE/'attempt01').exists() and not (P/BASE/'held_dispatch_record.json').exists();assert not s['formal_main_progress']['test_opened'] and not s['formal_main_progress']['global_release_created'] and s['formal_main_progress']['completed_final_trials']==0
report=dict(schema='formal_main_v2',kind='independent_Goal_prefix58_actual_publication_review',status='passed',blockers=[],publication=ref(pub),authorization=ref(authpath),published_files=verified,canonical_candidate_R_P_all7_equal=True,CPU_readiness_refs=reviews,original173_R_and_snapshot_unchanged=True,pre_dispatch_no_duplicate_no_pending=True,state_observed_sha256=sha(R/'results/experiment_supervisor/state.json'),state_modified=False,actual_GPU_runtime_chain_verified=False,scientific_release=False,dispatcher_independent=ref(D/'dispatch_v3_attempt02/independent_review.json'),original200_and_new_Goal_science_HOLD=True,limits=['CPU/pre-execution identity verification only; root may execute one held dispatch after original lifecycle gates pass.','No actual GPU command, Slurm call, weight load or final value read was performed.'])
put('independent_review.json',report);print(json.dumps(ref(O/'independent_review.json')))
