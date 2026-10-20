"""Independent actual-P closure, source derivation, dispatch and storage audit.
Read only production. Never calls production main/execute or scheduler. Weight
bytes are hashed only for the two exact already-selected Goal checkpoints.
"""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,re,shutil,sys,time,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=R/'.local/goal_paired_independent_20261020T2156';A=R/'.local/goal_gate_integration_20261020T2156';PKG='scripts/ops/formal_goal_paired_input_gate_v1'
MSHA='7e7da3f5b514102f08d105677e1dff504989aaf6c647f320405526d1fd2982ec';ESHA='1e8caecfda12f1f0a1d55a5652e9c300d25dff5fb0cf071cf4555a68b8605977';CSHA='104ebf29df89a91e6156d0c3acead203df95234a9393ba7c6545965a8ba9d669'
DISPATCH='.local/goal_paired_dispatch_20261020T2156_v3.py';DSHA='d3a8a445f5d0d13dfd93440256a8567fabfbb82a598bec6deb363bfd8b09ca17';SOURCEINV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';INVH='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
checks=[];seen={};began=time.perf_counter();cpu=time.process_time()
def ck(n,v,detail=None):
 checks.append({'name':n,'passed':bool(v),'detail':detail})
 if not v:raise AssertionError(n)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def watch(p,expected=None):
 p=Path(p);h=sha(p)
 if expected is not None:ck('SHA:'+str(p),h==expected)
 if str(p) in seen:ck('stable:'+str(p),seen[str(p)]['sha256']==h)
 seen[str(p)]={'sha256':h,'bytes':p.stat().st_size};return {'path':str(p),'sha256':h}
def read(p,pin=None):watch(p,pin);return json.loads(Path(p).read_bytes())
def write(name,obj):
 p=D/name
 with p.open('x') as f:json.dump(obj,f,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2);f.write('\n')
 return {'path':str(p.relative_to(R)),'sha256':sha(p)}
def load(p,name,pin):
 watch(p,pin);sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def reject(n,fn):
 try:fn()
 except (ValueError,RuntimeError):ck(n,True)
 else:ck(n,False)
def audit_guard(event,args):
 if event in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'):raise RuntimeError('no process/network during independent actual-P check')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  if any('sealed' in x.lower() for x in p.parts) or (p.name=='panel.json' and 'final' in p.parts) or p.name=='init_states_test.json':raise RuntimeError('no final values')
  mode,flags=args[1:3];w=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if w and not p.is_relative_to(D):raise RuntimeError('write outside independent private directory')
