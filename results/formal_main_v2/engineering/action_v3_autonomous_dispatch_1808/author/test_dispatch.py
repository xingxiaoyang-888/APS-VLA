"""CPU synthetic submit transaction tests; original science closure mocked ONLY here.
Real contract/source/hash/registered Slurm validation is separate check-only evidence.
"""
import copy, hashlib, importlib.util, json, subprocess
from pathlib import Path
from types import SimpleNamespace
import pytest
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=Path(__file__).resolve().parent

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
fmod=module(D/'facade.py','_test_facade');entry=module(D/'entry.py','_test_entry')
ctl=fmod.load(R/fmod.CONTROLLER_REL,'_test_original_controller',fmod.CONTROLLER_SHA)
orig=fmod.load(R/(entry.SOURCE+'submit.py'),'_test_original_submit',entry.BINDINGS['submit.py'])
node=fmod.load(R/(entry.SOURCE+'node_exclusion.py'),'_test_original_node',entry.BINDINGS['node_exclusion.py'])

@pytest.fixture
def box(tmp_path,monkeypatch):
    root=tmp_path/'synthetic_project';root.mkdir()
    def put(rel,data):
        p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    for rel in [fmod.SUPERVISOR_REL,fmod.RESERVATION['path'],fmod.ACTIVATION['path'],entry.NODE_REG['path']]:put(rel,(R/rel).read_bytes())
    nr=json.loads((R/entry.NODE_REG['path']).read_bytes())
    for rel in nr['failure_evidence_sha256']:put(rel,(R/rel).read_bytes())
    put(orig.c.WRAPPER,(R/orig.c.WRAPPER).read_bytes())
    jobs=[dict(job_id=fmod.COORDINATOR,experiment='formal_main_v2',mode='engineering',stage_key='controller',status='RUNNING',gpus=0),
          dict(job_id='100',experiment='g0',status='COMPLETED',exit_code=0,gpus=1),
          dict(job_id='101',experiment='formal_main_v2',mode='engineering',stage_key='old_gpu',status='COMPLETED',exit_code='0:0',gpus=1),
          dict(job_id='102',experiment='formal_main_v2',mode='engineering',stage_key='old_cpu',status='COMPLETED',exit_code='0:0',gpus=0)]
    jobs += [dict(job_id=str(201+i),experiment='formal_main_v2',mode='engineering',stage_key='active_'+str(i),status='RUNNING',gpus=1) for i in range(7)]
    state=dict(registered_jobs=jobs,pending_submission=None,current_round_cost={'registered_jobs':10,'allocated_gpu_seconds':12345},
        autonomous_training_v1=dict(controller_job_id=fmod.COORDINATOR,activation=fmod.ACTIVATION,reserved_GPU_slots=1,reservation_root_record=fmod.RESERVATION,
            root_submission_hold=None,completed_pairs={'keep':{'training':'unchanged'}},occupied_job_ids=[str(201+i) for i in range(7)]),
        formal_main_progress={'parallel_execution':{'registered_requested_active_GPU_jobs':7,'next_actions':['keep original actions']}},
        next_actions=['do not replace'],updated_utc='previous')
    sp=root/'results/experiment_supervisor/state.json';ctl.atomic_json(sp,state)
    (sp.parent/'.writer.lock').write_bytes(b'')
    context=SimpleNamespace(root=root,sp=sp,initial=copy.deepcopy(state),rows={},queued={},seen=[],commands=[],fault=None,checkcalls=0,absentcalls=0)
    for j in jobs:
        context.rows[j['job_id']]=[j['job_id'],j['status'],'0:0','100',f"cpu=1,gres/gpu={j['gpus']}",'gpu0000','cti-test','']
        if j['status']=='RUNNING':context.queued[j['job_id']]=['RUNNING','']
    def scheduler(argv,**kwargs):
        context.seen.append(argv)
        ids=argv[argv.index('-j')+1].split(',')
        if argv[0]=='sacct':out=''.join('|'.join(context.rows[i])+'\n' for i in ids if i in context.rows)
        elif argv[0]=='squeue':out=''.join(i+'|'+ '|'.join(context.queued[i])+'\n' for i in ids if i in context.queued)
        else:raise AssertionError(argv)
        return SimpleNamespace(returncode=0,stdout=out,stderr='')
    context.scheduler=scheduler
    watched={orig.c.P+'/'+rel:entry.BINDINGS[Path(rel).name] for rel in [orig.c.SUBMITTER,orig.c.LAUNCHER,orig.c.ENTRY,orig.c.WRAPPER]}
    checked=dict(watched_files=watched,deployment_files=[])
    context.checked=checked;context.remote=dict(watched)
    def local_contract(*a,**kw):
        context.checkcalls+=1
        if context.fault=='local_contract':raise ValueError('synthetic contract drift')
        return checked
    def absent(f):context.absentcalls+=1
    def remote_hashes(f,names):
        if context.fault=='remote_mismatch':return {n:'f'*64 for n in names}
        return {n:context.remote.get(n) for n in names}
    def publish(f,local,server,expected):
        assert hashlib.sha256(Path(local).read_bytes()).hexdigest()==expected
        if context.fault=='publish':raise OSError('synthetic upload failure')
        context.remote[server]=expected
    def sbatch(argv,**kwargs):
        context.commands.append(argv)
        assert '--exclude=gpu4020' in argv[-1]
        if context.fault=='sbatch_raise':raise OSError('synthetic transport failure')
        if context.fault=='cas':
            changed=ctl.read_json(sp);changed['outside_writer']=True;ctl.atomic_json(sp,changed)
        if context.fault=='ambiguous':return SimpleNamespace(returncode=0,stdout='not-a-job\n',stderr='')
        if context.fault=='bad_rc':return SimpleNamespace(returncode=1,stdout='900\n',stderr='failure')
        jid='201' if context.fault=='duplicate_ack' else '900'
        return SimpleNamespace(returncode=0,stdout=jid+'\n',stderr='')
    monkeypatch.setattr(orig.c,'check_contract',local_contract)
    monkeypatch.setattr(orig,'remote_attempt_absent',absent)
    monkeypatch.setattr(orig,'remote_hashes',remote_hashes)
    monkeypatch.setattr(orig,'publish_missing',publish)
    monkeypatch.setattr(orig.subprocess,'run',sbatch)
    def build(writes=True):
        fac=fmod.Facade(root,ctl,orig.c,ctl.Slurm(runner=scheduler),root/'.local/dispatch_evidence',allow_writes=writes)
        fac.refs=entry.REFS;f=fac.attach();context.fac=fac;context.f=f;return fac,f
    context.build=build
    def run():
        fac,f=build()
        with node.exclude_future_sbatch(f,request={'kind':'action_execution_gpu_v3'},registration_ref=entry.NODE_REG,audit_relative='.local/dispatch_evidence/node.json'):
            return orig.execute_submit(root,checked,entry.REFS,f)
    context.run=run
    def amend(change):
        s=ctl.read_json(sp);change(s);ctl.atomic_json(sp,s)
    context.amend=amend
    return context

