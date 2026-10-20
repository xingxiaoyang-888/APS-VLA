from pathlib import Path
import ast,hashlib,importlib.util,sys,json,copy,traceback
D=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/.local/collect_terminal_independent_20261020T1949')
p=D/'audit_raw_v1.py';assert hashlib.sha256(p.read_bytes()).hexdigest()=='07fe8b598f495d25ed0e0aebc651def88679ae8a794afceeb717a7f6581d339f'
spec=importlib.util.spec_from_file_location('collect_ind_raw_helpers',p);a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
R=a.R;A=R/'.local/collect_terminal_20261020T1949'
PINS={'root_collect_terminal_v1.py':'1cd87061863737c8783e4498820d9d09929c93bc8e0427c650330baff31e1eb6','checks_v1.py':'737ef40d686992a3adb22d872a2cfead6d74492a986dfe712a57e7bf63a5d276','inputs.json':'5f3ad7c8ed294d27a6a4cf2b37851511dde751014b57ada728459c653551b4d5'}
def main():
 for name,pin in PINS.items():a.check(a.digest(A/name)==pin,'exact author input:'+name)
 spec=importlib.util.spec_from_file_location('independent_author_check_functions',A/'checks_v1.py');c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
 value=c.inputs();a.check(c.validate_files(value,a.P) is not None,'author original P file boundary passes')
 rawmap={x['relative']:x for x in a.read(D/'P_raw_files.json')['files']};authors={x['relative']:x for x in value['output_files']}
 for rel,x in rawmap.items():a.check(authors[rel]['sha256']==x['sha256'] and authors[rel]['bytes']==x['bytes'],'independent/author original P map agrees:'+rel)
 a.check(len(authors)==106 and len(rawmap)==100,'all100 raw artifacts plus6 original job receipt and Slurm logs')
 negative=[]
 def reject(label,f):
  try:f()
  except (ValueError,AssertionError,KeyError) as e:negative.append(dict(label=label,type=type(e).__name__,message=str(e)));return
  raise AssertionError('invalid input accepted: '+label)
 for job in value['selected_registered_jobs']:
  a.check(c.validate_job(job,job)[0]==job['suite'],'real author exact job validator')
  for key,bad in [('job_id','0'),('mode','final'),('suite','libero_goal'),('status','FAILED'),('exit_code','1:0'),('gpus',2),('elapsed_seconds',job['elapsed_seconds']+1),('method_ids',['dense','A']),('prior_job_ids',['0']),('resume',True),('source_sha256','0'*64),('run_root',str(a.P/'results/wrong'))]:
   x=copy.deepcopy(job);x[key]=bad;reject(job['job_id']+':'+key,lambda x=x:c.validate_job(x,x))
 for label,change in [('duplicate_inventory',lambda v:v['output_files'].append(v['output_files'][0])),('missing_inventory',lambda v:v['output_files'].pop()),('altered_original_SHA',lambda v:v['output_files'][0].update(sha256='0'*64)),('altered_original_owner',lambda v:v['output_files'][0].update(job_id='0'))]:
  v=copy.deepcopy(value);change(v);reject(label,lambda v=v:c.validate_files(v,a.P))
 source=(A/'root_collect_terminal_v1.py').read_text();tree=ast.parse(source)
 names=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
 a.check(not any(isinstance(n.func,ast.Name) and n.func.id in ('eval','exec') for n in names),'no dynamic execution builtin')
 a.check(not any(isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value in ('sbatch','scancel','scontrol','git') for n in ast.walk(tree)),'no scheduler or Git mutation command')
 withs=[n for n in ast.walk(tree) if isinstance(n,ast.With) and any(isinstance(i.context_expr,ast.Call) and isinstance(i.context_expr.func,ast.Attribute) and i.context_expr.func.attr=='exclusive_lock' for i in n.items)]
 a.check(len(withs)==1 and '.writer.lock' in ast.get_source_segment(source,withs[0].items[0].context_expr),'single shared writer lock encloses evidence transaction')
 text=ast.get_source_segment(source,withs[0]);order=[text.index(t) for t in ["output/'intent.json'",'puller.pull(',"output/'terminal_jobs_snapshot.json'",'reviewer.review(',"rr=c.write(R/f'results/formal_main_v2/downstream_reviews/",'consumer.review_downstream_output(',"output/'completion.json'"]]
 a.check(order==sorted(order),'intent/pull/immutable jobs/original reviewer/publish/original consumer/completion order')
 a.check("state_path.read_bytes()==before" in text and "finally:c.need(state_path.read_bytes()==before" in text,'state bytes checked before completion and finally')
 a.check("output.exists()" in text and "root review already exists; inspect prior transaction instead of replay" in text,'non-reentrant evidence transaction preserves partial failures')
 a.check('partial_outputs_preserved=True' in text and 'retry_automatic=False' in text,'failure retains partial outputs and prohibits automatic retry')
 a.check('cost_increment_gpu_seconds=0' in text and 'new_jobs=0' in text and 'new_scientific_trials=0' in text,'no new allocation/cost/scientific result claim')
 a.save('helper_independent_review.json',dict(schema='formal_main_v2',kind='independent_existing_collect_terminal_helper_review',status='passed',reviewed_by='independent',entrypoint_sha256=PINS['root_collect_terminal_v1.py'],files={str((A/n).relative_to(R)):h for n,h in PINS.items()},checks_passed=len(a.checks),checks=a.checks,negative_cases=negative,negative_count=len(negative),blockers=[],code_review_findings=['Root-only transaction with shared writer lock; no scheduler/Git/state mutation code.','Original pinned puller only two registered completed outputs; full exact106-file allowlist checked before and after.','Original action-v1 reviewer and original full consumer run sequentially without bypass or substituted results.','Each allocation is retained in original review cost; transaction adds zero cost because already in root accounting.','Root review may remain if later consumer/second-suite failure occurs; partial evidence is retained and reentry is refused.'],helper_executed=False,root_role_assumed=False,actual_terminal_acceptance=False,raw_review_reference=dict(path=str((D/'raw_observation_review.json').relative_to(R)),sha256=a.digest(D/'raw_observation_review.json')),limitations=['Static helper approval and private validator negatives; root must execute actual pull/reviewer/consumer and independent terminal reconstruction is still pending.']))
 print(json.dumps(dict(status='passed',checks=len(a.checks),negative_count=len(negative),report_sha256=a.digest(D/'helper_independent_review.json'))))
if __name__=='__main__':
 try:main()
 except BaseException as e:a.save('helper_failure_v1.json',dict(status='failed',type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),checks_passed=len(a.checks)));raise
