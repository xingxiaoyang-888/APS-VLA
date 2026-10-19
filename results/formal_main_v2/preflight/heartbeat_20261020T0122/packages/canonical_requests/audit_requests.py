from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/canonical_review_alias_1722'
KEYS=['libero_object_k128_seed23','libero_object_k256_seed17','libero_spatial_k256_seed17','libero_spatial_k256_seed23','libero_spatial_k256_seed41','libero_spatial_k64_seed17','libero_spatial_k64_seed41']
refs={};checks=[]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p,expected=None):
 p=Path(p);p=p if p.is_absolute() else R/p;p.resolve().relative_to(R)
 h=sha(p);rel=p.relative_to(R).as_posix();refs[rel]={'sha256':h,'bytes':p.stat().st_size}
 if expected:assert h==expected,(rel,h,expected)
 return json.loads(p.read_text())
def watch(p):
 p=R/p;refs[p.relative_to(R).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size};return p

def save(n,v):
 with (D/n).open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def ck(n,v):
 checks.append({'check':n,'passed':bool(v)})
 if not v:raise ValueError(n)
state=read('results/experiment_supervisor/state.json');state_sha=refs['results/experiment_supervisor/state.json']['sha256'];utc=datetime.now(timezone.utc).isoformat()
ck('pending_submission_currently_none',state.get('pending_submission') is None)
source='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';inventory=read(source)
registration=read('configs/experiments/formal_main_v2.json')
for p in ['scripts/review_formal_segment.py','scripts/review_formal_acceptance.py','scripts/ops/formal_asset_downstream_review.py','scripts/formal_execution_manifests.py','scripts/ops/formal_autonomous_training_v1/worker.py'] :watch(p)
reviewer='scripts/review_formal_segment.py';ck('exact_existing_reviewer',refs[reviewer]['sha256']=='566408f7f72bd3d878204175573a9c08b01db67be69358ed4a8ac2d0e0603790')
p=R/'scripts/ops/formal_asset_downstream_review.py';spec=importlib.util.spec_from_file_location('actual_read_only_pair_source_contract',p);helper=importlib.util.module_from_spec(spec);exec(compile(p.read_bytes(),str(p),'exec'),helper.__dict__)
rows=[]
for key in KEYS:
 suite,k,seed=re.fullmatch(r'(libero_object|libero_spatial)_k(128|256|64)_seed(17|23|41)',key).groups();k=int(k);seed=int(seed)
 completed=state['formal_main_progress']['completed_training_pairs'][key];term=completed['terminal_root_and_independent_review']
 rootref=term['root_review'];indref=term['independent_review'];root=read(rootref['path'],rootref['sha256']);ind=read(indref['path'],indref['sha256'])
 ck(key+'_accepted_integrity',root['kind']=='root_completed_pairs_terminal_integration' and root['status']=='accepted_training_integrity_not_scientific_efficacy' and ind['kind']=='independent_completed_training_evidence_review' and ind['status']=='passed' and ind['completed_by_arm']=={'A':5000,'B':5000})
 changes=[x for x in root['changes'] if x['pair_key']==key];ck(key+'_one_root_entry',len(changes)==1);change=changes[0]
 outref=completed['machine_verification']['machine_output'];out=read(outref['path'],outref['sha256']);ck(key+'_same_machine_binding',change['machine_output']==outref and ind['machine_output']==outref)
 mr=out['admission']['review_ref'];machine=read(mr['path'],mr['sha256']);raw=machine['original_review']
 ck(key+'_machine_claims_retained',machine['root_signature_claimed'] is False and machine['independent_review'] is False and machine['kind']=='automatic_machine_training_review' and raw['status']=='local_passed_remote_required')
 base=f'results/formal_main_v2/{suite}/k{k}/seed{seed}/training';summary=read(base+'/training_summary.json');jid=str(summary['job_id']);target=base+'/segment_reviews/'+jid+'.json'
 ck(key+'_canonical_absent',not (R/target).exists())
 ck(key+'_matching_completed_job',jid==raw['job_id']==ind['job_id'] and summary['status']=='completed' and summary['pair_complete'] is True and raw['completed_by_arm']=={'A':5000,'B':5000})
 history=sorted([j for j in state['registered_jobs'] if j.get('experiment')=='formal_main_v2' and j.get('stage_key')==f'{suite}_train_k{k}_seed{seed}'],key=lambda x:x['submitted_utc'])
 ck(key+'_newest_terminal5000',history and history[-1]['job_id']==jid and all(j['status']=='COMPLETED' and j['exit_code']=='0:0' for j in history) and history[-1]['segment_end']==5000)
 ck(key+'_same_original_history',{j['job_id']:helper.job_identity(j) for j in history}=={j['job_id']:helper.job_identity(j) for j in raw['registered_pair_jobs_at_review']})
 pulls=[]
 for pr,h in machine['raw_input_evidence'].items():
  if '/pulls/' not in pr or not pr.endswith('/receipt.json'):continue
  q=read(pr,h)
  if jid in q.get('requested_job_ids',[]):pulls.append((pr,h,q))
 ck(key+'_one_terminal_pull',len(pulls)==1);pr,ph,pull=pulls[0]
 ids={j['job_id'] for j in history}
 ck(key+'_pull_full_pair_scope',set(pull['requested_job_ids'])==ids and set(x['job_id'] for x in pull['selected_jobs'])==ids and pull['schema']=='formal_main_v2' and pull['kind']=='nonweight_pull' and pull['status']=='verified_nonweight_snapshot' and pull['final_evidence'] is True and not pull['missing'])
 for when in ['accounting_before','accounting_after']:
  for j in history:
   observed=pull[when]['jobs'][j['job_id']]
   ck(key+'_'+when+'_'+j['job_id'],all(observed[x]==j[x] for x in ['status','exit_code','elapsed_seconds']) and 'gres/gpu=1' in observed['allocation'].split(','))
 for suffix in ['inventory_before.json','inventory_after.json']:
  pp=str(Path(pr).with_name(suffix));ii=read(pp,machine['raw_input_evidence'][pp]);ck(key+'_'+suffix,refs[pp]['sha256']==pull['inventory_sha256'])
 pull_files={x['relative']:x for x in pull['files']}
 ck(key+'_pull_covers_original_required_files',all(p in pull_files and pull_files[p]['sha256']==h for p,h in raw['files'].items()))
 current_small=[]
 for rel in [base+'/training_summary.json',base+'/A/training_report.json',base+'/B/training_report.json',base+'/A/deployment_receipt.json',base+'/B/deployment_receipt.json']:
  d=read(rel,raw['files'][rel]);current_small.append({'path':rel,**refs[rel]})
 expect={'schema':'formal_main_v2','kind':'root_segment_review','status':'passed','suite':suite,'visual_tokens':k,'seed':seed,'source_sha256':helper.SOURCE_SHA256,'output_relative':base,'job_id':jid,'requested_segment_end':5000,'completed_by_arm':{'A':5000,'B':5000},'ab_same_registered_boundary':True,'resume_required':False,'continuation':'formal_training_complete_no_extension'}
 old=read(change['original_root_review']);tests=[]
 for name,value,sourcepath in [('aggregate_root',root,rootref['path']),('machine_envelope',machine,mr['path']),('machine_nested_original',raw,mr['path']+'#/original_review'),('previous_boundary_root',old,change['original_root_review'])]:
  mismatches={x:{'actual':value.get(x),'expected':v} for x,v in expect.items() if value.get(x)!=v}
  try:helper.same(value,expect,'final segment review');accepted=True;error=None
  except ValueError as e:accepted=False;error=str(e)
  ck(key+'_'+name+'_rejected_as_alias',not accepted)
  tests.append({'source':sourcepath,'same_original_consumer_call':'formal_asset_downstream_review.same(actual, expected_final5000_fields, final segment review)','accepted':accepted,'error':error,'mismatches':mismatches})
 request={'pair_key':key,'job_id':jid,'canonical_target':target,'direct_byte_alias_available':False,'existing_terminal_root':rootref,'existing_independent_review':indref,'machine_output':outref,'original_machine_review':mr,'original_false_review_status':raw['status'],'prior_root_review':{'path':change['original_root_review'],**refs[change['original_root_review']]},'original_reviewer':{'path':reviewer,**refs[reviewer]},'original_review_call':{'function':'review_formal_segment.review','job_id':jid,'source_inventory':source,'pull_receipt':pr,'verify_server_resume':True,'root':str(R)},'source_inventory_ref':{'path':source,**refs[source]},'pull_receipt_ref':{'path':pr,'sha256':ph,'bytes':refs[pr]['bytes']},'pull_origin':'Exact original real terminal worker pull, selected from immutable machine raw_input_evidence; not a synthetic or new pull.','requested_full_pair_job_ids':sorted(ids,key=int),'latest_registered_job':{k:history[-1].get(k) for k in ['job_id','suite','visual_tokens','training_seed','status','exit_code','segment_end','run_root','source_sha256','invocation','invocation_sha256']},'small_terminal_products_rehashed':current_small,'alias_rejections':tests,'root_execute_requirements':['Reacquire shared writer lock and verify current pending_submission is None, exact latest same-pair job and unchanged sources.','Run this existing reviewer via exact-SHA reviewed server transport with verify_server_resume=True; it reconstructs full raw evidence and freshly hashes the two server resume files.','Let only the original successful reviewer publish its canonical result. Do not copy machine bytes or manually change status.','Then run original suite_rows/source_provenance for the selected methods. No GPU retraining required for this operational receipt step.'],'not_performed_here':['verify_server_resume=True','checkpoint byte hash/deserialization','canonical publication','full raw reviewer rerun','Slurm','state/Git/P writes']}
 rows.append(request)
