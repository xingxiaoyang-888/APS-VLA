from pathlib import Path
import hashlib,json,ast
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_remaining5_runtime_20261021T0449'
old=R/'.local/goal_full200_author_20261021T0110/cpu_full200_v3.py'
source=old.read_text()
keys=['libero_goal_k256_seed23','libero_goal_k256_seed41','libero_goal_k64_seed17','libero_goal_k64_seed23','libero_goal_k64_seed41']
for key in keys:
 tokens=int(key.split('_k')[1].split('_')[0]);seed=int(key.split('_seed')[1])
 s=source.replace("OUT=D/'CPU_full200_v3'","OUT=D/'CPU_"+key+"'")
 s=s.replace("gate=load(D/'package/paired_input_gate_v1.py','goal_paired_gate_cpu');","scope=load(D/'package/scope.py','scope_cpu');ctx=scope.context('"+key+"');gate=load(D/'package/paired_input_gate_v1.py','goal_paired_gate_cpu');")
 s=s.replace('gate.fixed_prefix()','gate.fixed_prefix(ctx)').replace('gate.PairedInputGate(','gate.PairedInputGate(ctx,')
 s=s.replace('A256_seed17','A'+str(tokens)+'_seed'+str(seed)).replace('B256_seed17','B'+str(tokens)+'_seed'+str(seed))
 # Old accepted real panel source stays read-only, but own identities are rebuilt.
 ast.parse(s)
 with (D/('cpu_'+key+'_v1.py')).open('x') as f:f.write(s)
with (D/'cpu_test_derivation.json').open('x') as f:json.dump({'original_entry':str(old),'sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'changes':['private output folder','explicit new immutable pair context','new methods only; runtime seed17 unchanged'],'tests':keys,'CPU_fixtures_only':True},f,indent=2)
print(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.glob('cpu_libero*_v1.py')},indent=2))
