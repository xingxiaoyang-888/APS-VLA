from pathlib import Path
import hashlib,json,runpy,sys
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/object_single_error_gateway_20261021T0110')
for n,h in {'gateway.py': '8471bba1419a9e0ca31f84e7e55ff232cd6fb0fcb4bcb89320140ea76292d727', 'build.py': 'a7f08f90a44ba7eac2b8193e597beced79afbe73f1283ef2fd82f40b83519207', 'verify_cpu.py': '21149d9e50067520598de510c7f1e2c4b225279cec2e7ad7f7e86b3c1f120340'}.items():assert hashlib.sha256((D/n).read_bytes()).hexdigest()==h
m=runpy.run_path(str(D/'verify_cpu.py'),run_name='_object_gateway_final_cpu')
g=m['g']
old=g.read(D/'live_inputs_v3_before_pending_binding.json')
with g.shared_writer_lock():
 b=g.raw(g.R/g.STATE);assert g.sha(b)==old['state_sha256']
 state=json.loads(b);assert state['autonomous_training_v1'].get('pending_submission') is None
 old['state_for_projection']=m['state_for_projection'](state)
 old['nested_pending_binding']=dict(utc=g.utc(),state_sha256=g.sha(b),autonomous_pending=None,original_observation_utc=old['result']['utc'],new_Slurm_query=False)
 with (D/'live_inputs.json').open('x') as f:json.dump(old,f,ensure_ascii=False,sort_keys=True,indent=2)
sys.argv=[str(D/'verify_cpu.py')]
m['main']()