save('request_index.json',{'schema':'formal_main_v2','kind':'canonical_root_review_reconstruction_requests','status':'prepared_for_root_original_reviewer_not_executed','utc':utc,'state_snapshot_sha256':state_sha,'pending_submission_at_observation':None,'pair_count':7,'byte_alias_count':0,'requests':rows})
save('audit_review.json',{'schema':'formal_main_v2','kind':'read_only_canonical_root_path_review','status':'passed_readonly_request_preparation_no_alias','utc':utc,'existing_training_acceptance_unchanged':True,'same_contract_alias_rejections':28,'checks':checks,'evidence_refs':refs,'scopes':{'canonical_written':False,'root_claim_created':False,'verify_server_resume_called':False,'checkpoint_bytes_read':False,'model_loaded':False,'Slurm_calls':0,'state_modified':False,'P_modified':False,'Git_modified':False,'sealed_values_read':False},'conclusion':'All seven aggregate root+independent acceptances are genuine but no final root_segment_review/status=passed standalone bytes are bound. Rebuild with the exact original root reviewer and corresponding immutable original terminal pull; no new consumer framework or status editing required.'})
print(json.dumps({'status':'prepared_not_executed','requests':len(rows),'byte_alias_count':0,'checks':len(checks),'evidence_refs':len(refs),'jobs':[x['job_id'] for x in rows]},ensure_ascii=False))
