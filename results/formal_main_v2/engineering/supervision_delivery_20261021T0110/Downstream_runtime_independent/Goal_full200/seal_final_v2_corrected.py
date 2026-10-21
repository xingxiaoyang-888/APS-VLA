from pathlib import Path
import json,hashlib,tarfile,ast,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=Path(__file__).parent
A=R/'.local/goal_full200_author_20261021T0110_v2';V=D/'v2'
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def write(p,v):
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
ver=json.loads((V/'independent_checks.json').read_bytes());assert ver['status']=='passed' and len(ver['checks'])==123 and all(x['passed'] for x in ver['checks'])
rep=json.loads((V/'CPU_replay/report.json').read_bytes());assert len(rep['checks'])==74 and all(x['passed'] for x in rep['checks']) and rep['rejections']==56
pm=json.loads((A/'package/package_manifest.json').read_bytes());pins=pm['files']
sourcefile=R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';assert sha(sourcefile.read_bytes())=='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
src=json.loads(sourcefile.read_bytes());assert len(src['files'])==173
sourcechecks=[]
for root in (R,S):
 for p,h in src['files'].items():
  assert sha((root/p).read_bytes())==h,(str(root),p)
 sourcechecks.append({'root':str(root),'files':173,'verified':True})
top=json.loads((A/'actual_old58_loader_topology.json').read_bytes());p=R/top['raw_source']['path'];assert ref(p)==top['raw_source']
raw=[json.loads(x) for x in p.read_bytes().splitlines()];ls=[(i,x['phase']) for i,x in enumerate(raw) if x.get('phase','').startswith('existing_loader_event:')]
assert [x for i,x in ls]==top['loader_phase_order'] and len(ls)==8 and [i for i,x in ls]==list(range(8))
assert len([x for x in raw if x.get('event')=='trial_end'])==58
preservation={'schema':'formal_main_v2','source173_verified':True,'source_manifest':ref(sourcefile),'frozen_roots':sourcechecks,'actual_old58_topology':{'source':ref(p),'loader_phases':top['loader_phase_order'],'all_eight_before_original_first_trial':True,'original_terminal_witnesses':58,'not_new200_GPU_acceptance':True}}
write(V/'source_and_historical_loader_verification.json',preservation)
write(V/'read_only_helper_compatibility_note.json',{'status':'retained_read_only_helper_failure','error':'Login python3 lacked ast.get_source_segment; first in-memory read-only extraction exited before any writes. Repeated same source read under registered venv interpreter. No scientific/runtime code executed or changed.'})
tests=[]
for p in (D/'CPU_full200_v3/report.json',D/'CPU_outer_v3/report.json',D/'CPU_consumer_v2/report.json',V/'CPU_replay/report.json',V/'independent_checks.json'):
 x=json.loads(p.read_bytes());assert all(c['passed'] for c in x['checks'])
 tests.append({**ref(p),'check_count':len(x['checks']),'rejects':x.get('rejections',x.get('negative_cases',x.get('independent_rejections'))),'scope':'source/CPU fixture; real old metadata where explicitly identified; no new200 GPU terminal'})
gates=['Root exact immutable R/P publication of the 11-file package and source-only installation verification.',
       'Actual canonical P metadata/identity/storage verification and exact root authorization; available disk is not proof of quota.',
       'Separately audited native atomic held-ACK/CAS/all-mode8/same-Goal dispatcher and compute-node fresh storage ownership/exclusive claim.',
       'Exactly one prospective fixed200 execution; any input gate/policy_error/storage exception halts while retaining originals and cost.',
       'Future actual raw200 typed original consumer plus root and independent terminal review before new scientific adoption. Old200 remains HOLD; final global release is separate.']
