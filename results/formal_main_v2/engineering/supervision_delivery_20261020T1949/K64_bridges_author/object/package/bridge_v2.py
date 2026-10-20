"""Explicit Object64 seed23 source-only compatibility, never a runtime/science patch.
Only the policy-pinned full history for libero_object k64 seed23 is admitted.
All other evidence checks execute the exact original consumer with three bounded
operational substitutions. Original files and 173 science files stay unchanged.
"""
from pathlib import Path
from types import SimpleNamespace
import hashlib, importlib.util, json, difflib
ROOT=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
POLICY_SHA256='2740fdd578a24d6c74a39d76b34223af46e6457932d797b9e0096124e479edcd'
VERSION='object64-seed23-startup-source-bridge-v2'
POLICY_PATH=Path(__file__).with_name('policy_v1.json')
P='/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA'

def require(ok,label):
    if not ok: raise ValueError('Object64s23 bounded bridge: '+label)

def policy():
    raw=POLICY_PATH.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==POLICY_SHA256,'policy byte SHA changed')
    return json.loads(raw)

def load(evidence,ref):
    require(evidence.watch(ref['path'])==ref['sha256'],'pinned source changed: '+ref['path'])
    path=evidence.path(ref['path'])
    spec=importlib.util.spec_from_file_location('object23_bridge_'+path.stem,path)
    mod=importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(),str(path),'exec'),mod.__dict__)
    return mod

def read_ref(evidence,ref):
    require(evidence.watch(ref['path'])==ref['sha256'],'pinned evidence changed: '+ref['path'])
    return evidence.read(ref['path'])

def scope_guard(p,*,suite,pair,method_rows,relevant):
    require(suite==p['suite'] and pair==p['pair'],'only exact registered Object64 seed23 pair')
    require([r['identity']['method_id'] for r in method_rows]==p['method_ids'],'only exact paired A256/B256 seed23; no baseline/other method')
    require(len(relevant)==len(p['all_job_ids']) and {j['job_id'] for j in relevant}==set(p['all_job_ids']),'full exact-allocation history required')
    for j in relevant:
        jid=j['job_id']; failed=jid==p['failure_job_id']
        expect={'experiment':'formal_main_v2','suite':p['suite'],'training_seed':23,'visual_tokens':64,'mode':'train','run_root':P+'/'+p['base'],'gpus':1,'elapsed_seconds':p['allocation_seconds'][jid],'status':'FAILED' if failed else 'COMPLETED','exit_code':'1:0' if failed else '0:0'}
        require(all(j.get(k)==v for k,v in expect.items()),'allocation identity/status/cost differs: '+jid)
    for row in method_rows:
        identity=row['identity'];arm=identity.get('method')
        require(arm in ('A','B') and identity.get('suite')==suite and identity.get('visual_tokens')==64 and identity.get('training_seed')==23,'selected method scientific identity differs')
        require(identity.get('checkpoint_sha256')==p['selected_checkpoints'][arm]['sha256'],'selected checkpoint SHA differs')

def validate_documents(p,*,saved,independent,recovery_root,recovery_independent,failure,recovery_authorization,continuous_authorization):
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


def audit_exact_history(evidence,*,suite,pair,method_rows,relevant,saved):
    p=policy();scope_guard(p,suite=suite,pair=pair,method_rows=method_rows,relevant=relevant)
    require(evidence.watch(POLICY_PATH.relative_to(ROOT).as_posix())==POLICY_SHA256,'policy watch changed')
    refs=p['references']; docs={k:read_ref(evidence,refs[k]) for k in ('final_root','final_independent','recovery_root','recovery_independent','failure','recovery_authorization','continuous_authorization','selected_server')}
    require(saved==docs['final_root'],'final immutable review differs')
    for key in refs:
        if key.startswith('earlier_') or key=='continuous_document_binding':read_ref(evidence,refs[key])
    selected=docs['selected_server']
    require(selected.get('job_id')==p['final_job_id'] and selected.get('root_review')==refs['final_root'] and selected.get('status')=='verified_actual_server_bytes','actual selected-server proof differs')
    require(len(selected.get('checks',[]))==2 and {x['arm'] for x in selected['checks']}=={'A','B'},'two exact selected-server arms required')
    for row in selected['checks']:
        expected=p['selected_checkpoints'][row['arm']]
        require(row.get('path')==expected['path'] and row.get('sha256')==expected['sha256'] and row.get('selected_update')==expected['update'],'selected-server identity differs')

    success=validate_documents(p,saved=saved,independent=docs['final_independent'],recovery_root=docs['recovery_root'],recovery_independent=docs['recovery_independent'],failure=docs['failure'],recovery_authorization=docs['recovery_authorization'],continuous_authorization=docs['continuous_authorization'])
    for key in ('recovery_authorization','continuous_authorization'):
        # Every explicit review/repair/slot/publication ref remains original bytes.
        for item in docs[key].values():
            if isinstance(item,dict) and set(('path','sha256'))<=set(item): read_ref(evidence,item)
    failed=next(j for j in relevant if j['job_id']=='3028468')
    verifier=load(evidence,refs['failure_verifier'])
    require(verifier.require_saved(evidence,job=failed,saved=docs['failure'])==docs['failure'],'original raw startup failure did not rebuild')
    # Check selected-server proof bytes and agreement with independently audited rows;
    # live checkpoint bytes are checked separately by root at runtime admission.
    return success

