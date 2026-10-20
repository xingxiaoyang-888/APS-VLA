"""CPU-only synthetic evidence, no real model, GPU, or sealed state loader."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,random,signal,sys,time,types
import numpy as np
D=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('probe_under_cpu_test',D/'probe.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def test(name,fn):
    fn();checks.append(name)
def req(condition):assert condition
c=m.read(D/'config.json')
test('fixed configuration',lambda:req(m.validate_config(c)))
for key,value in [('resets',13),('wait_steps',9),('source_state_index',41),('task_id',3),('suite','libero_10'),('policy_actions_executed',1),('maximum_wall_seconds',1801),('order',list(reversed(c['order']))[:-1]),('final_evaluation_enabled',True)]:
    def reject(key=key,value=value):
        bad=copy.deepcopy(c);bad[key]=value
        try:m.validate_config(bad)
        except ValueError:return
        raise AssertionError('scope substitution accepted '+key)
    test('reject scope substitution '+key,reject)
test('exact original loading prefix',lambda:req(m.validate_prefix(m.S/'scripts/eval_formal_selector_libero.py',D/'original_loading_prefix.py',c['prefix_proof'])['original_prefix_ast_unchanged']))
# Synthetic arrays resemble dimensions but never use a real observation.
def obs():return dict(agentview_image=np.zeros((4,4,3),dtype=np.uint8),robot0_eye_in_hand_image=np.ones((4,4,3),dtype=np.uint8),robot0_eef_pos=np.array([.1,.2,.3]),robot0_eef_quat=np.array([0.,0.,0.,1.]),robot0_gripper_qpos=np.array([.02,-.02]))
a=obs();b=m.arrays(a);a['robot0_eef_quat'][3]=.9
test('snapshot deep copies before policy mutation',lambda:req(b['robot0_eef_quat'][3]==1.))
test('five-array aggregate matches original recipe',lambda:req(m.aggregate(b)==hashlib.sha256(b''.join(n.encode()+str(v.dtype).encode()+str(v.shape).encode()+np.ascontiguousarray(v).tobytes() for n,v in b.items())).hexdigest()))
d=m.differences(b,m.arrays(a))
test('mutation max delta is visible',lambda:req(not d['robot0_eef_quat']['byte_equal'] and abs(d['robot0_eef_quat']['max_abs_difference']-.1)<1e-12))
class Sim:
    def __init__(self):self.data=types.SimpleNamespace(qpos=np.zeros(3),qvel=np.zeros(3))
    def get_state(self):return np.r_[self.data.qpos,self.data.qvel]
class Env:
    def __init__(self):self.sim=Sim();self.steps=[];self.reset_calls=0;self.init_calls=0;self.closed=False;self.ob=obs()
    def reset(self):self.reset_calls+=1;return self.ob
    def set_init_state(self,value):self.init_calls+=1;return self.ob
    def step(self,action):
        assert action==list(m.DUMMY);self.steps.append(action);self.sim.data.qpos+=.001;return self.ob,0.,False,{}
    def close(self):self.closed=True
class Policy:
    def __init__(self,mutation=False,fail=False):self.calls=0;self.resets=0;self.mutation=mutation;self.fail=fail
    def reset(self):self.resets+=1
    def __call__(self,ob,instruction):
        self.calls+=1
        if self.fail:raise RuntimeError('synthetic intentional policy failure')
        if self.mutation:ob['robot0_eef_quat'][0]+=.2
        return dict(synthetic=True)
def run_case(name,mutation=False,fail=False):
    out=D/'cpu_fixture'/name;out.mkdir(parents=True,exist_ok=False);rec=m.Recorder(out);envs=[]
    policies={k:Policy(mutation=mutation and k==m.METHODS[1],fail=fail) for k in m.METHODS}
    def factory(state):
        env=Env();envs.append(env);return env,'synthetic',dict(synthetic=True)
    def reseed():random.seed(17);np.random.seed(17)
    result=None;error=None
    try:result=m.run_fixed_queries(state={'initial_state':[0.]},policies=policies,factory=factory,reseed=reseed,recorder=rec,check_chunk=lambda mid,ch:dict(synthetic=True),absolute_deadline=time.monotonic()+30.)
    except RuntimeError as e:error=str(e)
    return result,error,envs,policies,rec
result,error,envs,policies,rec=run_case('constant')
test('exact 12 resets with fixed ABBA x3 order',lambda:req(error is None and len(envs)==12 and all(e.reset_calls==e.init_calls==1 for e in envs) and [r['method_id'] for r in result['query_records']]==list(m.ORDER)))
test('120 dummy actions only; no predicted action stepping',lambda:req(sum(len(e.steps) for e in envs)==120 and all(a==list(m.DUMMY) for e in envs for a in e.steps)))
test('six A and six B queries and resets',lambda:req(all(p.calls==p.resets==6 for p in policies.values())))
test('all 12 fresh environments closed',lambda:req(all(e.closed for e in envs)))
test('24 observation phases per query with five arrays and sim snapshots',lambda:req(rec.arrays_written==288 and len(list((rec.out/'arrays').glob('*.npz')))==288))
test('all-match synthetic still cannot release scientific trials',lambda:req(result['all_current_probe_pairs_equal'] and result['scientific_gate']=='HOLD' and result['scientific_trials_accepted']==0 and not result['retry_authorized']))
result,error,envs,policies,rec=run_case('mutation',mutation=True)
test('input mutation detected without result-conditioned order changes',lambda:req(len(result['query_records'])==12 and not result['all_current_probe_pairs_equal'] and sum(not r['input_unchanged'] for r in result['query_records'])==6))
test('pair mismatch retains HOLD and all raw observations',lambda:req(result['scientific_gate']=='HOLD' and len(result['pair_diagnostics'])==6 and rec.arrays_written==288))
result,error,envs,policies,rec=run_case('failure',fail=True)
test('policy exception stops immediately and preserves evidence',lambda:req(result is None and error=='synthetic intentional policy failure' and len(envs)==1 and len(envs[0].steps)==10 and envs[0].closed and rec.arrays_written==23))
def deadline_check():
    with m.deadline(5.):
        before=signal.getitimer(signal.ITIMER_REAL)[0]
        with m.deadline(1.):assert signal.getitimer(signal.ITIMER_REAL)[0]<=1
        after=signal.getitimer(signal.ITIMER_REAL)[0];assert 0<after<=before
    assert signal.getitimer(signal.ITIMER_REAL)[0]==0
test('nested deadline restores outer bound',deadline_check)
test('candidate no GPU imports during synthetic tests',lambda:req('torch' not in sys.modules))
# Fail closed before a run for a missing/unsigned root authorization.
try:m.validate_authorization({},c,D/'config.json',D/'probe.py')
except (KeyError,ValueError):checks.append('unsigned root authorization rejected')
else:raise AssertionError('unsigned authorization accepted')
report=dict(status='passed',kind='CPU_synthetic_only',checks=checks,count=len(checks),GPU_runs=0,actual_GPU_evidence=False,Slurm_submissions=0,state_mutations=0,Git_mutations=0,sealed_values_read=False,probe_sha256=m.sha(D/'probe.py'),config_sha256=m.sha(D/'config.json'))
m.publish(D/'cpu_tests.json',report);print(json.dumps(report,indent=2))
