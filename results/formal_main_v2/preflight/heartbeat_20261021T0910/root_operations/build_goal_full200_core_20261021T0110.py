from pathlib import Path
import ast,hashlib,json,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_full200_author_20261021T0110';D.mkdir(exist_ok=False);PK=D/'package';PK.mkdir()
OLD=R/'scripts/ops/formal_goal_paired_input_gate_v1'
H=lambda b:hashlib.sha256(b).hexdigest()
pins={'observer_v3.py':'7a33c4ec531e0524a5e30b51e18205dc7d354868afa6190e3f39dcf14b283241','paired_input_gate_v1.py':'389cab5bb9e8464fa3666fac23db34be9e500a8ea92f7cea12223406796797d0','ast_observer_v2.py':'e88222ea96c290019b2ec838ff68fe25a9f94d115ae996d92735e18e4cf0800e','ast_gate_v2.py':'820c1dd19eff95ea17233101f75f72ed2e3a2a1dc1f2b6941c68318c31e1fb07','entry.py':'1e8caecfda12f1f0a1d55a5652e9c300d25dff5fb0cf071cf4555a68b8605977'}
derivations=[]
def read(n):
 b=(OLD/n).read_bytes();assert H(b)==pins[n];return b.decode()
def put(n,t):
 b=t.encode() if isinstance(t,str) else t
 if n.endswith('.py'):ast.parse(b)
 with (PK/n).open('xb') as f:f.write(b)
 return H(b)
def replace(t,old,new,count=1):
 assert t.count(old)==count,(old,t.count(old),count)
 return t.replace(old,new)