def test_success_original_submit_all_rows_node_and_exact_state(box):
    outcome=box.run();assert outcome['submitted']
    s=ctl.read_json(box.sp)
    assert len(s['registered_jobs'])==len(box.initial['registered_jobs'])+1
    assert s['registered_jobs'][:-1]==box.initial['registered_jobs']
    assert s['current_round_cost']=={'registered_jobs':11,'allocated_gpu_seconds':12345}
    assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0
    assert s['autonomous_training_v1']['reservation_root_record']==fmod.RESERVATION
    assert s['autonomous_training_v1']['completed_pairs']==box.initial['autonomous_training_v1']['completed_pairs']
    assert s['next_actions']==box.initial['next_actions']
    assert len(box.commands)==1 and box.checkcalls==1 and box.absentcalls==2
    observed=json.loads((box.fac.audit/'scheduler_observation.json').read_bytes())
    assert set(observed['queried_job_ids'])=={j['job_id'] for j in box.initial['registered_jobs']}
    assert fmod.COORDINATOR in observed['snapshot']['rows'] and '100' in observed['snapshot']['rows']
    assert len(observed['capacity']['occupied'])==7 and observed['evidence_filtered'] is False
    assert observed['confirmed_CPU_zero_job_ids']==[fmod.COORDINATOR,'102']
    assert json.loads((box.fac.audit/'node.json').read_bytes())['node_exclusion']==['gpu4020']
    assert box.f.refresh.__self__ is box.fac and box.f.write.__self__ is box.fac

