from pathlib import Path
from contextlib import contextmanager
import ast,copy,fcntl,hashlib,json,os,sys,difflib
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/k64_spatial_reconcile_independent_20261020T1949/Object3053894';SOURCE=R/'.local/reconcile_k64_object_3053894_20261020T1949.py';PIN='313d9db3fbf3750012695df185c34279b04aa768b7c9c6b9daa5fe3bd8acd2ef';OLD=R/'.local/reconcile_k64_spatial_3053875_20261020T1949.py'
checks=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(n,v):assert v,n;checks.append(n)
def ref(p):return {'path':str(p.relative_to(R)),'sha256':h(p)}
def save(n,x):
 p=D/n
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2);f.write('\n')
 return ref(p)
ck('current_exact_source',h(SOURCE)==PIN);ck('previous_exact_audited_source',h(OLD)=='ffe310f91a936291ac766c190956cb048feeea7fc4d034726a73618861728368')
old=OLD.read_text();text=SOURCE.read_text();mapped=old
mapping={'79d22ee8370f95551c259894ad7deccffa7bebc4a1ffecab1c9d567d393cf855':'36b24fd96344e48b5241a5253b807e4f8f6e65a997713c796d8f471f8c2f2b74','3053875':'3053894','spatial64seed23':'object64seed23','13ceb3c9789d93a42c63e7fdc10757744438b7cd51301e47f4527718da531c9a':'692d9d53a9707671526eab64546e41c87fa12d6716c0762212e04e448079fcf9','82f9b835caa6e85f7ff23ce0607f1dcf3ec9b4584299e1c8c6ffcccbd9bd65c6':'2f1e28cc16d1d23bade3626377a267cfcab0fb782b2503826aa1022f13b20627',"==218":"==225","==551":"==530",'Spatial64s23':'Object64s23','/Spatial/':'/Object/','31ef1a9894d37d9a07d99351fc07121d0397fedcc6d7e119ae3df8f66bfcb8de':'714a5e5468e3366b548617b7fb8f58638830b25aff75062f16c1f560994b9719','libero_spatial':'libero_object'}
for a,b in mapping.items():mapped=mapped.replace(a,b)
ck('only_exact_identity_and_evidence_count_substitutions',mapped==text)
with (D/'root_source_exact.py').open('x') as f:f.write(text)
with (D/'exact_identity_diff.patch').open('x') as f:f.write(''.join(difflib.unified_diff(old.splitlines(True),text.splitlines(True))))
save('exact_substitutions.json',mapping)
tree=ast.parse(text);blocks=[x for x in tree.body if isinstance(x,ast.With)];ck('single_transaction',len(blocks)==1);block=blocks[0]
ck('shared_writer_EX_lock_retained',ast.unparse(block.items[0].context_expr)=="c.exclusive_lock(R / 'results/experiment_supervisor/.writer.lock')")
ck('no_submit_commands',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('run','submit','publish') for n in ast.walk(tree)))
ck('one_CAS',sum(isinstance(n,ast.Call) and ast.unparse(n.func)=='c.atomic_json' for n in ast.walk(tree))==1)
end=next(i for i,n in enumerate(block.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='scheduler' for t in n.targets))
ck('stops_before_scheduler_or_mutation',not any(isinstance(n,ast.Call) and ast.unparse(n.func) in ('g.record','c.atomic_json','scheduler.observe') for st in block.body[:end] for n in ast.walk(st)))
@contextmanager
def readonly(path):
 with path.open('rb') as f:
  fcntl.flock(f,fcntl.LOCK_SH)
  try:yield
  finally:fcntl.flock(f,fcntl.LOCK_UN)
def guard(ev,args):
 if ev=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes)):
   p=Path(os.fsdecode(path)).absolute()
   if p.suffix.lower() in ('.pt','.pth','.safetensors','.ckpt','.bin','.pkl','.pickle','.init','.pruned_init'):raise RuntimeError('binary payload forbidden')
   if isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_TRUNC) and not p.is_relative_to(D):raise RuntimeError('production write forbidden')
 if ev in ('subprocess.Popen','os.system','os.remove','os.unlink','os.rename','os.rmdir') or ev.startswith('socket.'):raise RuntimeError('side effect forbidden')
