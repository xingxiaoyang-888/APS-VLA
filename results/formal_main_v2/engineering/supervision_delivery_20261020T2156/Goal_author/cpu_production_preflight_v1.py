"""Read-only actual production closure and native MuJoCo CPU observation probe."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,importlib.util,sys,os,shutil,time,traceback,ctypes.util
os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['MUJOCO_GL']='egl'
D=Path(__file__).parent;R=D.parents[1];P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';OUT=D/'CPU_production_preflight01';OUT.mkdir(exist_ok=False);checks=[]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def write(name,v):(OUT/name).write_text(json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def ck(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def main():
 entry=load(D/'package/entry.py','goal_production_candidate_preflight');package=json.loads((D/'package/package_manifest.json').read_text())
 ck('private_eight_file_closure',len(package['files'])==8 and all(sha(D/'package'/Path(p).name)==h for p,h in package['files'].items()))
 entry.validate_config(json.loads((D/'package/config.json').read_text()))
 started=time.monotonic();inv,wrapper,ctx,legacy=entry.prepare_original();duration=time.monotonic()-started
 prefix=json.loads((D/'package/prefix58.json').read_text())['rows'];prefix_proof=entry.validate_prefix(inv,legacy,prefix)
 ck('actual_original_wrapper_verify_and_selected_checkpoints',True)
 ck('actual_original_prefix58_not_new_science',prefix_proof['original_fixed58_identity_order'] and prefix_proof['unique_development_states']==29)
 files={}
 def add(p,expected=None,category='production'):
  p=Path(p);h=sha(p)
  if expected is not None:ck('sourcepin:'+str(p),h==expected)
  files[str(p)]={'sha256':h,'bytes':p.stat().st_size,'category':category}
 for p,h in inv['watched_files'].items():add(p,h,'original_invocation_watched')
 add(entry.ORIGINAL,entry.ISHA);add(entry.WRAPPER,entry.WSHA);add(entry.LEGACY,entry.LSHA)
 frozen=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text())['files'];ck('173_frozen_inventory',len(frozen)==173)
 for root in (R,S,R/'snapshots/formal_main_v2_run_564be0995e'):
  for rel,pin in frozen.items():add(root/rel,pin,'frozen173_exact')
 for name,module in sorted(list(sys.modules.items())):
  p=getattr(module,'__file__',None)
  if p:
   p=Path(p)
   if p.is_file() and any(p.is_relative_to(x) for x in (R,P,S)):add(p,category='actually_imported_module')
 checkpoint={}
 manifest=json.loads(Path(inv['execution_manifest']).read_bytes())
 for method in manifest['methods']:
  p=Path(method['checkpoint']);checkpoint[method['identity']['method_id']]={'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size};ck('checkpoint:'+method['identity']['method_id'],checkpoint[method['identity']['method_id']]['sha256']==method['identity']['checkpoint_sha256'])
 write('source_closure.json',{'status':'actual_P_readonly_closure_verified_new_package_private_only','files':files,'checkpoint_identities_server_only':checkpoint,'candidate_package':package,'prefix_proof':prefix_proof,'prepare_original_wall_seconds':duration,'ctx_keys':sorted(ctx),'module_global_path_redirects':False,'production_writes':0,'GPU_jobs':0,'real_GPU_acceptance':False})
 # Worst-case bound uses all58 prefixes and the official300 controls. Deliberately
 # counts before+after images separately, even though the recorder deduplicates.
 f=P/'results/formal_main_v2/engineering/goal_prefix58_20261020T1825/attempt01/observer/events.jsonl'
 rows=[json.loads(line) for line in f.open()];obs=[r for r in rows if r.get('observation_arrays')]
 image_shapes=sorted({(k,tuple(v['shape']),v['dtype'],v['bytes']) for r in obs for k,v in r['observation_arrays'].items()})
 array_bytes=max(sum(v['bytes'] for v in r['observation_arrays'].values()) for r in obs)
 sim_bytes=max(sum(v['bytes'] for v in r.get('sim_array_blobs',{}).values()) for r in rows)
 rng_bytes=max(r.get('global_rng',{}).get('bytes',0) for r in rows);line_bytes=max(len(json.dumps(r,ensure_ascii=False,separators=(',',':')).encode()) for r in rows)
 queries_per_trial=(300+7)//8;query_captures=58*queries_per_trial*2
 nonquery_per_trial=max(sum(1 for r in rows if r.get('ordinal')==i and r.get('phase') not in ('t0_query_before','t0_query_after')) for i in range(1,59))
 capture_count=query_captures+58*nonquery_per_trial+32
 max_blob_bytes=capture_count*(array_bytes+sim_bytes+rng_bytes)
 # Each JSON line generously budgeted64KiB and duplicate original ledger with
 # token arrays/identity metadata another256MiB; no images/video besides blobs.
 text_bytes=capture_count*max(65536,line_bytes*4)+58*300*4096+256*(1<<20)
 upper=max_blob_bytes+text_bytes;free=shutil.disk_usage(P).free;safety=1<<30
 storage={'sample':{'path':str(f),'sha256':sha(f),'rows':len(rows),'observation_shapes':image_shapes,'max_observation_bytes':array_bytes,'max_sim_bytes':sim_bytes,'max_rng_bytes':rng_bytes,'max_event_bytes':line_bytes},'all58_maximum_policy_queries':58*queries_per_trial,'query_captures':query_captures,'nonquery_captures_per_trial_conservative':nonquery_per_trial,'capture_count_bound':capture_count,'no_dedup_blob_bytes_bound':max_blob_bytes,'text_and_original_ledger_budget_bytes':text_bytes,'total_estimated_upper_bytes':upper,'P_free_bytes_at_check':free,'required_free_including_1GiB_margin':upper+safety,'sufficient_at_check':free>=upper+safety,'estimate_is_not_guaranteed_cross_process_disk_reservation':True,'output_mapping_changed':False}
 write('storage_bound.json',storage);ck('P_space_bound_with_margin_at_check',storage['sufficient_at_check'])
 # Real native MuJoCo data; synthetic wrapper/images and no LIBERO reset/render.
 import numpy as np,mujoco
 gate=load(D/'package/paired_input_gate_v1.py','goal_native_passivity_gate')
 model=mujoco.MjModel.from_xml_string('<mujoco><worldbody><body><joint name="probe_joint" type="slide"/><geom type="sphere" size="0.1" mass="1"/></body></worldbody><actuator><motor joint="probe_joint"/></actuator></mujoco>')
 data=mujoco.MjData(model);mujoco.mj_forward(model,data)
 env=SimpleNamespace(env=SimpleNamespace(sim=SimpleNamespace(data=SimpleNamespace(_data=data)),np_random=np.random.RandomState(81),timestep=0))
 observation={'agentview_image':np.zeros((256,256,3),dtype=np.uint8),'robot0_eye_in_hand_image':np.ones((256,256,3),dtype=np.uint8),'robot0_eef_pos':np.zeros(3),'robot0_eef_quat':np.array([0.,0.,0.,1.]),'robot0_gripper_qpos':np.zeros(2)}
 ob=gate.PairedInputGate(OUT/'native_passive_capture',allow_cpu_fixture=False)
 before=gate.recorder.passive_environment(env,allow_cpu_fixture=False)[0];rng=gate.recorder.global_rng();obj=gate.recorder.object_guard(observation)
 ob.capture('native_CPU_existing_state_before',env,observation)
 after=gate.recorder.passive_environment(env,allow_cpu_fixture=False)[0]
 ck('actual_MjData_supported_native_route',before.get('native_type')=='mujoco._structs.MjData' and all('missing' not in v for k,v in before['fields'].items() if k!='time'))
 ck('native_CPU_data_RNG_observation_passive',before==after and rng==gate.recorder.global_rng() and obj==gate.recorder.object_guard(observation))
 ck('production_gate_fixture_disabled',ob.allow_cpu_fixture is False and ob.sink is None and ob.runtime_context=='real_environment_engineering')
 cuda=sys.modules.get('torch.cuda');ck('CUDA_not_initialized',cuda is None or not cuda.__dict__.get('_initialized'))
 write('native_passivity.json',{'status':'passed_actual_native_MjData_CPU_route_only','mujoco_version':mujoco.__version__,'allow_cpu_fixture':False,'actual_native_MjData':True,'synthetic_wrapper':True,'synthetic_images':True,'full_LIBERO_environment':False,'render_or_GPU_requested':False,'OSMesa_library_available':bool(ctypes.util.find_library('OSMesa')),'global_RNG_observation_native_state_unchanged':True,'not_real_GPU_acceptance':True,'source':'existing CPU native descriptors under pinned observer; no simulator getter/step/render invoked inside capture'})
 return {'status':'passed_CPU_production_closure_and_native_passivity','checks':checks,'check_count':len(checks),'production_writes':0,'GPU_jobs':0,'scientific_trials_added':0,'old200_HOLD':True,'new_Goal_science_HOLD':True,'real_GPU_acceptance':False}
try:report=main()
except BaseException as e:
 report={'status':'failed_CPU_preflight','checks':checks,'error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()};write('report.json',report);print(json.dumps({k:report[k] for k in ('status','error_type','error')}));raise
write('report.json',report);print(json.dumps({k:report[k] for k in ('status','check_count','production_writes','GPU_jobs')}))
