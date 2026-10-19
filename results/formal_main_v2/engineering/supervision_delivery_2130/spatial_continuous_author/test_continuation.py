"""CPU-only gateway faults; production raw science is separately reconstructed.
Transactions use real controller lock/CAS/capacity and identity corroboration, fake
Slurm/IO/science. NativeIO tests use tiny files, never production checkpoints.
"""
import copy, fcntl, importlib.util, json, hashlib, os
from pathlib import Path
from types import SimpleNamespace
import pytest
C=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('candidate_gateway',C/'gateway.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
a=g.a
REAL=a.R
c=g.load(REAL/g.CONTROLLER,g.CONTROLLER_SHA,'real_controller')
d=g.load(REAL/g.IDENTITY,g.IDENTITY_SHA,'real_job_identity')
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(a.canonical(v));return {'path':str(p),'sha256':a.digest(p.read_bytes())}
def source_plan():
 return json.loads((C/'actual_prepare_a2.json').read_bytes())['plan']
@pytest.fixture
def box(tmp_path):
 root=tmp_path/'project';root.mkdir();e=a.Evidence(root)
 prior=source_plan();pairrows=copy.deepcopy(prior['prior_jobs'])
 ctl={'activation':a.ACTIVATION,'activation_sha256':a.ACTIVATION['sha256'],'controller_job_id':'3034538','owner_id':'synthetic-owner',
   'root_submission_hold':None,'reserved_GPU_slots':1,'blocked_pairs':{a.PAIR:{'reason':'retained_failure','history_sha256':'historical'}},
   'completed_pairs':{},'verified_pairs':{},'arbitrary_controller_field':'preserve'}
 reservation={'kind':'synthetic_reserved_for_Spatial_only','reserved_slots':1}
 rr='results/formal_main_v2/synthetic_spatial_reservation.json';save(root/rr,reservation)
 ctl['reservation_root_record']={'path':rr,'sha256':a.digest((root/rr).read_bytes())}
 cpu=dict(job_id='3034538',name='cti-controller',gpus=0,status='RUNNING',exit_code='0:0',experiment='formal_main_v2',mode='controller')
 gpu=[dict(job_id=str(900+i),name='cti-engineering',gpus=1,status='RUNNING',exit_code='0:0',experiment='formal_main_v2',mode='engineering') for i in range(6)]
 state={'pending_submission':None,'registered_jobs':pairrows+[cpu]+gpu,'autonomous_training_v1':ctl,
   'current_round_cost':{'registered_jobs':9,'retained_other_cost':99},
   'formal_main_progress':{'parallel_execution':{'pair_tracking':{a.PAIR:{'last_root_reviewed_common_update':1500}},'registered_requested_active_GPU_jobs':6}},
   'unrelated_top_level':['preserve']}
 save(root/a.STATE,state);(root/a.STATE).parent.joinpath('.writer.lock').touch()
 work=root/'results/formal_main_v2/autonomous_training/run_v1';work.mkdir(parents=True)
 lease=work/'controller.lease.lock';lease.touch();fd=lease.open('rb');fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 save(work/'owner.json',dict(version=c.VERSION,owner_id='synthetic-owner',activation_sha256=a.ACTIVATION['sha256'],
  coordinator_job_id='3034538',hostname='synthetic_cpu',lock=str(lease),lease='fcntl_flock_held_for_process_lifetime'))
 auth={'controller_job_id':'3034538','gateway_files':g.source_files(),**a.proof_refs(prior['invocation']['continuous_admission'])}
 ref={'path':'configs/experiments/synthetic_once.json','sha256':'a'*64}
 class Science:
  def __init__(self):self.e=a.Evidence(root)
  def prepare(self,state,auth,ref):
   a.history(state);p=copy.deepcopy(prior)
   p['invocation']=a.continuation(p['prior_invocation'],auth,ref,'2026-10-19T11:11:00+00:00',p['server_resume_checks'],auth['gateway_files'])
   return p
 class IO:
  fault=None
  def preflight(self,plan):return {'synthetic_checkpoint_hashes':True}
  def publish(self,plan,raw,immutable):
   assert c.read_json(root/a.STATE)['pending_submission']['status']=='prepared_before_invocation_publication'
   if self.fault=='publish':raise OSError('publication failure')
  def recheck(self,plan):
   if self.fault=='checkpoint':raise ValueError('checkpoint bytes changed')
 class Scheduler:
  fault=None
  calls=[]
  def observe(self,jobs):
   rows={};queue={}
   for j in jobs:
    jid=j['job_id'];status=j['status'];token=''
    if 'continuous_admission' in j:status='RUNNING';token=j['continuous_admission']['request_token']
    row=dict(job_id=jid,status=status,exit_code=j.get('exit_code','0:0'),elapsed_seconds=j.get('elapsed_seconds',1),
     allocation='gres/gpu='+str(j['gpus']),node='synthetic_cpu' if j['gpus']==0 else 'gpu4001',gpus=j['gpus'],
     scheduler_name=j['name'],scheduler_comment='')
    if self.fault=='unknown' and jid=='900':row['status']='UNKNOWN'
    if self.fault=='cpu_unconfirmed' and jid=='3034538':row['gpus']=1
    rows[jid]=row
    if status not in c.TERMINAL:queue[jid]={'status':row['status'],'comment':token}
   return dict(rows=rows,queue=queue,raw_sacct='synthetic',raw_squeue='synthetic')
  def submit(self,argv):
   assert c.read_json(root/a.STATE)['pending_submission'] is not None
   self.calls.append(argv)
   if self.fault=='timeout':raise TimeoutError('unknown submission')
   if self.fault=='ambiguous':return SimpleNamespace(returncode=0,stdout='12345\nwarning\n',stderr='')
   if self.fault=='old_id':return SimpleNamespace(returncode=0,stdout='3043399\n',stderr='')
   return SimpleNamespace(returncode=0,stdout='777777\n',stderr='')
 io=IO();slurm=Scheduler();slurm.calls=[]
 gate=g.Gateway(root,c,d,slurm,Science(),io,auth,ref,e)
 result=SimpleNamespace(root=root,state=state,gate=gate,io=io,slurm=slurm,auth=auth,ref=ref,lease_fd=fd,
  read=lambda:c.read_json(root/a.STATE),write=lambda value:save(root/a.STATE,value))
 yield result
 fcntl.flock(fd,fcntl.LOCK_UN);fd.close()
def test_readonly_no_mutation(box):
 before=(box.root/a.STATE).read_bytes();o=box.gate.run()
 assert o['status']=='read_only_verified_not_submitted' and o['historical_GPU_seconds']==11958
 assert (box.root/a.STATE).read_bytes()==before and not box.slurm.calls and not box.gate.audit.exists()
def test_success_preserves_failure_controller_and_spatial_reservation(box):
 old=box.read();o=box.gate.run(submit=True);now=box.read()
 assert o['status']=='submitted_once' and len(box.slurm.calls)==1
 assert now['registered_jobs'][:-1]==old['registered_jobs']
 assert now['autonomous_training_v1']==old['autonomous_training_v1']
 assert now['pending_submission'] is None and now['registered_jobs'][-1]['segment_end']==5000
 assert now['registered_jobs'][2]['status']=='FAILED'
 assert '--time=48:00:00' in box.slurm.calls[0] and '--exclude=gpu4020' in box.slurm.calls[0]
 assert '--chdir='+str(a.P) in box.slurm.calls[0] and '--output='+str(a.P/'results/slurm/%x_%j.out') in box.slurm.calls[0]
 assert d.registered_comment(now['registered_jobs'][-1])=='cti-spatial-continuous-v1:'+box.ref['sha256']
@pytest.mark.parametrize('fault',['timeout','ambiguous','old_id'])
def test_uncertain_submit_keeps_pending_no_second_attempt(box,fault):
 box.slurm.fault=fault
 with pytest.raises((ValueError,TimeoutError)):box.gate.run(submit=True)
 assert box.read()['pending_submission'] is not None and len(box.slurm.calls)==1
 with pytest.raises(ValueError):box.gate.run(submit=True)
 assert len(box.slurm.calls)==1
@pytest.mark.parametrize('fault',['publish','checkpoint'])
def test_before_sbatch_failure_keeps_pending(box,fault):
 box.io.fault=fault
 with pytest.raises((ValueError,OSError)):box.gate.run(submit=True)
 assert box.read()['pending_submission'] is not None and not box.slurm.calls
@pytest.mark.parametrize('fault',['unknown','cpu_unconfirmed'])
def test_scheduler_uncertainty_rejected(box,fault):
 box.slurm.fault=fault
 with pytest.raises(ValueError):box.gate.run(submit=True)
 assert box.read()['pending_submission'] is None and not box.slurm.calls
def test_reserved_capacity_not_spent(box):
 s=box.read();s['registered_jobs'].append(dict(job_id='999',name='cti-engineering',gpus=1,status='RUNNING',exit_code='0:0',experiment='formal_main_v2',mode='engineering'));box.write(s)
 with pytest.raises(ValueError,match='unreserved'):box.gate.run(submit=True)
 assert not box.slurm.calls
def test_duplicate_active_pair_blocks(box):
 s=box.read();j=copy.deepcopy(s['registered_jobs'][1]);j.update(job_id='999',status='RUNNING',exit_code='0:0');s['registered_jobs'].append(j);box.write(s)
 with pytest.raises(ValueError):box.gate.run(submit=True)
 assert not box.slurm.calls
@pytest.mark.parametrize('key,value',[('status','COMPLETED'),('elapsed_seconds',0),('visual_tokens',256)])
def test_failed_history_not_rewritten(box,key,value):
 s=box.read();s['registered_jobs'][2][key]=value;box.write(s)
 with pytest.raises(ValueError):box.gate.run(submit=True)
 assert not box.slurm.calls
def test_missing_failed_row_rejected(box):
 s=box.read();s['registered_jobs'].pop(2);box.write(s)
 with pytest.raises(ValueError):box.gate.run()
def test_existing_invocation_hold(box):
 p=box.root/a.INVREL;p.parent.mkdir(parents=True);p.write_bytes(b'{}')
 with pytest.raises(ValueError,match='published'):box.gate.run()
 assert not box.slurm.calls
def test_missing_writer_lock_does_not_create(box):
 lock=(box.root/a.STATE).parent/'.writer.lock';lock.unlink()
 with pytest.raises(ValueError,match='lock'):box.gate.run()
 assert not lock.exists()
@pytest.mark.parametrize('field,value',[('owner_id','wrong'),('coordinator_job_id','999'),('hostname','other')])
def test_wrong_controller_owner(box,field,value):
 path=box.root/'results/formal_main_v2/autonomous_training/run_v1/owner.json';v=c.read_json(path);v[field]=value;save(path,v)
 with pytest.raises(ValueError,match='owner'):box.gate.run()
def test_released_lease_fails(box):
 fcntl.flock(box.lease_fd,fcntl.LOCK_UN)
 with pytest.raises(ValueError,match='lease'):box.gate.run()
def test_cas_drift_before_publication_keeps_other_bytes(box,monkeypatch):
 original=box.gate.cas
 def drift(s):
  p=box.root/a.STATE;v=c.read_json(p);v['foreign_write']='must_not_overwrite';save(p,v);original(s)
 monkeypatch.setattr(box.gate,'cas',drift)
 with pytest.raises(ValueError,match='state changed'):box.gate.run(submit=True)
 assert box.read()['foreign_write']=='must_not_overwrite' and not box.slurm.calls
def test_acknowledged_but_final_cas_failure_retains_known_id(box,monkeypatch):
 original=box.gate.cas;n=[0]
 def cas(s):
  n[0]+=1
  if n[0]==3:raise OSError('final CAS unavailable')
  original(s)
 monkeypatch.setattr(box.gate,'cas',cas)
 with pytest.raises(OSError):box.gate.run(submit=True)
 assert box.read()['pending_submission']['known_job_id']=='777777'
 assert len(box.read()['registered_jobs'])==len(box.state['registered_jobs'])
def test_only_two_scientific_execution_arguments_change():
 p=source_plan();old=p['prior_invocation']
 new=a.continuation(old,a.proof_refs(p['invocation']['continuous_admission']), {'path':'synthetic.json','sha256':'a'*64},'2026-10-19T11:11:00+00:00',p['server_resume_checks'],{})
 reverted=copy.deepcopy(new);reverted.pop('continuous_admission');reverted['registered_utc']=old['registered_utc'];reverted['segment_end']=1500
 for flag in ['--stop-after-updates','--max-wall-seconds']:
  reverted['argv'][reverted['argv'].index(flag)+1]=old['argv'][old['argv'].index(flag)+1]
 assert reverted==old and new['repair_record']==old['repair_record']
 assert new['continuous_admission']['validation_updates']==list(range(0,5001,500))
@pytest.fixture
def io_case(tmp_path,monkeypatch):
 p=tmp_path/'P';h=tmp_path/'H';s=p/'snapshots/formal_main_v2_run_564be0995e'
 monkeypatch.setattr(a,'P',p);monkeypatch.setattr(a,'H',h);monkeypatch.setattr(a,'S',s)
 out=p/a.OUT;out.mkdir(parents=True);(out/'.training.lock').touch();rawrel=a.OUT+'/A/progress_report.json'
 raw=p/rawrel;raw.parent.mkdir();raw.write_bytes(b'original progress')
 src=s/'src/module.py';src.parent.mkdir(parents=True);src.write_bytes(b'original frozen source')
 checks=[]
 for arm in ('A','B'):
  ck=h/'checkpoints/formal_main_v2/libero_spatial/k64/seed23'/arm/'resume.pt';ck.parent.mkdir(parents=True);ck.write_bytes(arm.encode())
  checks.append(dict(arm=arm,path=str(ck),exists=True,**a.stable(ck)))
 plan=dict(invocation={'watched_files':{}},invocation_relative=a.INVREL,
  inventory={'files':{'src/module.py':a.stable(src)['sha256']}},root_review={'files':{rawrel:a.stable(raw)['sha256']}},server_resume_checks=checks,retained_finalizations=copy.deepcopy(a.RETAINED_FINALIZATIONS))
 for rel,expected in a.RETAINED_FINALIZATIONS.items():
  dst=p/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((REAL/rel).read_bytes());assert a.stable(dst)==expected
 return a.NativeIO(),plan
def test_native_preflight_then_published_invocation_recheck(io_case):
 io,p=io_case;before=io.preflight(p);io.publish(p,a.canonical(p['invocation']),g.immutable)
 assert io.recheck(p)==before
@pytest.mark.parametrize('change',['checkpoint','raw','source','invocation','new_output'])
def test_native_after_preflight_tamper_rejected(io_case,change):
 io,p=io_case;io.preflight(p);io.publish(p,a.canonical(p['invocation']),g.immutable)
 paths={'checkpoint':Path(p['server_resume_checks'][0]['path']),'raw':a.P/a.OUT/'A/progress_report.json',
  'source':a.S/'src/module.py','invocation':a.P/a.INVREL,'new_output':a.P/a.OUT/'new_attempt.json'}
 paths[change].write_bytes(b'changed')
 with pytest.raises(ValueError):io.recheck(p)

@pytest.fixture
def typed_fixture(tmp_path):
 # Real candidate and prerequisite bytes; only root/ind approval JSON is synthetic.
 # This isolated directory can never be consumed by the production CLI.
 for rel,h in {**g.source_files(),**a.DEPENDENCIES,g.CONTROLLER:g.CONTROLLER_SHA,g.IDENTITY:g.IDENTITY_SHA}.items():
  src=(C/Path(rel).name) if rel.startswith(a.CANON) else REAL/rel
  dst=tmp_path/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes());assert a.digest(dst.read_bytes())==h
 proofs=a.proof_refs(source_plan()['invocation']['continuous_admission'])
 for row in [*proofs.values(),a.ACTIVATION,a.AUTHORIZATION,a.NODE]:
  dst=tmp_path/row['path'];dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((REAL/row['path']).read_bytes())
  assert a.digest(dst.read_bytes())==row['sha256']
 def ref(name,value):
  p=tmp_path/('proof/'+name+'.json');save(p,value);return {'path':p.relative_to(tmp_path).as_posix(),'sha256':a.digest(p.read_bytes())}
 spec=importlib.util.spec_from_file_location('candidate_prepare',C/'prepare.py')
 prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep)
 v=prep.draft(proofs);v.update(status='approved_exact_once_1500_to5000',reviewed_by='root')
 v['independent_review']=ref('ind',dict(schema='formal_main_v2',kind='spatial_cuda_continuous_admission_independent_CPU_review',
  status='passed_CPU_review',blockers=[],files=g.source_files(),synthetic_fixture=True))
 return tmp_path,v,ref