def pull_with_original_ownership(evidence,*,saved,job,shared,required,receipt):
    if not saved.get('startup_failure_history'):
        return shared.require_pulled(evidence,receipt,job,required)
    p=policy(); refs=p['references']
    require(saved==read_ref(evidence,refs['final_root']) and job.get('job_id')=='3044844','only exact final startup-aware pull allowed')
    module=load(evidence,refs['ownership_verifier'])
    jobs={j['job_id']:j for j in saved['registered_pair_jobs_at_review']}
    owners=module.require_pulled_startup_ownership(evidence,receipt,job,required,jobs,saved['startup_failure_history'])
    require(owners==saved.get('startup_pull_ownership'),'root failure external ownership differs')
    require(len(owners)==3 and set(owners.values())=={'3028468'},'only three original failed external files allowed')
    return owners

def derived_source(raw):
    replacements=[
      ('    ids = {j["job_id"] for j in relevant}\n', '    ids = {j["job_id"] for j in relevant}\n    successful_ids = _bridge_history(evidence, suite=suite, pair=pair, method_rows=method_rows, relevant=relevant, saved=saved)\n'),
      ('require(set(saved.get("runtime_compatibility_history", {})) == ids, "metadata history does not cover every allocation")','require(set(saved.get("runtime_compatibility_history", {})) == successful_ids, "successful metadata history does not cover every successful allocation")'),
      ('    for job in relevant:\n        registered_job(jobs, job["job_id"], suite=suite, mode="train", output=base)','    for job in relevant:\n        if job["job_id"] == "3028468":\n            continue  # Rebuilt and fully billed by _bridge_history; no ordinary metadata exists.\n        registered_job(jobs, job["job_id"], suite=suite, mode="train", output=base)'),
      ('    shared.require_pulled(evidence, candidates[0], job, required)\n','    _bridge_pull(evidence, saved=saved, job=job, shared=shared, required=required, receipt=candidates[0])\n')]
    result=raw
    for old,new in replacements:
        require(result.count(old)==1,'pinned original substitution target not unique')
        result=result.replace(old,new,1)
    return result

def auditor(evidence):
    p=policy();ref=p['references']['original_consumer'];orig=load(evidence,ref)
    path=evidence.path(ref['path']);raw=path.read_text(encoding='utf-8');changed=derived_source(raw)
    spec=importlib.util.spec_from_file_location('object23_bounded_source_derivation',path)
    derived=importlib.util.module_from_spec(spec)
    exec(compile(changed,str(path)+'::<object64s23_source_bridge_v1>','exec'),derived.__dict__)
    derived._bridge_history=audit_exact_history
    derived._bridge_pull=pull_with_original_ownership
    derived.HELPER=Path(__file__).resolve().relative_to(ROOT).as_posix()
    derived.VERSION=VERSION
    original_review_source = derived.review_source_provenance
    def review_source_provenance(parent,**kw):
        require(Path(getattr(parent,'project',getattr(parent,'root',''))).resolve()==ROOT,'control repository evidence root must be exact R')
        rows=kw.get('method_rows',[])
        require(kw.get('suite')=='libero_object' and [x['identity']['method_id'] for x in rows]==p['method_ids'],'bridge only exact Object64 seed23 pair')
        result=original_review_source(parent,**kw)
        result['startup_failure_source_bridge']={
          'version':VERSION,'policy':{'path':POLICY_PATH.relative_to(ROOT).as_posix(),'sha256':POLICY_SHA256},
          'original_consumer':ref,'derived_source_sha256':hashlib.sha256(changed.encode()).hexdigest(),
          'operational_changes':['Separate successful metadata and raw failed startup provenance','Use original raw startup verifier for only3028468','Retain original per-job failed external-file pull ownership'],
          'failure_job_id':'3028468','successful_job_ids':['3044017', '3044844'],'all_pair_GPU_seconds':52868,'retained_failed_GPU_seconds':69,
          'checkpoint_live_bytes_checked_by_this_bridge':False,'test_opened':False,'new_GPU_runs':0,
          'normal_metadata_fabricated':False,'original_scientific_gates_replaced':False}
        return result
    # The original invocation consumer rebuilds the same explicitly versioned
    # proof, including the bridge field. This binding belongs only to this new
    # private module instance; the original imported module/file is untouched.
    derived.review_source_provenance = review_source_provenance
    def review_invocation(parent,**kw):
        require(kw['job'].get('suite')=='libero_object' and kw['job'].get('mode')=='development','candidate invocation audit is development-only')
        require(kw['invocation'].get('method_ids')==p['method_ids'],'candidate invocation pair differs')
        return derived.review_invocation(parent,**kw)
    # All scientific validators and runtime support are the original functions.
    return SimpleNamespace(review_suite_acceptance=orig.review_suite_acceptance,
        review_source_provenance=review_source_provenance,review_invocation=review_invocation,downstream_contract=orig.downstream_contract,
        original=orig,derived=derived,source_diff=''.join(difflib.unified_diff(raw.splitlines(True),changed.splitlines(True),fromfile=ref['path'],tofile='private-derived-memory-consumer-v1')))


def control_modules(evidence):
    """Return new source-bound factory/planner instances for explicit CPU planning.

    This is not a production gateway override and does not publish or submit.
    An admitted gateway must use this explicit factory/planner pair when it
    independently reconstructs the same plan, then retain all original guards.
    """
    p=policy()
    factory=load(evidence,p['references']['original_factory'])
    planner=load(evidence,{'path':'scripts/ops/formal_downstream_supervisor.py','sha256':'f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571'})
    factory.source_review_module=auditor
    planner.provenance_helper=auditor
    original_plan=planner.plan
    def development_plan(args,state,*,project=ROOT,helper=None):
        require(args.stage=='development' and not args.resume and args.stop_after is None,'candidate supports first complete development only')
        require(Path(project).resolve()==ROOT and (helper is None or helper is factory),'explicit control root/factory required')
        return original_plan(args,state,project=project,helper=factory)
    planner.plan=development_plan
    return factory,planner
