from pathlib import Path
import hashlib,importlib.util,json,sys
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261019T1743'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert sha(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def ref(rel):return {'path':rel,'sha256':sha(R/rel),'bytes':(R/rel).stat().st_size}
def write(rel,value):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 return ref(rel)
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','publish_0943_controller')
contract=mod('scripts/ops/formal_action_deployment_v1/contract.py','efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19','publish_0943_contract')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=sha(state)
 integration=json.loads((R/'results/formal_main_v2/preflight/heartbeat_20261019T1609/action_candidate_root_integration.json').read_text())
 # Pin the previously root-published seven exact source files.
 files={rel:sha(R/rel) for rel in contract.EXPECTED_NEW_FILES}
 expected={'runtime_scope.py':'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53','contract.py':'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19','wrapper.py':'d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33','entry.py':'2cdb69923146cbffcaaec555b970d03efbce0c9b9f74e3b743a2ce67a21aae19','gateway.py':'8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'}
 assert files=={contract.PREFIX+k:v for k,v in expected.items()}
 files.update(contract.GPU_REFS);copies=[]
 for rel,pin in sorted(files.items()):
  src=R/rel;dest=P/rel;contract.relative(rel);assert sha(src)==pin and not src.is_symlink()
  if dest.exists():
   assert not dest.is_symlink() and sha(dest)==pin;action='same_bytes_existing'
  else:
   dest.parent.mkdir(parents=True,exist_ok=True)
   with dest.open('xb') as f:f.write(src.read_bytes())
   assert sha(dest)==pin;action='published_exact_bytes'
  copies.append({'path':rel,'sha256':pin,'action':action})
 receipt=write('results/formal_main_v2/execution/action_spatial_resume_0943/runtime_publication.json',{'utc':datetime.now(timezone.utc).isoformat(),'files':copies,'runtime_directory':str(P),'readiness_issued':False,'stage_limit':'development','O2A_and_freeze_prohibited_without_separate_equivalence_gate':True,'new_GPU_jobs':0,'state_unchanged':sha(state)==before,'weights_copied':False})
 assert sha(state)==before
 print(json.dumps({'runtime_publication':receipt,'new_files':sum(x['action']=='published_exact_bytes' for x in copies),'GPU_jobs_submitted':0}),flush=True)
codec=mod('scripts/ops/nonweight_archive.py','f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2','root_archive_0943')
old='results/formal_main_v2/nonweight_archives/v1/snapshots/completed_training_20261019_0547_union17_v2.json'
assert sha(R/old)=='3f3d25952624f489f3182bc3111c1e070e7ecc52218d9ab6e4059a4941e8f6f3'
files=[{k:r[k] for k in ['path','sha256','bytes']} for r in json.loads((R/old).read_text())['files']]
new=['results/formal_main_v2/libero_object/k256/seed41/training/A/attempts/20261018T180039_8dcacbab339e/cost_events.jsonl','results/formal_main_v2/libero_object/k256/seed41/training/B/attempts/20261019T002040_ced2998819f1/cost_events.jsonl','results/formal_main_v2/libero_object/k256/seed41/training/cache_events/3034570_8f281e87d6dc.jsonl','results/formal_main_v2/libero_object/k256/seed23/training/A/attempts/20261019T074511_2e578cf574d4/cost_events.jsonl','results/formal_main_v2/libero_object/k256/seed23/training/B/attempts/20261019T085530_adfef4bf73f9/cost_events.jsonl','results/formal_main_v2/libero_object/k256/seed23/training/cache_events/3039258_c3b3a46774d4.jsonl']
for rel in new:
 row=ref(rel);assert sha(P/rel)==row['sha256'];files.append(row)
assert len(files)==23 and len({x['path'] for x in files})==23
provenance=[ref(old),ref(B+'/3034570_root_terminal.json'),ref(B+'/cuda_recovery_pull_v2.json'),ref('results/formal_main_v2/pulls/20261019T095542Z_e5d54e39d3ae/receipt.json')]
request='results/formal_main_v2/nonweight_archives/v1/requests/completed_training_20261019_0943_union23.json'
rr=write(request,{'schema':codec.SCHEMA,'kind':'archive_request','files':files,'provenance':provenance})
snapshot='results/formal_main_v2/nonweight_archives/v1/snapshots/completed_training_20261019_0943_union23.json'
result=codec.pack(R,request,snapshot);out=write(B+'/nonweight_archive_pack.json',result)
print(json.dumps({'archive_result':out,'snapshot':ref(snapshot),'files':len(files),'total_raw_bytes':sum(x['bytes'] for x in files),'new_raw_paths':new}),flush=True)
