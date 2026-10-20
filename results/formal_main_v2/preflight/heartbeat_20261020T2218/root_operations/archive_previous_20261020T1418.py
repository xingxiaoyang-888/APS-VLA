from pathlib import Path
import json,hashlib,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
E='results/formal_main_v2/engineering/supervision_delivery_20261020T1418/previous_delivery'
FILES={'.local/github_push_20261020T1317_verified.json':'37e2f4ee4f4f97850c21ea7c377bad60337cd59308629b100001ba2aa7742fd6','.local/git_commit_20261020T1317.json':'a610ed54ca489edd74fd4cb03ed9cbee8c793e33e0e9ba0d574f60c3cb1a8170','.local/reconcile_git_receipt_20261020T1317.py':'05891d3e0d144feafbc089db9b9895b8363314bb815096f12fbc30715f5b1546'}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('previousdelivery1418',p);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json');copies=[]
 for rel,pin in FILES.items():
  source=R/rel;assert h(source)==pin and not source.is_symlink()
  dst=R/E/source.name;dst.parent.mkdir(parents=True,exist_ok=True)
  with dst.open('xb') as f:f.write(source.read_bytes())
  copies.append(dict(source=dict(path=rel,sha256=pin,bytes=source.stat().st_size),archive=dict(path=dst.relative_to(R).as_posix(),sha256=h(dst))))
 push=json.loads((R/E/'github_push_20261020T1317_verified.json').read_bytes())
 assert push['local_head']==push['remote_head_after']=='e79204d66ecc25b3d9927499d01e2f4dd34a0fbb' and push['credentials_persisted'] is False
 receipt=dict(status='exact_previous_commit_remote_verification_preserved',copies=copies,old_postcommit_receipt_failure_preserved=True,state_unchanged=True)
 out=R/B/'previous_delivery.json'
 with out.open('x') as f:json.dump(receipt,f,sort_keys=True,indent=2);f.write('\n')
 assert h(R/'results/experiment_supervisor/state.json')==before
 print(json.dumps(dict(path=out.relative_to(R).as_posix(),sha256=h(out))))
