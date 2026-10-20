"""Independent follow-up: distinguish archive interruption from a proven query timeout."""
from pathlib import Path
import hashlib,importlib.util,json,os,random,sys,time,types,traceback
import numpy as np
D=Path(__file__).resolve().parent;C=D.parent/'goal_t0_probe_candidate_20261020T1418'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def put(p,v):
 assert D in Path(p).resolve().parents
 with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
def ref(p):return dict(path=str(p),sha256=sha(p),bytes=Path(p).stat().st_size)
assert sha(C/'probe.py')=='4d0eec76dddf7574521231911c29e0df8dbbeb372910d615c00914451a1cb92c'
sp=importlib.util.spec_from_file_location('independent_followup_probe',C/'probe.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
prior=read(D/'independent_review.json');prev=read(D/'independent_deadline/summary.json')
checks=[]
def check(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
try:
 check(prev['error']['type']=='TimeoutError' and prev['policy_calls']==0 and prev['closed']==1,'prior 80ms deadline was correctly partial-archive interruption, not policy query')
 warning='Exception ignored in: <function ZipFile.__del__ at 0x1536e76d3240>\nTraceback (most recent call last):\n  File "/share/apps/anaconda3/lib/python3.11/zipfile.py", line 1874, in __del__\n    self.close()\n  File "/share/apps/anaconda3/lib/python3.11/zipfile.py", line 1891, in close\n    self.fp.seek(self.start_dir)\nValueError: seek of closed file\n'
 put(D/'archive_interruption_tool_output_record.json',dict(kind='verbatim_warning_transcribed_from_tool_output',source='audit_v1 transport terminal response',warning=warning,original_report=ref(D/'independent_review.json'),fixture=ref(D/'independent_deadline/summary.json'),interpretation='Intentional deadline interrupted archive writing. Incomplete archives are retained engineering failure artifacts, not usable complete observations. Original candidate remained unmodified.'))
 def obs():return dict(agentview_image=np.zeros((2,2,3),dtype=np.uint8),robot0_eye_in_hand_image=np.ones((2,2,3),dtype=np.uint8),robot0_eef_pos=np.array([.1,.2,.3]),robot0_eef_quat=np.array([0.,0.,0.,1.]),robot0_gripper_qpos=np.array([.02,-.02]))
 class Sim:
  def __init__(self):self.data=types.SimpleNamespace(qpos=np.zeros(3),qvel=np.zeros(3));self.gets=0
  def get_state(self):self.gets+=1;return np.r_[self.data.qpos,self.data.qvel]
 class Env:
  def __init__(self):self.sim=Sim();self.ob=obs();self.steps=[];self.resets=0;self.inits=0;self.closed=False
  def reset(self):self.resets+=1;return self.ob
  def set_init_state(self,st):self.inits+=1;return self.ob
  def step(self,a):assert a==list(m.DUMMY);self.steps.append(a);return self.ob,0.,False,{}
  def close(self):self.closed=True
 class Policy:
  def __init__(self):self.calls=0
  def reset(self):pass
  def __call__(self,ob,text):self.calls+=1;time.sleep(6.);return {'never_executed':True}
 out=D/'independent_query_deadline_v2';out.mkdir();rec=m.Recorder(out);envs=[];pols={mid:Policy() for mid in m.METHODS}
 def factory(st):e=Env();envs.append(e);return e,'synthetic only',{'synthetic':True}
 def reseed():random.seed(17);np.random.seed(17)
 start=time.monotonic();error=None
 try:m.run_fixed_queries(state={'initial_state':[0.]},policies=pols,factory=factory,reseed=reseed,recorder=rec,check_chunk=lambda *a:{},absolute_deadline=time.monotonic()+4.)
 except TimeoutError as e:error=str(e)
 elapsed=time.monotonic()-start
 check(error is not None and sum(p.calls for p in pols.values())==1,'timeout occurs after entering exactly one policy query')
 check(len(envs)==1 and len(envs[0].steps)==10 and envs[0].closed,'query timeout closes first env; zero additional environments or policy actions')
 check(rec.arrays_written==23,'query timeout retains 23 complete prequery phases')
 check(3.5<=elapsed<5.,'actual synthetic query deadline bounded near 4 seconds')
 check(len([e for e in rec.events if e['event']=='rng_state' and e.get('phase')=='prequery'])==1,'prequery RNG event confirms query phase reached')
 for e in rec.events:
  if e['event']=='observation':
   with np.load(e['raw_archive']['path'],allow_pickle=False) as z:assert all(k in z for k in m.FIELDS)
 check(True,'all query-timeout archives remain readable and complete')
 put(out/'summary.json',dict(status='passed',synthetic=True,elapsed_seconds=elapsed,error=error,policy_calls=1,external_resets=1,dummy_actions=10,policy_actions=0,closed=True,archives=23))
 # Observe/capture instrumentation alone does not mutate fake state/arrays/global RNG.
 out=D/'independent_observe_nonmutation_v2';out.mkdir();rec=m.Recorder(out);env=Env()
 before={k:np.array(v,copy=True) for k,v in env.ob.items()};qpos=env.sim.data.qpos.copy();qvel=env.sim.data.qvel.copy();rng=m.capture_rng()
 rec.observe(env.ob,env,'synthetic','instrumentation_only');after_rng=m.capture_rng()
 check(all(np.array_equal(v,env.ob[k]) for k,v in before.items()),'recorder does not mutate observation arrays')
 check(np.array_equal(qpos,env.sim.data.qpos) and np.array_equal(qvel,env.sim.data.qvel),'recorder does not mutate simulator state in CPU fake')
 check(rng==after_rng,'recorder does not advance Python/NumPy RNG')
 check(not env.steps and env.resets==0 and env.inits==0,'recorder adds no reset/set_init/step on fake')
 check('torch' not in sys.modules,'follow-up uses no Torch/GPU')
 report=dict(prior)
 report['supersedes']=ref(D/'independent_review.json')
 report['checks']=[x if x!='Python query deadline stops bounded fake query with cleanup' else '80ms total deadline interrupted archive, preserved partial artifacts, closed environment' for x in prior['checks']]+checks
 report['check_count']=len(report['checks'])
 report['followup']=dict(script=ref(Path(__file__)),archive_interruption=ref(D/'archive_interruption_tool_output_record.json'),query_deadline=ref(D/'independent_query_deadline_v2/summary.json'))
 report['limitations']=prior['limitations']+['A total deadline can interrupt an NPZ archive write and emit ZipFile cleanup warnings. Such partial archives remain failure evidence and must not be treated as complete phase samples. Root must preserve failure/timeout outputs and not rerun automatically.']
 report['root_required_conditions']=prior['root_required_conditions']+['Any incomplete NPZ phase or failed completion is engineering failure/HOLD, not complete diagnosis']
 put(D/'independent_review_v2.json',report)
 print(json.dumps(dict(status='passed',review=ref(D/'independent_review_v2.json'),additional_checks=checks),ensure_ascii=False))
except BaseException as e:
 put(D/'audit_followup_v2_failure.json',dict(status='failed',error=str(e),type=type(e).__name__,traceback=traceback.format_exc(),checks=checks));raise
