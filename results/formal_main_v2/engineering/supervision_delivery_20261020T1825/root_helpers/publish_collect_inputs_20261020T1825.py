from pathlib import Path
import fcntl,hashlib,json,os
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0225'
D=R/'.local/spatial_object_collect_20261020T1825'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def safe(p):
 assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]);return p
def publish(p,raw):
 safe(p);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw;return
 with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
pins={'Spatial':['788611fd20e81853f8500172efb08c73148c02a2188c8eabec2dad37f3fc7777','c7c4eeebe1b4ee933f641109f5f842df29eb0c22e2b945d6da0e94ba3c3dd692','adcff0fb51d7d5a09ae702e17cbd88afbe980f4188a96f94740967ae8ab6add5'],'Object':['45197f0dc711ebc09a685e25a8edc251c25b881eb1ad477ef8dbbe89a9aed13d','d7cb39702f71fc4558661a4d2df47e5a6094a73ee1c391b0b612489e0d7644a2','10c772b3ca42d905222d887d73712d64eddb620dd16b2b7af4c8b2c6fc475247']}
with (R/'results/experiment_supervisor/.writer.lock').open('a+b') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read(sp);assert s['pending_submission'] is None
 allrows=[]
 for suite,hashes in pins.items():
  files=['dense_development.json','collection_selection_registration.json','dense_input_evidence.json']
  for name,pin in zip(files,hashes):assert h(safe(D/suite/name))==pin
  inp=read(D/suite/files[0]);reg=read(D/suite/files[1]);ev=read(D/suite/files[2]);panel=read(safe(R/inp['development_panel']))
  assert inp['suite']=='libero_'+suite.lower() and inp['split']=='development' and inp['environment']=={'action_chunk':8,'environment_seed':0,'max_steps':220 if suite=='Spatial' else 280,'runtime_seed':17,'wait_steps':10}
  assert len(inp['methods'])==1 and inp['methods'][0]['identity']['method_id']=='dense' and inp['methods'][0]['identity']['visual_tokens']==512 and inp['methods'][0]['identity']['future_head_deployed'] is False
  assert h(R/inp['development_panel'])==inp['development_panel_sha256'] and panel['split']=='development' and len(panel['states'])==100
  expected=[min([x for x in panel['states'] if x['task_id']==t],key=lambda x:x['source_state_index']) for t in range(10)]
  assert reg['selected_states']==expected and reg['expected_observations']==30 and reg['final_values_read'] is False and reg['full_or_components_timing_authorized'] is False and reg['submission_authorized'] is False
  assert not any(j.get('mode')=='collect' and j.get('suite')==inp['suite'] for j in s['registered_jobs'])
  dest=Path(ev['canonical_path']);assert dest==Path('results/formal_main_v2/execution')/(suite.lower()+'_collect_action_v1_20261020T1825')/'dense_development.json'
  for name,pin in zip(files,hashes):
   rel=dest.parent/name;raw=(D/suite/name).read_bytes()
   for root in [R,P]:publish(root/rel,raw);assert h(root/rel)==pin
   allrows.append({'source':str((D/suite/name).relative_to(R)),'destination':rel.as_posix(),'sha256':pin,'bytes':len(raw),'roots':['R','P']})
 assert h(sp)==before
 receipt={'schema':'formal_main_v2','kind':'exact_Spatial_Object_collect_input_publication','status':'source_only_published_verified','files':allrows,'state_before_sha256':before,'state_unchanged':True,'new_GPU_jobs':0,'final_values_read':False,'submission_authorized':False,'scientific_settings_changed':False,'utc':datetime.now(timezone.utc).isoformat()}
 out=B/'Spatial_Object_collect_input_publication.json';publish(out,(json.dumps(receipt,sort_keys=True,indent=2)+'\n').encode());print(json.dumps({'path':str(out.relative_to(R)),'sha256':h(out),'files':len(allrows)}))
