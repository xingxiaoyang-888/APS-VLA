from pathlib import Path
import ast,hashlib,json,shutil
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
OLD=R/'.local/goal_full200_author_20261021T0110'
D=R/'.local/goal_full200_author_20261021T0110_v2'
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,b):
 with p.open('xb') as f:f.write(b)
def j(v):return (json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
oldmanifest=(OLD/'delivery_manifest.json').read_bytes()
assert sha(oldmanifest)=='56c590f04b514de9bd3a4dcde0fcba93aa7dafe7f739f651c1ee97a1e99b0f53'
manifest=json.loads(oldmanifest)
for row in manifest['files']:
 p=OLD/row['path'];b=p.read_bytes();assert sha(b)==row['sha256'] and len(b)==row['bytes']
K=D/'package';K.mkdir(exist_ok=False)
oldpackage=json.loads((OLD/'package/package_manifest.json').read_bytes())
for rel,h in oldpackage['files'].items():
 p=OLD/'package'/Path(rel).name;b=p.read_bytes();assert sha(b)==h;write(K/p.name,b)
source=(K/'consumer.py').read_text()
newfn=(D/'reconstruct_gate_v2.txt').read_text()
tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='reconstruct_gate')
lines=source.splitlines(keepends=True)
rewritten=''.join(lines[:node.lineno-1])+newfn+'\n'+''.join(lines[node.end_lineno:])
# consumer is the only source file changed from the frozen v1 package.
(K/'consumer.py').write_bytes(rewritten.encode())
a=ast.parse(source);b=ast.parse(rewritten)
dump=lambda n:ast.dump(n,include_attributes=False)
assert [dump(n) for n in a.body if not(isinstance(n,ast.FunctionDef) and n.name=='reconstruct_gate')]==[dump(n) for n in b.body if not(isinstance(n,ast.FunctionDef) and n.name=='reconstruct_gate')]
m=json.loads((OLD/'package/package_manifest.json').read_bytes())
m['files']['scripts/ops/formal_goal_full200_gate_v1/consumer.py']=sha(rewritten.encode())
write(K/'package_manifest.json',j(m))
proof=R/'.local/downstream_runtime_independent_20261021T0110/Goal_full200/counterexample_v1/blocker.json'
assert sha(proof.read_bytes())=='371b76c3e4144b45bbc6a28a9e90e6f3d995808b0c400300abb158c6e7e5ba8a'
write(D/'independent_v1_blocker.json',proof.read_bytes())
write(D/'source_delta.json',j({'schema':'formal_main_v2','kind':'Goal_full200_consumer_v2_bounded_delta','previous_manifest_sha256':sha(oldmanifest),'previous_package_manifest_sha256':sha((OLD/'package/package_manifest.json').read_bytes()),'package_manifest_sha256':sha((K/'package_manifest.json').read_bytes()),'only_changed_source':'consumer.py','unchanged_source_count':9,'unchanged_other_consumer_AST':True,'v1_independent_counterexample_sha256':sha(proof.read_bytes()),'old200_HOLD':True,'production_ready':False,'new_GPU_submissions':0,'new_scientific_trials':0}))
print(json.dumps({'consumer_sha256':sha((K/'consumer.py').read_bytes()),'package_manifest_sha256':sha((K/'package_manifest.json').read_bytes()),'source_delta_sha256':sha((D/'source_delta.json').read_bytes())}))