def main():
 sys.dont_write_bytecode=True;os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['CUDA_VISIBLE_DEVICES']='';sys.addaudithook(audit_guard)
 manifest=read(P/PKG/'package_manifest.json',MSHA);watch(R/PKG/'package_manifest.json',MSHA);watch(A/'package/package_manifest.json',MSHA)
 ck('exact_eight_file_closure',set(manifest['files'])=={PKG+'/'+n for n in ['entry.py','observer_v3.py','ast_observer_v2.py','paired_input_gate_v1.py','ast_gate_v2.py','config.json','prefix58.json','run.slurm']})
 for rel,h in manifest['files'].items():
  for root in [R,P]:watch(root/rel,h);ck('no_symlink:'+str(root/rel),(root/rel).resolve()==root/rel and not (root/rel).is_symlink())
  watch(A/'package'/Path(rel).name,h)
 entry=load(P/PKG/'entry.py','_goal_ind_actual_P_entry',ESHA);config=read(P/PKG/'config.json',CSHA);entry.validate_config(config)
 ck('production_runtime_namespace_unredirected',entry.P==P and entry.R==R and entry.S==S and entry.ENTRY==P/PKG/'entry.py')
 inv,wrapper,ctx,legacy=entry.prepare_original();prefix=read(P/PKG/'prefix58.json',entry.PREFIX_SHA)['rows'];prefixproof=entry.validate_prefix(inv,legacy,prefix);ck('actual_P_original_entry_and_two_selected_checkpoints_verified',True)
 ck('exact58_order_29states',prefixproof['original_fixed58_identity_order'] and prefixproof['unique_development_states']==29)
 for path,pin in inv['watched_files'].items():watch(path,pin)
 watch(entry.ORIGINAL,entry.ISHA);watch(entry.WRAPPER,entry.WSHA);watch(entry.LEGACY,entry.LSHA)
 frozen=read(R/SOURCEINV,INVH)['files'];ck('173frozen',len(frozen)==173)
 for root in [R,S,R/'snapshots/formal_main_v2_run_564be0995e']:
  for rel,h in frozen.items():watch(root/rel,h)
 old=R/'scripts/ops/formal_goal_prefix58_observer_v2';deriv=read(A/'source_derivation.json','8fa4acec52c6f6c0a7d47ce4000e9a6f8f26c007df2a00216a117fb75a219506');oldtext=(old/'entry.py').read_text();newtext=(P/PKG/'entry.py').read_text();watch(old/'entry.py',deriv['old_entry_sha256'])
 for name in deriv['unchanged_protected_entry_functions']:
  x=next(n for n in ast.parse(oldtext).body if isinstance(n,ast.FunctionDef) and n.name==name);y=next(n for n in ast.parse(newtext).body if isinstance(n,ast.FunctionDef) and n.name==name);ck('protected_original_AST:'+name,ast.dump(x,include_attributes=False)==ast.dump(y,include_attributes=False))
 for name in deriv['copied_exact_files']:ck('exact_old_'+name,(old/name).read_bytes()==(P/PKG/name).read_bytes())
 for filename,original,key in [('entry.py',old/'entry.py','entry_replacements'),('paired_input_gate_v1.py',R/'.local/goal_cpu_gate_20261020T2054/paired_input_gate_v1.py','gate_replacements'),('ast_gate_v2.py',R/'.local/goal_cpu_gate_20261020T2054/ast_gate_v2.py','AST_engine_replacements')]:
  watch(original);s=original.read_text()
  for c in deriv[key]:ck('derivation_unique:'+filename+':'+str(c['old'][:45]),s.count(c['old'])==c['occurrences']);s=s.replace(c['old'],c['new'])
  ck('derived_exact_full_file:'+filename,s.encode()==(P/PKG/filename).read_bytes())
 gate=load(P/PKG/'paired_input_gate_v1.py','_goal_ind_real_gate',manifest['files'][PKG+'/paired_input_gate_v1.py']);ck('GateAbort_outside_Exception',issubclass(gate.GateAbort,BaseException) and not issubclass(gate.GateAbort,Exception))
 en=ast.parse(newtext);execute=next(n for n in en.body if isinstance(n,ast.FunctionDef) and n.name=='execute');gates=[n for n in ast.walk(execute) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='PairedInputGate'];ck('one_production_gate_fixture_false',len(gates)==1 and len(gates[0].keywords)==1 and gates[0].keywords[0].arg=='allow_cpu_fixture' and gates[0].keywords[0].value.value is False)
 ck('production_entry_requires_no_sink',"observer.sink is None" in newtext and 'a.stop_after=58' in newtext and "=={'output','stop_after'}" in newtext)
 ck('one_original_runner_call_no_replay',len([n for n in ast.walk(execute) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='legacy' and n.func.attr=='run'])==1)
 ck('entry_no_submission_API',not any(t in newtext for t in ['sbatch(',"['sbatch'",'subprocess.','scancel']))
 ck('scientific_HOLD_cost_one_allocation',"scientific_trials_added=0,original_goal200_HOLD=True,new_Goal_science_HOLD=True,final_release=False" in newtext and 'Charge complete Slurm allocation once' in newtext)
 # Independently derive budget from original real58 raw observations, preserving all queries.
 sample=P/'results/formal_main_v2/engineering/goal_prefix58_20261020T1825/attempt01/observer/events.jsonl';watch(sample);events=[json.loads(x) for x in sample.read_text().splitlines()];obs=[x for x in events if x.get('observation_arrays')]
 obbytes=max(sum(v['bytes'] for v in x['observation_arrays'].values()) for x in obs);simbytes=max(sum(v['bytes'] for v in x.get('sim_array_blobs',{}).values()) for x in events);rngbytes=max(x.get('global_rng',{}).get('bytes',0) for x in events);linebytes=max(len(json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()) for x in events)
 nonquery=max(sum(1 for x in events if x.get('ordinal')==i and x.get('phase') not in ('t0_query_before','t0_query_after')) for i in range(1,59));captures=58*38*2+58*nonquery+32
 upper=captures*(obbytes+simbytes+rngbytes)+captures*max(65536,linebytes*4)+58*300*4096+256*(1<<20);required=upper+(1<<30)
 ck('storage_bound_no_dedup_no_query_dropping',upper==3289879290 and required==4363621114)
 storage=read(A/'CPU_production_preflight01/storage_bound.json','46d3af434e0496574dab46c09ccf5bf79d56708a85e10f68dddd7f631ccc41a7');ck('author_bound_independently_reproduced',upper==storage['total_estimated_upper_bytes'] and required==storage['required_free_including_1GiB_margin'])
 free=shutil.disk_usage(P).free;ck('current_P_free_satisfies_full_recording_plus_margin',free>=required)
 ds=(R/DISPATCH).read_text();dispatch=load(R/DISPATCH,'_goal_ind_dispatch_no_main',DSHA);tree=ast.parse(ds);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 ck('one_sbatch_submit',len([n for n in ast.walk(main) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='submit'])==1)
 for phrase in ["with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock')", "s['pending_submission'] is None", "ctl['reserved_GPU_slots']==0", "ctl['root_submission_hold'] is None", "len(cap['occupied'])+1<=8", "not cap['unknown']", "not cap['findings']", "require(not held", "free_bytes>=4363621114", "'--hold'", "'--no-requeue'", "'intent_persisted_before_sbatch'", "'unknown sbatch: reconcile exact token without resend'", "'acknowledged_held_job_not_released'", "'registered_held_pending_release'", "'release uncertain: pending retained'", "f==old['formal_main_progress']", "s['current_round_cost']==old['current_round_cost']"]:ck('dispatch_guard:'+phrase,phrase in ds)
 ck('pending_before_sbatch_before_ACK_registration_before_release_before_clear',ds.index("s['pending_submission']=copy.deepcopy(pending)")<ds.index('result=slurm.submit(argv)')<ds.index("s['registered_jobs'].append(job)")<ds.index("['scontrol','release',jid]")<ds.index("s['pending_submission']=None"))
 # Test actual_identity purely, no scheduler command is called.
 fields={'JobId':'999999','JobName':'cti-goal-paired-input','Comment':'token','Requeue':'0','TimeLimit':'00:30:00','Partition':'L40','Account':'p_p15016','ExcNodeList':'gpu4020','NumCPUs':'7','MinMemoryNode':'64G','Command':str(P/PKG/'run.slurm'),'WorkDir':str(S),'Restarts':'0','QOS':'cpu-500_core-l40-8_card-a800-8_card','TresPerNode':'gres:gpu:l40:1','JobState':'PENDING','Reason':'JobHeldUser'}
 dispatch.actual_identity(fields,'999999','token',True);ck('pure_held_identity_positive',True)
 for key,value in [('JobId','999998'),('Comment','different'),('Requeue','1'),('Restarts','1'),('NumCPUs','8'),('TimeLimit','01:00:00'),('TresPerNode','gres:gpu:l40:2'),('Reason','Resources'),('Command','/tmp/other')]:
  bad=dict(fields);bad[key]=value;reject('held_identity_reject_'+key,lambda bad=bad:dispatch.actual_identity(bad,'999999','token',True))
 # Execute just the new all-mode collision guard extracted from the actual dispatch AST.
 block=next(n for n in main.body if isinstance(n,ast.With));seq=block.body;idx=next(i for i,n in enumerate(seq) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='active_registered' for t in n.targets));snippet=ast.Module(body=copy.deepcopy(seq[idx:idx+2]),type_ignores=[]);code=compile(ast.fix_missing_locations(snippet),'<exact-v3-all-mode-guard>','exec')
 for tag,job in [('development_suite',{'suite':'libero_goal','mode':'development'}),('engineering_stage',{'stage_key':'goal_prefix','mode':'engineering'}),('legacy_runroot',{'run_root':'/path/libero_goal/development','mode':'evaluate'}),('jobname',{'name':'cti-goal-observer','mode':'engineering'})]:
  ns={'s':{'registered_jobs':[{'job_id':'42',**job}]},'cap':{'occupied':['42'],'active_pairs':{}},'require':dispatch.require};reject('all_mode_collision_'+tag,lambda ns=ns:exec(code,ns))
 ns={'s':{'registered_jobs':[{'job_id':'42','suite':'libero_object','mode':'development'}]},'cap':{'occupied':['42'],'active_pairs':{}},'require':dispatch.require};exec(code,ns);ck('other_suite_does_not_block_goal_gate',True)
 ck('old3053440_closed_diagnostic_HOLD',"elapsed_seconds']==803" in ds and "completed_diagnostic_not_reproduced_scientific_HOLD" in ds and "terminal_review_status']=='HOLD_initial_observation_mismatch'" in ds)
 # Raw independent replay outputs must exist and be successful, not author intermediate reports.
 core=read(D/'independent_core/report.json');outer=read(D/'independent_outer/report.json');ck('independent_core66_actual_P',core['status']=='passed_CPU_source_candidate_only' and core['check_count']==66 and all(x['passed'] for x in core['checks']));ck('independent_outer138_actual_P',outer['status']=='passed_CPU_production_outer_integration' and outer['check_count']==138 and all(x['passed'] for x in outer['checks']))
 for path,x in seen.items():ck('final_stable:'+path,sha(path)==x['sha256'])
 cuda=sys.modules.get('torch.cuda');ck('no_CUDA_initialized',cuda is None or not cuda.__dict__.get('_initialized'))
 evidence=write('actual_P_evidence.json',{'files':seen,'prefix_proof':prefixproof,'actual_package_manifest':manifest,'actual_original_source_and_checkpoint_verification':True,'module_namespace_redirected':False,'no_GPU_execution':True})
 detailed=write('detailed_review.json',{'status':'passed_CPU_actual_P_and_dispatch_only','reviewed_by':'independent','review_agent':'/root/spatial588_recovery_audit_2054','checks':checks,'check_count':len(checks),'actual_P_evidence':evidence,'independent_core_assertions':66,'independent_outer_assertions':138,'actual_native_MjData_in_outer':True,'outer_policy_model_loader_explicitly_synthetic':True,'full_GPU_or_LIBERO_environment_executed':False,'storage':{'upper_bytes':upper,'required_bytes_including_margin':required,'free_bytes_at_check':free,'not_cross_process_disk_reservation':True,'all_query_recording_preserved':True},'original200_and_new_Goal_science_HOLD':True,'no_cause_or_repair_claim':True,'no_exact_historical_replay_claim':True,'GPU_seconds_added':0,'Slurm_commands':0,'state_Git_production_mutations':0,'wall_seconds':time.perf_counter()-began,'CPU_seconds':time.process_time()-cpu})
 readiness={'schema':'formal_main_v2','kind':'goal_prefix58_single_attempt_CPU_readiness','status':'passed','reviewed_by':'independent','version':entry.VERSION,'package_manifest_sha256':MSHA,'config_sha256':CSHA,'original_chain_preserved':True,'observer_gaps_fixed':True,'paired_input_gate_CPU_passed':True,'pre_policy_pair_equality_gate':True,'all_query_input_integrity_gate':True,'original_policy_error_retained_then_halt':True,'real_GPU_acceptance':False,'scientific_release':False,'actual_P_published_package_verified':True,'detailed_review':detailed,'actual_P_evidence':evidence,'maximum_authorizable_engineering_attempts':1,'maximum_wall_seconds':1800,'old_Goal200_and_all_new_Goal_science_HOLD':True,'final_release':False,'review_agent':'/root/spatial588_recovery_audit_2054'}
 entry.check_review(readiness,'independent',MSHA,CSHA);rr=write('independent_readiness.json',readiness)
 dr=write('dispatch_review.json',{'schema':'formal_main_v2','kind':'independent_exact_Goal_dispatch_review','status':'passed','entrypoint':DISPATCH,'entrypoint_sha256':DSHA,'blockers':[],'actual_P_readiness':rr,'detailed_review':detailed,'findings_fixed':[{'old_v2_missing_all_mode_same_goal_collision':'fixed by exact v3; four nontraining collision fixtures reject even when train active_pairs empty'}],'conditions_enforced_at_execution':['Fresh separate root authorization and distinct readiness SHA','Actual P source/checkpoint/prefix recheck','writer.lock/CAS, no pending/reservation, completed controller lease free','all-mode<=8, no active Goal job, known scheduler identities only','One held job, exact ACK/comment/token before registration then release','Unknown submission/release leaves pending for reconciliation, no retry','P free>=4363621114 bytes immediately before reservation; all query records retained','Old Goal200 and all new Goal science remainHOLD; single58 engineering only'],'GPU_or_scheduler_called_by_review':False,'new_scientific_trials':0})
 print(json.dumps({'readiness':rr,'dispatch_review':dr,'detailed_review':detailed,'checks':len(checks)}),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as e:
  write('audit_failure_'+str(time.time_ns())+'.json',{'error':str(e),'traceback':traceback.format_exc(),'checks':checks,'GPU_jobs':0});raise
