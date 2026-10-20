"""Read-only rerun of pinned independent audit; reconstructs every saved output in memory.
The sole substitution is the output sink: compare exact bytes instead of writing.
CPU/wall-clock durations in the final receipt are excluded from equality.
No scientific/source/validation function is replaced.
"""
import hashlib,json,sys,types
from pathlib import Path
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/object599_independent_20261020T2253')
p=D/'audit_object599_v4.py';b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=='288b4ad7332b8d46d445d11b9b5f24544e504a897388bf7363d81128a0fe4715'
m=types.ModuleType('_saved_object599_reconstruction');m.__file__=str(p);sys.modules[m.__name__]=m;exec(compile(b,str(p),'exec',dont_inherit=True),m.__dict__)
outputs=[]
def compare(name,value,jl=False):
 b=b''.join(m.canon(v)+b'\n' for v in value) if jl else json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2).encode()+b'\n'
 actual=(D/name).read_bytes()
 if name=='independent_review.json':
  a=json.loads(actual);c=json.loads(b)
  for key in ['CPU_seconds','wall_seconds']:a.pop(key);c.pop(key)
  assert a==c,'final receipt differs beyond timing'
 else:assert actual==b,'saved output differs: '+name
 # The original audit hook counted one authorized private write per emitted file.
 # Preserve the assertion counter while this rerun performs zero writes.
 m.ck(True,'private_write_only')
 outputs.append(name)
 return {'path':str((D/name).relative_to(m.R)),'sha256':hashlib.sha256(actual).hexdigest(),'bytes':len(actual)}
m.out=compare;m.main();assert p.read_bytes()==b
print(json.dumps({'status':'passed_read_only_full_reconstruction','saved_outputs':outputs,'new_GPU_seconds':0,'new_scientific_trials':0,'writes':0}),flush=True)
