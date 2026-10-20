"""Static compile and mutation-boundary inspection only; do not import/call drafts."""
from pathlib import Path
import ast,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/collect_terminal_20261020T1949/development_gateway'
PINS={'root_sign_readiness_v1.py':'773bc105bd77ddab8a9927e981f87c2050ff1baecb34cfdb4009916099e81338','root_dispatch_v1.py':'750a8178ef670d7a45ffc9797a05f6fb492ff0d123f9fbb0f095211b4a5af041'}
checks=[]
for name,pin in PINS.items():
 raw=(D/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==pin
 compile(raw,str(D/name),'exec',dont_inherit=True);tree=ast.parse(raw)
 calls=[ast.unparse(x.func) for x in ast.walk(tree) if isinstance(x,ast.Call)]
 assert not any(x in {'os.system','eval','exec','c.Slurm().submit','subprocess.Popen'} for x in calls)
 assert 'root-reviewed-source-sha256' in raw.decode() and 'sha(Path(__file__))' in raw.decode()
 for node in tree.body:
  if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call):raise AssertionError('unconditional top-level call '+name)
 if name.startswith('root_sign'):
  assert not any(x.startswith('subprocess.') or x.endswith('.atomic_json') or x.endswith('.run') or x.endswith('.publish') for x in calls)
  assert 'wrapper.verify' in calls and 'io.preflight' in calls and 'g.FrozenPlan(R, aa, ee, plan, inner, inv).prepare' in calls
 else:
  assert calls.count('subprocess.run')==2 and calls.count('c.atomic_json')==1
  assert not any(x in {'os.remove','os.unlink','shutil.rmtree','os.replace'} for x in calls)
  assert 'g.capacity_gate' in calls and 'g.validate_authorization' in calls
 checks.append({'source':str((D/name).relative_to(R)),'sha256':pin,'compiled':True,'not_imported_or_executed':True,'original_transaction_delegated':True})
report={'kind':'root_draft_static_compile_only','status':'passed_static_checks','checks':checks,'not_a_dynamic_or_root_readiness_acceptance':True,'production_writes':0,'Slurm_calls':0,'GPU_calls':0,'limits':'No root helper function was imported or executed; root and independent review plus actual root execution remain required.'}
p=D/'root_drafts_static_check.json'
with p.open('x') as f:json.dump(report,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'report':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
