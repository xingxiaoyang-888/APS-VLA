from pathlib import Path
import copy,hashlib,importlib.util,json,sys,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/integration_candidate_20261020T1418';P=D/'integrate_1418_v2.py'
assert hashlib.sha256(P.read_bytes()).hexdigest()=='b2c472fded9a1eed04ab769a97592b347e93b86d3c1a73c8ba28e96c3a807efd'
spec=importlib.util.spec_from_file_location('candidate_test',P);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
checks=[];t=time.perf_counter()
def ok(name,test):
 assert test,name;checks.append(name)
def rejected(name,fn):
 try:fn()
 except (ValueError,AssertionError,KeyError):checks.append(name);return
 raise AssertionError('not rejected: '+name)
state_path=R/'results/experiment_supervisor/state.json';state_before=m.sha(state_path);docs_before={p:m.sha(m.path(p)) for p in ['docs/'+n+'.md' for n in m.DOCS]}
s=m.rd('results/experiment_supervisor/state.json');m.precondition(s);d=m.inputs();checks.append('all original exact evidence/source173 pins reverified')
dispatch=m.rd(m.B+'/dispatch_root_report.json','69089fa48014bda5a438879d1e63e24990488b9539e08697ae15ee7fda153304');m.verify_dispatch(s,dispatch);checks.append('actual three dispatch ACK/committed/reservation/RP identities')
preview=m.rd('.local/integration_candidate_20261020T1418/preview_df3ead4d8590/'+m.SUMMARY)
obs=preview['scheduler'];cap=preview['capacity']
# PURE synthetic transaction fixture: align only the pre-cost floor with the frozen scheduler snapshot.
# Live controller has advanced independently; never apply this fixture to canonical state.
s=copy.deepcopy(s);s['current_round_cost']['allocated_gpu_seconds']=preview['allocated_GPU_seconds'];s['current_round_cost']['allocated_gpu_hours']=preview['allocated_GPU_hours']
after,summary,outputs=m.prepare(s,state_before,d,dispatch,m.ref(m.B+'/dispatch_root_report.json'),obs,cap,'CPU_SELFTEST_NOT_A_SCIENTIFIC_RESULT')
f=after['formal_main_progress'];ok('accept exactly1000',f['completed_development_trials']==5012 and f['current_action_development_trial_count']==3800)
ok('400 uniqueinitials and explicitLong600 retained',f['current_action_development_unique_initial_states']==400 and f['Long22_development_statistics']['explicit_legacy_equivalent_trials']==600)
ok('Goalheld200 excluded', '3049679' not in f['new_action_development_verified_by_job'] and next(x for x in f['nonLong_development_submissions_1317'] if x['job_id']=='3049679')['completed_trials_accepted']==0)
ok('new600 not accepted',sum(x['completed_trials_accepted'] for x in f['nonLong_development_submissions_1418'])==0)
ok('controller and registeredjobs byte-equivalent JSON',after['autonomous_training_v1']==s['autonomous_training_v1'] and after['registered_jobs']==s['registered_jobs'])
ok('training64 preserved',f['root_and_independent_completed_arms']==64 and f['completed_training_pairs']==s['formal_main_progress']['completed_training_pairs'] and f['automatic_machine_verified_pairs']==s['formal_main_progress']['automatic_machine_verified_pairs'])
ok('final stillsealed',f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created'])
ok('freshcost not acceptancecost addedtwice',after['current_round_cost']['allocated_gpu_seconds']==preview['allocated_GPU_seconds'])
for label,edit in [
 ('pending',lambda x:x.update(pending_submission={'status':'unknown'})),
 ('reservation',lambda x:x['autonomous_training_v1'].update(reserved_GPU_slots=1)),
 ('hold',lambda x:x['autonomous_training_v1'].update(root_submission_hold={'reason':'engineering'})),
 ('already applied',lambda x:x['formal_main_progress'].update(current_action_development_trial_count=3800)),
 ('finalreleased',lambda x:x['formal_main_progress'].update(global_release_created=True)),
 ('changedtrainingacceptance',lambda x:x['formal_main_progress'].update(root_and_independent_completed_arms=66))]:
 x=copy.deepcopy(s);edit(x);rejected('reject '+label,lambda:m.precondition(x))
x=copy.deepcopy(dispatch);x['submissions'][0]['suite']='libero_goal';rejected('reject heldGoal dispatcher substitution',lambda:m.verify_dispatch(s,x))
x=copy.deepcopy(dispatch);x['submissions'][0]['completed_trials_accepted']=200;rejected('reject unreviewed dispatch countedcomplete',lambda:m.verify_dispatch(s,x))
x=copy.deepcopy(s);x['formal_main_progress']['new_action_development_verified_by_job']['3049132']={};rejected('reject duplicate terminal acceptance',lambda:m.accept_terminals(x,d))
x=copy.deepcopy(obs);x['rows']['3043762']['status']='RUNNING';rejected('reject unbound3043762completedclaim',lambda:m.prepare(s,state_before,d,dispatch,m.ref(m.B+'/dispatch_root_report.json'),x,cap,'test'))
x=copy.deepcopy(cap);x['occupied']=list(map(str,range(9)));rejected('reject >8 GPU',lambda:m.prepare(s,state_before,d,dispatch,m.ref(m.B+'/dispatch_root_report.json'),obs,x,'test'))
rejected('reject path traversal',lambda:m.path('../state.json'));rejected('reject absolute path',lambda:m.path('/etc/passwd'))
docs,pins=m.documents(d,summary,'CPU_SELFTEST_ONLY')
for p in pins:
 original=m.path(p).read_bytes();ok('preserve prior document body '+p,docs[p].endswith(original.partition(b'\n')[2]))
ok('all7docs+blocker',len(docs)==8)
ok('GoalmeanCI documented','−1.333pp' in docs['docs/正式Goal主预算开发结果.md'].decode() and '100初态不因seed重复增至300' in docs['docs/正式Goal主预算开发结果.md'].decode())
ok('no canonicaldocs writes',all(m.sha(m.path(p))==v for p,v in docs_before.items()))
# A live controller may advance state independently; this CPU selfcheck never opens state for writing.
report=dict(schema='formal_main_v2',kind='integration_candidate_CPU_selfcheck',status='passed',checks=checks,count=len(checks),
 source=m.ref(str(P.relative_to(R))),private_synthetic_test=True,canonical_mutations=False,new_GPU_jobs=0,Slurm_mutations=False,Git_mutations=False,
 state_before_sha256=state_before,state_after_observed_sha256=m.sha(state_path),controller_may_independently_update=True,
 synthetic_cost_floor_aligned_to_private_preview=True,retained_prior_harness_failure='results/formal_main_v2/control_transport/integration_candidate_CPU_selfcheck_20261020T1418_v2.jsonl',elapsed_CPU_wall_seconds=time.perf_counter()-t,exact_dispatch=m.ref(m.B+'/dispatch_root_report.json'),root_bootstrap=m.pref('root_bootstrap'))
q=D/'cpu_selfcheck_v3.json'
with q.open('xb') as f:f.write(m.rawjson(report))
print(json.dumps(dict(status='passed',checks=len(checks),report=m.ref(str(q.relative_to(R)))),ensure_ascii=False))