def test_typed_full_byte_bound_gate_and_canonical_sources(typed_fixture):
 root,v,ref=typed_fixture;got,e=g.validate_authorization(root,ref('auth',v))
 assert got==v and a.REVIEWER in e.hashes and a.CANON+'admission.py' in e.hashes
 assert (root/a.REVIEWER).parents[2]==root

@pytest.mark.parametrize('field,value',[
 ('status','draft_not_authorized'),('target_updates_per_arm',5500),('historical_GPU_seconds',11885),
 ('consume_reservation',True),('resume',False),('recovery_job_id','3039258'),
 ('completed_before',{'A':1500,'B':1000}),('cursor_before',{'A':12000,'B':8000})])
def test_typed_scope_changes_rejected(typed_fixture,field,value):
 root,v,ref=typed_fixture;v[field]=value
 with pytest.raises(ValueError,match='typed'):g.validate_authorization(root,ref('auth',v))

def test_typed_pin_drift_rejected(typed_fixture):
 root,v,ref=typed_fixture;auth=ref('auth',v);(root/a.CANON/'admission.py').write_bytes(b'changed')
 with pytest.raises(ValueError,match='SHA'):g.validate_authorization(root,auth)

def test_typed_wrong_independent_rejected(typed_fixture):
 root,v,ref=typed_fixture
 v['independent_review']=ref('wrong_ind',dict(schema='formal_main_v2',kind='cuda_continuous_admission_independent_CPU_review',status='passed_CPU_review',blockers=[],files=g.source_files()))
 with pytest.raises(ValueError,match='independent'):g.validate_authorization(root,ref('auth',v))

