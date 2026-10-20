"""Read-only independent review of terminal integration source and exact preview."""
from pathlib import Path
import ast,copy,hashlib,itertools,json,sys,time,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=Path(__file__).parent
V=R/'.local/last_terminals_integration_preview_20261020T1644';SOURCE=R/'.local/integrate_last_terminals_20261020T1644.py'
SPIN='6ec451e21f344496bdcf076205fb24671649ff6f22e65d778fdee6c01d0e8b0a';IPIN='e67484f76f91c492adc1700a022684fb05c51d91cdfb91f262d9cd937d0a1572'
checks=[];refs={};hashes={};t0=time.process_time();wall=time.monotonic()
NEWPAIRS={'libero_goal_k64_seed23','libero_object_k64_seed23'}
ADMITS={'libero_object_k256_seed23','libero_spatial_k64_seed23','libero_object_k64_seed23'}
NEWJOBS={'3050870','3050890','3050901','3050916'}
B='results/formal_main_v2/preflight/heartbeat_20261021T0044'
PUBLICATION_SOURCES={
 'results/formal_main_v2/libero_goal/k64/seed23/training/segment_reviews/3043813_independent.json':'.local/last_two_training_independent_20261020T1644/goal/3043813_independent_review.json',
 'results/formal_main_v2/libero_object/k64/seed23/training/segment_reviews/3044844_independent.json':'.local/last_two_training_independent_20261020T1644/object/independent_review.json',
 'results/formal_main_v2/downstream_reviews/four64_20261020T1644_independent.json':'.local/four_development_independent_20261020T1644/independent_review.json',
 B+'/last_terminals_integration.json':'.local/last_terminals_integration_preview_20261020T1644/summary.json'}
def ck(name,value,detail=None):
 checks.append({'name':name,'passed':bool(value),'detail':detail})
 if not value:raise AssertionError(name)
def h(p):
 p=Path(p);st=p.stat();key=(str(p),st.st_size,st.st_mtime_ns)
 if key in hashes:return hashes[key]
 x=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):x.update(b)
 assert p.stat()==st,'file changed during hash '+str(p)
 hashes[key]=x.hexdigest();return hashes[key]
def write(name,x):
 p=D/name
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
 return {'source':str(p.relative_to(R)),'path':name,'sha256':h(p),'bytes':p.stat().st_size}
def readref(ref):
 n=ref['path'];p=R/PUBLICATION_SOURCES.get(n,n);ck('safe metadata ref '+n,not Path(n).is_absolute() and '..' not in Path(n).parts and p.resolve().is_relative_to(R));ck('evidence bytes '+n,h(p)==ref['sha256']);refs[n]={'source':str(p.relative_to(R)),'sha256':h(p),'bytes':p.stat().st_size};return json.loads(p.read_text())
def cmp_untouched(before,after,allowed,label):
 ck(label+' keys',set(after)-set(before)<=set(allowed) and set(before)-set(after)<=set(allowed))
 for k,v in before.items():
  if k not in allowed:ck(label+' preserve '+k,after[k]==v)
def rawdiff(a,b,path=''):
 if type(a)!=type(b):return [{'path':path,'kind':'type_change'}]
 if isinstance(a,dict):
  ret=[]
  for k in sorted(set(a)|set(b)):
   q=path+'/'+k
   if k not in a:ret.append({'path':q,'kind':'added'})
   elif k not in b:ret.append({'path':q,'kind':'removed'})
   else:ret+=rawdiff(a[k],b[k],q)
  return ret
 if isinstance(a,list):
  if a!=b:return [{'path':path,'kind':'list_changed','before_length':len(a),'after_length':len(b)}]
  return []
 return [] if a==b else [{'path':path,'kind':'value_changed','before':a,'after':b}]
