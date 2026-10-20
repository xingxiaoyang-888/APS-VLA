from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib,copy,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T2330';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1530'
KEY='supervision_integrity_review_20261020T1530';SREF=dict(path=B+'/summary_after_dispatch.json',sha256='3bced1812b1002f276f6327674c37779d8747ecbb9e368d8073e7cd9bc32b216')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=h(p),bytes=p.stat().st_size)
def cp(src,dst,pin):
 assert src.is_relative_to(R/'.local/dispatch_independent_20261020T1530') and dst.is_relative_to(R/E/'final_independent') and h(src)==pin
 assert not any(p.is_symlink() for p in [src,*src.parents,dst,*dst.parents])
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert dst.read_bytes()==src.read_bytes()
 else:
  with dst.open('xb') as f:f.write(src.read_bytes())
 return dict(source=ref(src),archive=ref(dst))
ap=argparse.ArgumentParser();ap.add_argument('--manifest',required=True);ap.add_argument('--manifest-sha256',required=True);ap.add_argument('--report',required=True);ap.add_argument('--report-sha256',required=True);a=ap.parse_args()
mf=R/a.manifest;rp=R/a.report;assert h(mf)==a.manifest_sha256 and h(rp)==a.report_sha256
manifest=json.loads(mf.read_bytes());report=json.loads(rp.read_bytes());assert report['status'].startswith('passed')
assert mf.parent==rp.parent and mf.parent.is_relative_to(R/'.local/dispatch_independent_20261020T1530')
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('finalaccept1530ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';before=h(statepath);s=rd('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress']
 assert f[KEY]['status']=='pending_final_cross_check' and f[KEY]['summary']==s['last_root_supervision_snapshot']==SREF and h(R/SREF['path'])==SREF['sha256']
 assert f['root_and_independent_completed_arms']==66 and f['current_action_development_trial_count']==4400 and f['completed_development_trials']==5612 and f['current_action_development_unique_initial_states']==400
 assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0 and s['autonomous_training_v1']['root_submission_hold'] is None
 assert not f['global_release_created'] and not f['test_opened'] and f['completed_final_trials']==0
 copies=[]
 assert isinstance(manifest['files'],dict) and len(manifest['files'])==21
 for name,row in manifest['files'].items():
  rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts
  src=mf.parent/rel;assert src.stat().st_size==row['bytes'];copies.append(cp(src,R/E/'final_independent'/rel,row['sha256']))
 copies.append(cp(mf,R/E/'final_independent'/mf.name,a.manifest_sha256))
 dest=R/E/'final_independent'/rp.name;assert h(dest)==a.report_sha256;ir=dict(path=dest.relative_to(R).as_posix(),sha256=a.report_sha256)
 f[KEY]=dict(status='passed',utc=datetime.now(timezone.utc).isoformat(),independent_review=ir,root_accepted_summary=SREF,pre_final_cross_check_record=old['formal_main_progress'][KEY],new_training_groups_accepted=2,new_development_trials_accepted=600,new_submitted_trials_accepted=0,current_action_trials=4400,held_unaccepted_Goal_trials=200,original_summary_pending_status_is_historical=True,no_original_guard_waived=True,final_release=False)
 expected=copy.deepcopy(old);expected['formal_main_progress'][KEY]=copy.deepcopy(f[KEY]);assert s==expected
 c.atomic_json(statepath,s,before)
 out=R/B/'final_integrity_delivery.json';payload=dict(status='passed',copies=copies,independent_review=ir,summary=SREF,state_before_sha256=before,state_after_sha256=h(statepath),only_final_integrity_status_changed=True,no_scientific_increment=True)
 with out.open('x') as fp:json.dump(payload,fp,ensure_ascii=False,sort_keys=True,indent=2);fp.write(chr(10))
 print(json.dumps(dict(receipt=ref(out),independent_review=ir,files=len(copies))),flush=True)
