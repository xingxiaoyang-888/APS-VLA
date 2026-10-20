from pathlib import Path
import json,hashlib,sys,copy,ast
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
O=R/'.local/long_collect_independent_0830';sys.dont_write_bytecode=True
checks=[];evidence={}
def ck(ok,name):
 if not ok:raise AssertionError(name)
 checks.append(name)
def read(rel,pin=None):
 p=Path(rel)
 if not p.is_absolute():p=R/p
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
 if pin:ck(h==pin,'SHA '+str(rel))
 evidence[str(p.relative_to(R)) if p.is_relative_to(R) else str(p)]=h
 return b
def js(rel,pin=None):return json.loads(read(rel,pin))
mrel='results/formal_main_v2/execution/long_collect_action_v1_0830/dense_development.json'
mraw=read(mrel,'703980515d5b063c31276b0e610ffd6cdf68adae5e1f43cfb65ecd61d92923f1')
ck(read(P/mrel)==mraw,'published R/P Dense input equality');manifest=json.loads(mraw)
pub=js('results/formal_main_v2/preflight/heartbeat_20261020T1630/Long_collect_dense_input_publication.json','cd5845df1efd1f37a7df73b635e53c65a9975816a38a96fac3d8cf597f3d81bc')
ck(pub['canonical']['path']==mrel and pub['canonical']['sha256']==hashlib.sha256(mraw).hexdigest() and pub['status']=='published_input_only_no_submission_authorization','root publication identity')
old=js('results/formal_main_v2/execution/libero_10_development_first_pair_v1.json','d8c22787050b3223390627d74a804505c62f470b064bab112c2c230c4369051a')
expected=copy.deepcopy(old);expected['methods']=[x for x in old['methods'] if x['identity']['method_id']=='dense']
ck(manifest==expected,'Dense-only manifest exact projection of registered official Long identity')
ck(manifest['environment']==dict(action_chunk=8,environment_seed=0,max_steps=520,runtime_seed=17,wait_steps=10),'fixed Long environment')
ident=manifest['methods'][0]['identity'];ck(ident['visual_tokens']==512 and ident['model_revision']=='95220f9a3421a7ff12d4218e73d09ade830fa9a3' and not ident['future_head_deployed'],'official Long dense512 identity')
registration=js('configs/experiments/formal_main_v2.json','a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9')
panel=js(manifest['development_panel'],manifest['development_panel_sha256'])
ck(panel['split']=='development' and len(panel['states'])==100 and len(panel['task_catalog'])==10,'100 existing developer states only')
chosen=[min([x for x in panel['states'] if x['task_id']==i],key=lambda x:x['source_state_index']) for i in range(10)]
selection=js('.local/long_collection_prepare_0830/collection_selection_registration.json','f7e3a5b243e6bbc0bf9c35d6029e516328afd2b9f9460828c2a6fde800c382be')
ck(selection['selected_states']==chosen and selection['trajectory_count']==10 and selection['repeated_scientific_success_trials']==0 and not selection['success_based_replacement'],'candidate states independently derived by minimum source index')
inventory=js('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
ck(len(inventory['files'])==173,'173 source files')
for name,pin in inventory['files'].items():ck(read(name,pin)==read(S/name,pin),'R/S exact '+name)
sys.path.insert(0,str(S/'src'))
from cti_vla.evaluation import formal_profiling as f
ck(Path(f.__file__).resolve()==S/'src/cti_vla/evaluation/formal_profiling.py','actual frozen profiling module')
ck(f.validate_profile_manifest(manifest,registration,collect=True)==['dense'],'original manifest validation passes')
ck(f.fixed_profile_states(panel)==chosen,'original fixed_profile_states agrees with independent minimum')
for count in [3,4,5,519,520]:ck(f.selected_control_steps(count)==[0,(count-1)//2,count-1],'first-middle-last exact '+str(count))
for count in [True,False,-1,0,1,2,3.0]:
 try:f.selected_control_steps(count)
 except ValueError:ck(True,'reject insufficient/noninteger '+repr(count))
 else:ck(False,'reject insufficient/noninteger '+repr(count))
for label,bad in [('nondevelopment',dict(manifest,split='final')),('mixed methods',old)]:
 try:f.validate_profile_manifest(bad,registration,collect=True)
 except ValueError:ck(True,'reject '+label)
 else:ck(False,'reject '+label)
import numpy as np
class Fake:
 def __init__(self):self.obs={k:np.zeros((1,),dtype=np.float64) for k in f.RAW_KEYS};self.n=0
 def reset(self):return self.obs
 def set_init_state(self,x):return self.obs
 def step(self,a):
  self.n+=1
  for v in self.obs.values():v[:]=self.n
  return self.obs,0,False,{}
fake=Fake();capture=f.CaptureControlObservations(fake);capture.reset();capture.set_init_state([])
for i in range(13):capture.step(np.zeros(7))
ck(len(capture.captured)==3,'wait10 excluded; every subsequent actual control step captured')
ck(all(float(capture.captured[j][k][0])==10+j for j in range(3) for k in f.RAW_KEYS),'pre-action copies immune to simulator observation buffer mutation')
try:capture.reset()
except ValueError:ck(True,'collection cannot resample same proxy')
else:ck(False,'collection cannot resample same proxy')
script=read('scripts/profile_formal.py','4b8a7ac0b8be904f8f6b66d9fe7f6c3f7425056e013db903ac6b480191e2ebf6').decode()
for text in ['random.seed(17)','np.random.seed(17)','torch.manual_seed(17)','env.seed(0)','if result["status"] != "completed":','formal collection failed; retain it without substituting a task or state','new_success_trials=False, test_opened=False']:
 ck(text in script,'frozen collection rule '+text)
planner=read('scripts/ops/formal_downstream_supervisor.py','f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571').decode()
ck('if args.stage in ("final", "full", "components"):' in planner and 'raise ValueError("This stage requires the complete global freeze")' in planner,'full/components/final retain global gate')
ck('elif args.freeze_directory is not None:' in planner and 'Collection cannot substitute an existing observation panel' in planner,'collect does not accept unrelated freeze or panel substitution')
report=dict(schema='formal_main_v2',kind='independent_Long_collect_input_preflight',status='passed_inputs_only_plan_not_yet_accepted',checks=checks,checks_passed=len(checks),manifest={'path':mrel,'sha256':hashlib.sha256(mraw).hexdigest()},fixed_states=[{k:x[k] for k in ('task_id','trial_id','source_state_index','initial_state_sha256')} for x in chosen],expected_observations=30,expected_trajectories=10,new_scientific_success_trials=0,new_GPU_jobs=0,new_scheduler_queries=0,state_registry_Git_modified=False,source173_unchanged=True,final_states_read=False,production_chain_complete=False,evidence_sha256=evidence,audit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),utc=datetime.now(timezone.utc).isoformat())
with (O/'input_independent_review.json').open('x') as out:json.dump(report,out,ensure_ascii=False,sort_keys=True,indent=2);out.write('\n')
print(json.dumps(dict(status=report['status'],checks_passed=len(checks),report_sha256=hashlib.sha256((O/'input_independent_review.json').read_bytes()).hexdigest())))
