from pathlib import Path
import ast,hashlib,json
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/goal_remaining5_runtime_20261021T0449');Q=D/'package'
pin=hashlib.sha256((Q/'scope.py').read_bytes()).hexdigest()
out=[]
for n,needle in [('entry.py'," path=Path(__file__).parent/'scope.py'"),('consumer.py',"    p=Path(__file__).parent/'scope.py'")]:
 p=Q/n;b=p.read_bytes()
 with (Q/(n+'.pre_scope_pin_v5')).open('xb') as f:f.write(b)
 s=b.decode();assert s.count(needle)==1
 var='path' if n=='entry.py' else 'p';indent=' ' if n=='entry.py' else '    '
 after=needle+'\n'+indent+"if hashlib.sha256("+var+".read_bytes()).hexdigest()!='"+pin+"':raise ValueError('exact scope source differs before import')"
 s=s.replace(needle,after);ast.parse(s);p.write_text(s)
 out.append({'path':n,'before_sha256':hashlib.sha256(b).hexdigest(),'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
r={'status':'bounded_scope_preimport_pin_complete','scope_sha256':pin,'changes':out,'old_package_or_scientific_loop_changed':False,'production_writes':0}
with (D/'scope_preimport_v5_result.json').open('x') as f:json.dump(r,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps(r))
