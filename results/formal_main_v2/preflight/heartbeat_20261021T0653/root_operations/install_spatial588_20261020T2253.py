from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import hashlib,importlib.util,json,os,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0653';X='results/formal_main_v2/execution/spatial588_pre_dispatch_v1';E='results/formal_main_v2/engineering/supervision_delivery_20261020T2156'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(p):assert p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents));return p
def load(rel,pin,name):
 p=safe(R/rel);assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def save(rel,obj):
 p=safe(R/rel);p.parent.mkdir(parents=True,exist_ok=True);p.open('x').write(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n');return dict(path=rel,sha256=h(p))
ctl=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','install2253ctl')
mp=R/'.local/spatial588_integration_20261020T2156/phase2_v2/install_files.json';assert h(mp)=='60fb788f3f8f13ee9b1f24b5312c435f48d22fa2668ac736649f24f202defb85';mapping=json.loads(mp.read_bytes());assert len(mapping['files'])==13
ir=E+'/Spatial_independent/independent_review.json';ih=E+'/Spatial_phase2_independent/independent_history_review.json';assert h(R/ir)=='3cb7efa91ebbdb42c8ae91afef2f34ade5b237ee169a369a721353b0840bbf50' and h(R/ih)=='db89d100fdc77f3ea7185ca8ffb1d20cbce333a88b627f8d477618f1924f6cc9'
ind=json.loads((R/ih).read_bytes());assert ind['blockers']==[] and ind['status']=='passed_CPU_review'
with ctl.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statep=R/'results/experiment_supervisor/state.json';before=h(statep);state=json.loads(statep.read_bytes());assert before=='63c74e7e591283409a792a7597fdb9bf99d1936ff1311e123bd687a83237a51f';assert state['pending_submission'] is None
 for row in mapping['files']:
  src=safe(R/row['source']);dst=safe(R/row['destination']);assert dst.relative_to(R).as_posix().startswith('scripts/ops/formal_spatial588_predispatch_v1/') and src.stat().st_size==row['bytes'] and h(src)==row['sha256'];assert not dst.exists()
 for row in mapping['files']:
  dst=safe(R/row['destination']);dst.parent.mkdir(parents=True,exist_ok=True);dst.open('xb').write((R/row['source']).read_bytes());assert h(dst)==row['sha256']
 c=load('scripts/ops/formal_spatial588_predispatch_v1/control.py','e2e7c3fe7f6dcf4f63b4550c3f5bc8ec50a05aaf462b38ed961ce356cc414683','canonical_spatial588_2253');bridge=c.compatibility_module();factory,planner=c.control_modules();ev=factory.Evidence(R)
 assert c.closure()==ind['history_control_sources'] and c.descriptor()==ind['typed_predispatch_history']
 real_history=c.verify_history(ev,planner.formal_jobs(state));real_prefix=bridge.audit_prefix(ev);assert real_history==c.descriptor() and real_prefix==bridge.descriptor();ev.unchanged()
 adoption=bridge.adoption_proposal();adoption.update(status='root_adopted',reviewed_by='root',independent_review=dict(path=ir,sha256=h(R/ir)),root_review_utc=datetime.now(timezone.utc).isoformat(),rationale='Root rechecked the canonical source closure, real12/122/917 bytes and original identity; independent source-derived historical controller/RNG limitations retained. Legacy origin stays separate; no new scientific trial or global release.')
 bridge.validate_adoption_documents(adoption,json.loads((R/ir).read_bytes()),independent_ref=adoption['independent_review']);ar=save(bridge.ADOPTION,adoption)
 repair=c.repair_proposal();repair.update(status='reviewed',reviewed_by='root',root_authorized=True,independent_history_review=dict(path=ih,sha256=h(R/ih)),root_review_utc=datetime.now(timezone.utc).isoformat());rr=save(c.REPAIR,repair)
 ev=factory.Evidence(R);c.check_repair(ev,c.REPAIR,planner.formal_jobs(state));bridge.check_adoption(ev);ev.unchanged()
 args=SimpleNamespace(stage='development',source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',execution_manifest=c.policy()['manifest']['path'],output_relative=None,freeze_directory=None,profile_panel=None,prior_review=c.policy()['prefix_review']['path'],collection_review=None,repair_record=c.REPAIR,resume=True,stop_after=None)
 planned=planner.plan(args,state,project=R,helper=factory);c.scope_invocation(planned['invocation']);assert planned['invocation_relative'].endswith('_attempt03.json');pr=save(X+'/scientific_plan.json',planned)
 assert h(statep)==before
 receipt=dict(status='canonical_control_installed_root_legacy12_adoption_and_typed_history_repair_verified',source_mapping=dict(path=str(mp.relative_to(R)),sha256=h(mp)),canonical_files=[dict(path=x['destination'],sha256=x['sha256']) for x in mapping['files']],independent_history=dict(path=ih,sha256=h(R/ih)),root_adoption=ar,root_repair=rr,scientific_plan=pr,source_closure=c.closure(),typed_history=c.descriptor(),legacy12=bridge.descriptor(),state_sha256_unchanged=before,new_GPU_jobs=0,new_scientific_trials=0,actual_P_verify=False,exact_gateway_authorized=False,final_release=False)
 result=save(B+'/Spatial_canonical_install.json',receipt);print(json.dumps({'receipt':result,'scientific_plan':pr,'root_adoption':ar,'root_repair':rr,'remaining_trial_count':588,'new_GPU_jobs':0,'actual_P_verify':False}))
