"""Auditor launcher fault injection; all scheduler calls and admission proof mocked."""
import importlib.util,sys,subprocess,fcntl,json,os
from pathlib import Path
from types import SimpleNamespace
import pytest
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
sys.path.insert(0,str(R/'.local/autonomous_training_v1/controller'))
import controller as c
spec=importlib.util.spec_from_file_location('audited_launcher',R/'scripts/ops/formal_autonomous_training_v1/activate.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
@pytest.fixture
def case(tmp_path,monkeypatch):
    root=tmp_path/'control';runtime=tmp_path/'runtime';monkeypatch.setattr(c,'R',root);monkeypatch.setattr(c,'P',runtime)
    state=root/'results/experiment_supervisor/state.json';monkeypatch.setattr(a,'STATE',state)
    c.atomic_json(state,dict(registered_jobs=[],pending_submission=None,formal_main_progress={'completed_training_pairs':{}},execution_authorization_update={}))
    wrapper=root/'scripts/ops/formal_autonomous_training_v1/service.slurm';wrapper.parent.mkdir(parents=True);wrapper.write_text('# synthetic shell\n')
    act=dict(controller_sha256=c.file_sha(Path(c.__file__)),controller_run_root='results/formal_main_v2/autonomous_training/run_v1')
    monkeypatch.setattr(c,'load_activation',lambda *args:act)
    monkeypatch.setattr(a,'inherited_pairs',lambda *args:{'synthetic_inherited':{'new_machine_review_claimed':False}})
    class Scheduler:
        def observe(self,jobs):return dict(rows={},queue={},raw_sacct='',raw_squeue='')
    monkeypatch.setattr(c,'Slurm',Scheduler)
    q=dict(root=root,runtime=runtime,state=state,activation=act,calls=[],submit_error=None,answer=SimpleNamespace(returncode=0,stdout='999;cluster\n',stderr=''),release_error=False)
    def run(args,**kwargs):
        q['calls'].append(args)
        assert not any(k.startswith('CTI_SERVER_CONTROL_') for k in kwargs.get('env',{}))
        if args[0]=='sbatch':
            assert '--hold' in args and '--partition=intel' in args and not any('gres=gpu' in x for x in args)
            assert c.read_json(state)['pending_submission']['requested_gpus']==0
            for p in [state.parent/'.writer.lock',root/act['controller_run_root']/'controller.lease.lock']:
                with p.open('a+b') as fd:
                    with pytest.raises(BlockingIOError):fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if q['submit_error']:raise q['submit_error']
            return q['answer']
        if args[0]=='scontrol':
            for p in [state.parent/'.writer.lock',root/act['controller_run_root']/'controller.lease.lock']:
                with c.exclusive_lock(p):pass
            s=c.read_json(state);assert s['pending_submission'] is None and s['registered_jobs'][-1]['job_id']=='999'
            return SimpleNamespace(returncode=1 if q['release_error'] else 0,stdout='',stderr='synthetic release fail' if q['release_error'] else '')
        return SimpleNamespace(returncode=0,stdout='synthetic startup accepted',stderr='')
    monkeypatch.setattr(a.subprocess,'run',run)
    q['args']=['--activation','synthetic_activation.json','--activation-sha256','a'*64,'--wrapper',str(wrapper.relative_to(root)),'--wrapper-sha256',c.file_sha(wrapper)]
    return q

def test_cpu_registration_durable_and_both_locks_released_before_release(case):
    assert a.main(case['args']+['--submit'])==0
    s=c.read_json(case['state']);j=s['registered_jobs'][0]
    assert j['run_root']==str(case['runtime']/'results/formal_main_v2/autonomous_training_controller_v1')
    assert j['control_run_root']==str(case['root']/case['activation']['controller_run_root'])
    spec=importlib.util.spec_from_file_location('puller_readonly_shape',R/'scripts/pull_formal_results.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);p.P=str(case['runtime'])
    assert p.registered_jobs(s)[0]['job_id']=='999'
    assert (Path(j['run_root'])/'999_registration.json').exists()

@pytest.mark.parametrize('fault',['timeout','nonzero','ambiguous'])
def test_unknown_submission_is_not_resent(case,fault):
    if fault=='timeout':case['submit_error']=subprocess.TimeoutExpired(['synthetic'],60)
    elif fault=='nonzero':case['answer']=SimpleNamespace(returncode=1,stdout='999\n',stderr='error')
    else:case['answer']=SimpleNamespace(returncode=0,stdout='999\n998\n',stderr='')
    with pytest.raises((ValueError,subprocess.TimeoutExpired)):a.main(case['args']+['--submit'])
    assert c.read_json(case['state'])['pending_submission'] is not None
    assert not c.read_json(case['state'])['registered_jobs']
    with pytest.raises(ValueError):a.main(case['args']+['--submit'])
    assert sum(args[0]=='sbatch' for args in case['calls'])==1
    assert not any(args[0]=='scontrol' for args in case['calls'])

def test_release_failure_keeps_registered_held_job_without_new_submission(case):
    case['release_error']=True
    with pytest.raises(ValueError):a.main(case['args']+['--submit'])
    assert c.read_json(case['state'])['registered_jobs'][0]['job_id']=='999'
    with pytest.raises(ValueError):a.main(case['args']+['--submit'])
    assert sum(args[0]=='sbatch' for args in case['calls'])==1

def test_check_only_writes_no_registry_or_invocation(case):
    before=c.file_sha(case['state']);assert a.main(case['args'])==0
    assert c.file_sha(case['state'])==before and not any(args[0] in ('sbatch','scontrol') for args in case['calls'])

def test_transport_environment_is_removed(monkeypatch):
    monkeypatch.setenv('CTI_SERVER_CONTROL_ROOT','synthetic');monkeypatch.setenv('CTI_SERVER_CONTROL_VERSION','synthetic')
    shim=str(c.R/'scripts/ops/server_control_transport_v1/bin');monkeypatch.setenv('PATH',shim+':/usr/bin')
    env=a.clean_environment();assert env['PATH']=='/usr/bin' and not any(k.startswith('CTI_SERVER_CONTROL_') for k in env)
