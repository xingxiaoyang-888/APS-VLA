"""Bounded independent historical provenance review. No simulator/model/Slurm/state/Git mutation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,zipfile,tarfile
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
H=Path('/share/home/u15016/XXY_CVPR/CTI-VLA')
OUT=R/'.local/legacy6_independent_readiness_0830'
evidence={}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(path,pin=None):
 p=Path(path)
 if not p.is_absolute():p=R/p
 b=p.read_bytes();s=sha(b)
 if pin:assert s==pin,str(p)
 evidence[str(p.relative_to(R)) if p.is_relative_to(R) else str(p)]={'sha256':s,'bytes':len(b)}
 return b
def js(path,pin=None):return json.loads(read(path,pin))
def filehash(p,pin):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 assert h.hexdigest()==pin
 evidence[str(p)]={'sha256':pin,'bytes':p.stat().st_size}
 return pin
candidate=js('.local/long_legacy6_followup_0727/report.json','22a47a847ed81d7a18360354dd6a53b8e1153c716df78a87264bcbca25c49f18')
js('.local/long_legacy6_followup_0727/delivery_final.json','c1309c1066274cdf5bbd876117aa185795c7ae6d3444d0e0dac18b8d22ecd001')
js('.local/long_legacy6_followup_0727/minimum_followup_plan.json','2e8f7a13557b69041a4eba4b0f6963b1f9911a6114912b1e01fc2b6472464826')
registration=js('configs/experiments/formal_main_v2_action_execution_compat_v1.json','0917bff60e632a5be3c2db50b16daa0b904e4754a3ba31334802060f75d3eefe')
rule=registration['historical_development']['normal_trial_reuse_rule']
assert 'controller and environment were identical' in rule and 'adapter adds no numerical or RNG change' in rule
installer=read('results/formal_main_v2/engineering/supervision_delivery_2130/terminal_independent/dependencies/6d88db46acaf_install_libero_runtime.sh.txt','6d88db46acaf6a69feba8590af801ae5ea6576de059899ef05d7fec9cca922c5').decode()
assert 'PY=/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python' in installer
assert 'Verified transferred runtime packages:' in installer and 'sha256' in installer and 'external/wheels-libero/*.whl' in installer
freeze=read('results/setup/after_libero_freeze.txt','8bac807b631bb9c9691df977eae1b26f202b6a2d8d4a440153a74bb96b7a9b06')
assert read(P/'results/setup/after_libero_freeze.txt')==freeze
transfer=js('configs/assets/libero_wheels_transfer.json','bfd7901791c5858e405188cfc1e917fdd3db73a277a2468dd94b8d620ec0cb23')
read('configs/requirements-libero.txt','d255285a470c034692b493904ca8335847e58ffec6388775ddef7ccc8419987c')
read('results/setup/runtime_sources.json','2a34306de02495b145620038aeb4a79fbbd9574de518183aa56088b5a4a09b16')
env=dict(os.environ);env['GIT_OPTIONAL_LOCKS']='0'
def git(*args):
 q=subprocess.run(['git','--no-optional-locks',*args],cwd=R,env=env,capture_output=True,check=True);return q.stdout
commit='5c15d256796661cfd91375ac4721356d1e1888dc'
anchors=[]
for rel in ['results/setup/after_libero_freeze.txt','configs/assets/libero_wheels_transfer.json','configs/requirements-libero.txt']:
 b=git('show',commit+':'+rel);assert b==read(rel)
 log=git('log','--follow','--format=%H %aI %cI %s','--',rel).decode().strip()
 assert log.startswith(commit+' 2026-10-14T12:48:52+08:00')
 anchors.append({'path':rel,'commit':commit,'sha256':sha(b),'history':log})
installlog=read(P/'results/setup/install_libero_local_attempt4.log','2f89cb36baf0e7e6695090a6b858c8dc17db27f703cbf74a72736a8214bd7822').decode()
for text in ['Verified transferred runtime packages: 11','Processing ./external/wheels-libero/robosuite-1.4.1-py3-none-any.whl','Successfully installed','robosuite-1.4.1','No broken requirements found.','runtime_imports_passed','/share/home/u15016/XXY_CVPR/CTI-VLA/venv/lib/python3.11/site-packages']:
 assert text in installlog,text
assert read(P/'results/setup/install_runtime_local.exit','9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa')==b'0\n'
for rel,pin in [('results/setup/install_libero_local.log','82e539d0d8746cffccc7df45006c2a445f9dad6c33f40f791a913f548618ebb0'),('results/setup/install_runtime_local_attempt3.exit','4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865')]:read(P/rel,pin)
wheelrow=next(x for x in transfer['files'] if x['path']=='robosuite-1.4.1-py3-none-any.whl')
assert wheelrow['sha256']=='62587cd5888d9d3d813f3ffcc7017f6f77efa618952527a0b9bb139ffd0a3741'
wheel=P/'external/wheels-libero'/wheelrow['path'];filehash(wheel,wheelrow['sha256'])
assert wheel.stat().st_size==wheelrow['size'] and wheelrow['sha256'].encode() in freeze
members={}
with zipfile.ZipFile(wheel) as z:
 for rel in ['robosuite/controllers/base_controller.py','robosuite/controllers/osc.py','robosuite/controllers/config/osc_pose.json','robosuite/controllers/__init__.py','robosuite/robots/single_arm.py']:
  b=z.read(rel);now=read(H/'venv/lib/python3.11/site-packages'/rel)
  members[rel]={'wheel_member_sha256':sha(b),'current_file_sha256':sha(now),'current_matches_pinned_distribution':b==now,'is_historical_instance_capture':False}
  assert b==now
  if rel.endswith('osc_pose.json'):
   limits=json.loads(b);assert limits['control_delta'] is True and limits['type']=='OSC_POSE' and limits['input_max']==1 and limits['input_min']==-1 and limits['output_max']==[0.05,0.05,0.05,0.5,0.5,0.5]
  if rel.endswith('osc.py'):
   text=b.decode();assert 'self.use_delta = control_delta' in text and 'scaled_delta = self.scale_action(delta)' in text
archive=P/'external/libero-8f1084e.tar'
filehash(archive,'e0a261753ce056649da67f4c71938391a8d7c55a3eae53e4c17a5d79649da55c')
with tarfile.open(archive,'r:') as tar:
 names=[n for n in tar.getnames() if n.endswith('/libero/libero/envs/env_wrapper.py') or n=='libero/libero/envs/env_wrapper.py']
 assert len(names)==1,names
 wrapper=tar.extractfile(names[0]).read()
assert sha(wrapper)=='2880cad5b3fe46ea105816f42798faf4c22e16839098b679ebcad7b51acfdbd0'
assert read(P/'external/LIBERO/libero/libero/envs/env_wrapper.py')==wrapper
for text in ['controller="OSC_POSE"','suite.load_controller_config(default_controller=controller)','controller_configs=controller_configs']:
 assert text in wrapper.decode(),text
factory=read('scripts/eval_formal_selector_libero.py','de5a2b0a20f8121b57da8a1f766e4f5b48f3c86e214eae7aa3d08d642753f887').decode()
for text in ['from libero.libero.envs import OffScreenRenderEnv','random.seed(17)','np.random.seed(17)','torch.manual_seed(17)','env.seed(0)','camera_heights=256, camera_widths=256']:
 assert text in factory,text
oldconfigrel='results/formal_main_v2/libero_10/downstream/development/8c843c1d4ee8383c/attempt01/config.json'
old=js(oldconfigrel,'35724e624de06166c78e11c9e4bcd56b199cce73e5d5df284b3cc4365e0b7e14')
assert old['source_files']['scripts/eval_formal_selector_libero.py']=='de5a2b0a20f8121b57da8a1f766e4f5b48f3c86e214eae7aa3d08d642753f887'
assert old['source_verification']['libero']['archive_sha256']=='e0a261753ce056649da67f4c71938391a8d7c55a3eae53e4c17a5d79649da55c'
assert not any('robosuite' in k for k in old['watched_files'])
error_pins={'3016981':'bebeaa6a16ae2046f15cd5a003b1525a614d57f0f642d63e0e63c2965a3a6f86','3017161':'2942cb1269cc8e63fb5c16a50a318231fc238135041ca864c5aa943f39a24125','3017959':'94b293ae626db838248125d4cdbdd78bd54b260f29b5d8e6874af0cefcceb961','3018505':'3053c7ddb964a47643b15f5368da66b712ca1804d69e7d2a0be80ac9341d48be','3019176':'5e0880b821375804dedef91a363b05919770c175980c0092246775ac3ed6669d','3019954':'68f0e359b7901b3a1ac2fbc0c0a8eb6e0d3ad37cd2fbabc6024a896804aecd9e'}
historical=[]
for obj in candidate['environment_rng_evidence']['historical_invocation_evidence']:
 journal=read(obj['journal'],obj['journal_sha256'])
 events=[json.loads(x) for x in journal.splitlines()]
 verified=[x for x in events if x.get('event')=='official_source_verified']
 assert len(verified)==2 and any(x['verification']['archive_sha256']=='e0a261753ce056649da67f4c71938391a8d7c55a3eae53e4c17a5d79649da55c' for x in verified)
 invrel=obj['journal'].removesuffix('l');inv=js(invrel,candidate['read_evidence_sha256'][invrel])
 assert inv['job_id']==obj['job_id'] and inv['eval_script_sha256']==old['source_files']['scripts/eval_formal_selector_libero.py'] and inv['frozen_source_unchanged']
 errrel='results/slurm/cti-formal-downstream_'+obj['job_id']+'.err'
 err=read(errrel,error_pins[obj['job_id']]).decode()
 warning='/share/home/u15016/XXY_CVPR/CTI-VLA/venv/lib/python3.11/site-packages/robosuite/scripts/setup_macros.py'
 assert warning in err and 'No private macro file found!' in err
 historical.append({'historical_import_warning_path':warning,'historical_stderr':errrel,'historical_stderr_sha256':error_pins[obj['job_id']],'job_id':obj['job_id'],'journal':obj['journal'],'journal_sha256':obj['journal_sha256'],'finished_utc':inv['finished_utc'],'frozen_factory_bound':True,'LIBERO_archive_bound':True,'actual_robosuite_load_SHA_bound_in_old_watched_files':False})
assert len(historical)==6
report={'schema':'formal_main_v2','kind':'bounded_independent_legacy600_historical_readiness_review','status':'historical_installation_and_factory_evidence_recovered_runtime_identity_adoption_unresolved','production_reuse_authorized':False,'scope':'Read-only provenance and interpretation of 0917 registration; not an independent replay of 600 traces or a bridge-consumer acceptance.','registration_rule':rule,'registered_requirements':['Exact old/new identity and action trace; removed branch never taken and all full emitted chunks finite/within former threshold.','Controller/environment identity established for old and target execution.','Adapter adds no numerical or RNG change; explicit per-trial equivalence receipts.'],'RNG_requirement_interpretation':{'old_full_RNG_dump_required_by_0917':False,'no_new_RNG_draw_and_control_flow_identity_required':True,'absence_of_old_RNG_dump_alone_is_not_a_new_stop_condition':True,'candidate_AST_and_fake_CPU_replay_are_supporting_evidence_not_simulator_regeneration':True,'candidate_action_trace_result_inherited_not_newly_certified':candidate['status']},'historical_installation_evidence':{'pre_old600_Git_anchors':anchors,'robosuite_wheel_sha256':wheelrow['sha256'],'installation_attempt4_exit_zero_and_import_success':True,'previous_installation_failures_retained':True,'same_registered_venv_path':'/share/home/u15016/XXY_CVPR/CTI-VLA/venv','wheel_members_compared':members},'factory_chain':{'old_frozen_factory_sha256':old['source_files']['scripts/eval_formal_selector_libero.py'],'historically_verified_LIBERO_archive_sha256':old['source_verification']['libero']['archive_sha256'],'env_wrapper_member_sha256':sha(wrapper),'constructor':'OffScreenRenderEnv -> ControlEnv(controller=OSC_POSE) -> suite.load_controller_config -> pinned robosuite OSC_POSE -> OperationalSpaceController.use_delta','pinned_distribution_limits':limits,'old_attempts':historical},'established':['Exact robosuite/MuJoCo distribution provenance was committed 2026-10-14, before old600 jobs.','Recorded installer targets the same project venv and successful attempt4 installs transferred wheels and imports the runtime.','All six old invocations bound the frozen evaluation factory and verified the exact LIBERO archive; their original stderr warnings also identify the same venv robosuite import path and absence of private macro.','The wheel reproduces controller defaults and current v4 source bytes; this is corroboration, not a retrospective instance measurement.'],'remaining_unproven':['The old600 receipts did not hash the actual imported robosuite modules or record bound controller attributes. The recovered installation provenance alone does not demonstrate absence of intervening in-place changes between install and all six old jobs.','Whether the recovered historical installation/factory chain is accepted as sufficient identity evidence requires explicit root/independent bridge review; no production consumer is changed here.','The complete per-trial equivalence bridge and its consumer interface are not independently accepted by this bounded readiness review.'],'document_corrections':['Replace any assertion that no historical controller source provenance exists with: old per-invocation capture missing, but pre-run exact wheel/install/factory provenance recovered.','Do not present missing historical full RNG snapshots as a registered independent blocker; assess adapter RNG noninterference under the original requirement.','Do not claim wheel/current equality or four first-chunk matches prove whole600 environment execution equivalence.'],'new_GPU_jobs':0,'new_scientific_trials':0,'new_scheduler_queries':0,'weights_read':False,'sealed_values_read':False,'state_git_or_production_mutations':False,'evidence':evidence,'audit_source_sha256':sha(Path(__file__).read_bytes()),'utc':datetime.now(timezone.utc).isoformat()}
dest=OUT/'independent_readiness.json'
with dest.open('x') as f:json.dump(report,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':report['status'],'report':str(dest),'sha256':sha(dest.read_bytes()),'evidence_files':len(evidence)}))