@pytest.mark.parametrize('fault',['publish','sbatch_raise','ambiguous','bad_rc','duplicate_ack','cas'])
def test_after_pending_failure_keeps_pending_and_reservation(box,fault):
    box.fault=fault
    with pytest.raises((ValueError,OSError,RuntimeError)):box.run()
    s=ctl.read_json(box.sp)
    assert s['pending_submission']['status']=='prepared_before_invocation_publication'
    assert s['autonomous_training_v1']['reserved_GPU_slots']==1
    assert s['registered_jobs']==box.initial['registered_jobs']
    if fault=='cas':assert s['outside_writer'] is True

@pytest.mark.parametrize('fault',['remote_mismatch','local_contract'])
def test_before_pending_rejection_changes_no_state(box,fault):
    box.fault=fault;before=box.sp.read_bytes()
    with pytest.raises(ValueError):box.run()
    assert box.sp.read_bytes()==before and not box.commands

@pytest.mark.parametrize('variant',['cpu_missing','gpu_missing','cpu_unknown','terminal_drift','multigpu','duplicate_row','foreign_active','controller_on_GPU'])
def test_unknown_or_disagreement_fails_before_publication(box,variant):
    if variant=='cpu_missing':box.rows.pop(fmod.COORDINATOR)
    elif variant=='gpu_missing':box.rows.pop('201')
    elif variant=='cpu_unknown':box.rows[fmod.COORDINATOR][1]='MYSTERY'
    elif variant=='terminal_drift':box.rows['101'][1]='FAILED'
    elif variant=='multigpu':box.rows['201'][4]='cpu=2,gres/gpu=2'
    elif variant=='duplicate_row':box.amend(lambda s:s['registered_jobs'].append(copy.deepcopy(s['registered_jobs'][0])))
    elif variant=='foreign_active':box.amend(lambda s:s['registered_jobs'][4].update(experiment='another'))
    elif variant=='controller_on_GPU':box.rows[fmod.COORDINATOR][4]='cpu=1,gres/gpu=1'
    before=box.sp.read_bytes()
    with pytest.raises(ValueError):box.run()
    assert box.sp.read_bytes()==before and not box.commands

@pytest.mark.parametrize('variant',['pending','missing_pending','no_reservation','two_reservations','wrong_ref','root_hold','already_stage','duplicate_active_stage','prior_invocation'])
def test_registration_and_one_shot_guards(box,variant):
    if variant=='pending':box.amend(lambda s:s.update(pending_submission={'unknown':True}))
    elif variant=='missing_pending':box.amend(lambda s:s.pop('pending_submission'))
    elif variant=='no_reservation':box.amend(lambda s:s['autonomous_training_v1'].update(reserved_GPU_slots=0))
    elif variant=='two_reservations':box.amend(lambda s:s['autonomous_training_v1'].update(reserved_GPU_slots=2))
    elif variant=='wrong_ref':box.amend(lambda s:s['autonomous_training_v1'].update(reservation_root_record={'path':'other','sha256':'0'*64}))
    elif variant=='root_hold':box.amend(lambda s:s['autonomous_training_v1'].update(root_submission_hold={'reason':'root'}))
    elif variant=='already_stage':box.amend(lambda s:s['registered_jobs'][0].update(stage_key=orig.c.STAGE))
    elif variant=='duplicate_active_stage':box.amend(lambda s:s['registered_jobs'][5].update(stage_key=s['registered_jobs'][4]['stage_key']))
    elif variant=='prior_invocation':
        p=box.root/orig.c.INVOCATION;p.parent.mkdir(parents=True);p.write_text('{}')
    before=box.sp.read_bytes()
    with pytest.raises(ValueError):box.run()
    assert box.sp.read_bytes()==before and not box.commands