@pytest.mark.parametrize('target',['finalizations/unregistered.json','finalizations/3024716_d693020e24f0.json'])
def test_finalization_unknown_or_changed_rejected(io_case,target):
 io,p=io_case;io.preflight(p);(a.P/a.OUT/target).write_bytes(b'changed')
 with pytest.raises(ValueError):io.preflight(p)

def test_retained_finalization_map_cannot_be_omitted(io_case):
 io,p=io_case;p.pop('retained_finalizations')
 with pytest.raises(ValueError,match='retained'):io.preflight(p)

def test_actual_registered_science_projection_is_only_execution_bound():
 p=source_plan();inv=p['invocation'];contract=inv['continuous_admission']
 assert contract['prior_job_ids']==a.HISTORY_IDS
 assert contract['historical_GPU_seconds']==11958 and contract['sample_cursor_before']=={'A':12000,'B':12000}
 assert p['wrapper']==str(a.S/'scripts/server/formal_main.slurm')
 assert 'runtime_compatibility' not in inv and inv['entrypoint']=='scripts/run_formal_future.py'
 assert inv['argv'][inv['argv'].index('--stop-after-updates')+1]=='5000'
 assert inv['argv'][inv['argv'].index('--max-wall-seconds')+1]=='169200'
 assert inv['repair_record']==p['prior_invocation']['repair_record']
