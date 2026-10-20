"""Independent read-only verification of fixed Spatial pending reconciliation."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,json,sys,traceback
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=Path(__file__).resolve().parent
C=R/'.local/reconcile_spatial_pending_0238_a2.py'
PIN='6cc0bce095f6f33bacd1fe6bd65ce2e3e1c8baa72ebaf0d27d96193c07e097cb'
READS={}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def raw(p,pin=None):
 p=Path(p);b=p.read_bytes();h=sha(b)
 if pin is not None and h!=pin:raise ValueError('exact source differs '+str(p))
 READS[str(p)]=h;return b
def check(ok,msg):
 if not ok:raise AssertionError(msg)
def save(name,value):
 b=(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2)+'\n').encode()
 with (D/name).open('xb') as f:f.write(b)
 return {'path':(D/name).relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
def reject(fn):
 try:fn()
 except ValueError as e:return {'status':'rejected','error':str(e)}
 raise AssertionError('malformed case accepted')
def main():
 text=raw(C,PIN).decode();tree=ast.parse(text,str(C));calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
 check(not any(isinstance(n.func,ast.Attribute) and n.func.attr in {'submit','cancel'} for n in calls),'candidate may submit/cancel')
 check(not any(isinstance(n.func,ast.Name) and n.func.id in {'eval','exec'} for n in calls),'dynamic execution in candidate')
 withs=[n for n in tree.body if isinstance(n,ast.With)];check(len(withs)==1,'one shared writer transaction expected')
 tx=withs[0];mutation="state['registered_jobs'].append(job)"
 cut=[i for i,n in enumerate(tx.body) if ast.unparse(n)==mutation];check(len(cut)==1,'one first in-memory registration boundary expected')
 prefix=copy.deepcopy(tree);ptx=next(n for n in prefix.body if isinstance(n,ast.With));ptx.body=ptx.body[:cut[0]]
 prefixcalls=[n for n in ast.walk(prefix) if isinstance(n,ast.Call)]
 forbidden={'record','atomic_json','publish','submit','cancel','immutable','write_text','write_bytes'}
 check(not any(isinstance(n.func,ast.Attribute) and n.func.attr in forbidden for n in prefixcalls),'write/submit in read-only prefix')
 check((R/'results/experiment_supervisor/.writer.lock').is_file(),'existing shared lock required')
 # Execute only the exact precommit source prefix; no candidate mutation or publication statements exist in this AST.
 ns={'__name__':'independent_precommit_prefix','__file__':str(C)}
 exec(compile(ast.fix_missing_locations(prefix),str(C),'exec'),ns)
 g,c,d=ns['g'],ns['c'],ns['d'];state=ns['state'];before=ns['before'];snapshot=ns['snapshot'];job=ns['job'];jobs=ns['jobs'];token=ns['token'];auth=ns['auth'];co=ns['corroboration']
 check(c.file_sha(R/g.a.STATE)==before,'state changed after independent prefix')
 check(state==ns['old'] and state['pending_submission']['known_job_id']=='3044479','prefix changed memory state or pending')
 check(ns['detail'].returncode==0 and len([x for x in ns['detail'].stdout.splitlines() if x.strip()])==1,'single scontrol record required')
 fields={}
 for field in ['JobId','JobName','JobState','WorkDir','Comment','Requeue','Restarts','ExcNodeList','TimeLimit','Command','StdOut','StdErr']:
  rows=[x.split('=',1)[1] for x in ns['detail'].stdout.split() if x.startswith(field+'=')]
  check(len(rows)==1,'ambiguous detail field '+field);fields[field]=rows[0]
 check(ns['caps']['unknown']==[] and ns['caps']['findings']==[],'accounting uncertainty')
 neg={}
 bad=copy.deepcopy(snapshot);bad['rows'].pop('3044479');neg['missing_known_accounting_row']=reject(lambda:d.reconcile_submission(c,jobs,bad,job,token,auth['controller_job_id'],co))
 bad=copy.deepcopy(snapshot)
 if '3044479' in bad['queue']:
  bad['queue']['3044479']['comment']='wrong-token';neg['wrong_new_job_queue_token']=reject(lambda:d.reconcile_submission(c,jobs,bad,job,token,auth['controller_job_id'],co))
 else:
  wrong=copy.deepcopy(co);wrong['comment']='wrong-token';neg['wrong_new_job_scontrol_token']=reject(lambda:d.reconcile_submission(c,jobs,bad,job,token,auth['controller_job_id'],wrong))
 terminal=next(j['job_id'] for j in state['registered_jobs'] if j.get('experiment')=='formal_main_v2' and j.get('status')=='COMPLETED')
 bad=copy.deepcopy(snapshot);bad['rows'][terminal]['exit_code']='1:0';neg['historical_terminal_exit_drift']=reject(lambda:d.reconcile_submission(c,jobs,bad,job,token,auth['controller_job_id'],co))
 # Simulate only the original candidate's in-memory update statements, cut before its first record call.
 muttree=copy.deepcopy(tree);mtx=next(n for n in muttree.body if isinstance(n,ast.With));recordcut=next(i for i,n in enumerate(mtx.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='record')
 updates=mtx.body[cut[0]:recordcut]
 check(not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in {'atomic_json','record','publish','submit','cancel'} for stmt in updates for n in ast.walk(stmt)),'filesystem call in memory simulation')
 exec(compile(ast.fix_missing_locations(ast.Module(body=updates,type_ignores=[])),str(C),'exec'),ns)
 changed=ns['state'];old=ns['old'];check(changed['registered_jobs'][:-1]==old['registered_jobs'],'old registry altered')
 check(changed['autonomous_training_v1']==old['autonomous_training_v1'],'controller/reservation/block altered')
 check(changed['pending_submission'] is None and changed['registered_jobs'][-1]==job,'wrong in-memory commit')
 check(c.file_sha(R/g.a.STATE)==before,'memory simulation touched real state')
 check(not (R/'results/formal_main_v2/submissions/3044479.json').exists() and not (R/ns['AD']/'committed.json').exists(),'production published by audit')
 inv=ns['inventory']
 for rel,pin in inv['files'].items():raw(R/rel,pin);raw(g.a.S/rel,pin)
 for rel,pin in ns['e'].hashes.items():raw(R/rel,pin)
 for rel in [ns['AD']+'/preflight.json',ns['AD']+'/sbatch_result.json',ns['AD']+'/failed_transaction.json',ns['invrel']]:raw(R/rel)
 raw(ns['P']/ns['invrel'],ns['invsha']);raw(C,PIN)
 raw(R/'.local/reconcile_spatial_pending_0238.py','5817957111f8d181e2dedf982938ed189113b874324535f5e322ec22276faa73')
 result={'schema':'formal_main_v2','kind':'Spatial_pending_reconciliation_independent_precommit_check','status':'passed_read_only','utc':datetime.now(timezone.utc).isoformat(),'candidate':{'path':C.relative_to(R).as_posix(),'sha256':PIN},'job_id':'3044479','original_preflight':ns['ref'](ns['AD']+'/preflight.json'),'original_ACK':ns['ref'](ns['AD']+'/sbatch_result.json'),'original_failure':ns['ref'](ns['AD']+'/failed_transaction.json'),'authorization':ns['AR'],'pending_before':old['pending_submission'],'state_before_sha256':before,'state_after_sha256':c.file_sha(R/g.a.STATE),'registry_before_count':len(old['registered_jobs']),'job_from_original_gateway_constructor':job,'full_scheduler_observation':snapshot,'corroboration_optional':co,'actual_scontrol_detail':{'argv':ns['detail_argv'],'returncode':ns['detail'].returncode,'stdout':ns['detail'].stdout,'stderr':ns['detail'].stderr,'unique_fields':fields},'capacity':ns['caps'],'controller_owner':ns['owner'],'tests':{'no_submit_or_cancel_call_in_candidate':True,'exact_precommit_prefix_executed_without_write_nodes':True,'actual_complete_registry_and_known_job_identity':True,'actual_CPU0_and_owner_lease':True,'R_P_invocation_exact_original_preflight':True,'all173_R_and_S_same_SHA':True,'isolated_in_memory_original_mutation_passed':True,'state_and_controller_unmodified':True,'negative_cases':neg},'expected_root_mutation_only':['append exact original g.job for3044479','clear this exact known pending after CAS','update this pair tracking and active count','refresh allocated GPU cost from exact observed registered formal allocations','immutable reconciliation/submission receipts retaining failure'],'new_GPU_submissions':0,'Slurm_mutation':False,'real_state_modified':False,'real_invocation_modified':False,'production_registration_written':False,'optimizer_rng_verified':False,'scientific_results_claimed':False,'read_evidence_sha256':READS}
 ref=save('precommit_checks_a1.json',result)
 print(json.dumps({'status':'passed_read_only','receipt':ref,'registered_plus_known_job':len(jobs),'occupied':len(ns['caps']['occupied']),'negative_cases':len(neg),'refs':len(READS)}),flush=True)
try:main()
except BaseException as e:
 save('precommit_failure_a1.json',{'status':'failed','type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'read_evidence_sha256':READS});raise
