"""Exact before-query pairing and input-integrity engineering gate.

No GPU submission, scientific result admission, state or Git mutations. Uses an
explicitly derived private copy of the previously audited passive recorder.
The old Goal 200 and all new Goal scientific work remain HOLD.
"""
from pathlib import Path
from types import ModuleType
from collections import OrderedDict
import hashlib,json
import numpy as np
R=Path(__file__).resolve().parent
OBSERVER='observer_v3.py'
OBSERVER_SHA='630ce0c6d6733bc77afe296b6d6aa663c6e208a1929d4378992cde90a85ec79c'
PREFIX='specification.json'
PREFIX_SHA='ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad'
VERSION='goal-full200-before-policy-integrity-v1'
def sha(b):return hashlib.sha256(b).hexdigest()
def jbytes(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def load_recorder():
 p=R/OBSERVER;raw=p.read_bytes()
 if sha(raw)!=OBSERVER_SHA:raise ValueError('pinned passive recorder changed')
 text=raw.decode();changes=[
  ("VERSION = 'goal-full200-passive-observer-v1'", "VERSION = 'goal-full200-before-policy-all-query-recorder-v1'"),
  ('        if control_step is not None and control_step != 0:\n            return\n',''),
  ("                self.t0.setdefault(self.current['trial_id'], {})[phase] = event.get('observation_sha256')", "                self.t0.setdefault(self.current['trial_id'], {})[phase] = event.get('observation_sha256')\n            self.last_capture = event")]
 for old,new in changes:
  if text.count(old)!=1:raise ValueError('private recorder derivation not unique')
  text=text.replace(old,new,1)
 module=ModuleType('_goal_pair_gate_passive_candidate');module.__file__=str(p)
 exec(compile(text,str(p)+'::<candidate-all-query-copy>','exec'),module.__dict__)
 module.derivation={'source':OBSERVER,'source_sha256':OBSERVER_SHA,'derived_sha256':sha(text.encode()),'operational_changes':['recorder version','remove nonzero-step capture filter','expose completed immutable capture record'],'source_file_changed':False}
 return module
recorder=load_recorder();GateAbort=recorder.ObserverAbort

def fixed_prefix():
 p=R/PREFIX;raw=p.read_bytes()
 if sha(raw)!=PREFIX_SHA:raise ValueError('fixed original full200 identity table changed')
 return json.loads(raw)['rows']

def identity_signature(observation):
 return {'mapping_id':id(observation),'components':{k:{'id':id(observation[k]),'pointer':observation[k].__array_interface__['data'][0]} for k in recorder.OBS_KEYS}}

def content_signature(event,instruction):
 # Deliberately excludes pointer/stride/elapsed: cross-method inputs may be
 # separately allocated, but every component's dtype, shape and bytes must match.
 return {'components':{k:{a:event['observation_arrays'][k][a] for a in ('dtype','shape','bytes','sha256')} for k in recorder.OBS_KEYS},
         'instruction_utf8_sha256':sha(instruction.encode('utf-8'))}

class PairedInputGate(recorder.PassiveObserver):
 def __init__(self,output,*,allow_cpu_fixture=False,sink=None,raw_observation_root=None):
  super().__init__(output,fixed_prefix(),allow_cpu_fixture=allow_cpu_fixture,sink=sink)
  expected_raw=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/results/formal_main_v2/raw_runtime/goal_full200_20261021T0110/attempt01')
  self.raw_observation_root=Path(raw_observation_root) if raw_observation_root is not None else expected_raw
  if not allow_cpu_fixture:
   recorder.require(self.raw_observation_root==expected_raw and self.raw_observation_root.is_dir() and self.raw_observation_root.resolve()==expected_raw and not self.raw_observation_root.is_symlink(),'only exact root-approved claimed raw observation root permitted')
  else:
   if raw_observation_root is None:self.raw_observation_root=self.output/'CPU_raw_observations'
   self.raw_observation_root.mkdir(exist_ok=False)
  self.runtime_context='synthetic_CPU_fixture' if allow_cpu_fixture else 'real_environment_engineering'
  self.query_pending=None;self.query_counts={};self.state_baselines={};self.paired_keys=set()
  self.executed_policy_steps=0;self.gate_journal=self.output/'gate.jsonl';self.last_gate_abort=None
  self._record({'event':'paired_input_gate_open','version':VERSION,'source_derivation':recorder.derivation,'prefix_sha256':PREFIX_SHA,
     'scientific_trials_added':0,'original200_HOLD':True,'new_Goal_science_HOLD':True,'runtime_context':self.runtime_context,'CPU_fixture_enabled':self.allow_cpu_fixture,'GPU_authorization_owned_by_outer':True})
 def _record(self,event):
  if len(jbytes(event)) > 16384:raise GateAbort('gate event exceeds storage ceiling')
  with self.gate_journal.open('ab') as f:f.write(jbytes(event)+b'\n');f.flush()
 def _abort(self,reason,**detail):
  self.dead=True;event={'event':'paired_input_gate_abort','version':VERSION,'reason':reason,'ordinal':self.begun,
   'trial_identity':self.current,'finished_trials_retained':self.finished,'executed_policy_steps_retained':self.executed_policy_steps,
   'detail':detail,'automatic_retry':False,'scientific_trials_added':0,'original200_HOLD':True,'new_Goal_science_HOLD':True}
  self.last_gate_abort=event
  try:self._record(event)
  except BaseException as error:event['abort_record_failure']=type(error).__name__+': '+str(error)
  raise GateAbort(reason)
 def _call(self,fn):
  if self.dead:raise GateAbort('candidate gate dead; no restart/retry')
  try:return fn()
  except BaseException as error:
   if self.last_gate_abort is not None:raise
   self._abort('gate_or_capture_exception',error_type=type(error).__name__,error=str(error))
 def _need(self,yes,reason,**detail):
  if not yes:self._abort(reason,**detail)
 def trial_begin(self,identity,state):
  def go():
   self._need(self.query_pending is None,'query pending at next trial')
   super(PairedInputGate,self).trial_begin(identity,state)
   self.query_counts[self.current['trial_id']]=0
  return self._call(go)
 def capture(self,phase,env=None,observation=None,*,control_step=None,wait_steps=None,chunk=None,instruction=None):
  def go():
   is_query=phase in ('t0_query_before','t0_query_after','query_before','query_after')
   if is_query:
    self._need(type(control_step) is int and 0<=control_step<300 and control_step%8==0,'query control_step changed or exceeds300')
    self._need(sum(self.query_counts.values())<7600 or phase.endswith('_after'),'query total exceeds7600')
    self._need(self.query_counts.get(self.current['trial_id'],0)<38,'trial query count exceeds38')
    self._need(type(instruction) is str and self.current is not None,'query instruction/identity missing')
    self._need(phase.startswith('t0_')==(control_step==0),'t0 marker control_step mismatch')
   if observation is not None and not self.allow_cpu_fixture:
    expected={'agentview_image':('uint8',(256,256,3)),'robot0_eye_in_hand_image':('uint8',(256,256,3)),'robot0_eef_pos':('float64',(3,)),'robot0_eef_quat':('float64',(4,)),'robot0_gripper_qpos':('float64',(2,))}
    self._need(type(observation) in (dict,OrderedDict),'exact raw mapping required')
    self._need(all(k in observation and type(observation[k]) is np.ndarray and (str(observation[k].dtype),observation[k].shape)==v for k,v in expected.items()),'raw observation schema exceeds fixed storage/scientific shape')
   super(PairedInputGate,self).capture(phase,env,observation,control_step=control_step,wait_steps=wait_steps,chunk=chunk)
   if not is_query:return
   event=self.last_capture
   self._need(event['phase']==phase and event['control_step']==control_step,'capture not durably recorded')
   content=content_signature(event,instruction)
   obj_guard=recorder.object_guard(observation)
   if phase.endswith('_before'):
    self._need(self.query_pending is None,'overlapping policy query')
    self._need(control_step==8*self.query_counts[self.current['trial_id']],'missing/reordered query')
    if control_step==0:
     key=tuple(self.current[k] for k in ('state_trial_id','task_id','task_name','source_state_index','initial_state_sha256'))
     if self.current['method']=='A256_seed17':
      self._need(key not in self.state_baselines,'duplicate first method/state baseline')
      self.state_baselines[key]={'content':content,'ordinal':self.begun,'trial_id':self.current['trial_id']}
      pairing='baseline_recorded_before_first_policy'
     else:
      self._need(self.current['method']=='B256_seed17' and key in self.state_baselines and key not in self.paired_keys,'missing/duplicate method-independent baseline')
      baseline=self.state_baselines[key]
      self._need(content==baseline['content'],'paired_t0_input_mismatch_before_B_policy',baseline=baseline,actual_content=content,actual_capture_event_index=event['event_index'])
      self.paired_keys.add(key);pairing='exact_before_policy_pair_passed'
     self._record({'event':'t0_pair_gate','ordinal':self.begun,'trial_identity':self.current,'pairing':pairing,
       'content':content,'instruction_utf8_hex':instruction.encode().hex(),'capture_event_index':event['event_index'],'scientific_trials_added':0})
    self.query_pending={'ordinal':self.begun,'trial_id':self.current['trial_id'],'step':control_step,'content':content,'object_guard':obj_guard,'identity_signature':identity_signature(observation),'instruction':instruction}
   else:
    pending=self.query_pending
    self._need(pending is not None and pending['trial_id']==self.current['trial_id'] and pending['step']==control_step,'postquery has no exact prequery')
    self._need(content==pending['content'] and obj_guard==pending['object_guard'] and instruction==pending['instruction'],
       'policy_changed_input_identity_or_bytes',pre_content=pending['content'],post_content=content,control_step=control_step)
    self._need(chunk is not None,'postquery lacks original chunk')
    # Preserve returned numeric actions for partial-attempt provenance; never alter them.
    outputs={}
    for name in ('normalized_actions','environment_actions'):
     value=getattr(chunk,name);meta,raw=recorder.array_copy(value)
     self._need(value.shape==(8,7) and np.isfinite(value).all(),'returned chunk invalid')
     outputs[name]={**meta,'bytes_hex':raw.hex()}
    self._record({'event':'query_integrity_passed','ordinal':self.begun,'trial_identity':self.current,
      'control_step':control_step,'content':content,'instruction_utf8_hex':instruction.encode().hex(),'input_identity_before':pending['identity_signature'],'input_identity_after':identity_signature(observation),'returned_actions':outputs,'capture_event_index':event['event_index'],
      'scientific_trials_added':0})
    self.query_pending=None;self.query_counts[self.current['trial_id']]+=1
  return self._call(go)
 def step_before(self,action,control_step,completed_steps,policy_calls):
  def go():
   self._need(self.current is not None and self.query_pending is None,'step before accepted query missing')
   self._need(type(control_step) is int and 0<=control_step<300 and completed_steps==control_step,'per-trial control bound/order differs')
   self._need(self.executed_policy_steps<60000,'total control bound exceeds60000')
   self._need(policy_calls==self.query_counts[self.current['trial_id']],'step has unaccepted query')
  return self._call(go)
 def step_after(self,action,control_step,completed_steps,policy_calls):
  def go():
   self._need(self.current is not None and self.query_pending is None,'step outside accepted query/trial')
   self._need(type(control_step) is int and completed_steps==control_step+1 and policy_calls==self.query_counts[self.current['trial_id']],'executed step accounting differs')
   before=recorder.object_guard(action);rng_before=recorder.global_rng();meta,raw=recorder.array_copy(action)
   self._need(action.shape==(7,) and np.isfinite(action).all(),'executed action shape/value differs')
   self._record({'event':'policy_step_executed','ordinal':self.begun,'trial_identity':self.current,'control_step':control_step,
      'action':{**meta,'bytes_hex':raw.hex()},'scientific_trials_added':0})
   self._need(recorder.object_guard(action)==before and recorder.global_rng()==rng_before,'step observer modified action/RNG')
   self.executed_policy_steps+=1
  return self._call(go)
 def trial_end(self,row,ledger):
  def go():
   self._need(self.query_pending is None,'trial ends with unfinished query')
   self._need(row.get('policy_calls')==self.query_counts.get(self.current['trial_id']),'original query count mismatch')
   super(PairedInputGate,self).trial_end(row,ledger)
  return self._call(go)
 def finish(self):
  def go():
   self._need(len(self.state_baselines)==len(self.paired_keys)==100 and self.query_pending is None,'incomplete exact pairs')
   self._need(sum(self.query_counts.values())<=7600 and self.executed_policy_steps<=60000,'full200 bounds exceeded')
   old=super(PairedInputGate,self).finish()
   out={**old,'version':VERSION,'status':'full200_inputs_checked_pending_terminal_acceptance','runtime_context':self.runtime_context,
    'exact_paired_t0_checks':len(self.paired_keys),'all_query_checks':sum(self.query_counts.values()),
    'executed_policy_steps_recorded':self.executed_policy_steps,'old_cause_identified':False,'old_failure_repaired':False,
    'scientific_trials_added':0,'original200_HOLD':True,'new_Goal_science_HOLD':True,'final_release':False}
   self._record({'event':'paired_input_gate_finished',**out});return out
  return self._call(go)