def guard(event,args):
 if event in ('subprocess.Popen','os.system','os.exec','os.posix_spawn','socket.connect'):raise RuntimeError('independent integration audit forbids execution/network')
 if event=='open':
  p,mode,flags=args
  if isinstance(p,(str,bytes)):
   path=Path(p).resolve();writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and bool(flags&(1|2|64|512|1024)))
   if writing and not path.is_relative_to(D):raise RuntimeError('production or foreign write blocked '+str(path))
   if not writing and ('/sealed/' in str(path) or path.suffix=='.pruned_init'):raise RuntimeError('sealed values forbidden')
def run():
 sys.dont_write_bytecode=True;sys.addaudithook(guard)
 ck('pinned candidate source',h(SOURCE)==SPIN);ck('pinned preview intent',h(V/'intent.json')==IPIN)
 intent=json.loads((V/'intent.json').read_text());old=json.loads((V/'state_before.json').read_text());new=json.loads((V/'state_after.json').read_text());summary=json.loads((V/'summary.json').read_text())
 ck('preview hashes',h(V/'state_before.json')==intent['state_before_sha256'] and h(V/'state_after.json')==intent['state_after_sha256']);ck('preview source bound',intent['source']=={'path':str(SOURCE.relative_to(R)),'sha256':SPIN})
 for path,pin in intent['publications'].items():ck('publication exact bytes '+path,h(R/PUBLICATION_SOURCES[path])==pin)
 ck('publication exact four set',set(intent['publications'])==set(PUBLICATION_SOURCES))
 f0=old['formal_main_progress'];f=new['formal_main_progress'];a0=old['autonomous_training_v1'];a=new['autonomous_training_v1']
 cmp_untouched(old,new,{'formal_main_progress','autonomous_training_v1','last_root_supervision_snapshot','current_work','next_actions'},'top')
 allowed_f={'completed_training_pairs','new_action_development_verified_by_job','nonLong_development_submissions_1530','root_and_independent_completed_arms','root_and_independent_reviewed_arm_updates','trained_arms','current_action_development_trial_count','completed_development_trials','last_terminals_integration_20261020T1644','latest_new_action_development_verified'}
 cmp_untouched(f0,f,allowed_f,'formal')
 cmp_untouched(a0,a,{'completed_pairs','blocked_pairs','root_terminal_completed_pair_admissions_20261020T1644'},'controller')
 ck('science config and all registry exact unchanged',old['current_authorization']==new['current_authorization'] and old['current_method']==new['current_method'] and old['registered_jobs']==new['registered_jobs'] and old['restrictions']==new['restrictions'])
 ck('all GPU cost exact unchanged',old['current_round_cost']==new['current_round_cost'] and old['previous_round_costs']==new['previous_round_costs'])
 ck('68 to72 and 341000 to360000',f0['root_and_independent_completed_arms']==68 and f['root_and_independent_completed_arms']==72 and f0['root_and_independent_reviewed_arm_updates']==341000 and f['root_and_independent_reviewed_arm_updates']==360000)
 ck('developer totals exact',f0['current_action_development_trial_count']==4400 and f['current_action_development_trial_count']==5200 and f0['completed_development_trials']==5612 and f['completed_development_trials']==6412)
 ck('unique400 unchanged',f['current_action_development_unique_initial_states']==400 and f0['current_action_development_unique_initial_states']==400)
 ck('final and release sealed',not f['test_opened'] and not f['global_release_created'] and f['completed_final_trials']==0 and f['expected_final_trials']==35200)
 ck('summary counters and compatible600',all(summary[k]==v for k,v in {'training_arms':72,'reviewed_arm_updates':360000,'new_training_arms':4,'new_reviewed_updates':19000,'new_development_trials':800,'current_action_development_trials':5200,'compatible_legacy_Long_trials':600,'compatible_development_trials':5800,'all_historical_accepted_development_trials':6412,'unique_development_initial_states':400,'final_trials':0,'new_GPU_submissions':0}.items()))
 ck('summary holds/sealed preserved',summary['Goal_original200_HOLD'] and summary['all_new_Goal_scientific_HOLD'] and summary['final_sealed'] and not summary['global_release'])
 ck('root cost uses same ledger',summary['allocated_GPU_hours']==new['current_round_cost']['allocated_gpu_hours'])
 sref={'path':B+'/last_terminals_integration.json','sha256':h(V/'summary.json')}
 for x in [new['last_root_supervision_snapshot'],f['last_terminals_integration_20261020T1644'],f['latest_new_action_development_verified'],a['root_terminal_completed_pair_admissions_20261020T1644']]:ck('summary reference exact',x==sref)
 suites=('libero_10','libero_spatial','libero_object','libero_goal');matrix={f'{s}_k{k}_seed{seed}' for s,k,seed in itertools.product(suites,(256,128,64),(17,23,41))}
 ck('36 pairs exact matrix',set(f['completed_training_pairs'])==matrix and len(matrix)==36)
 for pair,row in f0['completed_training_pairs'].items():
  if pair not in NEWPAIRS:ck('old training pair preserved '+pair,f['completed_training_pairs'][pair]==row)
 # Independent metadata and selected actual bytes for all72 identities. Never load checkpoint tensors.
 identities=[];allrefs=[]
 for pair in sorted(matrix):
  row=f['completed_training_pairs'][pair];suite,ks,ss=pair.rsplit('_',2);budget=int(ks[1:]);seed=int(ss[4:])
  if 'terminal_root_and_independent_review' in row:
   terminal=row['terminal_root_and_independent_review'];rrref=terminal['root_review'];irref=terminal['independent_review'];ck('terminal full5000 '+pair,terminal['completed_by_arm']=={'A':5000,'B':5000});rr=readref(rrref);ir=readref(irref)
   ck('bulk root specifically names pair '+pair,rr['status']=='accepted_training_integrity_not_scientific_efficacy' and any(x['pair_key']==pair and x['common_update']==5000 and x['independent_review']==irref for x in rr['changes']))
   ck('bulk independent full pair '+pair,ir['pair_key']==pair and ir['status']=='passed' and ir['completed_by_arm']=={'A':5000,'B':5000})
   selected_by_arm={arm:{'expected_sha256':x['best_checkpoint_sha256'],'selected_update':x['best_update'],'validation_metric':x['best_task_macro_teacher_l1']} for arm,x in ir['arms'].items()}
  else:
   rrref={'path':row['root_review'],'sha256':row['root_review_sha256']};irref={'path':row['independent_review'],'sha256':row['independent_review_sha256']};rr=readref(rrref);ir=readref(irref)
   ck('root full pair '+pair,rr['status']=='passed' and rr['completed_by_arm']=={'A':5000,'B':5000} and (rr['suite'],rr['visual_tokens'],rr['seed'])==(suite,budget,seed))
   ck('independent accepted identity '+pair,str(ir['status']).startswith('passed') and (ir.get('suite',suite),ir.get('visual_tokens',budget),ir.get('seed',seed))==(suite,budget,seed))
   selected_by_arm={x['arm']:x for x in row['selected_checkpoints']};ck('two selected arms '+pair,set(selected_by_arm)=={'A','B'})
   if row.get('selected_server_review'):readref({'path':row['selected_server_review'],'sha256':row['selected_server_review_sha256']})
  allrefs.extend([rrref,irref])
  for arm in ('A','B'):
   path=R/f'results/formal_main_v2/{suite}/k{budget}/seed{seed}/training/{arm}/deployment_receipt.json';receipt=json.loads(path.read_text());md=receipt['metadata'];tc=receipt['training_config'];selected=selected_by_arm[arm]
   ck('arm metadata identity '+pair+arm,(md['suite'],md['visual_tokens'],md['seed'],md['arm'])==(suite,budget,seed,arm))
   ck('arm training complete '+pair+arm,receipt['training_complete'] and receipt['completed_updates']==receipt['planned_updates']==5000 and receipt['base_frozen'] and receipt['checkpoint_unchanged'])
   ck('11 original val nodes '+pair+arm,[v['update'] for v in receipt['evaluations']]==list(range(0,5001,500)))
   best=min(receipt['evaluations'],key=lambda x:(x['validation_metric'],x['update']))
   ck('hard teacher task equal selection and early tie '+pair+arm,md['selection_metric']=='task_macro_hard_validation_teacher_l1' and md['update']==best['update']==selected['selected_update'] and md['validation_metric']==best['validation_metric']==selected['validation_metric'])
   ck('same frozen scientific training '+pair+arm,tc['training']['updates']==5000 and tc['training']['effective_batch']==8 and tc['training']['learning_rate']==1e-4 and tc['training']['weight_decay']==0.01 and tc['training']['gradient_clip_norm']==1.0 and tc['training']['optimizer']=='AdamW' and tc['training']['vla_frozen'] and tc['training']['gradient_through_vla'] and tc['future']['horizon']==8 and tc['future']['weight_A']==0 and tc['future']['weight_B']==0.1 and tc['future']['projection_seed']==917 and tc['gate']['alpha_start']==2.0 and tc['gate']['alpha_end']==0.1)
   ck('same action loss '+pair+arm,tc['action_loss']['teacher_l1_weight']==tc['action_loss']['demonstration_l1_weight']==0.5)
   checkpoint=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2')/suite/f'k{budget}'/f'seed{seed}'/arm/'best.pt';beforestat=checkpoint.stat();digest=h(checkpoint)
   ck('selected actual bytes '+pair+arm,digest==receipt['checkpoint_sha256']==selected['expected_sha256'] and checkpoint.stat()==beforestat)
   identities.append({'pair':pair,'arm':arm,'suite':suite,'budget':budget,'seed':seed,'selected_update':best['update'],'selected_checkpoint':{'path':str(checkpoint),'sha256':digest,'bytes':beforestat.st_size},'deployment_receipt':{'path':str(path.relative_to(R)),'sha256':h(path)},'root_review':rrref,'independent_review':irref})
 ck('all72 unique identity and 360000 updates',len(identities)==72 and len({(x['pair'],x['arm']) for x in identities})==72 and 72*5000==f['root_and_independent_reviewed_arm_updates'])
 ck('summary all36 pins complete',sorted(allrefs,key=lambda x:(x['path'],x['sha256']))==sorted(summary['all36_root_and_independent_refs'],key=lambda x:(x['path'],x['sha256'])))
 oi=readref({'path':'results/formal_main_v2/libero_object/k64/seed23/training/segment_reviews/3044844_independent.json','sha256':'9d357b032ae9c8c3d1aa4f901875eec4ef4fca7c2912805c52e114813e3b2150'})
 ck('Object original500 already1000 reviewed',oi['new_reviewed_arm_updates']==9000 and len(oi['historical_dual_review_receipts'])==1 and oi['historical_dual_review_receipts'][0]['completed_by_arm']=={'A':500,'B':500} and f0['object64seed23_continuous_ready']['original500_complete'])
 for key in ('root','independent'):readref(oi['historical_dual_review_receipts'][0][key])
 ck('19000 counts only remainder',sum(t['new_reviewed_arm_updates'] for t in summary['training'])==19000 and {t['pair']:t['new_reviewed_arm_updates'] for t in summary['training']}=={'libero_goal_k64_seed23':10000,'libero_object_k64_seed23':9000})
 ck('exact three old blocked pairs',set(a0['blocked_pairs'])==ADMITS and not a['blocked_pairs'] and set(a['completed_pairs'])-set(a0['completed_pairs'])==ADMITS and set(a['completed_pairs'])==matrix)
 for pair,row in a0['completed_pairs'].items():ck('machine old entry preserved '+pair,a['completed_pairs'][pair]==row)
 admissions={x['pair']:x for x in summary['controller_completion_admissions']};ck('summary three admissions',set(admissions)==ADMITS)
 for pair in sorted(ADMITS):
  row=a['completed_pairs'][pair];entry=admissions[pair];ck('original blocked verbatim '+pair,entry['retained_original_block']==a0['blocked_pairs'][pair] and entry['failed_history_not_erased'] and entry['new_machine_review_claimed'] is False)
  ck('inherited only never machine audit claim '+pair,row['verification_origin']=='inherited_root_and_independent_review' and row['new_machine_review_claimed'] is False and row['selected_checkpoints_verified'] and row['inherited_checkpoint_bytes_rechecked_by_root'] and row['completed_by_arm']=={'A':5000,'B':5000} and row['validation_updates']==list(range(0,5001,500)))
  ck('admission evidence and actual identity match '+pair,row['evidence_refs']==entry['root_and_independent'] and row['selected_checkpoint_checks']==entry['selected_actual_bytes'])
  for ref in row['evidence_refs']:readref(ref)
  for x in row['selected_checkpoint_checks']:
   match=next(y for y in identities if y['pair']==pair and y['arm']==x['arm']);ck('actual admission hash '+pair+x['arm'],x['path']==match['selected_checkpoint']['path'] and x['sha256']==match['selected_checkpoint']['sha256'] and x['bytes']==match['selected_checkpoint']['bytes'] and x['exists'] and x['stable_during_hash'])
 # Four new accepted development shards; originals and denominator keys stay intact.
 olddev=f0['new_action_development_verified_by_job'];newdev=f['new_action_development_verified_by_job'];ck('exact four new dev ids',set(newdev)-set(olddev)==NEWJOBS and set(olddev)<=set(newdev))
 for jid,row in olddev.items():ck('old dev preserved '+jid,newdev[jid]==row)
 devsource=readref({'path':'results/formal_main_v2/downstream_reviews/four64_20261020T1644_independent.json','sha256':'d3170418334cc545bd760472463a7e165a44b233393b81dff76f5eea72c397ce'})
 ck('fourdev independent passed exact scope',devsource['status']=='passed' and set(devsource['jobs'])==NEWJOBS and devsource['totals']=={'allocated_gpu_seconds':8708,'chunks':12551,'executed_actions':97621,'trials':800} and not devsource['new_held_job_ids'])
 dev_counts=[];unique={};registry={str(x['job_id']):x for x in new['registered_jobs']};ck('registry job identities unique',len(registry)==len(new['registered_jobs']))
 for jid,entry in newdev.items():
  rr=readref(entry['root_review']);ck('accepted dev root '+jid,rr['status']=='passed' and rr['scientific_complete'] and rr['completed_trials']==entry['completed_trials'])
  unique.setdefault(rr['suite'],set())
  for pair in rr['reconstructed_summary']['paired_AB'].values():unique[rr['suite']].update(x['state_trial_id'] for x in pair['results'])
  if jid not in NEWJOBS:continue
  v=devsource['jobs'][jid];ck('new dev exact totals and identity '+jid,entry['completed_trials']==v['trials']==200 and entry['unique_initial_states']==v['unique_initial_states']==100 and entry['suite']==v['suite'] and entry['seed']==v['seed'] and entry['visual_tokens']==64)
  for ek,vk in [('successes','successes'),('B_minus_A_percentage_points','B_minus_A_pp'),('paired_outcomes','discordance'),('per_task','per_task'),('raw_ledger','raw_ledger'),('full_action_chunks','full_action_chunks'),('executed_control_actions','executed_control_actions'),('offline_validation_diagnostics','offline_validation_diagnostics'),('t0_token_diagnostics','t0_token_diagnostics')]:ck('independent copied member '+jid+ek,entry[ek]==v[vk])
  ck('new dev source consumer/final boundaries '+jid,v['full_original_consumer_reconstruction_passed'] and v['raw_start_result_pairs_exact'] and not entry['O2A_complete'] and not entry['scientific_final_release'])
  ck('GPU allocation already in unchanged global ledger '+jid,entry['GPU_seconds']==v['allocated_GPU_seconds']==registry[jid]['elapsed_seconds']*registry[jid]['gpus'])
  raw=entry['raw_ledger'];path=R/raw['path']
  if not path.exists():path=P/raw['path']
  ck('raw ledger exact '+jid,path.stat().st_size==raw['bytes'] and h(path)==raw['sha256'])
  records=[json.loads(line) for line in path.read_text().splitlines() if line.strip()];results=[x for x in records if x.get('event')=='result'];starts=[x for x in records if x.get('event')=='start'];ck('raw200 start results '+jid,len(results)==len(starts)==200 and [x['trial_id'] for x in results]==[x['trial_id'] for x in starts] and len({x['trial_id'] for x in results})==200)
  successes={method:sum(bool(x['success']) for x in results if x['method']==method) for method in {x['method'] for x in results}};ck('raw success recalculation '+jid,successes==entry['successes']);ck('raw100 unique states '+jid,len({x['state_trial_id'] for x in results})==100)
  dev_counts.append({'job_id':jid,'trials':len(results),'successes':successes,'GPU_seconds':entry['GPU_seconds']})
 ck('four suite400 unique', {k:len(x) for k,x in unique.items()}=={s:100 for s in suites})
 ck('current raw denominator5200',sum(x['completed_trials'] for x in newdev.values())==5200 and '3049679' not in newdev and '3052166' not in newdev)
 submissions0={x['job_id']:x for x in f0['nonLong_development_submissions_1530']};submissions={x['job_id']:x for x in f['nonLong_development_submissions_1530']}
 ck('same four submission records',set(submissions)==set(submissions0)==NEWJOBS)
 for jid,row in submissions.items():
  cmp_untouched(submissions0[jid],row,{'completed_trials_accepted','observed_status','scientific_terminal_acceptance_pending','terminal_root_review','terminal_independent_review'},'submission '+jid)
  ck('terminal submission update only '+jid,row['completed_trials_accepted']==200 and row['observed_status']=='COMPLETED' and row['scientific_terminal_acceptance_pending'] is False and row['terminal_root_review']==newdev[jid]['root_review'] and row['terminal_independent_review']==newdev[jid]['independent_review'])
 ck('3052166 one original registration, no replay',sum(str(x['job_id'])=='3052166' for x in new['registered_jobs'])==1 and registry['3052166']['downstream_gateway']['automatic_retry'] is False and not registry['3052166']['resume'] and summary['existing_Object256s23_development_job']=='3052166')
 # Static source inspection: no invocation of candidate; only its audited AST is inspected.
 tree=ast.parse(SOURCE.read_text());calls=[x for x in ast.walk(tree) if isinstance(x,ast.Call)]
 ck('source no Slurm/process/Git execution',not any(isinstance(n.func,ast.Name) and n.func.id in ('eval','exec','system','sbatch','scancel') for n in calls) and not any(isinstance(n.func,ast.Attribute) and n.func.attr in ('Popen','system','sbatch','scancel') for n in calls))
 locks=[x for x in ast.walk(tree) if isinstance(x,ast.With) and any(isinstance(i.context_expr,ast.Call) and ast.unparse(i.context_expr.func)=='c.exclusive_lock' for i in x.items)]
 ck('one shared writer lock encloses transaction',len(locks)==1 and 'results/experiment_supervisor/.writer.lock' in ast.unparse(locks[0]))
 atomic=[x for x in calls if isinstance(x.func,ast.Attribute) and ast.unparse(x.func)=='c.atomic_json'];ck('single CAS atomic write only after --apply branch',len(atomic)==1 and ast.unparse(atomic[0])=='c.atomic_json(R / sn, s, before)' and any(isinstance(x,ast.If) and ast.unparse(x.test)=='not opt.apply' and atomic[0] in list(ast.walk(ast.Module(body=x.orelse,type_ignores=[]))) for x in ast.walk(locks[0])))
 ck('state-before retained before CAS','put(B + \'/last_terminals_state_before.json\', statebytes)' in ast.unparse(locks[0]))
 # Exact preview plus independent immutable-subtree mutation sentinels.
 negative=[]
 def safetycheck(x):
  assert x['registered_jobs']==old['registered_jobs'];assert x['current_round_cost']==old['current_round_cost'];assert x['autonomous_training_v1']['owner_id']==a0['owner_id'];assert not x['formal_main_progress']['test_opened'];assert x['formal_main_progress']['completed_final_trials']==0;assert x['formal_main_progress']['root_and_independent_reviewed_arm_updates']==360000;assert '3049679' not in x['formal_main_progress']['new_action_development_verified_by_job'];assert all(row['new_machine_review_claimed'] is False for pair,row in x['autonomous_training_v1']['completed_pairs'].items() if pair in ADMITS)
 for name in ['cost_duplicate','owner_changed','open_final','wrong_update_increment','admit_Goal200','claim_machine_review','duplicate_3052166']:
  mutated=copy.deepcopy(new)
  if name=='cost_duplicate':mutated['current_round_cost']['allocated_gpu_seconds']+=8708
  elif name=='owner_changed':mutated['autonomous_training_v1']['owner_id']='other'
  elif name=='open_final':mutated['formal_main_progress']['test_opened']=True
  elif name=='wrong_update_increment':mutated['formal_main_progress']['root_and_independent_reviewed_arm_updates']+=1000
  elif name=='admit_Goal200':mutated['formal_main_progress']['new_action_development_verified_by_job']['3049679']={}
  elif name=='claim_machine_review':mutated['autonomous_training_v1']['completed_pairs']['libero_object_k64_seed23']['new_machine_review_claimed']=True
  else:mutated['registered_jobs'].append(copy.deepcopy(registry['3052166']))
  try:safetycheck(mutated)
  except AssertionError:negative.append({'name':name,'rejected':True})
  else:raise AssertionError('negative not rejected '+name)
 frozen=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text())['files'];ck('173 exact frozenR/S',len(frozen)==173 and all(h(base/path)==pin for base in (R,S) for path,pin in frozen.items()))
 identity_ref=write('selected72_identities.json',{'identities':identities,'actual_checkpoint_bytes_hashed':72,'tensors_loaded':False,'weights_copied':False})
 diffref=write('exact_state_diff.json',{'before_sha256':intent['state_before_sha256'],'after_sha256':intent['state_after_sha256'],'changes':rawdiff(old,new),'off_scope_changes':[]})
 evref=write('read_evidence.json',refs)
 result={'schema':'formal_main_v2','kind':'independent_last_terminals_preapply_review','status':'passed_exact_preview_only_not_applied','source':intent['source'],'preview':{'directory':str(V.relative_to(R)),'intent_sha256':IPIN,'state_before_sha256':intent['state_before_sha256'],'state_after_sha256':intent['state_after_sha256'],'summary_sha256':h(V/'summary.json')},'checks':checks,'check_count':len(checks),'negative_cases':negative,'actual_selected72_identity_evidence':identity_ref,'exact_state_diff':diffref,'read_evidence':evref,'new_root_independent_arms':4,'new_reviewed_updates':19000,'new_development_trials':800,'result_totals':{'training_arms':72,'reviewed_updates':360000,'current_development':5200,'compatible_development':5800,'historical_development':6412,'unique_initial_states':400,'final_trials':0},'controller_admissions_original_blocks_preserved':True,'new_machine_review_claimed':False,'Object500_not_double_counted':True,'existing_cost_not_added':True,'existing_3052166_one_registration':True,'Goal_original200_HOLD_preserved':True,'new_Goal_science_HOLD_preserved':True,'production_state_modified':False,'Git_or_Slurm_calls':0,'GPU_calls':0,'CPU_seconds':time.process_time()-t0,'wall_seconds':time.monotonic()-wall,'limits':'Source reviewed statically and exact preview independently checked; candidate not executed by auditor. Root --apply must use shared lock and fresh CAS. Final state/actual published bytes require separate independent postcheck; training completion does not authorize final evaluation.'}
 print(json.dumps({'report':write('preapply_review.json',result),'checks':len(checks),'negative_cases':len(negative),'CPU_seconds':result['CPU_seconds']}))
if __name__=='__main__':
 try:run()
 except BaseException as e:
  write('failure_v1.json',{'status':'independent_review_failed','type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'checks':checks,'CPU_seconds':time.process_time()-t0});raise
