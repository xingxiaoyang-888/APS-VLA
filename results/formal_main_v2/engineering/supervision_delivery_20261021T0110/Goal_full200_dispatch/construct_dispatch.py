from pathlib import Path
import ast,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_full200_dispatch_20261021T0110'
P=R/'.local/object_single_error_gateway_20261021T0110/gateway.py'
raw=P.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='8471bba1419a9e0ca31f84e7e55ff232cd6fb0fcb4bcb89320140ea76292d727'
s=raw.decode();lines=s.splitlines();t=ast.parse(s)
nodes={n.name:n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def get(n):
 node=nodes[n];start=min([node.lineno]+[x.lineno for x in node.decorator_list]) if isinstance(node,ast.FunctionDef) else node.lineno
 return '\n'.join(lines[start-1:node.end_lineno])+'\n'
primitives=['require','canonical','sha','utc','safe','relative','raw','read','ref','read_ref','immutable','record','load','controller','parse_ack','fields','argv_of','option','expected_live','validate_live_identity','shared_writer_lock','probe_lease','actual_observation']
body='\n'.join(get(n) for n in primitives).replace("'_object_single_exact_controller'","'_goal_full200_exact_controller'").replace("'object_single_error_gateway'","'goal_full200_gateway'")
projection=get('normalized_projection').replace("'Object_single_error_durable_pending'","'Goal_full200_durable_pending'").replace('original_GPU_seconds=6713','original_GPU_seconds=1643').replace("'same pair or Object allocation occupied'","'same pair or Goal allocation occupied'")
native=get('Native').replace("self.audit=R/X/'gateway_attempt01'","self.audit=R/X/'dispatch_attempt01'")
old=""" def absent(self):
   require(not self.audit.exists(),'prior audit/pending/failed attempt exists; reconcile only')
   for root in (R,P):require(not (root/INV).exists(),'immutable invocation already exists')
   require(not (P/OUT).exists() and not (P/'results/formal_main_v2/object_single_error_invocations'/(STAGE+'.once_claim.json')).exists(),'runtime attempt already exists')
"""
# Methods keep exact original indentation (one class-level space).
start=native.index(' def absent(self):');end=native.index(' def revalidate(self):')
native=native[:start]+""" def absent(self):
  require(not self.audit.exists(),'prior dispatch audit or failed intent forbids retry')
  require(not (P/OUT).exists() and not (R/RAW).exists(),'prior attempt/raw claim forbids repeat')
  for root in (R,P):
   require(not (root/DISPATCH).exists() and not (root/RESERVATION).exists(),'old dispatch/reservation forbids repeat')
"""+native[end:]
native=native.replace("checked=authorization(self.bundle['authorization_ref']['sha256'])","checked=admission(self.bundle['admission_ref']['sha256'])")
start=native.index(' def publish_invocation(self):');end=native.index(' def submit(self,argv):')
native=native[:start]+""" def publish_reservation(self):
  value=reservation(self.bundle)
  for root in (R,P):record(root/RESERVATION,value)
 def dispatch_proof(self,jid,state,version):
  require(self.read_state()[1]==version,'CAS drift before held dispatch proof')
  measured=self.observe(state,allow_job=jid)
  reserved=reservation(self.bundle);rb=canonical(reserved)+b'\\n'
  for root in (R,P):require(raw(root/RESERVATION)==rb,'root slot reservation changed')
  d=dict(schema=EXPERIMENT,kind='root_goal_full200_held_dispatch',status='held_registered_before_release',
   stage_key=STAGE,job_id=jid,authorization=dict(path=str(P/AUTH),sha256=self.bundle['authorization_sha256']),
   request_token=self.bundle['token'],capacity_limit_all_GPU_modes=8,reserved_slots=1,maximum_attempts=1,
   new_submissions=1,no_requeue=True,scientific_release=False,resources=RUNTIME_RESOURCES,
   occupied_job_ids=measured['derived']['occupied'],state_after_sha256=version,
   reservation=dict(path=str(P/RESERVATION),sha256=sha(rb)),actual_sbatch_argv=sbatch_argv(self.bundle),
   original_sbatch_ACK_fact=X+'/dispatch_attempt01/sbatch_result.json',source_files=self.bundle['sources'])
  if (R/DISPATCH).exists():
   old=read(R/DISPATCH)
   for k in d:
    if k not in ('state_after_sha256','occupied_job_ids'):require(old.get(k)==d[k],'existing dispatch identity differs')
   require(jid in old['occupied_job_ids'] and len(old['occupied_job_ids'])<=8,'original dispatch capacity invalid')
   d=old
  e=load(P/PROD/'entry.py',self.bundle['runtime_package']['files'][PROD+'/entry.py'],'_goal_dispatch_held_validate')
  e.validate_dispatch(d,reserved,self.bundle['authorization'],self.bundle['authorization_sha256'],jid,sha(rb))
  for root in (R,P):record(root/DISPATCH,d,allow_identical=True)
  return measured
"""+native[end:]
tx=get('Transaction').replace("'Object_single_error_durable_pending'","'Goal_full200_durable_pending'").replace("audit_path=X+'/gateway_attempt01'","audit_path=X+'/dispatch_attempt01'").replace('io.publish_invocation()','io.publish_reservation()')
tx=tx.replace("  io.actual(jid,True)\n  attempt=","  io.dispatch_proof(jid,state,version)\n  io.actual(jid,True)\n  attempt=")
assert 'io.dispatch_proof' in tx
out=(D/'header.txt').read_text()+body+'\n'+(D/'custom.txt').read_text()+'\n'+projection+'\n'+native+'\n'+tx+'\n'+(D/'suffix.txt').read_text()
compile(out,str(D/'dispatch.py'),'exec')
p=D/'dispatch.py';assert not p.exists();p.write_text(out)
derivation=dict(source=str(P.relative_to(R)),source_sha256=hashlib.sha256(raw).hexdigest(),retained_low_level_functions={n:hashlib.sha256(get(n).encode()).hexdigest() for n in primitives},
 explicit_scope='separate exact Goal full200 only; Object authorization/repair/adoption never reused',
 core_derivation='Copy low-level validation/atomic transaction functions into independent exact Goal entry; specialize constants, full200 authorization, reservation/held-dispatch consumer, dual pending, Goal overlap and resources; no runtime monkeypatch or Object dispatch call',
 source173_changed=False,old_Object_package_changed=False,new_Slurm_submissions=0)
(D/'derivation.json').write_text(json.dumps(derivation,sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(path=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)))
