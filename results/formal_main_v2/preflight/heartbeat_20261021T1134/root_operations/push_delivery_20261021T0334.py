from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,os,subprocess,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261021T1134'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def module(n,pin,label):
 p=R/n;assert h(p)==pin;sp=importlib.util.spec_from_file_location(label,p);m=importlib.util.module_from_spec(sp);sys.modules[label]=m;sp.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument('--expected-head',required=True);a=ap.parse_args()
assert os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R)
assert len(a.expected_head)==40 and all(x in '0123456789abcdef' for x in a.expected_head)
ctl=module('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','push0334ctl')
with ctl.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert h(R/'results/experiment_supervisor/state.json')=='54ee7389fe300b4ec553998d91b9bf727ca3231c2066e35a86716559a3c1406d'
 assert h(R/B/'final_summary.json')=='35a12c33d2bf81331e96aad4fe2879ae06fa7269a518fc14933fea8dc65aac02'
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==a.expected_head
 assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)
 helper=R/'scripts/ops/server_github_sync.py'
 assert h(helper)=='218bf59be0f28ed145a38ed4196cf02b5a6134fcf8a4531abf127f838cc5f729'
 auth=sys.stdin.buffer.read();value=json.loads(auth)
 assert isinstance(value['username'],str) and isinstance(value['password'],str) and value['password']
 p=subprocess.run([sys.executable,'-B',str(helper),'--operation','push'],input=auth,capture_output=True)
 del auth,value
 if p.returncode:
  raise RuntimeError(p.stderr.decode('utf-8','replace'))
 result=json.loads(p.stdout)
 assert result['remote_head_after']==result['local_head']==a.expected_head and result['credentials_persisted'] is False
 result.update(utc=datetime.now(timezone.utc).isoformat(),root_state_sha256=h(R/'results/experiment_supervisor/state.json'),summary_sha256=h(R/B/'final_summary.json'),mode='non_force_push_and_remote_HEAD_verify')
 q=R/'.local/github_push_20261021T0334_verified.json';assert not q.exists();q.open('xb').write((json.dumps(result,sort_keys=True,indent=2)+'\n').encode())
 print(json.dumps(result))
