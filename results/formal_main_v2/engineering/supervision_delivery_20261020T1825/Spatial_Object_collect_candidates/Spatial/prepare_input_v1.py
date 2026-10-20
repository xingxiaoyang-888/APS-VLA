"""Exact frozen-helper Dense collect input; private CPU preparation, never submit."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,os,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/spatial_object_collect_20261020T1825/Spatial'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
BUILDER='scripts/formal_execution_manifests.py'
BUILDER_SHA='614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89'
PANEL='configs/manifests/formal_main_v2/libero_spatial/initial_states/development.json'
CANONICAL='results/formal_main_v2/execution/spatial_collect_action_v1_20261020T1825/dense_development.json'
sys.dont_write_bytecode=True
sys.path[:0]=[str(R/'src'),str(R/'scripts')]
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No subprocess/network in preparation')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(path));p=p if p.is_absolute() else Path.cwd()/p
   if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or p.suffix.lower() in {'.pt','.pth','.safetensors','.pkl','.pickle','.ckpt','.bin','.pruned_init','.init'}:raise RuntimeError('No sealed/weight reads: '+str(p))
   writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
   if writing and D not in p.parents:raise RuntimeError('Write outside private preparation: '+str(p))
sys.addaudithook(guard)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=digest(p),bytes=p.stat().st_size)
def write(name,value):
 p=D/name;raw=value if isinstance(value,bytes) else (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(raw)
 return ref(p)
def require(v,m):
 if not v:raise ValueError(m)
def main():
 require(digest(R/BUILDER)==BUILDER_SHA,'original builder changed')
 spec=importlib.util.spec_from_file_location('spatial_collect1825_exact_builder',R/BUILDER);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
 ev=h.Evidence(R);sources=h.source_contract(ev,INV);reg=h.registration_contract(ev,h.REGISTRATION)
 rows=h.suite_rows(ev,reg,'libero_spatial',sources,['dense']);manifest=h.make_execution(reg,'libero_spatial',rows)
 manifest.update(development_panel=PANEL,development_panel_sha256=ev.watch(PANEL))
 from cti_vla.evaluation import formal_profiling as fp
 from cti_vla.data.formal_initial_states import load_formal_development_panel
 require(fp.validate_profile_manifest(manifest,reg,collect=True)==['dense'],'exact Dense collect manifest')
 dev=load_formal_development_panel(ev.path(PANEL));states=fp.fixed_profile_states(dev)
 require(len(dev['states'])==100 and len(states)==10 and [x['task_id'] for x in states]==list(range(10)),'fixed100 development/10 task panel')
 require(manifest['environment']['wait_steps']==10 and manifest['environment']['action_chunk']==8 and manifest['environment']['max_steps']==220,'environment protocol')
 previous=ev.read('results/formal_main_v2/execution/libero_spatial_development_first_pair_v1.json')
 require(rows==[previous['methods'][0]],'Dense identity differs from established official reference')
 inventory=ev.read(INV);frozen=[]
 for root in (R,S,R/'snapshots/formal_main_v2_run_564be0995e'):
  for rel,expected in inventory['files'].items():require(digest(root/rel)==expected,'173 frozen source differs: '+str(root/rel))
  frozen.append(dict(root=str(root),files=173,aggregate_sha256=inventory['source_sha256']))
 raw=(R/'results/experiment_supervisor/state.json').read_bytes();state=json.loads(raw)
 existing=[j for j in state['registered_jobs'] if j.get('suite')=='libero_spatial' and (j.get('mode') in ('collect','full','components') or j.get('stage') in ('collect','full','components'))]
 require(not existing,'collect/profile job already registered; no fresh proposal')
 observed=[]
 for root in (R,P):
  down=root/'results/formal_main_v2/libero_spatial/downstream'
  stages=sorted(x.name for x in down.iterdir()) if down.exists() else []
  require(not set(stages)&{'collect','full','components'},'existing formal profile output')
  observed.append(dict(root=str(root),stages=stages))
 manifest_ref=write('dense_development.json',manifest)
 ev.unchanged()
 selection=write('collection_selection_registration.json',dict(schema='formal_main_v2',kind='Spatial_dense_fixed30_collection_registration_candidate',status='candidate_pending_root_and_independent_readiness',suite='libero_spatial',stage='collect',development_panel=dict(path=PANEL,sha256=ev.watch(PANEL)),development_states_total=100,selected_state_rule='minimum source_state_index per task 0..9',selected_states=states,observations_per_trajectory='control pre-action first, floor((N-1)/2), last; N>=3',control_steps_exclude_wait=True,expected_observations=30,trajectory_count=10,environment=manifest['environment'],policy='official Dense512 two views; one actual rollout per fixed initial state',success_based_replacement=False,insufficient_trajectory='fail without padding or replacement',RNG=dict(python=17,numpy=17,torch=17,simulator=0),repeated_scientific_success_trials=0,collection_ledger_separate=True,weights_deserialized=False,final_values_read=False,global_freeze_required=False,full_or_components_timing_authorized=False,new_GPU_seconds=0,submission_authorized=False))
 write('dense_input_evidence.json',dict(schema='formal_main_v2',kind='Spatial_dense_collect_input_candidate',status='CPU_input_preparation_passed_pending_canonical_publication',created_utc=datetime.now(timezone.utc).isoformat(),source_builder=dict(path=BUILDER,sha256=BUILDER_SHA),candidate=manifest_ref,canonical_path=CANONICAL,selection_registration=selection,source_provenance=ev.source_provenance,protected_source_checks=frozen,state_observation_sha256=hashlib.sha256(raw).hexdigest(),registered_profile_jobs=existing,output_observation=observed,read_evidence_sha256=ev.files,scientific_settings_changed=False,no_source_or_state_or_Git_mutation=True,submission_authorized=False))
 print(json.dumps(dict(candidate=manifest_ref,canonical_path=CANONICAL,selected=[dict(task_id=x['task_id'],source_state_index=x['source_state_index'],trial_id=x['trial_id']) for x in states],status='passed_CPU_input_only'),ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  write('input_preparation_failure_v1.json',dict(error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc()));raise