def test_eight_GPU_and_CPU_no_submission(box):
    j=dict(job_id='208',experiment='formal_main_v2',mode='engineering',stage_key='eighth',status='RUNNING',gpus=1)
    box.amend(lambda s:s['registered_jobs'].append(j));box.rows['208']=['208','RUNNING','0:0','4','gres/gpu=1','gpu0001','cti',''];box.queued['208']=['RUNNING','']
    before=box.sp.read_bytes();out=box.run()
    assert out['submitted'] is False and out['reason']=='all8slotsoccupied'
    assert len(out['active_request_job_ids'])==8 and box.sp.read_bytes()==before and not box.commands

def test_requested_GPU_zero_allocation_remains_counted(box):
    box.rows['201'][4]='cpu=0';box.rows['201'][1]='PENDING';box.queued['201'][0]='PENDING'
    box.run();assert '201' in box.fac.observation['capacity']['occupied']

def test_state_whitelist_and_read_only_refresh(box):
    fac,f=box.build();before=box.sp.read_bytes()
    with f.supervisor_lock():
        s=f.read(f.STATE);view=f.refresh(s);assert s==box.initial and len(view)==8
        s['pending_submission']=dict(stage_key=orig.c.STAGE,invocation=orig.c.INVOCATION,invocation_sha256='0'*64,status='prepared_before_invocation_publication',utc='2026-10-18')
        s['autonomous_training_v1']['completed_pairs']={}
        with pytest.raises(ValueError,match='whitelist'):f.write(f.STATE,s)
    assert box.sp.read_bytes()==before

def test_check_only_cannot_write_or_create_audit(box):
    fac,f=box.build(False);before=box.sp.read_bytes()
    with f.supervisor_lock():
        s=f.read(f.STATE);f.refresh(s)
        with pytest.raises(ValueError,match='write outside'):f.write(f.STATE,s)
    assert box.sp.read_bytes()==before and not fac.audit.exists()

def test_writer_lock_conflict_no_state_change(box):
    before=box.sp.read_bytes()
    with ctl.exclusive_lock(box.sp.parent/'.writer.lock'):
        with pytest.raises(BlockingIOError):box.run()
    assert box.sp.read_bytes()==before and not box.commands

def test_receipt_failure_keeps_observed_identifier(box,monkeypatch):
    original=fmod.exclusive_json
    def fail(path,value):
        if str(path).endswith('/submissions/900.json'):raise OSError('synthetic receipt disk failure')
        return original(path,value)
    monkeypatch.setattr(fmod,'exclusive_json',fail)
    with pytest.raises(OSError):box.run()
    s=ctl.read_json(box.sp);assert s['pending_submission']['known_job_id']=='900'
    assert s['pending_submission']['status']=='submitted_identifier_observed' and s['autonomous_training_v1']['reserved_GPU_slots']==1

def test_sacct_empty_final_comment_parser_real_format():
    row='1|RUNNING|0:0|3|cpu=1,gres/gpu=0|cpu1|cti|\n'
    assert ctl.parse_sacct(row,{'1'})['1']['scheduler_comment']==''
    with pytest.raises(ValueError):ctl.parse_sacct(row.rstrip('\n')+'unexpected|bad\n',{'1'})


def test_missing_shared_lock_fails_without_creating_it(box):
    lock=box.sp.parent/'.writer.lock';lock.unlink()
    before=box.sp.read_bytes()
    fac,f=box.build(False)
    with pytest.raises(ValueError,match='shared writer lock missing'):
        with f.supervisor_lock():pass
    assert not lock.exists() and box.sp.read_bytes()==before and not fac.audit.exists()
