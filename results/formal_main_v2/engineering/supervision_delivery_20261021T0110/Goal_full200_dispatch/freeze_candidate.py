"""Freeze exact final runtime identity into this private Goal dispatcher only."""
from pathlib import Path
import argparse,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_full200_dispatch_20261021T0110'
EXPECTED=R/'.local/goal_full200_author_20261021T0110_v2'
BASE='scripts/ops/formal_goal_full200_dispatch_v1'
PROD='scripts/ops/formal_goal_full200_gate_v1'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2).encode()+b'\n'
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--package-sha256',required=True);p.add_argument('--delivery-sha256',required=True);a=p.parse_args()
 package=EXPECTED/'package/package_manifest.json';b=package.read_bytes()
 assert sha(b)==a.package_sha256
 m=json.loads(b);assert len(m['files'])==10
 assert sha((EXPECTED/'delivery_manifest.json').read_bytes())==a.delivery_sha256
 for rel,pin in m['files'].items():assert sha((EXPECTED/'package'/Path(rel).name).read_bytes())==pin
 scope=dict(schema='formal_main_v2',kind='Goal_full200_exact_dispatch_scope',version='goal-full200-held-atomic-dispatch-v1',
  stage_key='goal_full200_20261021T0110',suite='libero_goal',visual_tokens=256,training_seed=17,
  pair_id='5b1bc1ab99e1bfa1545ef8270ca3fbe8364349ab462f8a64fb4858eb15576e1e',
  method_ids=['A256_seed17','B256_seed17'],unique_development_states=100,maximum_trials=200,
  maximum_total_control_steps=60000,maximum_total_policy_queries=7600,
  runtime_package_manifest_sha256=a.package_sha256,runtime_files=m['files'],
  runtime_author=dict(root=str(EXPECTED.relative_to(R)),delivery_manifest_sha256=a.delivery_sha256),
  original_scientific_invocation=dict(path='results/formal_main_v2/invocations/libero_goal_development_5185766bb353c8e6_attempt01.json',
   sha256='c07489c5e56cc3255b60f5eb6df34146e37e4b60fa7151cc97f8008f402b8803'),
  original_engineering_allocations=[dict(job_id='3053440',gpu_seconds=803),dict(job_id='3054127',gpu_seconds=840)],
  maximum_attempts=1,maximum_GPU_jobs=1,capacity_all_GPU_modes=8,automatic_retry=False,other_Goal1000_HOLD=True,
  old_Goal200_HOLD=True,final_allowed=False,release_requires_real_root_readiness=True,
  CPU_scope_only=True,GPU_execution_authorized=False)
 scopebytes=dump(scope);sp=D/'scope.json'
 with sp.open('xb') as f:f.write(scopebytes)
 path=D/'dispatch.py';text=path.read_text()
 assert text.count('RUNTIME_MANIFEST_PENDING_FINAL_PIN')==1 and text.count('SCOPE_PENDING_FINAL_PIN')==1
 text=text.replace('RUNTIME_MANIFEST_PENDING_FINAL_PIN',a.package_sha256).replace('SCOPE_PENDING_FINAL_PIN',sha(scopebytes));path.write_text(text)
 tests=D/'verify_cpu.py';s=tests.read_text().replace(".local/goal_full200_author_20261021T0110/package",".local/goal_full200_author_20261021T0110_v2/package")
 s=s.replace("lp=R/'.local/object_single_error_gateway_20261021T0110/live_inputs.json'","lp=D/'saved_real_observation.json'")
 tests.write_text(s)
 live=R/'.local/object_single_error_gateway_20261021T0110/live_inputs.json'
 with (D/'saved_real_observation.json').open('xb') as f:f.write(live.read_bytes())
 names=['dispatch.py','scope.json'];files={BASE+'/'+n:sha((D/n).read_bytes()) for n in names}
 pub=dict(schema='formal_main_v2',kind='Goal_full200_exact_dispatch_publication_map',source_root=str(D.relative_to(R)),
  installation_scope='R_and_P_source_only_no_state_no_GPU_authorization',files=files,
  install_files=[dict(source=str((D/n).relative_to(R)),destination=BASE+'/'+n,bytes=(D/n).stat().st_size,sha256=files[BASE+'/'+n]) for n in names],
  runtime_separate_package_manifest_sha256=a.package_sha256,production_admitted=False,actual_P_verified=False)
 with (D/'publication_map.json').open('xb') as f:f.write(dump(pub))
 pin=dict(dispatch=files[BASE+'/dispatch.py'],scope=files[BASE+'/scope.json'],verify_cpu=sha(tests.read_bytes()),
  prepare_admission=sha((D/'prepare_admission.py').read_bytes()),runtime_package_manifest=a.package_sha256)
 with (D/'final_pins.json').open('xb') as f:f.write(dump(pin))
 print(json.dumps(pin,sort_keys=True))
if __name__=='__main__':main()
