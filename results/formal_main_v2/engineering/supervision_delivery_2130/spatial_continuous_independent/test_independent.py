import copy,hashlib,importlib.util,json,sys
from pathlib import Path
import pytest
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');C=R/'.local/spatial_continuous_admission_2130'
for n,h in {'gateway.py':'71af9cf0bce935d00934db8c8198f7f9624fd7194f570e36efd95f77da0634c6','admission.py':'0e5d2bbdca27640c4784393b3ea6a17969a7c6235bdeeb10b61c4a8ab7546b74','test_continuation.py':'a684c5c449246e66511537ae684fff5cdf5b12e4c5303bb88bab2bc3864a3d7b','actual_prepare_a2.json':'6705874a0d4fc784da3bed7a0bb310044c376c7d5d415213469061674eab2529'}.items():assert hashlib.sha256((C/n).read_bytes()).hexdigest()==h
sp=importlib.util.spec_from_file_location('spatial_author_fixtures',C/'test_continuation.py');t=importlib.util.module_from_spec(sp);sys.modules[sp.name]=t;sp.loader.exec_module(t)
g=t.g;a=t.a;box=t.box;io_case=t.io_case;typed_fixture=t.typed_fixture

def test_actual_execution_only_registered_three_fields_change():
 p=t.source_plan();new=p['invocation'];old=p['prior_invocation'];restored=copy.deepcopy(new);restored.pop('continuous_admission');restored['registered_utc']=old['registered_utc'];restored['segment_end']=old['segment_end'];restored['argv']=copy.deepcopy(old['argv']);assert restored==old
 changed=[(i,x,y) for i,(x,y) in enumerate(zip(old['argv'],new['argv'])) if x!=y];assert [(x,y) for _,x,y in changed]==[('1500','5000'),('12600','169200')]
 assert new['continuous_admission']['validation_updates']==list(range(0,5001,500));assert new['continuous_admission']['checkpoint_every_updates']==50
 argv,raw,h,token=g.sbatch_argv(p,{'path':'synthetic','sha256':'a'*64});assert argv[-1]==str(a.S/'scripts/server/formal_main.slurm');assert 'formal_asset_main' not in str(argv);assert 'runtime_compatibility' not in new
 assert '--resume'==new['argv'][-1] and '--time=48:00:00' in argv and '--exclude=gpu4020' in argv

def test_real_unsigned_draft_cannot_authorize():
 ref={'path':'.local/spatial_continuous_admission_2130/authorization_a2_draft.json','sha256':'7d1d972b0b37ce7dabef2bfff93580f6f403eac94c4d85bcf75f96023f667721'}
 with pytest.raises(ValueError,match='typed'):g.validate_authorization(R,ref)

@pytest.mark.parametrize('mutation',['missing_success','hidden_failure','wrong_seconds','extra_attempt'])
def test_four_history_fails_closed(mutation):
 p=t.source_plan();s={'registered_jobs':copy.deepcopy(p['prior_jobs'])}
 if mutation=='missing_success':s['registered_jobs'].pop(0)
 if mutation=='hidden_failure':s['registered_jobs'].pop(2)
 if mutation=='wrong_seconds':s['registered_jobs'][2]['elapsed_seconds']=0
 if mutation=='extra_attempt':s['registered_jobs'].append({**s['registered_jobs'][-1],'job_id':'999999'})
 with pytest.raises(ValueError):a.history(s)

@pytest.mark.parametrize('mutation',['archive_bytes','pull_ownership','duplicate_pull'])
def test_exact_finalization_provenance_rejects_change(mutation):
 proof=t.source_plan()['invocation']['continuous_admission'];failure=json.loads((R/proof['canonical_failure_review']['path']).read_bytes());pull=json.loads((R/proof['terminal_pull']['path']).read_bytes());rel=next(iter(a.RETAINED_FINALIZATIONS))
 if mutation=='archive_bytes':failure['evidence_bundle'][rel]['bytes']+=1
 elif mutation=='pull_ownership':next(x for x in pull['files'] if x.get('relative')==rel)['job_ids']=['3024716']
 else:pull['files'].append(copy.deepcopy(next(x for x in pull['files'] if x.get('relative')==rel)))
 with pytest.raises(ValueError):a.retained_finalizations(a.Evidence(R),failure,pull)

def test_native_B_resume_is_not_exchangeable(io_case):
 io,p=io_case;io.preflight(p);p['server_resume_checks'][1]=copy.deepcopy(p['server_resume_checks'][0])
 with pytest.raises(ValueError,match='exact two'):io.preflight(p)

def test_post_ACK_accounting_lag_keeps_known_pending(box):
 old=box.slurm.observe
 def delayed(jobs):
  snap=old(jobs)
  if any('continuous_admission' in j for j in jobs):snap['rows'].pop('777777')
  return snap
 box.slurm.observe=delayed
 with pytest.raises(ValueError,match='accounting incomplete'):box.gate.run(submit=True)
 pending=box.read()['pending_submission'];assert pending['known_job_id']=='777777' and pending['status']=='submitted_identifier_observed';assert len(box.slurm.calls)==1
 with pytest.raises(ValueError):box.gate.run(submit=True)
 assert len(box.slurm.calls)==1 and box.read()['pending_submission']==pending

def test_CPU_row_missing_does_not_release_controller_reservation(box):
 old=box.slurm.observe
 def missing(jobs):
  snap=old(jobs);snap['rows'].pop('3034538');return snap
 box.slurm.observe=missing;before=box.read()
 with pytest.raises(ValueError,match='accounting'):box.gate.run(submit=True)
 assert box.read()==before and not box.slurm.calls

def test_positive_fixture_does_not_clear_retained_block_or_reservation(box):
 before=box.read();box.gate.run(submit=True);after=box.read();assert before['autonomous_training_v1']==after['autonomous_training_v1'];assert after['registered_jobs'][2]['status']=='FAILED';assert after['registered_jobs'][-1]['startup_recovery']['version']==a.VERSION;assert after['registered_jobs'][-1]['continuous_admission']['historical_GPU_seconds']==11958

def test_only_spatial_independent_type_is_accepted(typed_fixture):
 root,v,ref=typed_fixture;v['independent_review']=ref('object_ind',dict(schema='formal_main_v2',kind='cuda_continuous_admission_independent_CPU_review',status='passed_CPU_review',blockers=[],files=g.source_files()))
 with pytest.raises(ValueError,match='independent'):g.validate_authorization(root,ref('new_auth',v))