sys.addaudithook(guard)
prefix=copy.deepcopy(tree);pb=next(n for n in prefix.body if isinstance(n,ast.With));pb.items[0].context_expr=ast.Call(func=ast.Name(id='readonly',ctx=ast.Load()),args=[copy.deepcopy(block.items[0].context_expr.args[0])],keywords=[]);pb.body=pb.body[:end];ast.fix_missing_locations(prefix)
ns={'__name__':'independent_CPU_input_prefix','__file__':str(SOURCE),'readonly':readonly}
exec(compile(prefix,str(SOURCE)+'::CPU_INPUT_PREFIX_ONLY','exec'),ns)
s=ns['s'];job=ns['job'];auth=ns['auth'];p=ns['pre'];before=ns['before'];g=ns['g']
ck('known_original_ACK_identity',ns['ack']['stdout']=='3053894\n' and s['pending_submission']['known_job_id']=='3053894')
ck('known_original_one_slot_pending',s['autonomous_training_v1']['reserved_GPU_slots']==1 and s['pending_submission']['automatic_retry'] is False)
ck('only_Object64s23_development_scope',job['suite']=='libero_object' and job['mode']=='development' and job['gpus']==1 and job['resume'] is False and job['prior_job_ids']==[])
ck('original_sources530_runtime225',len(p['read_evidence_sha256'])==530 and len(p['runtime_preflight']['checked_files'])==225)
ck('previous_Spatial_unique_registry',sum(str(j['job_id'])=='3053875' for j in s['registered_jobs'])==1)
ck('new_Object_not_yet_registered',all(str(j['job_id'])!='3053894' for j in s['registered_jobs']))
ck('root_Object_readiness_exact',h(R/'results/formal_main_v2/preflight/heartbeat_20261021T0349/Object64s23_runtime_readiness_root.json')=='24e7511cba602382662a900ed4b673ab5c5ae729186078c582c24e64890340ea')
ck('independent_Object_post_exact',h(R/'.local/k64_seed23_bridges_independent_20261020T1949/post_readiness/Object/post_readiness_independent.json')=='714a5e5468e3366b548617b7fb8f58638830b25aff75062f16c1f560994b9719')
ck('state_still_exact_original_pending',h(R/'results/experiment_supervisor/state.json')==before)
ns['e'].unchanged()
save('actual_pending_state_before.json',s);save('original_gateway_rebuilt_job.json',job)
save('actual_original_ACK_and_preflight_refs.json',{'ack':ref(ns['D']/'sbatch_result.json'),'failure':ref(ns['D']/'failed_transaction.json'),'preflight':ref(ns['D']/'preflight.json'),'state_sha256':before,'authorization':ns['ar']})
report=save('helper_source_independent_review.json',{'schema':'formal_main_v2','kind':'Object3053894_exact_pending_reconciliation_independent_CPU_review','status':'passed','entrypoint_sha256':PIN,'source':ref(SOURCE),'job_id':'3053894','expected_state_sha256':before,'checks':checks,'checks_passed':len(checks),'blockers':[],'inherited_reconciliation_negatives':{'path':'.local/k64_spatial_reconcile_independent_20261020T1949/expected_rejections.json','sha256':h(D.parent/'expected_rejections.json'),'count':10},'exact_full_source_identity_substitutions_only':True,'actual_CPU_input_prefix_reconstructed':True,'scheduler_or_mutation_suffix_executed':False,'production_writes':0,'Slurm_queries':0,'submission_calls':0,'scientific_trials_added':0,'required_root_action':'Only execute exact helper with original EX writer lock, exact expected state and original ACK; original fresh reconcile guard must pass. Never resubmit. True terminal status records cost only, never scientific success.'})
print(json.dumps(report))
