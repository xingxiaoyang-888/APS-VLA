from pathlib import Path
import ast,hashlib,json
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/goal_full200_author_20261021T0110');K=D/'package'
H=D/'before_blob_symlink_guard';H.mkdir(exist_ok=False)
for n in ['observer_v3.py','paired_input_gate_v1.py','package_manifest.json']:(H/n).write_bytes((K/n).read_bytes())
p=K/'observer_v3.py';s=p.read_text();old="        if path.exists():\n";assert s.count(old)==1
s=s.replace(old,"        require(not path.is_symlink(), 'content-addressed blob symlink forbidden')\n"+old)
p.write_text(s);oldsha=hashlib.sha256((H/'observer_v3.py').read_bytes()).hexdigest();newsha=hashlib.sha256(p.read_bytes()).hexdigest()
p=K/'paired_input_gate_v1.py';s=p.read_text();assert s.count(oldsha)==1;p.write_text(s.replace(oldsha,newsha))
s=(D/'cpu_full200_v2.py').read_text().replace("OUT=D/'CPU_full200_v2'","OUT=D/'CPU_full200_v3'")
old="  ck('ordinary_Exception_does_not_catch_gate'"
ins="""  q=gate.PairedInputGate(OUT/'blob_link_guard',allow_cpu_fixture=True)
  payload=b'CPU explicitly forbidden linked blob';target=OUT/'link_target';target.write_bytes(payload)
  link=q.blobs/(hashlib.sha256(payload).hexdigest()+'.bin');link.symlink_to(target)
  excepts('local_blob_symlink_refused',lambda:q._blob(payload,'.bin'),(gate.GateAbort,))
  link.unlink()
"""
assert s.count(old)==1;s=s.replace(old,ins+old);(D/'cpu_full200_v3.py').write_text(s)
s=(D/'cpu_outer_v2.py').read_text().replace("O=D/'CPU_outer_v2'","O=D/'CPU_outer_v3'");(D/'cpu_outer_v3.py').write_text(s)
m=json.loads((K/'package_manifest.json').read_bytes());m['files']={('scripts/ops/formal_goal_full200_gate_v1/'+p.name):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(K.iterdir()) if p.is_file() and p.name!='package_manifest.json'}
(K/'package_manifest.json').write_text(json.dumps(m,sort_keys=True,indent=2)+'\n')
for p in K.glob('*.py'):ast.parse(p.read_text())
print(json.dumps({'tests':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['cpu_full200_v3.py','cpu_outer_v3.py']},'package_manifest_sha256':hashlib.sha256((K/'package_manifest.json').read_bytes()).hexdigest(),'files':m['files']}))
