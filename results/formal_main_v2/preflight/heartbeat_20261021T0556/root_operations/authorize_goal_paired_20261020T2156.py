"""Root CPU admission and exact new engineering authority; never submits a job."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,os,shutil,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
PKG='scripts/ops/formal_goal_paired_input_gate_v1';BASE='results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156';B='results/formal_main_v2/preflight/heartbeat_20261021T0556'
MSHA='7e7da3f5b514102f08d105677e1dff504989aaf6c647f320405526d1fd2982ec';CSHA='104ebf29df89a91e6156d0c3acead203df95234a9393ba7c6545965a8ba9d669';ESHA='1e8caecfda12f1f0a1d55a5652e9c300d25dff5fb0cf071cf4555a68b8605977';DSHA='d3a8a445f5d0d13dfd93440256a8567fabfbb82a598bec6deb363bfd8b09ca17'
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rd(p):return json.loads(Path(p).read_bytes())
def ref(p):return dict(path=str(p),sha256=h(p))
def safe(p):
 p=Path(p);assert p.is_absolute() and p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents));return p
def load(p,pin,name):
 assert h(safe(p))==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def write(p,x):
 safe(p);p.parent.mkdir(parents=True,exist_ok=True);raw=x if isinstance(x,bytes) else (json.dumps(x,sort_keys=True,indent=2)+'\n').encode()
 with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--independent-review',required=True);ap.add_argument('--independent-sha256',required=True);ap.add_argument('--dispatch-review',required=True);ap.add_argument('--dispatch-sha256',required=True);a=ap.parse_args()
 assert Path.cwd()==R and sys.dont_write_bytecode
 ip=safe(R/a.independent_review);dp=safe(R/a.dispatch_review)
 assert all(p.is_relative_to(R/'.local/goal_paired_independent_20261020T2156') for p in (ip,dp))
 assert h(ip)==a.independent_sha256 and h(dp)==a.dispatch_sha256
 ind=rd(ip);dispatch=rd(dp);assert ind.get('actual_P_published_package_verified') is True and not ind.get('blockers')
 assert dispatch['status']=='passed' and dispatch['entrypoint_sha256']==DSHA and not dispatch.get('blockers')
 assert h(R/'.local/goal_paired_dispatch_20261020T2156_v3.py')==DSHA
 c=load(R/'scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','goalauthctl')
 with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
  sp=R/'results/experiment_supervisor/state.json';before=h(sp);state=rd(sp);f=state['formal_main_progress'];ctl=state['autonomous_training_v1']
  assert f['root_and_independent_completed_arms']==72 and len(ctl['completed_pairs'])==36 and not f['test_opened'] and not f['global_release_created'] and state['pending_submission'] is None
  assert ctl['root_submission_hold'] is None and ctl['reserved_GPU_slots']==0
  assert f['Goal_prefix58_engineering_registration']['status']=='completed_diagnostic_not_reproduced_scientific_HOLD'
  assert '3049679' not in f.get('new_action_development_verified_by_job',{})
  for root in (R,P):
   assert h(safe(root/PKG/'package_manifest.json'))==MSHA
   for n,pin in rd(root/PKG/'package_manifest.json')['files'].items():assert h(safe(root/n))==pin
   for n in ('root_readiness.json','independent_readiness.json','root_authorization.json'):assert not safe(root/BASE/n).exists()
  assert not (P/BASE/'attempt01').exists() and not (P/BASE/'held_dispatch_record.json').exists()
  assert shutil.disk_usage(P).free>=4363621114
  entry=load(P/PKG/'entry.py',ESHA,'goalauthentry');entry.check_review(ind,'independent',MSHA,CSHA)
  author=R/'.local/goal_gate_integration_20261020T2156/author_report.json';assert h(author)=='91c9e3db7269883c1e2f81687c091e50a7b1d27a8e64a319701960cb12d7a773';ar=rd(author);assert ar['status']=='passed_CPU_candidate_only' and ar['check_count']==961
  pub=R/B/'Goal_paired_publication.json';pv=rd(pub);assert pv['status']=='published_exact_eight_files_actual_P_CPU_verified_no_GPU_authority' and pv['package_manifest_sha256']==MSHA
  closure=R/'.local/goal_gate_integration_20261020T2156/CPU_production_preflight01/source_closure.json';assert h(closure)=='0c21661833a02a5a7e870c2280d137c8f2d9d3fa8eeb48fe02ab95b384d22639'
  for p,v in rd(closure)['files'].items():assert h(safe(p))==v['sha256']
  inv,w,ctx,legacy=entry.prepare_original();pp=entry.validate_prefix(inv,legacy,rd(P/PKG/'prefix58.json')['rows'])
  root=dict(schema='formal_main_v2',kind='goal_prefix58_single_attempt_CPU_readiness',status='passed',reviewed_by='root',version=entry.VERSION,package_manifest_sha256=MSHA,config_sha256=CSHA,original_chain_preserved=True,observer_gaps_fixed=True,paired_input_gate_CPU_passed=True,pre_policy_pair_equality_gate=True,all_query_input_integrity_gate=True,original_policy_error_retained_then_halt=True,real_GPU_acceptance=False,scientific_release=False,actual_P_published_package_verified=True,root_source_review=True,author_CPU_evidence=ref(author),independent_review=ref(ip),dispatch_review=ref(dp),publication=ref(pub),prefix_proof=pp,production_fixtures_disabled=True,all_query_raw_records_retained=True,space_required_bytes=4363621114,original_3053440_not_exact_replay=True,old_cause_identified=False,Goal_original200_and_new_science_HOLD=True,utc=datetime.now(timezone.utc).isoformat())
  entry.check_review(root,'root',MSHA,CSHA)
  for workspace in (R,P):
   write(workspace/BASE/'root_readiness.json',root);write(workspace/BASE/'independent_readiness.json',ip.read_bytes())
  auth=dict(schema='formal_main_v2',kind='root_goal_prefix58_single_attempt_authorization',version=entry.VERSION,status='approved',reviewed_by='root',stage_key=entry.STAGE,config_sha256=CSHA,package_manifest_sha256=MSHA,entrypoint_sha256=ESHA,maximum_gpu_jobs=1,maximum_attempts=1,maximum_wall_seconds=1800,counts_against_8_GPU_slots=True,automatic_retry=False,scientific_release=False,original_goal200_HOLD=True,new_Goal_science_HOLD=True,maximum_trials=58,resources=entry.RESOURCES,dispatch_record_path=str(entry.DISPATCH),reservation_path=str(entry.RESERVATION),root_review=ref(P/BASE/'root_readiness.json'),independent_review=ref(P/BASE/'independent_readiness.json'))
  entry.validate_authorization(auth,CSHA,MSHA,ESHA)
  for workspace in (R,P):write(workspace/BASE/'root_authorization.json',auth)
  assert h(sp)==before
  out=dict(status='exact_one_new_engineering_authority_CPU_admitted',authorization=ref(R/BASE/'root_authorization.json'),dispatch_review=ref(dp),maximum_trials=58,scientific_trials_added=0,old200_and_all_new_Goal_science_HOLD=True,Slurm_submissions=0,state_unchanged=True)
  write(R/B/'Goal_paired_root_admission.json',out);print(json.dumps(out))
if __name__=='__main__':main()