review={'schema':'formal_main_v2','kind':'Goal_full200_v2_independent_source_CPU_review','status':'passed','reviewed_by':'independent','scope':'source_CPU_only','version':'goal-full200-prospective-single-attempt-v1','package_manifest':ref(A/'package/package_manifest.json'),'package_manifest_sha256':sha((A/'package/package_manifest.json').read_bytes()),'config':ref(A/'package/config.json'),'config_sha256':sha((A/'package/config.json').read_bytes()),'production_sources':pins,'package_files':pins,'install_files':ref(A/'install_files.json'),'author_delivery_manifest':ref(A/'delivery_manifest.json'),'source_delta':ref(A/'source_delta.json'),'blockers':[],'previous_version_rejected':ref(D/'v1_independent_review.json'),'original_v1_counterexample':ref(D/'counterexample_v1/blocker.json'),'v2_independent_rebuild':ref(V/'independent_checks.json'),'original_counterexample_now_rejected':True,'all_query_raw_five_components_required':True,'whole_capture_and_gate_order_verified':True,'source173_verified':True,'source_and_real_old_loader_verification':ref(V/'source_and_historical_loader_verification.json'),'independent_replayed_tests':tests,'unchanged_runtime_source_count':9,'other_consumer_AST_unchanged':True,'unchanged_scientific_scope':{'trial_count':200,'unique_development_initial_states':100,'methods':['A256_seed17','B256_seed17'],'policy_control_steps_bound':60000,'warmup_steps_separate':2000,'query_bound':7600,'single_attempt':True,'original_200_HOLD':True,'final_states_opened':False},'storage':{'RAW_required_bytes':9345375040,'P_required_bytes':5157355520,'raw_root':str(R/'results/formal_main_v2/raw_runtime/goal_full200_20261021T0110/attempt01'),'all_original_blobs_preserved_no_truncation':True,'capacity_and_write_exceptions_fail_closed':True,'available_bytes_not_quota':True,'requires_compute_node_fresh_capacity_owner_and_exclusive_claim':True},'limitations':['CPU fixture adaptation explicitly changes CPU marker assertion and two image dimensions; synthetic loader records are labelled and not actual GPU evidence. The production function rejects unmodified CPU arrays.','The 86 original-loop and 872 outer/source checks are inherited from this independent audit against exactly unchanged runtime sources, not rerun as new actual P acceptance.','Original old58 complete metadata chain demonstrates historical identities only. The new fixed200 full terminal does not yet exist.','Equal executed commands do not prove intermediate simulator state/RNG equality; old missing q9 arrays cannot be reconstructed and old200 is not admitted.'],'remaining_production_gates':gates,'production_ready':False,'production_admitted':False,'actual_P_verified':False,'real_GPU_acceptance':False,'GPU_execution_authorized':False,'new_GPU_submissions':0,'Slurm_queries':0,'state_written':False,'P_written':False,'Git_operations':0,'new_scientific_trials':0,'old200_HOLD':True,'final_sealed':True}
write(D/'final_independent_review.json',review)
ready={k:review[k] for k in ('schema','status','reviewed_by','version','package_manifest_sha256','config_sha256','production_sources','package_files','package_manifest','config','blockers','production_ready','production_admitted','remaining_production_gates','old200_HOLD','final_sealed')}
ready.update(kind='goal_full200_single_attempt_CPU_readiness',scope='source_CPU_only',original_chain_preserved=True,observer_gaps_fixed=True,paired_input_gate_CPU_passed=True,pre_policy_pair_equality_gate=True,all_query_input_integrity_gate=True,original_policy_error_retained_then_halt=True,full200_bound_tests_passed=True,original_typed_raw_consumer_ready=True,two_root_storage_contract_verified=True,real_GPU_acceptance=False,scientific_release=False,actual_P_verified=False,new_GPU_submissions=0,independent_full_review=ref(D/'final_independent_review.json'))
sp=importlib.util.spec_from_file_location('goal_final_schema',A/'package/entry.py');e=importlib.util.module_from_spec(sp);sys.modules[sp.name]=e;sp.loader.exec_module(e)
e.check_review(ready,'independent',ready['package_manifest_sha256'],ready['config_sha256'])
write(D/'independent_readiness.json',ready)
# Archive exactly the two newly produced private CPU raw directories. Do not
# duplicate loose archived trees in the delivery, but retain them on the server.
archives=[]
for path in (V/'CPU_replay',V/'independent_fixture'):
 files=sorted([p for p in path.rglob('*') if p.is_file()]);assert not any(p.is_symlink() for p in files)
 tar=path.with_name(path.name+'.independent.tar.gz')
 with tarfile.open(tar,'x:gz') as tf:
  for p in files:tf.add(p,arcname=p.relative_to(path).as_posix(),recursive=False)
 members=path.with_name(path.name+'.members.json');items=[{'path':p.relative_to(path).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files]
 write(members,{'file_count':len(items),'files':items})
 with tarfile.open(tar,'r:gz') as tf:
  actual=tf.getmembers();assert len(actual)==len(items)
  for a,b in zip(actual,items):assert a.isfile() and a.name==b['path'] and sha(tf.extractfile(a).read())==b['sha256']
 archives.append({'archive':ref(tar),'members':ref(members),'file_count':len(items)})
write(V/'independent_CPU_archives.json',{'archives':archives})
excluded=['CPU_full200_v3/','CPU_outer_v3/','CPU_consumer_v2/','counterexample_v1/','v2/CPU_replay/','v2/independent_fixture/']
files=[]
for p in sorted(D.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(D).as_posix()
 if any(rel.startswith(x) for x in excluded):continue
 if rel=='Goal_full200_manifest.json':continue
 files.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())})
assert not any(p.is_symlink() for p in D.rglob('*'))
manifest={'schema':'formal_main_v2','kind':'Goal_full200_independent_delivery_manifest','status':'frozen_source_CPU_review','files':files,'file_count':len(files),'source_root':str(D),'production_sources':pins,'package_manifest_sha256':ready['package_manifest_sha256'],'independent_readiness':ref(D/'independent_readiness.json'),'independent_full_review':ref(D/'final_independent_review.json'),'v1_blocker_preserved_in_exact_archive':True,'CPU_raw_records_exact_archives_not_scientific_results':True,'production_admitted':False,'GPU_execution_authorized':False,'new_GPU_submissions':0,'new_scientific_trials':0,'old200_HOLD':True,'final_sealed':True}
write(D/'Goal_full200_manifest.json',manifest)
for f in ('final_independent_review.json','independent_readiness.json','Goal_full200_manifest.json'):print(json.dumps(ref(D/f)))
