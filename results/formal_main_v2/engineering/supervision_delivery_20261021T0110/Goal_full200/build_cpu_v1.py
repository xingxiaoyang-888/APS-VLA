from pathlib import Path
import ast,json,hashlib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_full200_author_20261021T0110';K=D/'package'
hist=D/'before_cpu_hardening';hist.mkdir(exist_ok=False)
for n in ['observer_v3.py','paired_input_gate_v1.py','entry.py','consumer.py']:(hist/n).write_bytes((K/n).read_bytes())
p=K/'observer_v3.py';s=p.read_text()
old="                with self.journal.open('ab') as f: f.write(jbytes(failure)+b'\\n')"
assert s.count(old)==1
s=s.replace(old,"                require(len(jbytes(failure))<=16384, 'abort event exceeds storage ceiling; no truncation')\n"+old)
p.write_text(s)
h=hashlib.sha256(p.read_bytes()).hexdigest()
p=K/'paired_input_gate_v1.py';s=p.read_text().replace("OBSERVER_SHA='630ce0c6d6733bc77afe296b6d6aa663c6e208a1929d4378992cde90a85ec79c'","OBSERVER_SHA="+repr(h))
s=s.replace("self.last_gate_abort=None","self.last_gate_abort=None;self.gate_event_count=0")
s=s.replace("  if len(jbytes(event)) > 16384:", "  if self.gate_event_count>=68032:raise GateAbort('gate event count exceeds full200 bound')\n  if len(jbytes(event)) > 16384:")
old="  with self.gate_journal.open('ab') as f:f.write(jbytes(event)+b'\\n');f.flush()";assert s.count(old)==1
s=s.replace(old,old+"\n  self.gate_event_count+=1")
p.write_text(s)
p=K/'entry.py';s=p.read_text().replace('paired-input58 engineering attempt','full200 prospective attempt').replace('exact original58 diagnostic scope/resource configuration required','exact prospective200 scope/resource configuration required').replace('original_fixed58_identity_order=True,unique_development_states=29','original_fixed200_identity_order=True,unique_development_states=100')
p.write_text(s)
old=R/'.local/goal_cpu_gate_20261020T2054/cpu_check_v1.py';raw=old.read_bytes();assert hashlib.sha256(raw).hexdigest()=='8a6cc29c77d890285be69c752d714b2e40b7c8bbc07df2992d349daf1a530e0a'
s=raw.decode().replace("OUT=D/'CPU_attempt01'","OUT=D/'CPU_full200_v1'")
s=s.replace("load(D/'paired_input_gate_v1.py'","load(D/'package/paired_input_gate_v1.py'").replace("load(D/'ast_gate_v2.py'","load(D/'package/ast_gate_v2.py'")
s=s.replace('stop_after=58','stop_after=200').replace("'full58_29_exactpairs',n==58 and result['exact_paired_t0_checks']==29","'full200_100_exactpairs',n==200 and result['exact_paired_t0_checks']==100")
s=s.replace("'all174_queries_986_policy_steps',result['all_query_checks']==174 and result['executed_policy_steps_recorded']==986","'all600_queries_3400_policy_steps',result['all_query_checks']==600 and result['executed_policy_steps_recorded']==3400")
s=s.replace("self.n,dtype=np.uint8","self.n%255,dtype=np.uint8").replace("self.n+1,dtype=np.uint8","(self.n+1)%255,dtype=np.uint8")
insertion="""
  # Complete horizon failures are original completed outcomes, not errors.
  class HorizonEnv(Env):
   def step(self,action):
    ob,reward,done,info=super().step(action);return ob,reward,False,info
  htrace=[];hg=gate.PairedInputGate(OUT/'horizon_pair',allow_cpu_fixture=True);hl=runtime.TrialLedger(OUT/'horizon_pair.jsonl',run_signature='e'*64)
  with adapter.observer_scope(runtime,trials,hg,emit=emit):
   hn=trials.evaluate_formal_trials(panel,{m:Policy(htrace) for m in ('A256_seed17','B256_seed17')},hl,lambda state:(HorizonEnv(htrace),'fixed instruction'),reseed=reseed,stop_after=2)
  hr=[r for r in hl.events if r['event']=='result']
  ck('horizon_false_original_completed_retained',hn==2 and all(r['status']=='completed' and not r['success'] and r['control_steps']==300 and r['wait_steps']==10 and r['policy_calls']==38 for r in hr))
  ck('horizon_separate_wait_and_control_counts',hg.executed_policy_steps==600 and sum(hg.query_counts.values())==76 and len([x for x in htrace if x[0]=='step'])==620)
  excepts('partial2_cannot_finish_full200',hg.finish,(gate.GateAbort,))
  for name,action in [('oversize_event',lambda x:x._record({'value':'x'*16384})),
    ('gate_count',lambda x:(setattr(x,'gate_event_count',68032),x._record({'event':'x'}))),
    ('local_rng_blob',lambda x:x._blob(b'x'*65537,'.rng.json')),
    ('raw_blob',lambda x:x._blob(b'x'*196609,'.bin',observation=True)),
    ('capture_count',lambda x:(setattr(x,'event_count',21032),x.capture('sentinel')))]:
   q=gate.PairedInputGate(OUT/('bound_'+name),allow_cpu_fixture=True);excepts('refuse_'+name,lambda q=q,action=action:action(q),(gate.GateAbort,))
  for name,setup,call in [
    ('query_step300',lambda x:None,lambda x:x.capture('query_before',Env([]),Env([]).obs(),control_step=300,instruction='fixed instruction')),
    ('query_count38',lambda x:x.query_counts.update({prefix[0]['trial_id']:38}),lambda x:x.capture('query_before',Env([]),Env([]).obs(),control_step=296,instruction='fixed instruction')),
    ('total_query7600',lambda x:x.query_counts.update({'other':7600}),lambda x:x.capture('t0_query_before',Env([]),Env([]).obs(),control_step=0,instruction='fixed instruction')),
    ('control_total60000',lambda x:setattr(x,'executed_policy_steps',60000),lambda x:x.step_before(np.ones(7),0,0,0)),
    ('control_step300',lambda x:None,lambda x:x.step_before(np.ones(7),300,300,0))]:
   q=gate.PairedInputGate(OUT/('bound_'+name),allow_cpu_fixture=True);q.current={k:prefix[0][k] for k in gate.recorder.IDENTITY_KEYS};q.begun=1;q.query_counts[q.current['trial_id']]=0
   setup(q);excepts('refuse_'+name,lambda q=q,call=call:call(q),(gate.GateAbort,));ck('latched_'+name,q.dead)
  ck('ordinary_Exception_does_not_catch_gate',issubclass(gate.GateAbort,BaseException) and not issubclass(gate.GateAbort,Exception))
"""
needle=" ck('original_functions_restored'";assert s.count(needle)==1
s=s.replace(needle,insertion+needle)
p=D/'cpu_full200_v1.py';p.write_text(s)
for p in K.glob('*.py'):ast.parse(p.read_text())
ast.parse(s)
files={('scripts/ops/formal_goal_full200_gate_v1/'+p.name):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(K.iterdir()) if p.is_file() and p.name!='package_manifest.json'}
m={'schema':'formal_main_v2','kind':'goal_full200_gate_package','files':files,'old200_HOLD':True,'production_installed':False}
(K/'package_manifest.json').write_text(json.dumps(m,sort_keys=True,indent=2)+'\n')
print(json.dumps({'cpu_entry':str(p),'cpu_sha256':hashlib.sha256((D/'cpu_full200_v1.py').read_bytes()).hexdigest(),'package':hashlib.sha256((K/'package_manifest.json').read_bytes()).hexdigest()}))
