"""Independent current-server evidence read, with the actual shared lock; never submits."""
import copy,hashlib,importlib.util,json,sys
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/cuda_recovery_autonomous_audit_1940'
C=R/'.local/cuda_recovery_autonomous_1940'
GP='c97b66100a0a21a722b17e32129b7a220fac7b2b2cb8b9cc9678b88f605476c3'
EP='96e5e0a653c2ed884f09f7c3bf1ce19f0664c1665921a183bc351a97f5ff9d87'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert digest(C/'gateway.py')==GP and digest(C/'evidence.py')==EP
sp=importlib.util.spec_from_file_location('ind1940_actual',C/'gateway.py')
g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g);e=g.e
c=g.load(R/g.CONTROLLER,'ind1940_actual_controller',g.CONTROLLER_SHA)
maps={}
def read(rel,pin=None):
    path=R/rel;checksum=digest(path)
    if pin:assert checksum==pin,rel
    maps[rel]=checksum
    return json.loads(path.read_bytes())
inventory=read('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
previous={'3028460':'libero_object_train_k256_seed23_attempt01.json','3028468':'libero_object_train_k64_seed23_attempt01.json','3028522':'libero_spatial_train_k64_seed23_attempt03.json'}
current={'3028460':'libero_object_train_k256_seed23_attempt02.json','3028468':'libero_object_train_k64_seed23_attempt02.json','3028522':'libero_spatial_train_k64_seed23_attempt04.json'}
statepath=R/g.STATE;lock=statepath.parent/'.writer.lock';assert lock.is_file()
results={}
with c.exclusive_lock(lock):
    state_before=c.file_sha(statepath);state=c.read_json(statepath)
    assert c.file_sha(statepath)==state_before
    observation=c.Slurm().observe(state['registered_jobs'])
    capacity=c.capacity(state['registered_jobs'],observation,state.get('autonomous_training_v1',{}).get('controller_job_id'))
    for jid,case in e.CASES.items():
        rel=f'results/formal_main_v2/{case[0]}/k{case[1]}/seed23/training/startup_failure_reviews/{jid}.json'
        proof=read(rel,case[5])
        original=read('results/formal_main_v2/invocations/'+previous[jid],proof['invocation_sha256'])
        watched=dict(original['watched_files'])
        if 'runtime_compatibility' in original:
            watched.update({str(e.P/path):sha for path,sha in original['runtime_compatibility']['files'].items()})
        wr,wp=e.WRAPPERS[case[0]]
        plan=dict(inventory=inventory,remote_watched=watched,wrapper=str((e.P if case[0]=='libero_object' else e.S)/wr),wrapper_sha256=wp,
            proof=proof,fresh=case[3]==500,invocation_relative='results/formal_main_v2/invocations/'+current[jid])
        got=e.NativeIO().preflight(plan)
        assert got['server_resume_checks']==[dict(x,**({'stable_during_hash':True} if x['exists'] else {})) for x in proof['server_resume_checks']]
        assert proof['failed_status']=='FAILED' and proof['failed_exit_code']=='1:0'
        assert proof['current_allocation_new_updates']==0 and proof['current_allocation_arm_initializations']==0
        results[jid]=dict(allowed_original_target=case[3],retained_failed_GPU_seconds=case[4],
            completed_by_arm=proof['completed_by_arm'],next_sample_cursor=proof['next_sample_cursor'],preflight=got)
        for path,row in got['control_metadata'].items():maps[Path(path).relative_to(R).as_posix()]=row['sha256']
    state_after=c.file_sha(statepath)
    assert state_before==state_after,'production state mutated during read-only audit'
assert not any(x=='torch' or x.startswith('tensorflow') for x in sys.modules)
maps[(C/'gateway.py').relative_to(R).as_posix()]=GP;maps[(C/'evidence.py').relative_to(R).as_posix()]=EP
maps[g.CONTROLLER]=g.CONTROLLER_SHA
maps[Path(__file__).relative_to(R).as_posix()]=digest(Path(__file__))
for rel,sha in maps.items():assert digest(R/rel)==sha,rel
result=dict(schema='formal_main_v2',kind='independent_current_server_read_only_failure_recovery_checks',
    status='passed_read_only_evidence_check_not_retry_authorized',utc=datetime.now(timezone.utc).isoformat(),
    production_state_same_under_shared_lock=state_before,state_before_sha256=state_before,state_after_sha256=state_after,
    registered_jobs_snapshot=state['registered_jobs'],scheduler_observation=observation,capacity_observation=capacity,
    checkpoint_bytes_hashed_without_loading=True,model_or_environment_loaded=False,Slurm_submitted=False,final_states_opened=False,
    three_failures=results,failed_GPU_seconds_total=226,checks_not_admission='No new root authorization or dedicated CUDA reservation is asserted. Root must repeat locked preflight immediately before an exact one-shot submission.',
    read_evidence_sha256=maps)
dest=D/'current_server_read_only.json'
with dest.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'status':result['status'],'registered_jobs':len(state['registered_jobs']),'capacity':capacity,'failed_GPU_seconds':226,'proof':str(dest),'sha256':digest(dest)},sort_keys=True))
