from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,sys,json,subprocess
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--expected-head',required=True);args=ap.parse_args()
assert len(args.expected_head)==40 and all(ch in '0123456789abcdef' for ch in args.expected_head)
helper=R/'scripts/ops/server_github_sync.py'
assert h(helper)=='218bf59be0f28ed145a38ed4196cf02b5a6134fcf8a4531abf127f838cc5f729'
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('gitpush20261020T2054ctl',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
auth=json.load(sys.stdin)
assert set(auth)=={'username','password'} and all(isinstance(v,str) and v for v in auth.values())
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert subprocess.check_output(['git','-C',str(R),'rev-parse','HEAD'],text=True).strip()==args.expected_head
 assert subprocess.check_output(['git','-C',str(R),'diff','--cached','--name-only'])==b''
 result=subprocess.run([sys.executable,'-B',str(helper),'--operation','push'],input=json.dumps(auth),capture_output=True,text=True)
 del auth
 if result.returncode:
  print(result.stderr,file=sys.stderr);raise SystemExit(result.returncode)
 value=json.loads(result.stdout)
 assert value['operation']=='push' and value['local_head']==value['remote_head_after']==args.expected_head and value['credentials_persisted'] is False
 value.update(helper_sha256=h(helper),verified_utc=datetime.now(timezone.utc).isoformat(),transient_proxy_only=True)
 out=R/'.local/github_push_20261020T2054_verified.json'
 with out.open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(value),flush=True)
