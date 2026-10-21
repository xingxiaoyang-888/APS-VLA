from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import ast, copy, hashlib, json, os, subprocess, sys, traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/goal_remaining5_Delivery_independent_20261021T0449'
B='results/formal_main_v2/preflight/heartbeat_20261021T1249'
E='results/formal_main_v2/engineering/supervision_delivery_20261021T0449'
STATE='results/experiment_supervisor/state.json'
ST='0621504d45ef43e44f6d46c01d0a8c4d0c9acdfdd29d05df9101d75979fc5d6e'
BEFORE='58e4ff5cd74c07c667a942119d2ed2de80059efb294ad8f21d192cdbe14bdac7'
SUM='281cb598d6dda4b50420be5439256607fdb5e9c70bf59a8dafba1e68b7546391'
INDEX='7b84527592221abab8dffc3096a623432c8d92560c89f57dc04cc5b13046f6a6'
HEAD='0b46f1169042e407c128e226b8cc7eabb468e873'
REQ='daf0c53e281d7f637b2a20ba53dc7182d400242b1b5978b006b3aee3a2d01e19'
KEYS=['libero_goal_k256_seed23','libero_goal_k256_seed41','libero_goal_k64_seed17','libero_goal_k64_seed23','libero_goal_k64_seed41']
IDS=['3057505','3057510','3057515','3057526','3057533']
PKG='scripts/ops/formal_goal_remaining5_gate_v1'
GATE='scripts/ops/formal_goal_remaining5_dispatch_v1'
CHECKS=[];NEG=[];INVENTORY={};PACKAGES=[]
def need(v,n):
 if not v:raise AssertionError(n)
 CHECKS.append(n)
def digest(b):return hashlib.sha256(b).hexdigest()
def h(p):
 z=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):z.update(b)
 return z.hexdigest()
def safe(n,root=R):
 p=PurePosixPath(n);need(not p.is_absolute() and '..' not in p.parts,'relative-safe:'+n)
 q=root/n
 need(not any(x.is_symlink() for x in [q,*q.parents] if x!=Path('/')),'no-symlink:'+str(q))
 need('/raw_runtime/' not in str(q) and '/attempt01/original_run/' not in str(q) and '/observer/blobs/' not in str(q),'not-live-raw:'+str(q))
 return q
def ref(n,root=R):
 p=safe(n,root);return dict(path=n,bytes=p.stat().st_size,sha256=h(p))
def checked(n,pin=None,size=None,root=R):
 p=safe(n,root);r=dict(path=n,bytes=p.stat().st_size,sha256=h(p))
 if pin:need(r['sha256']==pin,'hash:'+str(p))
 if size is not None:need(r['bytes']==size,'size:'+str(p))
 if root==R:INVENTORY[n]=r
 return p
def rd(n,pin=None):
 return json.loads(checked(n,pin).read_bytes())
def verify_ref(v,root=R):
 need(isinstance(v,dict) and isinstance(v.get('path'),str) and len(v.get('sha256',''))==64,'typed-ref')
 return checked(v['path'],v['sha256'],v.get('bytes'),root)
