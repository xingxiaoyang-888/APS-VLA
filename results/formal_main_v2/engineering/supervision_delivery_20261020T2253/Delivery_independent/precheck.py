from pathlib import Path
import hashlib,json,os,sys,time,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R/'.local/delivery_independent_20261020T2253';E=R/'results/formal_main_v2/engineering/supervision_delivery_20261020T2253';B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0653'
checks=[];refs={}
def ck(n,x):
 checks.append({'name':n,'passed':bool(x)})
 if not x:raise AssertionError(n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p,pin=None):
 h=sha(p)
 if pin:ck('SHA '+str(p),h==pin)
 refs[str(p)]={'sha256':h,'bytes':p.stat().st_size};return json.loads(p.read_bytes())
def guard(event,args):
 if event in ['subprocess.Popen','os.system','socket.connect','socket.bind','os.posix_spawn']:raise RuntimeError('No scheduler/network/process in audit')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  if any('sealed' in n.lower() for n in p.parts) or ('final' in p.parts and p.name=='panel.json'):raise RuntimeError('No sealed values')
  mode,flags=args[1:3];write=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if write and not p.is_relative_to(D):raise RuntimeError('Private writes only')
def save(n,obj):
 p=D/n
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 return {'path':str(p.relative_to(R)),'sha256':sha(p)}
def verify_archive(name,mname,pin,private):
 base=E/name;m=rd(base/mname,pin);rows=m['files'];expected={}
 if isinstance(rows,dict):expected=rows
 else:
  for row in rows:
   rel=Path(row['path']).relative_to(private);ck('safe_member '+str(rel),not rel.is_absolute() and '..' not in rel.parts and str(rel) not in expected);expected[str(rel)]={'sha256':row['sha256'],'bytes':row['bytes']}
 ck('count '+name,len(expected)==m['file_count'])
 for rel,item in expected.items():
  p=base/rel;ck('file_regular '+str(p),p.is_file() and not p.is_symlink());ck('exact_member '+str(p),sha(p)==item['sha256'] and p.stat().st_size==item['bytes'])
  refs[str(p)]=item
 actual={str(p.relative_to(base)) for p in base.rglob('*') if p.is_file()};ck('exact_archive_members '+name,actual==set(expected)|{mname})
 return {'manifest_sha256':pin,'file_count':len(expected),'total_bytes':sum(v['bytes'] for v in expected.values())}
