"""Independent CPU fault injection. All writes target pytest-owned isolated roots."""
import copy, importlib.util, json
from pathlib import Path
from types import SimpleNamespace
import pytest
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
C=R/'.local/cuda_recovery_autonomous_1940'
sp=importlib.util.spec_from_file_location('ind1940_author_fixture',C/'test_gateway.py')
a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
g,c,e=a.g,a.c,a.e
def fresh(tmp_path,**kw):return a.dataset(tmp_path/'synthetic_control',**kw)

def test_real_slurm_observation_queries_every_registry_ID_without_submission():
    jobs=[
      dict(job_id='11',experiment='formal_main_v2',mode='engineering',gpus=1,status='RUNNING'),
      dict(job_id='12',experiment='formal_main_v2',mode='controller',gpus=0,status='RUNNING'),
      dict(job_id='13',experiment='G0',gpus=1,status='COMPLETED',exit_code=0)]
    calls=[]
    def runner(argv,**kwargs):
        calls.append(argv)
        if argv[0]=='sacct':
            return SimpleNamespace(returncode=0,stdout='11|RUNNING|0:0|5|cpu=7,gres/gpu=1|g1|cti|x\n12|RUNNING|0:0|7|cpu=1|c1|ctl|y\n13|COMPLETED|0:0|9|gres/gpu=1|g0|g0|\n',stderr='')
        assert argv[0]=='squeue'
        return SimpleNamespace(returncode=0,stdout='11|RUNNING|x\n12|RUNNING|y\n',stderr='')
    snap=c.Slurm(runner=runner).observe(jobs)
    assert calls[0][calls[0].index('-j')+1]=='11,12,13'
    assert calls[1][calls[1].index('-j')+1]=='11,12'
    cap=c.capacity(jobs,snap,'12')
    assert cap==dict(occupied=['11'],unknown=[],active_pairs={},findings=[])
    assert not any(x[0]=='sbatch' for x in calls)

def test_unknown_CPU_record_still_blocks(tmp_path):
    f=fresh(tmp_path)
    f.slurm.mutate=lambda s:s['rows']['900'].update(status='UNKNOWN')
    before=f.path.read_bytes()
    with pytest.raises(ValueError,match='uncertain scheduler'):f.run.run(submit=True)
    assert before==f.path.read_bytes() and not f.slurm.calls

def test_second_capacity_query_denies_eighth_GPU(tmp_path):
    f=fresh(tmp_path,count=8);base=f.slurm.observe;seen=[]
    def observed(jobs):
        result=base(jobs);seen.append(1)
        if len(seen)==1:
            result['rows']['8']['status']='COMPLETED';result['queue'].pop('8')
        return result
    f.slurm.observe=observed
    with pytest.raises(ValueError,match='eight GPU'):f.run.run(submit=True)
    assert len(seen)==2 and not f.slurm.calls
    assert c.read_json(f.path)['pending_submission'] is None and not f.run.audit.exists()

def test_one_active_failed_pair_already_denied_below_capacity(tmp_path):
    f=fresh(tmp_path,count=6);s=c.read_json(f.path)
    j=copy.deepcopy(s['registered_jobs'][0]);j.update(job_id='88',status='PENDING',exit_code='0:0')
    s['registered_jobs'].append(j);a.write(f.path,s)
    with pytest.raises(ValueError,match='failed pair already active'):f.run.run(submit=True)
    assert not f.slurm.calls

def test_all_failed_rows_cost_and_opaque_controller_survive(tmp_path):
    f=fresh(tmp_path);s=c.read_json(f.path)
    for jid in ('3028468','3028522'):
        case=e.CASES[jid]
        s['registered_jobs'].append(dict(job_id=jid,experiment='formal_main_v2',mode='train',suite=case[0],visual_tokens=case[1],training_seed=23,status='FAILED',exit_code='1:0',elapsed_seconds=case[4],gpus=1))
    s['registered_jobs'].append(dict(job_id='123',experiment='G0',status='COMPLETED',exit_code=0,gpus=1))
    s['autonomous_training_v1'].update(extra_nested={'completed':['unrelated'],'journal':{'generation':98}})
    s['legacy_history']={'untouched':[False,3,'text']}
    a.write(f.path,s);old=copy.deepcopy(s)
    f.slurm.mutate=lambda snap:snap['rows']['123'].update(exit_code='0:0')
    result=f.run.run(submit=True);now=c.read_json(f.path)
    assert now['registered_jobs'][:-1]==old['registered_jobs']
    failed=[j for j in now['registered_jobs'] if j['status']=='FAILED']
    assert {j['job_id'] for j in failed}==set(e.CASES) and sum(j['elapsed_seconds'] for j in failed)==226
    assert now['legacy_history']==old['legacy_history']
    assert now['autonomous_training_v1']['extra_nested']==old['autonomous_training_v1']['extra_nested']
    assert now['autonomous_training_v1']['blocked_pairs']==old['autonomous_training_v1']['blocked_pairs']
    assert now['current_round_cost']['allocated_gpu_seconds']==226
    assert result['job']['segment_end']==500
    assert 'autonomous_execution' not in result['job']

