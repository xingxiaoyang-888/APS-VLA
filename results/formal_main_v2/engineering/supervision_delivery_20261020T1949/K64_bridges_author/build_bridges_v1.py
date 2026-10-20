from pathlib import Path
import json,hashlib,ast,re,difflib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent
T=R/'scripts/ops/formal_object256s23_source_bridge_v1'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return {'path':n,'sha256':h(R/n)}
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 data=v if isinstance(v,str) else json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+'\n'
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(data)
assert h(T/'bridge_v2.py')=='8785b42fe62dd513f796871875547c894de972516ac9762ad60a89d3df9a7c8e'
assert h(T/'control.py')=='09ae3486565e17bd2c41b09adbfaa7a6d99f38754d3e77071f77851c9ac54f6f'
registration=rd('configs/experiments/formal_main_v2.json')
specs=[('spatial','3028522','3043399','3044479',['3024716','3025205','3028522','3043399','3044479'],[3281,5203,73,3401,30522],1000,1500,'12ab9843ba7bd1982d4bbc1004b733db4a4d97ee2deb9863e3cfb9767add510c','cc04fd98fd39a2159ca32775167f262efcdd528ad3bb4945c4998d025fe7f554'),('object','3028468','3044017','3044844',['3028468','3044017','3044844'],[69,5141,47658],0,500,'6f3bd55f4772812c3e171f700587a753a2153c151c6fad554152fa84371c5ea9','9d357b032ae9c8c3d1aa4f901875eec4ef4fca7c2912805c52e114813e3b2150')]
new_validator=r"""def validate_documents(p,*,saved,independent,recovery_root,recovery_independent,failure,recovery_authorization,continuous_authorization):
    refs=p['references'];success=set(p['successful_job_ids'])
    require(saved.get('job_id')==p['final_job_id'] and saved.get('status')=='passed' and saved.get('completed_by_arm')=={'A':5000,'B':5000},'exact completed final training review required')
    if p['suite']=='libero_object':
        require(set(saved.get('runtime_compatibility_history',{}))==success,'successful Object metadata history differs')
    else:
        require(not any(k in saved for k in ('runtime_compatibility','runtime_compatibility_review','runtime_compatibility_history')),'Spatial cannot invent asset metadata')
    require(set(saved.get('startup_failure_history',{}))=={p['failure_job_id']} and saved['startup_failure_history'][p['failure_job_id']]==failure,'separate exact failed startup required')
    require(not(set(saved.get('runtime_compatibility_history',{}))&set(saved['startup_failure_history'])),'failure cannot become ordinary metadata')
    require(saved.get('pair_allocated_gpu_seconds')==p['total_GPU_seconds'],'complete pair bill differs')
    require(independent.get('status')=='passed_complete_training_only' and independent.get('root_review')==refs['final_root'],'exact independent final review required')
    require(independent.get('historical_failure_preserved_and_rebuilt') is True,'independent failure reconstruction absent')
    require(independent.get(p['independent_source_flag']) is True and independent.get('same_AB_initialization_and_full40000_order') is True,'source or AB/order acceptance absent')
    if p['suite']=='libero_object':require(independent.get('historical_failure_review')==refs['failure'],'Object independent failure ref differs')
    cost=independent.get('cost',{})
    require(cost.get('all_pair_allocated_GPU_seconds')==p['total_GPU_seconds'] and cost.get(p['independent_failed_cost_key'])==p['failed_GPU_seconds'],'independent bill differs')
    require(cost.get('allocations')==[{'GPU_seconds':p['allocation_seconds'][j],'job_id':j} for j in p['all_job_ids']],'all allocations must occur exactly once')
    target=p['recovery_target'];prior=p['failed_completed_before']
    require(recovery_root.get('job_id')==p['recovery_job_id'] and recovery_root.get('completed_by_arm')=={'A':target,'B':target} and recovery_root.get('pair_allocated_gpu_seconds')==p['pre_continuous_GPU_seconds'],'original target recovery boundary/bill differs')
    require(recovery_independent.get('status')=='passed_original_target_recovery_only' and recovery_independent.get('root_review')==refs['recovery_root'] and recovery_independent.get('historical_failure_preserved') is True,'original target independent recovery proof absent')
    require(recovery_independent.get('all173_source_R_and_S_match') is True,'recovery science source proof absent')
    require(failure.get('job_id')==p['failure_job_id'] and failure.get('status')=='verified_startup_failure' and failure.get('completed_by_arm')=={'A':prior,'B':prior},'failed allocation cannot claim new updates')
    require(failure.get('current_allocation_new_updates')==0 and failure.get('current_allocation_arm_initializations')==0 and failure.get('next_sample_cursor')=={'A':prior*8,'B':prior*8},'failed startup crossed the original boundary')
    require(failure.get('failed_allocation_gpu_seconds')==p['failed_GPU_seconds'],'failed cost differs')
    require(recovery_authorization.get('failed_job_id')==p['failure_job_id'] and recovery_authorization.get('original_target')==target,'recovery authorization differs')
    require(continuous_authorization.get('failed_job_id')==p['failure_job_id'] and continuous_authorization.get('recovery_job_id')==p['recovery_job_id'] and continuous_authorization.get('pair_key')==p['suite']+'_k64_seed23','continuous admission differs')
    require(continuous_authorization.get('historical_GPU_seconds')==p['pre_continuous_GPU_seconds'] and continuous_authorization.get('target_updates_per_arm')==5000 and continuous_authorization.get('scientific_settings_changed') is False,'continuous schedule or bill differs')
    for arm in ('A','B'):
        row=independent['arms'][arm];selected=row.get('selected_update',row.get('earliest_selected_update'));best=row.get('best_sha256',row.get('best',{}).get('sha256'))
        require(best==p['selected_checkpoints'][arm]['sha256'] and selected==p['selected_checkpoints'][arm]['update'],'original earliest selected checkpoint differs')
        require(row.get('completed_updates')==5000 and row.get('cursor')==40000 and row.get('sample_uses')==40000,'full completed arm evidence differs')
        require([x['update'] for x in row['validation']]==list(range(0,5001,500)),'all 11 original validation nodes required')
    return success
"""
rows=[]
for short,failed,recovered,final,ids,secs,prior,target,rootpin,indpin in specs:
 suite='libero_'+short;base=f'results/formal_main_v2/{suite}/k64/seed23/training';K=D/short/'package';K.mkdir(parents=True)
 root_ref=ref(base+'/segment_reviews/'+final+'.json');ind_ref=ref(base+'/segment_reviews/'+final+'_independent.json');assert root_ref['sha256']==rootpin and ind_ref['sha256']==indpin
 independent=rd(ind_ref['path']);pair=next(p for p in registration['pairs'] if p['suite']==suite and p['visual_tokens']==64 and p['seed']==23)
 refs={'final_root':root_ref,'final_independent':ind_ref,'recovery_root':ref(base+'/segment_reviews/'+recovered+'.json'),'recovery_independent':ref(base+'/segment_reviews/'+recovered+'_independent.json'),'failure':ref(base+'/startup_failure_reviews/'+failed+'.json'),'recovery_authorization':ref('configs/experiments/formal_main_v2_cuda_single_recovery_'+failed+'_v1.json'),'continuous_authorization':ref('configs/experiments/formal_main_v2_'+('spatial_cuda_continuous_3043399_v2' if short=='spatial' else 'object64_cuda_continuous_3044017_v1')+'.json'),'selected_server':independent['selected_server_review'],'original_consumer':ref('scripts/ops/formal_asset_downstream_review.py'),'original_factory':ref('scripts/formal_execution_manifests.py'),'failure_verifier':ref('scripts/formal_cuda_terminal_review_v1/startup_failure_evidence.py'),'ownership_verifier':ref('scripts/formal_cuda_terminal_review_v1/review_formal_segment_startup.py')}
 if short=='spatial':
  for jid in ['3024716','3025205']:
   refs['earlier_root_'+jid]=ref(base+'/segment_reviews/'+jid+'.json');refs['earlier_independent_'+jid]=ref(base+'/segment_reviews/'+jid+'_independent.json')
  refs['continuous_document_binding']=rd(refs['continuous_authorization']['path'])['historical_document_binding']
 selected={}
 for arm in ['A','B']:
  report=rd(base+'/'+arm+'/training_report.json');selected[arm]={'sha256':report['best_checkpoint_sha256'],'update':report['best_update'],'path':report['best_checkpoint']}
 p={'schema':'formal_main_v2','kind':'bounded_'+short+'64_seed23_source_bridge_policy','version':short+'64-seed23-startup-source-bridge-v1','status':'private_candidate_not_root_admitted','suite':suite,'visual_tokens':64,'seed':23,'pair':pair,'base':base,'method_ids':['A64_seed23','B64_seed23'],'failure_job_id':failed,'recovery_job_id':recovered,'final_job_id':final,'all_job_ids':ids,'successful_job_ids':[x for x in ids if x!=failed],'allocation_seconds':dict(zip(ids,secs)),'total_GPU_seconds':sum(secs),'failed_GPU_seconds':secs[ids.index(failed)],'pre_continuous_GPU_seconds':sum(secs[:-1]),'failed_completed_before':prior,'recovery_target':target,'independent_source_flag':'source173_R_S_mirror_match' if short=='spatial' else 'all173_R_S_and_mirror_match','independent_failed_cost_key':'retained_FAILED_GPU_seconds' if short=='spatial' else 'retained_failed_GPU_seconds','references':refs,'selected_checkpoints':selected,'final_release_authorized':False,'scientific_settings_changed':False,'training_or_development_rerun_authorized_by_bridge':False}
 write(K/'policy_v1.json',p);policyhash=h(K/'policy_v1.json')
 b=(T/'bridge_v2.py').read_text();old=b
 replacements=[('Object256','Spatial64' if short=='spatial' else 'Object64'),('object256',short+'64'),('libero_object',suite),('3028460',failed),('3039258',recovered),('3042627',final),('58917',str(sum(secs))),('6596',str(sum(secs[:-1]))),('9f4e753fbe9602593c33b6f5031e88006a3d07dacc0ace21ed1a204d8caab999',policyhash)]
 for a,z in replacements:b=b.replace(a,z)
 b=re.sub(r'\b256\b','64',b);b=re.sub(r'\b84\b',str(p['failed_GPU_seconds']),b)
 b=b.replace("len(relevant)==3", "len(relevant)==len(p['all_job_ids'])")
 tree=ast.parse(b);f=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='validate_documents');lines=b.splitlines(True);b=''.join(lines[:f.lineno-1])+new_validator+'\n'+''.join(lines[f.end_lineno:])
 marker="    require(saved==docs['final_root'],'final immutable review differs')"
 insertion="""    for key in refs:
        if key.startswith('earlier_') or key=='continuous_document_binding':read_ref(evidence,refs[key])
    selected=docs['selected_server']
    require(selected.get('job_id')==p['final_job_id'] and selected.get('root_review')==refs['final_root'] and selected.get('status')=='verified_actual_server_bytes','actual selected-server proof differs')
    require(len(selected.get('checks',[]))==2 and {x['arm'] for x in selected['checks']}=={'A','B'},'two exact selected-server arms required')
    for row in selected['checks']:
        expected=p['selected_checkpoints'][row['arm']]
        require(row.get('path')==expected['path'] and row.get('sha256')==expected['sha256'] and row.get('selected_update')==expected['update'],'selected-server identity differs')
"""
 assert b.count(marker)==1;b=b.replace(marker,marker+'\n'+insertion)
 literal="'successful_job_ids':"+str([recovered,final]).replace(' ', '')
 # Handle template syntax that contains no spaces in literal job list.
 b=b.replace("'successful_job_ids':['"+recovered+"','"+final+"']", "'successful_job_ids':"+repr(p['successful_job_ids']))
 b=b.replace('full three-allocation history required','full exact-allocation history required').replace('Only original failed startup '+failed+' followed by '+recovered+' and '+final+' is admitted.','Only the policy-pinned full history for '+suite+' k64 seed23 is admitted.')
 ast.parse(b);write(K/'bridge_v2.py',b);write(D/short/'template_derivation.diff',''.join(difflib.unified_diff(old.splitlines(True),b.splitlines(True),fromfile='published_Object256_bridge_v2.py',tofile=short+'_k64_private_bridge_v1.py')))
 rows.append({'suite':suite,'policy':ref((K/'policy_v1.json').relative_to(R).as_posix()),'bridge':ref((K/'bridge_v2.py').relative_to(R).as_posix()),'total_GPU_seconds':p['total_GPU_seconds'],'failure_GPU_seconds':p['failed_GPU_seconds'],'selected_checkpoints':selected})
write(D/'build_receipt.json',{'status':'two_private_exact_history_candidates_created','pairs':rows,'source_template':ref('scripts/ops/formal_object256s23_source_bridge_v1/bridge_v2.py'),'canonical_or_state_written':False,'GPU_runs':0,'scientific_trials':0})
print(json.dumps(rows))