specname='results/formal_main_v2/engineering/supervision_delivery_20261020T2358/Goal_bounded_diagnostic/prospective_full200_specification.json'
raw=(R/specname).read_bytes();assert H(raw)=='ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad'
put('specification.json',raw)
observer=read('observer_v3.py')
observer=replace(observer,"VERSION = 'goal-prefix58-passive-observer-v2'","VERSION = 'goal-full200-passive-observer-v1'")
observer=observer.replace('len(self.prefix) == 58','len(self.prefix) == 200').replace('len({r[\'trial_id\'] for r in self.prefix}) == 58','len({r[\'trial_id\'] for r in self.prefix}) == 200')
observer=observer.replace('exact original 58 unique trial identities required','exact original 200 unique trial identities required').replace('self.begun < 58','self.begun < 200').replace('trial 59 forbidden','trial 201 forbidden').replace('self.begun == self.finished == 58','self.begun == self.finished == 200').replace('returned_58_engineering_trials_only','returned_200_prospective_trials_pending_terminal_acceptance').replace('original_prefix_trials=58, unique_development_states=29','original_prefix_trials=200, unique_development_states=100')
observer=replace(observer,"def _blob(self, raw, suffix):\n        key = sha(raw);","def _blob(self, raw, suffix):\n        require(len(raw) <= 196608, 'blob exceeds admitted component/RNG ceiling')\n        key = sha(raw);")
observer=replace(observer,"def _append(self, event):\n        if self.sink","def _append(self, event):\n        require(len(jbytes(event)) <= 65536, 'observer event exceeds storage ceiling')\n        if self.sink")
observer=replace(observer,"            rng_before = global_rng()","            require(self.event_count < 21032, 'observer event count exceeds full200 bound')\n            rng_before = global_rng()")
observer=replace(observer,"            # Do not call the test sink twice.","            require(len(jbytes(event)) <= 65536, 'observer event exceeds storage ceiling')\n            # Do not call the test sink twice.")
osh=put('observer_v3.py',observer)
gate=read('paired_input_gate_v1.py')
gate=gate.replace(pins['observer_v3.py'],osh)
gate=gate.replace("PREFIX='prefix58.json'","PREFIX='specification.json'").replace("PREFIX_SHA='1e786af6b4aafb52dba32bce1494c5e4dd4ef05c41f10cb3b9a77342c2cbcb28'","PREFIX_SHA='ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad'")
gate=gate.replace("VERSION='goal-before-policy-paired-input-gate-engineering-v1'","VERSION='goal-full200-before-policy-integrity-v1'")
gate=gate.replace("VERSION = 'goal-prefix58-passive-observer-v2'","VERSION = 'goal-full200-passive-observer-v1'").replace('goal-before-policy-all-query-recorder-candidate-v1','goal-full200-before-policy-all-query-recorder-v1').replace('fixed original 58 identity prefix changed','fixed original full200 identity table changed')
gate=gate.replace("==29","==100").replace("prefix_inputs_checked_engineering_only","full200_inputs_checked_pending_terminal_acceptance")
gate=replace(gate,"  with self.gate_journal.open('ab') as f:f.write(jbytes(event)+b'\\n');f.flush()","  if len(jbytes(event)) > 65536:raise GateAbort('gate event exceeds storage ceiling')\n  with self.gate_journal.open('ab') as f:f.write(jbytes(event)+b'\\n');f.flush()")
gate=replace(gate,"    self._need(type(control_step) is int and control_step>=0 and control_step%8==0,'query control_step changed')","    self._need(type(control_step) is int and 0<=control_step<300 and control_step%8==0,'query control_step changed or exceeds300')\n    self._need(sum(self.query_counts.values())<7600 or phase.endswith('_after'),'query total exceeds7600')\n    self._need(self.query_counts.get(self.current['trial_id'],0)<38,'trial query count exceeds38')")
gate=replace(gate," def step_after(self,action,control_step,completed_steps,policy_calls):"," def step_before(self,action,control_step,completed_steps,policy_calls):\n  def go():\n   self._need(self.current is not None and self.query_pending is None,'step before accepted query missing')\n   self._need(type(control_step) is int and 0<=control_step<300 and completed_steps==control_step,'per-trial control bound/order differs')\n   self._need(self.executed_policy_steps<60000,'total control bound exceeds60000')\n   self._need(policy_calls==self.query_counts[self.current['trial_id']],'step has unaccepted query')\n  return self._call(go)\n def step_after(self,action,control_step,completed_steps,policy_calls):")
gate=replace(gate,"   self._need(len(self.state_baselines)==len(self.paired_keys)==100 and self.query_pending is None,'incomplete exact pairs')","   self._need(len(self.state_baselines)==len(self.paired_keys)==100 and self.query_pending is None,'incomplete exact pairs')\n   self._need(sum(self.query_counts.values())<=7600 and self.executed_policy_steps<=60000,'full200 bounds exceeded')")
gsh=put('paired_input_gate_v1.py',gate)
put('ast_observer_v2.py',read('ast_observer_v2.py'))
agt=read('ast_gate_v2.py')
agt=replace(agt," base.surround(derived,'result[\"control_steps\"] += 1'"," base.surround(derived,'observation, _, done, _ = env.step(action.tolist())',before=[base.NAME+'.step_before(action, control_step, result[\"control_steps\"], result[\"policy_calls\"])'])\n base.surround(derived,'result[\"control_steps\"] += 1'")
agt=replace(agt,"call.func.attr=='step_after'","call.func.attr in ('step_after','step_before')")
# Source-only derive the new exact normalized AST, then freeze its hash.
tmp={}
exec(compile(agt,str(PK/'ast_gate_v2.py'),'exec'),dict(__file__=str(PK/'ast_gate_v2.py')),tmp) if False else None
base_ns={'__file__':str(PK/'ast_observer_v2.py')}
exec(compile((PK/'ast_observer_v2.py').read_bytes(),str(PK/'ast_observer_v2.py'),'exec'),base_ns)
from types import ModuleType
bm=ModuleType('_author_projection');bm.__dict__.update(base_ns)
tree=ast.parse(agt);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='derive_run')
captured={}
def proof(a,b):captured['a']=a;captured['b']=b;return {}
bm.assert_projection=proof
env={'base':bm,'ast':ast,'copy':__import__('copy'),'sha':H}
exec(compile(ast.Module(body=[node],type_ignores=[]),str(PK/'ast_gate_v2.py'),'exec'),env)
env['derive_run']((R/'src/cti_vla/evaluation/libero_runtime.py').read_bytes())
newast=H(bm.text(captured['b']).encode())
agt=replace(agt,'2dc5763fb80b6eaa00ba24c8f0b529a046f6c0d2ef8a880059a5edcb8c1e6725',newast)
put('ast_gate_v2.py',agt)
derivations=[{'file':n,'original':str((OLD/n).relative_to(R)),'original_sha256':pins[n],'new_sha256':H((PK/n).read_bytes())} for n in ('observer_v3.py','paired_input_gate_v1.py','ast_observer_v2.py','ast_gate_v2.py')]
(D/'source_derivation_core.json').write_text(json.dumps({'rows':derivations,'full200_derived_run_AST_SHA':newast,'original_frozen_files_modified':False,'passive_gate_only_no_scientific_loop_branch_change':True},sort_keys=True,indent=2)+'\n')
print(json.dumps({'directory':str(D.relative_to(R)),'full200_AST':newast,'files':{p.name:H(p.read_bytes()) for p in PK.iterdir()}}))
