from pathlib import Path
import ast,hashlib,importlib.util,json,sys
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/goal_remaining5_runtime_20261021T0449')
Q=D/'package'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 b=(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return {'path':str(p),'sha256':sha(p),'bytes':len(b)}
sp=importlib.util.spec_from_file_location('final_r5_scope',Q/'scope.py');scope=importlib.util.module_from_spec(sp);sp.loader.exec_module(scope)
files={}
for rel in sorted(scope.PACKAGE_FILES):
 p=Q/Path(rel).relative_to(scope.PKG)
 assert p.is_file() and not p.is_symlink()
 if p.suffix=='.py':ast.parse(p.read_text())
 files[rel]=sha(p)
assert len(files)==20
for k in scope.KEYS:
 ctx=scope.context(k)
 assert ctx.config['pair_key']==k
 assert sha(Q/'pairs'/k/'specification.json')==ctx.spec_sha
baseline=json.loads((D/'baseline_provenance.json').read_text())
R=scope.R
for row in baseline['files']:assert sha(R/row['path'])==row['sha256']
package={'schema':'formal_main_v2','kind':'exact_five_Goal_runtime_source_package','version':scope.VERSION,'files':files,'pair_keys':list(scope.KEYS),'source_count':len(files),'production_installed':False,'real_GPU_acceptance':False,'new_GPU_submissions':0,'scientific_results_accepted':0,'original200_HOLD':True,'final_release':False,'root_fixed_design':scope.context(scope.KEYS[0]).root_decision,'root_storage_decision':scope.context(scope.KEYS[0]).storage_decision,'original_source_manifest_sha256':baseline['source_manifest_sha256'],'original_package_unchanged':True}
ref=write(Q/'package_manifest.json',package)
report={'schema':'formal_main_v2','kind':'remaining5_source_freeze','status':'source_frozen_pending_independent_actual_P_and_root_GPU_gates','package_manifest':ref,'files':files,'pair_keys':list(scope.KEYS),'old_package_byte_identity_verified':True,'production_writes':0,'new_GPU_submissions':0}
write(D/'source_freeze.json',report)
print(json.dumps(ref))
