"""Independent actual read-only science bridge; synthetic submission handoff only."""
from pathlib import Path
import sys,json,copy,hashlib,time
from types import SimpleNamespace
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');O=R/'.local/autonomous_training_v1/audit';D=R/'scripts/ops/formal_autonomous_training_v1'
sys.path[:0]=[str(D),str(R/'src'),str(R/'scripts')]
import controller as c,backend as b,worker as w
PINS={'controller.py':'4ac7dfa79345ec8a3db3ad1aa44c560d887ea691813d778bb8e1851e55ea9eec','backend.py':'54694bfd4c65db931a2a98574d0f4e916a262a5b4b5b4a67fd4debbc96bc0b7a','worker.py':'c96f8d0de3dd36e263a4bf7c332345db2abd52dd83a9e317620e00143cf86072','execution.py':'f74cd59b04bf616a29564784a07d1e36a5f31e33f565830d5b2aee905d75755b'}
for n,s in PINS.items():assert c.file_sha(D/n)==s
statepath=R/'results/experiment_supervisor/state.json';state_before=c.file_sha(statepath);state=c.read_json(statepath)
reg=c.read_json(R/'configs/experiments/formal_main_v2.json')
activation=dict(controller_run_root='.local/autonomous_training_v1/audit/bridge_work',execution_adapter={'path':str((D/'execution.py').relative_to(R)),'sha256':PINS['execution.py']},worker={'path':str((D/'worker.py').relative_to(R)),'sha256':PINS['worker.py']})
backend=b.Backend(R,activation)
rows=[]
for key in ['libero_goal_k256_seed17','libero_object_k64_seed41','libero_10_k128_seed17','libero_spatial_k128_seed17']:
    pair=next(p for p in reg['pairs'] if c.pair_key(p)==key)
    history=sorted([j for j in state['registered_jobs'] if c.job_pair(j)==key],key=lambda j:j['submitted_utc'])
    existing=None
    if history:
        assert all(j['status']=='COMPLETED' and j['exit_code']=='0:0' for j in history)
        path=pair['run_root_server'][len(str(c.P))+1:]+'/training/segment_reviews/'+history[-1]['job_id']+'.json'
        existing={'path':path,'sha256':c.file_sha(R/path)}
    check_output=str((O/('real_bridge_a1_'+key)).relative_to(R))
    began=time.time();outcome=backend.review_pair(pair,history,state,check_only=True,existing_review=existing,check_output=check_output)
    assert c.file_sha(statepath)==state_before
    assert outcome['decision'] in {'ready','complete'}
    if outcome['decision']=='ready':
        plan=outcome['plan'];c.validate_plan(plan,pair,history)
        assert not (R/plan['invocation']).exists() and not (c.P/plan['invocation']).exists()
        assert plan['target_updates']==5000 and plan['autonomous_execution']['validation_updates']==list(range(0,5001,500))
    else:
        assert outcome['completed_by_arm']=={'A':5000,'B':5000} and outcome['selected_checkpoints_verified']
    # Feed exact real outcome into real controller with synthetic registry/capacity and submission only.
    class DryBackend:
        def inspect_and_prepare(self,p,h,s):
            return copy.deepcopy(outcome) if c.pair_key(p)==key else {'decision':'blocked','reason':'outside_single_case_harness'}
        def verify_evidence(self,refs):backend.verify_evidence(refs,force=True)
        def verify_prepared_plan(self,p):
            assert p==outcome['plan'];c.validate_plan(p,pair,history)
            # Invocation publication intentionally excluded; tests cover orphan protection separately.
    class DryScheduler:
        def __init__(self):self.calls=[]
        def observe(self,jobs):
            return dict(rows={j['job_id']:dict(status=j['status'],exit_code=j['exit_code'],elapsed_seconds=j['elapsed_seconds'],allocation=j.get('allocation','gres/gpu=1'),node=j.get('node','audit'),gpus=1) for j in jobs},queue={},raw_sacct='synthetic_capacity_only',raw_squeue='')
        def submit(self,argv):self.calls.append(argv);return SimpleNamespace(returncode=0,stdout='9900001\n',stderr='')
    fake=O/('handoff_a1_'+key);fake_state=fake/'results/experiment_supervisor/state.json';c.atomic_json(fake_state,dict(registered_jobs=copy.deepcopy(history),pending_submission=None))
    scheduler=DryScheduler();co=c.Controller(fake,fake/'service',reg['pairs'],DryBackend(),scheduler,'d'*64,'synthetic')
    with co.leadership():result=co.tick()
    fs=c.read_json(fake_state)
    if outcome['decision']=='ready':
        assert result['status']=='submitted' and len(scheduler.calls)==1
        j=fs['registered_jobs'][-1]
        assert j['autonomous_execution']==outcome['plan']['autonomous_execution']
        assert j['allocation_time']=='48:00:00' and j['soft_wall_seconds']==169200 and j['name']=='cti-formal'
        for field in ['runtime_compatibility','component_compatibility']:
            assert j.get(field)==outcome['plan']['invocation_contents'].get(field)
    else:
        assert not scheduler.calls and fs['formal_main_progress']['trained_arms']==2
        assert fs['formal_main_progress']['completed_training_pairs'][key]['verification_kind']=='machine_automatic_not_independent'
    rows.append(dict(pair=key,decision=outcome['decision'],completed_by_arm=outcome['completed_by_arm'],actual_nonweight_and_checkpoint_hash_review=True,actual_checkpoint_deserialization=False,execution_seconds=time.time()-began,machine_output=outcome['machine_output'],evidence_refs=outcome['evidence_refs'],synthetic_controller_handoff=result,actual_Slurm_calls=0,actual_invocations_published=0))
    print(json.dumps({k:v for k,v in rows[-1].items() if k!='evidence_refs'}),flush=True)
assert c.file_sha(statepath)==state_before
for n,s in PINS.items():assert c.file_sha(D/n)==s
result=dict(schema='formal_main_v2',kind='independent_actual_readonly_bridge_and_synthetic_scheduler_handoff',status='passed',files={str((D/n).relative_to(R)):s for n,s in PINS.items()},cases=rows,real_state_sha256_before_after=state_before,actual_Slurm_calls=0,actual_invocations_published=0,new_GPU_seconds=0,sealed_states_opened=False,weight_bytes_copied=0)
w.immutable(O/'real_bridge_a1.json',result)
print('FINAL',c.file_sha(O/'real_bridge_a1.json'),flush=True)