def write(n,v):
 p=D/n
 with p.open('xb') as f:f.write((json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n').encode())
 return dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=h(p))
def reject(n,fn):
 try:fn()
 except (AssertionError,KeyError,ValueError,TypeError):NEG.append(dict(name=n,rejected=True))
 else:raise AssertionError('mutation accepted: '+n)
def git(*args):
 p=subprocess.run(['git',*args],cwd=R,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'),capture_output=True)
 need(p.returncode==0,'readonly-git:'+args[0]);return p.stdout
def recursive_refs(v):
 if isinstance(v,dict):
  if isinstance(v.get('path'),str) and isinstance(v.get('sha256'),str) and len(v['sha256'])==64:
   verify_ref(v)
  for k,x in v.items():
   if k not in ('path','sha256'):recursive_refs(x)
 elif isinstance(v,list):
  for x in v:recursive_refs(x)
def diff(a,b,path=''):
 if isinstance(a,dict) and isinstance(b,dict):
  rows=[]
  for k in sorted(set(a)|set(b)):
   n=path+'/'+str(k)
   if k not in a:rows.append(dict(path=n,change='added',after=b[k]))
   elif k not in b:rows.append(dict(path=n,change='removed',before=a[k]))
   else:rows+=diff(a[k],b[k],n)
  return rows
 if isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
  return sum((diff(x,y,path+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [] if a==b else [dict(path=path,change='changed',before=a,after=b)]

started=datetime.now(timezone.utc).isoformat()
try:
 need(os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R),'approved-transport-root')
 checked('.local/integrate_goal_remaining5_20261021T0449.py','38351487752e47ef204b321212df90025f860db5fecebdd686d05888708cdb27')
 state=rd(STATE,ST);before=rd(B+'/dispatch_supervisor_snapshot_before.json',BEFORE)
 summary=rd(B+'/final_summary.json',SUM)
 oldsummary=rd('results/formal_main_v2/preflight/heartbeat_20261021T1134/final_summary.json','35a12c33d2bf81331e96aad4fe2879ae06fa7269a518fc14933fea8dc65aac02')
 receipt=rd(B+'/root_integration_receipt.json','20221fe449e8ab98767f13d8527bb25d67cd186f3170e16ea13e980d4b761381')
 obs=rd(B+'/post_dispatch_observation.json','2bfccdc44ce0fd488be0d50bc76092aa071c07517d8ae9dccee2160e5bb6fcd2')
 sub=rd(B+'/Goal_remaining5_submissions_root_receipt.json','6e998ddf4cc4fdd7c24f547cc8ea0e45e7642b0140517cecb6d09ef92ab08489')
 need(obs['state_sha256']==BEFORE and obs['new_trials_accepted']==0 and obs['scientific_acceptance_inferred'] is False,'saved-observation-only-no-science')
 recursive_refs(receipt);recursive_refs(sub)
 need(receipt['prior_cost_display_metadata']==before['current_round_cost'],'stale-cost-metadata-retained')
 need([j['job_id'] for j in sub['jobs']]==IDS and [j['pair_key'] for j in sub['jobs']]==KEYS,'exact-five-root-registrations')
 need(sub['new_scientific_trials_accepted']==0 and sub['duplicate_submissions']==0 and sub['release_count_per_job']==1 and sub['all_first_sacct_delays_retained'] is True,'root-receipt-no-new-science')
 for i,(key,jid) in enumerate(zip(KEYS,IDS)):
  j=next(j for j in before['registered_jobs'] if j['job_id']==jid)
  row=obs['observation']['rows'][jid];r=sub['jobs'][i]
  need(row['status']=='RUNNING' and row['gpus']==1 and row['elapsed_seconds']==[260,225,194,142,113][i],'saved-running:'+jid)
  need(r['planned_trials']==200 and r['completed_trials_accepted']==0 and r['unique_development_states']==100 and r['scientific_terminal_acceptance_pending'] is True and r['maximum_attempts']==1 and r['automatic_retry'] is False,'registration-pending-not-accepted:'+jid)
  for k in ('job_id','pair_key','pair_id','method_ids','training_seed','attempt_root'):need(r[k]==j[k],'registered-origin:'+jid+':'+k)
  need(r['tokens']==j['visual_tokens'],'tokens:'+jid)
  X='results/formal_main_v2/execution/goal_remaining5_v1/'+key
  ack=rd(X+'/dispatch_attempt01/sbatch_result.json');com=rd(X+'/dispatch_attempt01/committed.json');rel=rd(X+'/dispatch_attempt01/release_result.json');fail=rd(X+'/dispatch_attempt01/failed_transaction.json')
  need(ack['stdout']==jid+'\n' and ack['returncode']==rel['returncode']==0 and com['job_id']==jid and com['automatic_retry'] is False,'original-ACK-commit-release:'+jid)
  need('--hold' in ack['actual_sbatch_argv'] and '--no-requeue' in ack['actual_sbatch_argv'],'held-no-requeue:'+jid)
  need('missing registered allocation' in json.dumps(fail),'accounting-latency-preserved:'+jid)
  need(r['original_ACK']['sha256']==h(R/X/'dispatch_attempt01/sbatch_result.json'),'root-original-ACK-pin:'+jid)
  need(r['raw_root']==str(R/'results/formal_main_v2/raw_runtime/goal_remaining5_v1'/key/'attempt01'),'raw-root-metadata-only:'+jid)
 expected=copy.deepcopy(before)
 for j in expected['registered_jobs']:
  if j['job_id'] in IDS:
   for k in ('status','exit_code','elapsed_seconds','allocation','node'):j[k]=obs['observation']['rows'][j['job_id']][k]
 expected['current_round_cost'].update(registered_jobs=278,allocated_gpu_seconds=1995402,allocated_gpu_hours=1995402/3600,final=False,observation=ref(B+'/post_dispatch_observation.json'),scope='All278 unique formal allocations once each at saved UTC '+obs['utc']+'; five RUNNING single-GPU allocations included as elapsed lower bounds, not final cost or parallel wall-clock estimate.')
 expected['formal_main_progress']['parallel_execution'].update(status='training_complete_remaining5_Goal_development_running',registered_requested_active_GPU_jobs=5,actual_running_allocated_GPUs=5,active_registered_GPU_jobs=IDS,latest_registered_job_observation=ref(B+'/post_dispatch_observation.json'))
 expected['autonomous_training_v1']['occupied_job_ids']=IDS
 expected['formal_main_progress']['Goal_remaining5_development_registration_20261021T0449']=sub['jobs']
 expected['formal_main_progress']['downstream_followups_20261021T0449']={
 'Goal_remaining1000':'five_exact_jobs_running_pending_terminal_review_no_resubmit',
 'Goal_fixed30':'CPU_design_only_not_collected','Goal_old200':'HOLD_cause_unresolved_not_retroactively_accepted',
 'runtime_independent':ref(E+'/Goal_runtime_independent/independent_review.json'),
 'dispatch_independent':ref(E+'/Goal_gateway_independent/independent_review.json'),
 'Goal30_design':ref(E+'/Goal_fixed30_design/Goal_fixed30_design.json'),
 'source_manifest':ref(PKG+'/package_manifest.json'),
 'submission_receipt':ref(B+'/Goal_remaining5_submissions_root_receipt.json'),
 'new_trials_accepted':0,'O2A_released':False,'final_release':False}
 expected['last_root_supervision_snapshot']=ref(B+'/final_summary.json')
 def validate_state(s):
  need(s==expected,'full-state-equals-only-allowed-saved-observation-integration')
  p=s['formal_main_progress']
  need(p['root_and_independent_completed_arms']==72 and p['root_and_independent_reviewed_arm_updates']==360000,'72-and360000-inherited')
  need(p['complete_development_batches_accepted_trials']==7800 and p['current_action_development_trial_count']==6589 and p['current_action_development_unique_initial_states']==400,'7800-and6589-and400-inherited')
  need(p['completed_final_trials']==0 and p['test_opened'] is False and p['global_release_created'] is False,'final-stays-sealed')
  need(s['pending_submission'] is None and s['autonomous_training_v1'].get('pending_submission') is None and s['autonomous_training_v1']['reserved_GPU_slots']==0 and not s['autonomous_training_v1'].get('root_submission_hold'),'pending-reserve-hold-clear')
 validate_state(state)
 need(state['registered_jobs'][:303]==before['registered_jobs'][:303],'prior303-registration-rows-unchanged')
 state_diff=diff(before,state);need(len(state_diff)==36,'exact36-leaf-differences')
 for field,value in [('complete_development_batches_accepted_trials',8800),('completed_final_trials',1),('test_opened',True),('global_release_created',True)]:
  bad=copy.deepcopy(state);bad['formal_main_progress'][field]=value;reject('state-'+field,lambda b=bad:validate_state(b))
 bad=copy.deepcopy(state);bad['current_round_cost']['final']=True;reject('cost-cannot-claim-final',lambda:validate_state(bad))
 bad=copy.deepcopy(state);bad['pending_submission']={'unresolved':True};reject('pending-cannot-be-ignored',lambda:validate_state(bad))
 bad=copy.deepcopy(state);bad['registered_jobs'][0]['status']='RUNNING';reject('historical-job-rewrite',lambda:validate_state(bad))
 formal=[j for j in state['registered_jobs'] if j.get('experiment')=='formal_main_v2']
 need(len(formal)==len({j['job_id'] for j in formal})==278,'278-unique-formal-allocations')
 total=sum(obs['observation']['rows'][j['job_id']]['elapsed_seconds']*obs['observation']['rows'][j['job_id']]['gpus'] for j in formal)
 need(total==1995402==summary['allocated_GPU_seconds']==state['current_round_cost']['allocated_gpu_seconds'],'independent-cost-sum1995402')
 need(obs['capacity']==dict(active_pairs={},findings=[],occupied=IDS,unknown=[]),'saved-5-occupancy-no-unknown')
 need(sum(obs['observation']['rows'][j]['gpus'] for j in IDS)==5,'saved-five-real-GPUs')
 changes={'utc','previous_snapshot','source_state_before_sha256','Goal_remaining1000_HOLD','Goal_remaining1000_acceptance_pending','Goal_remaining5_submissions','Goal_fixed30_design','active_registered_GPU_jobs','actual_running_allocated_GPUs','registered_formal_allocations','allocated_GPU_seconds','allocated_GPU_hours','capacity','cost_basis','cost_observed_utc','cost_final_for_current_registered_set','new_GPU_jobs','new_complete_batch_rows_accepted','new_current_development_trials_accepted','new_legacy_rows_entering_complete_batch_view','new_unique_initial_states','newly_accounted_GPU_seconds','next_actions'}
 need({k:v for k,v in summary.items() if k not in changes}=={k:v for k,v in oldsummary.items() if k not in changes},'all-prior-summary-scientific-claims-unchanged')
 def validate_summary(v):
  need(v['compatible_development_trials']==7800 and v['planned_development_trials']==8800 and v['current_action_development_trials']==6589 and v['unique_development_initial_states']==400,'summary-accepted-exact')
  need(v['new_complete_batch_rows_accepted']==v['new_current_development_trials_accepted']==v['new_legacy_rows_entering_complete_batch_view']==v['new_unique_initial_states']==0,'summary-round-new-zero')
  need(v['compatible_legacy_Long_trials']==600 and v['compatible_legacy_Spatial_trials']==12 and v['compatible_legacy_Object_trials']==599 and 6589+600+12+599==7800,'compatible-legacy-separated')
  need(v['global_release'] is False and v['O2A_released'] is False and v['final_sealed'] is True and v['final_trials']==0 and v['final_total']==35200,'summary-closed-final-and-O2A')
  need(v['Goal_remaining1000_HOLD'] is False and v['Goal_remaining1000_acceptance_pending'] is True and v['Goal_old200_HOLD'] is True and v['Goal_fixed30_observations_complete'] is False,'Goal-scope-specific-holds')
  need(v['registered_formal_allocations']==278 and v['allocated_GPU_seconds']==1995402 and v['allocated_GPU_hours']==1995402/3600 and v['cost_final_for_current_registered_set'] is False and v['newly_accounted_GPU_seconds']==934,'summary-running-lower-bound')
  need(v['new_GPU_jobs']==v['active_registered_GPU_jobs']==IDS and v['actual_running_allocated_GPUs']==5 and v['capacity']==obs['capacity'],'summary-exact-five')
 validate_summary(summary);recursive_refs(summary)
 for field,value in [('new_complete_batch_rows_accepted',1000),('Goal_fixed30_observations_complete',True),('Goal_old200_HOLD',False),('global_release',True),('O2A_released',True),('cost_final_for_current_registered_set',True)]:
  bad=copy.deepcopy(summary);bad[field]=value;reject('summary-'+field,lambda b=bad:validate_summary(b))
 # Existing original science and independent approvals are inherited, not rerun.
 ackreview=rd(E+'/Goal_ACK_independent/independent_review.json','8567a9f95a3c92004105a50a5779db76710612013d4d8c853dc4d2dc741fcbf5')
 need(ackreview['status']=='passed_real_transaction_evidence' and ackreview['blockers']==[] and ackreview['state_sha256']==BEFORE,'inherited-ACK-review-binds-before-state')
 need(ackreview['real_submissions_verified']==ackreview['original_ACK_reconciliations_verified']==ackreview['real_release_attempts_verified']==5 and ackreview['checks']==1558,'all-five-ACKs-previously-independently-reconstructed')
 runtime=rd(E+'/Goal_runtime_independent/independent_review.json','391b83925668927dfa69a4aa0dffd2a7afe2fb862d53cf009b1ff19871b4bc72')
 author=rd(E+'/Goal_runtime_author/author_readiness.json','375b95f12011a96bbc0fbeba402e7550c5b7ee0a1a4b12d41c1ce3ea24bd81d9')
 need(runtime['status']=='passed' and runtime['blockers']==[] and runtime['total_counted_checks']==1970 and runtime['CPU_replay_checks']==author['CPU_check_count']==1365,'1970-independent-1365-author-separate')
 need(runtime['independent_agent']=='/root/spatial588_recovery_audit_2054' and runtime['real_GPU_acceptance'] is False and runtime['scientific_results_accepted']==0,'different-agent-runtime-not-real-science')
 for item in runtime['root_actual_P_capture_refs']:verify_ref(item)
 # All final source publications in both roots; original frozen bytes in R/S.
 pub=rd(B+'/Goal_remaining5_runtime_publication.json','00b108d9042996a887ea4d840bde91f54364da0f6c277cecfe5a8c5830cff17b')
 manifest=rd(PKG+'/package_manifest.json','200dcef220601fd26565bb48106856612853739f486f8374ef91a4967e60692f')
 need(len(pub['source_rows'])==23 and len(manifest['files'])==20 and runtime['package_files']==manifest['files'],'20-runtime-and23-publication-set')
 for row in pub['source_rows']:
  need(row['destinations']==['R','P'],'source-dual-root')
  for root in (R,P):checked(row['path'],row['sha256'],row['bytes'],root)
 need({r['path']:r['sha256'] for r in pub['source_rows'] if r['path'] in manifest['files']}==manifest['files'],'published-map-exact-runtime')
 checked(GATE+'/gateway.py','45003c082efc508249e9ba41aac15639be7c4188d9517ee1717e71f563448f9b')
 checked(GATE+'/scope.json','f44e8cf97e0a9456782ea57ffeb4c4f39e47058b51c320b3947c73bd1a6cf27b')
 inventory=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 need(len(inventory['files'])==173,'frozen173-inventory')
 for n,pin in inventory['files'].items():
  for root in (R,S):checked(n,pin,root=root)
 # Prepared metadata and true per-pair roots remain exactly the actual publication.
 prep=rd(B+'/Goal_remaining5_prepared_invocations.json','45a1fe173f83597a8181f5129a5354bbdf0f49143743eac96de2dff8a418e578')
 need(len(prep['publication_map'])==10 and len(prep['original_invocations'])==5,'five-genuine-invocations-ten-metadata')
 for row in prep['publication_map']:
  for root in (R,P):checked(row['destination'],row['sha256'],root=root)
 for row in prep['original_invocations']:verify_ref(row)
 auth=rd(B+'/Goal_remaining5_root_authorization_publication.json','f199f4e5b04eb2054681a22c99f58ad1e8113e0bd80cddbbb293db52d20042b9')
 need(len(auth['files'])==20 and auth['global_release'] is False,'20-admission-root-files-not-final')
 for row in auth['files']:
  for root in (R,P):checked(row['path'],row['sha256'],row['bytes'],root)
 pindex=rd(B+'/Goal_remaining5_actual_P_index.json','7e449e03818eda3402871b49cf952941f7590318cf640cd32cac96c2ba1f6fad')
 need(len(pindex['captures'])==5,'five-actual-P-captures')
 for row in pindex['captures']:verify_ref(row)
 rd(E+'/Goal_published_interface_independent/independent_review.json','29e8a2ee4692e6c0ab46745d9687347fca5833793d97aecb74ed0658b80b141b')
 # Package archival exact member mappings; no rerun of science/CPU tests.
 for q in sorted((R/E).iterdir()):
  m=q/'delivery_manifest_original.json'
  maps=[q/x for x in ('source_map.json','root_publication_mapping.json') if (q/x).is_file()]
  if not m.is_file() or not maps:continue
  need(len(maps)==1,'unique-package-map:'+q.name)
  mrel=str(m.relative_to(R));mapping=rd(str(maps[0].relative_to(R)));md=rd(mrel)
  private_root=md.get('root',md.get('source_root',mapping.get('source_root')))
  need(isinstance(private_root,str),'package-root:'+q.name)
  if private_root.startswith(str(R)+'/'):private_root=private_root[len(str(R))+1:]
  need(private_root.startswith('.local/'),'private-package-root:'+q.name)
  sources={}
  for row in md['files']:
   n=row['path'];n=n[len(private_root)+1:] if n.startswith(private_root+'/') else n
   need(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts,'package-member-relative')
   n=private_root+'/'+n;need(n not in sources,'unique-source-member');sources[n]=row
  need(len(sources)==md.get('file_count',len(sources))==len(mapping['files']),'all-package-members:'+q.name)
  target_names=set()
  for row in mapping['files']:
   src=row['source'];dst=row.get('destination',row.get('path'))
   need(src in sources and row['sha256']==sources[src]['sha256'] and row['bytes']==sources[src]['bytes'],'archive-source-member-identity:'+q.name)
   need(dst.startswith(str(q.relative_to(R))+'/') and dst not in target_names,'archive-exact-destination:'+q.name);target_names.add(dst)
   checked(dst,row['sha256'],row['bytes'])
  mb=h(m)
  if mapping.get('manifest_sha256'):need(mapping['manifest_sha256']==mb,'archive-original-manifest-pin:'+q.name)
  if mapping.get('source_manifest'):need(mapping['source_manifest']['sha256']==mb,'archive-source-manifest-pin:'+q.name)
  PACKAGES.append(dict(name=q.name,file_count=len(sources),original_manifest=ref(mrel),mapping=ref(str(maps[0].relative_to(R)))))
 # Root-authored gateway archive has file-relative members.
 gm=rd(E+'/Goal_gateway_root_author/delivery_manifest.json','e079a02afa7b6595bd45ef2f5843897ba4b129091d3f090cdc9f5198c0c981bb')
 for row in gm['files']:checked(E+'/Goal_gateway_root_author/'+row['path'],row['sha256'],row['bytes'])
 # Documentation: new prefix exact and old bytes retained.
 prefix=None
 for n,change in receipt['documentation_changes'].items():
  b=checked(n,change['after_sha256']).read_bytes();end='正常作业留后续监督，不持续轮询。\n\n'.encode();at=b.index(end)+len(end)
  head,tail=b[:at],b[at:];need(digest(tail)==change['before_sha256'],'old-doc-byte-suffix:'+n)
  if prefix is None:prefix=head
  need(head==prefix,'identical-new-doc-prefix:'+n)
 text=prefix.decode()
 for v in ['7800/8800','6589 current','Long600','Spatial12','Object599','400唯一初态','本轮新增验收0','1995402','554.278333','下界','1365','1970','尚未采集','原因未明','final仍0/35200']:
  need(v in text,'doc-supported-claim:'+v)
 for jid in IDS:need(jid in text,'doc-job:'+jid)
 blocking=checked('docs/正式下游阻塞登记_20261021T0449.md').read_text()
 need('122项/10拒绝' in blocking and '仍需独立审计' in blocking and '运行期布尔收据不代替终验' in blocking and '新失败只作有界诊断' in blocking,'blocking-limits-accurate')
 for n in (PKG+'/README.md',GATE+'/README.md'):
  t=checked(n).read_text()
  for v in ['5×200','禁止重复提交或自动重试','不等于GPU或科学终验','独立终审后root接纳','共享writer锁/CAS','全模式8槽','一次release']:need(v in t,'README-bound:'+n+':'+v)
 goal30=rd(E+'/Goal_fixed30_design/Goal_fixed30_design.json','eaf63772f9a58bda0384cf4554fab881875a0ccf6e7ba41e6c14d37c98e9af44')
 design=rd(E+'/Goal_fixed30_design/CPU_design_report.json','c71c034de500ca2a2a3f4e90b512bc9648902c928a178e4cf20d2663e4d02399')
 need(goal30['actual_observations_collected']==0 and goal30['GPU_submission_authorized'] is False and goal30['O2A_or_components_authorized'] is False,'Goal30-not-collected-or-authorized')
 need(len(goal30['observation_slots'])==30 and goal30['method_ids']==['dense'] and goal30['maximum_attempts_proposed']==1,'Goal30-fixed-design-only')
 need(design['check_count']==122 and design['GPU_submissions']==0 and len(design['blockers'])==7,'Goal30-author-CPU-gaps-not-independent-admission')
 # Git: immutable current index, exact 710 required + three audit files; read blobs without index writes.
 need(h(R/'.git/index')==INDEX and git('rev-parse','HEAD').decode().strip()==HEAD,'exact-precommit-index-and-HEAD')
 required=rd(B+'/git_required_files_v1.json',REQ)
 req={r['path']:r for r in required['files']};need(len(req)==len(required['files'])==710,'710-unique-required-files')
 staged=[n for n in git('diff','--cached','--name-only','-z').decode().split('\0') if n]
 extras={B+'/'+n for n in ('git_required_files_v1.json','git_index_guard_v1.json','git_whitespace_diagnostic_v1.json')}
 need(len(staged)==713 and set(staged)==set(req)|extras,'exact713-stage-set')
 entries={}
 for line in git('ls-files','--stage','-z').split(b'\0'):
  if not line:continue
  meta,n=line.split(b'\t',1);mode,oid,stage=meta.decode().split();name=n.decode()
  need(stage=='0','no-index-conflict:'+name);entries[name]=(mode,oid)
 stage_rows=[]
 for n in staged:
  need(n in entries and entries[n][0]=='100644','staged-regular-file:'+n)
  need(not n.startswith('.local/') and '/raw_runtime/' not in n and '/observer/blobs/' not in n and not n.endswith(('.pt','.pth','.safetensors','.bin')),'no-weights-loose-raw-private:'+n)
  r=ref(n);need(r['bytes']<100*(1<<20),'staged-under100MiB:'+n)
  if n in req:need(r==req[n],'required-worktree-exact:'+n)
  stage_rows.append(dict(**r,git_oid=entries[n][1]))
 # Stream all current staged blob bytes and frozen staged files in one readonly git process.
 targets={r['path']:r for r in stage_rows}
 for n,pin in inventory['files'].items():targets.setdefault(n,dict(path=n,sha256=pin,bytes=(R/n).stat().st_size))
 proc=subprocess.Popen(['git','cat-file','--batch'],cwd=R,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 proc.stdin.write(''.join(entries[n][1]+'\n' for n in targets).encode());proc.stdin.close()
 for n,r in targets.items():
  header=proc.stdout.readline().decode().split();need(len(header)==3 and header[1]=='blob' and header[0]==entries[n][1],'git-blob-header:'+n)
  remaining=int(header[2]);need(remaining==r['bytes'],'git-blob-size:'+n);dig=hashlib.sha256()
  while remaining:
   raw=proc.stdout.read(min(1<<20,remaining));need(bool(raw),'git-blob-nontruncated');dig.update(raw);remaining-=len(raw)
  need(proc.stdout.read(1)==b'\n' and dig.hexdigest()==r['sha256'],'git-blob-exact:'+n)
 need(proc.wait()==0,'readonly-catfile-success')
 need(git('diff','--cached','--check')==b'','cached-whitespace-pass')
 guard=rd(B+'/git_index_guard_v1.json','35220f7fbc7f17b6ceca6ec6bd2dc5f29ca298867954c674bd04bb15ee77854f')
 need(guard['status']=='verified_index_archive_delivery' and guard['required_count']==710 and guard['frozen_files_verified_in_worktree_and_index']==173,'original-stage-guard-passed')
 need(guard['archive_verification']=='verified' and guard['restore_verification']=='restored_verified' and len(guard['raw_paths_restored_exactly'])==9,'nine-existing-nonweight-archives-original-restoration-proof')
 need(guard['snapshot_sha256']=='1ec87a42055015a0d0ea5e059d913d3d1de0d7be0870b023a81f7ee774976509','exact-existing-nine-archive-snapshot')
 # Scope of this current index is later than guard: only guard+whitespace receipts were appended.
 need(guard['index_sha256']!=INDEX and guard['ordinary_staged_files_verified']==711,'stage-guard-historical-index-boundary-explicit')
 tarpaths=[n for n in staged if n.endswith('.tar.gz')]
 need(len(tarpaths)==19 and all(n.startswith(E+'/') and '/archives/CPU_' in n for n in tarpaths),'19-explicit-CPU-archives-only')
 # Exact two initial source omissions are known and mandated in pinned finish_v2; not falsely called present in713.
 omitted_sources=[]
 for name,pin in [('scope_bootstrap.py','9ff5d967b8e058c5aff977fdbfac8abdcab741603fdd025d1ba8058d762c38d4'),('scope_bootstrap_v2.py','f37d20dc0e319893b3489c402516368d8808307955124fadfa023038e78c0e69')]:
  n='.local/goal_remaining5_independent_20261021T0449/'+name
  checked(n,pin);omitted_sources.append(dict(source=n,destination=E+'/Goal_identity_entry_sources/'+name,sha256=pin))
 # Static root helpers: no execution, exact hashes and mandatory lock/pins/guard/commit discipline.
 finish=checked('.local/finish_delivery_20261021T0449_v2.py','c2e24fb9991381826561aecfa198b05309ac0d4ba83bab9431d8e9d6c942e3bb').read_text()
 push=checked('.local/push_delivery_20261021T0449.py','6c4c54551f36440e2525b48c3d77eb99b7331a1c8b8dfe036160099e9550ac32').read_text()
 ft=ast.parse(finish);pt=ast.parse(push)
 need(any(isinstance(n,ast.With) and any(isinstance(x.context_expr,ast.Call) and isinstance(x.context_expr.func,ast.Attribute) and x.context_expr.func.attr=='exclusive_lock' for x in n.items) for n in ast.walk(ft)),'finish-shared-lock')
 for token in [INDEX,ST,SUM,REQ,HEAD,'assert expected==staged','assert git("show",":"+n).stdout==(R/n).read_bytes()','guard.check(R,SNAP,SSHA,raw,required)','git("commit"','control_end','assert p.name=="finish_delivery_20261021T0449_v2.jsonl"','len({n.casefold() for n in rows})']:
  need(token in finish,'finish-static-required:'+token[:60])
 for row in omitted_sources:
  need(row['sha256'] in finish and 'Goal_identity_entry_sources/' in finish and 'added.append(out)' in finish,'finish-v2-mandatory-exact-original-control-source')
 need('subprocess' in finish and 'Slurm' not in finish and 'sbatch' not in finish and 'squeue' not in finish,'finish-no-scheduler-operations')
 need('not out.endswith(".tar.gz")' in finish and '"/raw_runtime/" not in out' in finish and '"/attempt01/" not in n' in finish,'finish-new-package-bounds')
 need('a.delivery_report_sha256' in finish and 'a.stage_report_sha256' in finish and 'report.get("blockers")==[]' in finish,'finish-exact-pinned-review-inputs')
 need(finish.index('with ctl.exclusive_lock')<finish.index('package(dp,')<finish.index('guard.check(')<finish.index('git("commit"'),'finish-mutation-order')
 for token in [ST,SUM,'exclusive_lock','sys.stdin.buffer.read()','"scripts/ops/server_github_sync.py"','218bf59be0f28ed145a38ed4196cf02b5a6134fcf8a4531abf127f838cc5f729','"--operation","push"','result["remote_head_after"]==result["local_head"]==a.expected_head','result["credentials_persisted"] is False']:
  need(token in push,'push-static-required:'+token[:60])
 need('--force' not in push and 'password' in push and 'del auth,value' in push,'push-stdin-transient-nonforce-helper')
 need(h(R/'.git/index')==INDEX and h(R/STATE)==ST and h(R/B/'final_summary.json')==SUM,'review-no-index-state-summary-change')
 write('state_diff.json',dict(before_sha256=BEFORE,after_sha256=ST,leaf_change_count=len(state_diff),changes=state_diff))
 write('archival_member_verification.json',dict(packages=PACKAGES,root_gateway_history_files=len(gm['files']),CPU_tar_paths=tarpaths,CPU_tar_verification='exact staged compressed bytes matched archived manifests; member-level semantic restoration inherited from separately pinned Git_static_precheck and original guard, not rerun here'))
 write('staged_files_verified.json',dict(index_sha256=INDEX,head=HEAD,required_sha256=REQ,required_count=710,staged_count=713,files=stage_rows))
 write('input_inventory.json',dict(file_count=len(INVENTORY),files=[INVENTORY[n] for n in sorted(INVENTORY)]))
 report=dict(schema='formal_main_v2',kind='Goal_remaining5_root_delivery_independent_review',status='passed_final_delivery_review',blockers=[],reviewed_by='/root/spatial588_recovery_author_2054',review_scope='actual root integration, archived exact identities, current index and bounded static finish/push helpers; no new science, live scheduler or running raw read',state_sha256=ST,state_before_sha256=BEFORE,summary_sha256=SUM,index_sha256=INDEX,head=HEAD,required_files_sha256=REQ,checks=len(CHECKS),negative_checks=len(NEG),negative_results=NEG,source173_verified=True,frozen_source_roots=['R','S','Git index'],actual_R_P_source_files_verified=23,prepared_original_invocations_verified=5,root_admission_metadata_files_verified=20,original_ACK_transactions_inherited_review_sha256=ackreview and '8567a9f95a3c92004105a50a5779db76710612013d4d8c853dc4d2dc741fcbf5',original_ACK_submission_and_release_counts=[5,5],state_leaf_changes=len(state_diff),prior303_jobs_unchanged=True,accepted_development_trials=7800,planned_development_trials=8800,current_action_trials=6589,compatible_legacy=dict(Long=600,Spatial=12,Object=599),unique_development_initial_states=400,new_scientific_trials_accepted=0,root_completed_arms=72,root_reviewed_arm_updates=360000,registered_formal_allocations=278,saved_GPU_seconds=1995402,saved_GPU_hours=1995402/3600,GPU_cost_final=False,saved_active_job_ids=IDS,saved_actual_running_GPUs=5,saved_observation_UTC=obs['utc'],Goal_fixed30='CPU design only:0 collected;7 production gates remain',old_Goal200_HOLD=True,global_release=False,O2A_released=False,final_sealed=True,final_trials=0,final_total=35200,docs_prepend_old_bytes_preserved=4,new_blocking_document_verified=True,new_source_READMEs_verified=2,archived_packages_verified=len(PACKAGES),required_files_verified=710,staged_files_verified=713,stage_guard_inherited_previous_index_sha256=guard['index_sha256'],current_index_difference_from_guard='only already-described guard and whitespace receipts were added after required+diagnostic stage guard; all713 current blobs and173 original source blobs rechecked read-only',existing_nine_archive_restore_proof='inherited exact original guard snapshot; no redundant restoration run',CPU_archives_staged=19,finish_helper_sha256='c2e24fb9991381826561aecfa198b05309ac0d4ba83bab9431d8e9d6c942e3bb',push_helper_sha256='6c4c54551f36440e2525b48c3d77eb99b7331a1c8b8dfe036160099e9550ac32',finish_and_push_executed_by_reviewer=False,current713_original_control_sources_deferred_to_pinned_finish_v2=omitted_sources,final_delivery_requires_exact_pinned_finish_v2_and_final_guard=True,Git_index_written=False,canonical_state_written=False,live_scheduler_queries=0,running_scientific_raw_read=False,scientific_terminal_reviews_rerun=False,own_plan_authorship_disclosed=True,science_plan_independent_review='inherited separate agent E/Goal_plan_independent; this report is not an independent review of its author own plans',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat())
 write('independent_review.json',report)
 (D/'README.md').open('x').write('Independent actual delivery audit. Exact state 0621504d and summary281cb598 retain7800/8800 accepted, new0. Saved5RUNNING/278allocations/1995402GPU seconds are a lower bound, not science terminal evidence.173 source bytes R/S/index and23 newR/P publication files verified.710 required and713 current staged blobs checked; no index writes. Finish and push helpers are static-reviewed only and must revalidate pins under writer lock. Prior science acceptance and different-agent plan/runtime reviews are inherited, not rerun; this agent authored the plans and does not claim independent plan review. Goal30 remains CPU-only. No Slurm query or running raw read. Reproduce only against pinned current state/index via approved transport; later committed index cannot be treated as the same snapshot.\n')
 files=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=h(p)) for p in sorted(D.iterdir()) if p.is_file() and p.name!='delivery_manifest.json']
 mr=write('delivery_manifest.json',dict(schema='formal_main_v2',root=str(D.relative_to(R)),file_count=len(files),files=files))
 print(json.dumps(dict(status=report['status'],checks=report['checks'],negative_checks=report['negative_checks'],report=ref(str((D/'independent_review.json').relative_to(R))),manifest=mr),ensure_ascii=False))
except BaseException as e:
 if not (D/'failed_review.json').exists():write('failed_review.json',dict(status='review_failed',checks_completed=len(CHECKS),error=repr(e),traceback=traceback.format_exc(),state_sha256=h(R/STATE),index_sha256=h(R/'.git/index'),no_state_or_index_writes=True))
 raise