def main():
 sys.dont_write_bytecode=True;os.environ['CUDA_VISIBLE_DEVICES']='';sys.addaudithook(guard)
 archives={}
 archives['Goal']=verify_archive('Goal_terminal_independent','delivery_manifest_original.json','394bdfc06bc326b0ef72016302a5f5820f452e5a4bd2ba384231e0179ba385d9',None)
 archives['Object']=verify_archive('Object599_independent','delivery_manifest_original.json','08dd6ededfa12ba7827784cb0809db0c57128ffc880df831a977e558bded10f3','.local/object599_independent_20261020T2253')
 archives['Spatial']=verify_archive('Spatial_gateway_independent','delivery_manifest_final_original.json','2d1a06be074d19ec9598c5f2e4c78b2558e5a804ebc43b3a44d9f041e06ec9b2','.local/spatial_gateway_independent_20261020T2253')
 goal=rd(B/'Goal_terminal_acceptance.json','0ce97bb4913eb17d8b7a5dd81f05b16e60de62d60445d6b304033fff8670d49e')
 for k in ['root_review','independent_review','independent_archive_review','slurm_observation','archive_manifest']:rd(R/goal[k]['path'],goal[k]['sha256'])
 ck('Goal_engineering_only_exact',goal['status']=='root_and_independent_engineering_only_accepted' and goal['GPU_seconds']==840 and goal['prefix_trials']==58 and goal['accepted_queries']==940 and goal['executed_steps']==7302 and goal['paired_inputs']==29)
 ck('Goal_HOLD_no_result_claim',goal['new_Goal_science_HOLD'] and not any(goal[k] for k in ['old200_adopted','old_cause_identified','old_failure_repaired','final_release','automatic_retry','O2A_admitted']) and goal['new_scientific_trials']==0)
 gu=rd(B/'Goal_terminal_state_update.json','266893d22cfbc442a132d76eedec78a5c78033f1424dfbb35bf74ca42989b8b0');ck('Goal_increment_623_not840_twice',gu['GPU_seconds_newly_accounted']==623 and gu['GPU_seconds_total']==1985302 and gu['new_scientific_trials']==gu['new_GPU_submissions']==0)
 obj=rd(E/'Object599_independent/independent_review.json','62c0a39784953b14f061ae7d161813f5e4bbfa5c8db39297e7047327b28463f7')
 ck('Object599_only_compat_proof',obj['status']=='passed' and not obj['blockers'] and obj['scope']['normal_legacy_trials']==599 and obj['scope']['raw_historical_trials']==600 and obj['scope']['retained_policy_errors']==1 and obj['source_model_checkpoint_initial_state_controller_RNG_verified'] and not obj['production_reuse_authorized'] and not obj['whole600_compatibility_admitted'])
 ck('Object_cost_retained',obj['all_original_GPU_seconds']==6713 and obj['new_GPU_seconds']==obj['new_scientific_trials']==0 and not obj['final_release'])
 scope=rd(E/'Object599_independent/single_error_scope_guard_addendum.json','b3dc7454b046393d4542e560cbb5d3a223c6e4113713108990c251ffb6002ea0');ck('Object_replacement_HOLD',scope['status']=='CPU_design_only_HOLD' and not scope['submit_authorized'] and 'policy_error is included' in scope['observed_original_guard'] and 'prefill599 fake completion' in ' '.join(scope['consequences']))
 spatial=rd(E/'Spatial_gateway_independent/post_readiness_independent_review.json','8eb2e5b90395ee22d1528699008d5ed21b45ecf6e37a5592661a60a757837554')
 ck('Spatial_preflight_pass_not_terminal',spatial['status']=='passed' and not spatial['blockers'] and spatial['actual_P_new_outer_wrapper_verified'] and spatial['full_FrozenPlan_prepare_passed'] and spatial['actual_NativeIO_preflight_passed'] and not spatial['actual_GPU_runtime_chain_verified'] and spatial['new_scientific_trials']==0 and not spatial['final_release'])
 history=spatial['explicit_source_control'];ck('Spatial_history_not_fake_execution',history['all_prior_job_ids']==['3022743','3042529'] and history['executed_prior_job_ids']==['3022743'] and history['predispatch_failed_job_ids']==['3042529'] and history['predispatch_failure_GPU_seconds']==2 and history['prior_GPU_seconds']==395 and not history['failed_ledger_invocation_fabricated'] and not history['ordinary_failure_review_fabricated'])
 ck('Spatial_typed12_plus588',history['scope']['expected_trials']==600 and history['scope']['remaining_trials']==spatial['remaining_current_trials']==588 and history['scope']['retained_prefix_trials']==spatial['legacy_compatible_trials']==12 and len(spatial['legacy12_compatibility']['legacy_trial_ids'])==12 and spatial['legacy12_compatibility']['legacy_origin_preserved'])
 for key in ['authorization','effective_plan','prepared_invocation','runtime_readiness','scientific_plan','root_reservation_metadata','gateway_independent_review']:
  ref=spatial[key];rd(R/ref['path'],ref['sha256'])
 for rel,pin in spatial['runtime_sources'].items():
  for base in [R,P]:ck('Spatial_runtime_unchanged '+str(base/rel),sha(base/rel)==pin)
 for path,record in refs.items():ck('stable '+path,sha(Path(path))==record['sha256'])
 out=save('precheck_review.json',{'status':'passed_archived_evidence_precheck','blockers':[],'archives':archives,'Goal840_seconds_engineering_only':True,'Object599_proof_not_adopted':True,'Object_policy_error_retained':True,'Spatial12_legacy_plus588_current_separate':True,'scientific_result_increment':0,'final_state_not_yet_audited':True,'no_live_Slurm_queries':True,'source':'independent_review_of_pinned_raw_receipts_and_archive_integrity','files':refs,'checks':checks,'check_count':len(checks)})
 print(json.dumps({'review':out,'checks':len(checks)}))
if __name__=='__main__':
 try:main()
 except BaseException as e:save('failure_'+str(time.time_ns())+'.json',{'error':str(e),'traceback':traceback.format_exc(),'checks':checks});raise