def test_final_CAS_failure_keeps_known_job_pending_and_never_resends(tmp_path,monkeypatch):
    f=fresh(tmp_path);original=c.atomic_json;calls=[]
    def fault(path,value,expected_sha=None):
        calls.append(copy.deepcopy(value))
        if len(calls)==3:raise OSError('independent final-CAS failure')
        return original(path,value,expected_sha)
    monkeypatch.setattr(c,'atomic_json',fault)
    with pytest.raises(OSError,match='final-CAS'):f.run.run(submit=True)
    now=c.read_json(f.path)
    assert now['pending_submission']['known_job_id']=='9999'
    assert now['registered_jobs']==f.state['registered_jobs']
    assert now['autonomous_training_v1']['reserved_GPU_slots']==1
    assert (f.root/'results/formal_main_v2/submissions/9999.json').is_file()
    with pytest.raises(ValueError):f.run.run(submit=True)
    assert len(f.slurm.calls)==1

def typed_box(tmp_path):
    root=tmp_path/'typed_synthetic_root'
    copied=[C/'gateway.py',C/'evidence.py']+[R/x for x in e.FIVE]+[R/g.CONTROLLER,R/g.ACTIVATION['path'],R/e.PUBLICATION['path'],R/e.NODE['path']]
    for p in copied:
        dest=root/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    module_path=root/(C/'gateway.py').relative_to(R)
    sp=importlib.util.spec_from_file_location('ind_typed1940',module_path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
    def put(rel,value):
        path=root/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(m.canonical(value))
        return dict(path=rel,sha256=m.sha(path.read_bytes()))
    files=m.source_files(root)
    ind={'schema':'formal_main_v2','kind':'cuda_startup_server_recovery_gateway_independent_CPU_review','status':'passed_CPU_review','files':files,'synthetic':True}
    indref=put('results/formal_main_v2/synthetic_independent.json',ind)
    failure=put('results/formal_main_v2/synthetic_failure.json',{'synthetic':True})
    repair=put('results/formal_main_v2/synthetic_repair.json',{'synthetic':True})
    auth=dict(schema='formal_main_v2',kind='cuda_startup_single_recovery_authorization',version=m.VERSION,
      status='approved_for_exactly_one_original_target_recovery',failed_job_id='3028460',original_target=500,
      maximum_new_attempts=1,automatic_retry=False,resume=True,wall_seconds=12600,slurm_time='04:00:00',
      excluded_nodes=['gpu4020'],source_sha256=e.SOURCE_SHA,control_root=str(m.R),runtime_root=str(e.P),
      gateway_files=files,original_recovery_files=e.FIVE,canonical_publication=e.PUBLICATION,node_exclusion=e.NODE,
      independent_review=indref,controller_activation=m.ACTIVATION,controller_job_id='900',
      final_release_authorized=False,continuous5000_admission_authorized=False,repair_record=repair,canonical_failure_review=failure)
    authpath='configs/experiments/synthetic_authorization.json'
    def seal(changed=None,reservation_change=None):
        value=copy.deepcopy(auth)
        if changed:changed(value)
        reservation=dict(schema='formal_main_v2',kind='root_CUDA_recovery_GPU_slot_reservation',
          status='approved_for_named_single_recovery',reserved_slots=1,capacity_limit_all_GPU_modes=8,
          controller_job_id='900',failed_job_id='3028460',original_target=500,
          authorization_path=authpath,authorization_intent_sha256=m.intent_sha(value),automatic_retry=False)
        if reservation_change:reservation_change(reservation)
        value['root_reservation']=put('results/formal_main_v2/synthetic_reservation.json',reservation)
        return put(authpath,value)
    return SimpleNamespace(root=root,module=m,seal=seal,put=put,ind=ind,auth=auth)

def test_typed_gate_real_validator_positive_and_no_authorization_from_publication_alone(tmp_path):
    f=typed_box(tmp_path);ref=f.seal();auth,evidence=f.module.validate_authorization(f.root,ref)
    assert auth['original_target']==500 and len(evidence.hashes)>=14
    wrong=f.put('configs/experiments/wrong_authority.json',{'schema':'formal_main_v2','status':'passed'})
    with pytest.raises(ValueError,match='typed authorization'):f.module.validate_authorization(f.root,wrong)

@pytest.mark.parametrize('fault',['wrong_source','old_review_kind','target5000','v3_reservation','intent_drift','continuous_permission'])
def test_authorization_identity_and_ownership_rejected(tmp_path,fault):
    f=typed_box(tmp_path)
    def change(v):
        if fault=='wrong_source':v['gateway_files']={**v['gateway_files'],next(iter(v['gateway_files'])):'0'*64}
        if fault=='old_review_kind':
            ind=copy.deepcopy(f.ind);ind['kind']='startup_failure_review'
            v['independent_review']=f.put('results/formal_main_v2/old_review.json',ind)
        if fault=='target5000':v['original_target']=5000
        if fault=='continuous_permission':v['continuous5000_admission_authorized']=True
    def rchange(v):
        if fault=='v3_reservation':v['kind']='root_action_v3_reservation'
        if fault=='intent_drift':v['authorization_intent_sha256']='0'*64
    ref=f.seal(change,rchange)
    with pytest.raises(ValueError):f.module.validate_authorization(f.root,ref)

@pytest.mark.parametrize('path',['configs/manifests/formal_main_v2/libero_goal/initial_states/sealed_final.json','results/x/initial_states/value.json','results/final_states/b.json','results/a/test_state99.json'])
def test_state_value_path_fails_before_stat_open(tmp_path,monkeypatch,path):
    ev=e.Evidence(tmp_path)
    def forbidden(*args,**kwargs):raise AssertionError('forbidden path reached filesystem')
    monkeypatch.setattr(e,'stable_sha',forbidden)
    with pytest.raises(ValueError):ev.read(path)

def native_case(tmp_path,monkeypatch,fresh):
    P=tmp_path/'P';H=tmp_path/'H';S=P/'snapshots/source'
    monkeypatch.setattr(e,'P',P);monkeypatch.setattr(e,'H',H);monkeypatch.setattr(e,'S',S)
    suite,budget=('libero_object',256) if fresh else ('libero_spatial',64)
    rel=f'results/formal_main_v2/{suite}/k{budget}/seed23/training';out=P/rel;out.mkdir(parents=True)
    (out/'.training.lock').touch();(out/'failure.json').write_bytes(b'{"synthetic":true}\n')
    checkpoint=H/f'checkpoints/formal_main_v2/{suite}/k{budget}/seed23';checks=[]
    for arm in ('A','B'):
        p=checkpoint/arm/'resume.pt'
        if fresh:checks.append(dict(arm=arm,path=str(p),exists=False))
        else:
            p.parent.mkdir(parents=True);p.write_bytes(b'CPU-fixture-'+arm.encode())
            checks.append(dict(arm=arm,path=str(p),exists=True,**e.stable_sha(p)))
    S.mkdir(parents=True);(S/'source.py').write_bytes(b'pass\n')
    wrapper=P/'wrapper.slurm';wrapper.write_bytes(b'# CPU fixture\n')
    plan=dict(inventory={'files':{'source.py':e.stable_sha(S/'source.py')['sha256']}},remote_watched={},
       wrapper=str(wrapper),wrapper_sha256=e.stable_sha(wrapper)['sha256'],invocation_relative='results/formal_main_v2/invocations/new.json',
       proof=dict(output_relative=rel,suite=suite,visual_tokens=budget,server_resume_checks=checks,
           evidence_bundle={rel+'/failure.json':e.stable_sha(out/'failure.json')}),fresh=fresh)
    return plan,out,checkpoint

@pytest.mark.parametrize('fault',['zero_root','new_update','resume_bytes'])
def test_native_read_only_preflight_rejects_new_training_evidence(tmp_path,monkeypatch,fault):
    plan,out,checkpoint=native_case(tmp_path,monkeypatch,fault!='resume_bytes')
    before=set(tmp_path.rglob('*'))
    result=e.NativeIO().preflight(plan)
    assert set(tmp_path.rglob('*'))==before and result['model_loaded'] is False
    if fault=='zero_root':checkpoint.mkdir(parents=True)
    elif fault=='new_update':
        (out/'A').mkdir();(out/'A/training_progress.json').write_bytes(b'{"update":1}')
    else:(checkpoint/'B/resume.pt').write_bytes(b'changed CPU fixture')
    with pytest.raises(ValueError):e.NativeIO().preflight(plan)
