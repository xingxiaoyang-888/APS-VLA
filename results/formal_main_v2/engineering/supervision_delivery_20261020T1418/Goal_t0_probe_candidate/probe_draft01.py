"""Bounded engineering t0 probe. Not a scientific rollout and never submits Slurm."""
from __future__ import annotations
import argparse,ast,base64,copy,hashlib,importlib.util,json,os,platform,random,re,signal,sys,time,traceback,types
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
FIELDS=('agentview_image','robot0_eye_in_hand_image','robot0_eef_pos','robot0_eef_quat','robot0_gripper_qpos')
METHODS=('A256_seed17','B256_seed17')
DUMMY=(0.,0.,0.,0.,0.,0.,-1.)
ORDER=tuple(m for _ in range(3) for m in (METHODS[0],METHODS[1],METHODS[1],METHODS[0]))
INITIAL_SHA='5d0e63172c7ef5d2be8e9451bfca1200b0af32b8a31d6f2b82ea23aef37a2172'
TASK='put_the_wine_bottle_on_top_of_the_cabinet'
VERSION='goal-t0-bounded-probe-candidate-v1'

def require(ok,message):
    if not ok:raise ValueError(message)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def dump(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,allow_nan=False)
def read(path):return json.loads(Path(path).read_text())
def publish(path,obj):
    with Path(path).open('x',encoding='utf-8') as f:f.write(dump(obj)+'\n');f.flush();os.fsync(f.fileno())
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def record_ref(path):return dict(path=str(path),sha256=sha(path),bytes=Path(path).stat().st_size)
def check_ref(ref):
    p=Path(ref['path']);require(p.is_absolute() and p.resolve()==p,'canonical input path required')
    require('sealed' not in p.name.lower() and sha(p)==ref['sha256'],'pinned nonsealed input differs: '+str(p));return p

def validate_config(c):
    require(c['version']==VERSION and c['kind']=='engineering_only_t0_probe','probe identity changed')
    require(c['suite']=='libero_goal' and c['task_id']==2 and c['source_state_index']==42 and c['task_name']==TASK,'only diagnosed development state is allowed')
    require(c['initial_state_sha256']==INITIAL_SHA and c['split']=='development','state identity changed')
    require(c['order']==list(ORDER) and c['resets']==12 and c['wait_steps']==10,'fixed counterbalanced sequence changed')
    require(c['environment_seed']==0 and c['runtime_seed']==17 and c['policy_actions_executed']==0,'environment/scientific scope changed')
    require(c['maximum_gpu_jobs']==1 and c['maximum_wall_seconds']==1800 and c['application_deadline_seconds']==1680,'bounded allocation changed')
    require(c['scientific_acceptance_enabled'] is False and c['final_evaluation_enabled'] is False,'probe cannot release science')
    require(c['output_root']==str(P/'results/formal_main_v2/engineering/goal_t0_probe_20261020T1418/attempt01'),'probe output changed')
    require(c['method_ids']==list(METHODS) and len(c['methods'])==2,'only original A/B methods')
    require([r['identity']['method_id'] for r in c['methods']]==list(METHODS),'method identity order')
    for row in c['methods']:
        i=row['identity'];require(i['suite']=='libero_goal' and i['visual_tokens']==256 and i['training_seed']==17 and i['future_head_deployed'] is False,'deployment identity changed')
    return True

def validate_prefix(source,prefix,proof):
    raw=Path(source).read_bytes();require(hashlib.sha256(raw).hexdigest()==proof['source_file_sha256'],'frozen evaluation source differs')
    tree=ast.parse(raw);fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='execute')
    cut=next(i for i,x in enumerate(fn.body) if isinstance(x,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='run_config' for v in x.targets))
    expected=copy.deepcopy(fn);expected.body=expected.body[:cut]
    got=ast.parse(Path(prefix).read_text()).body[0]
    require(isinstance(got,ast.FunctionDef) and got.name=='execute','prefix function mismatch')
    require(isinstance(got.body[-1],ast.Return) and ast.unparse(got.body[-1].value)=='locals()','engineering prefix needs explicit locals return')
    got.body=got.body[:-1]
    class Strip(ast.NodeTransformer):
        def visit_Expr(self,node):
            if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='probe_record_rng':return None
            return self.generic_visit(node)
    got=Strip().visit(got)
    require(ast.dump(got,include_attributes=False)==ast.dump(expected,include_attributes=False),'original loading/identity prefix was modified')
    require(cut==proof['original_top_level_statements_retained'],'prefix cut changed')
    return dict(original_prefix_ast_unchanged=True,original_statements=cut,scientific_trial_loop_called=False)

def arrays(observation):
    result={name:np.array(observation[name],copy=True,order='C') for name in FIELDS}
    require(all(np.isfinite(v).all() for v in result.values()),'nonfinite observed arrays')
    for name in FIELDS[:2]:require(result[name].dtype==np.uint8 and result[name].ndim==3 and result[name].shape[-1]==3,'raw RGB shape/dtype differs')
    require(result[FIELDS[2]].shape==(3,) and result[FIELDS[3]].shape==(4,) and result[FIELDS[4]].shape==(2,),'raw proprio shapes differ')
    return result

def aggregate(values):
    digest=hashlib.sha256()
    for name in FIELDS:
        v=np.ascontiguousarray(values[name]);digest.update(name.encode()+str(v.dtype).encode()+str(v.shape).encode()+v.tobytes())
    return digest.hexdigest()
def array_meta(values):
    return {k:dict(shape=list(v.shape),dtype=str(v.dtype),sha256=hashlib.sha256(v.tobytes()).hexdigest()) for k,v in values.items()}
def differences(a,b):
    result={}
    for name in a:
        av,bv=a[name],b[name];same=av.shape==bv.shape and av.dtype==bv.dtype
        result[name]=dict(shape_and_dtype_equal=same,byte_equal=same and av.tobytes()==bv.tobytes(),max_abs_difference=float(np.max(np.abs(av.astype(np.float64)-bv.astype(np.float64)))) if same and av.size else None)
    return result

def serial(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,(tuple,list)):return [serial(v) for v in value]
    if isinstance(value,dict):return {str(k):serial(v) for k,v in value.items()}
    if value is None or isinstance(value,(str,int,float,bool)):return value
    return dict(type=type(value).__module__+'.'+type(value).__qualname__,representation=repr(value))

def capture_rng():
    result=dict(python=serial(random.getstate()),numpy=serial(np.random.get_state()))
    torch=sys.modules.get('torch')
    if torch is None:result['torch']=dict(imported=False,cuda_initialized=False)
    else:
        cpu=torch.get_rng_state().cpu().numpy().tobytes()
        ready=torch.cuda.is_initialized();cuda=[x.cpu().numpy().tobytes() for x in torch.cuda.get_rng_state_all()] if ready else []
        result['torch']=dict(imported=True,cpu_base64=base64.b64encode(cpu).decode(),cpu_sha256=hashlib.sha256(cpu).hexdigest(),cuda_initialized=ready,cuda=[dict(base64=base64.b64encode(b).decode(),sha256=hashlib.sha256(b).hexdigest()) for b in cuda])
    result['state_sha256']=hashlib.sha256(dump(result).encode()).hexdigest();return result

def sim_snapshot(env):
    sim=env.sim
    return dict(qpos=np.array(sim.data.qpos,copy=True),qvel=np.array(sim.data.qvel,copy=True),flattened=np.array(sim.get_state().flatten(),copy=True))

class Recorder:
    def __init__(self,out):
        self.out=Path(out);self.events=[];self.count=0;self.arrays_written=0
        (self.out/'arrays').mkdir(exist_ok=False)
    def emit(self,event,**fields):
        row=dict(event=event,seq=self.count,utc=datetime.now(timezone.utc).isoformat(),monotonic_seconds=time.monotonic(),**fields)
        self.count+=1
        with (self.out/'events.jsonl').open('a',encoding='utf-8') as f:f.write(dump(row)+'\n');f.flush();os.fsync(f.fileno())
        self.events.append(row)
    def rng(self,phase,**fields):self.emit('rng_state',phase=phase,state=capture_rng(),**fields)
    def observe(self,obs,env,label,phase,previous=None):
        values=arrays(obs);sim=sim_snapshot(env)
        destination=self.out/'arrays'/f'{label}_{phase}.npz'
        with destination.open('xb') as f:np.savez_compressed(f,**values,**{'sim_'+k:v for k,v in sim.items()});f.flush();os.fsync(f.fileno())
        self.arrays_written+=1
        self.emit('observation',label=label,phase=phase,arrays=array_meta(values),aggregate_sha256=aggregate(values),simulation=array_meta(sim),raw_archive=record_ref(destination),difference_from_previous= differences(previous,values) if previous is not None else None)
        return values

@contextmanager
def deadline(seconds):
    require(seconds>0,'deadline exceeded before operation')
    prior=signal.getsignal(signal.SIGALRM)
    def stop(signum,frame):raise TimeoutError('bounded engineering operation deadline exceeded')
    signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_REAL,float(seconds))
    try:yield
    finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,prior)

def run_fixed_queries(*,state,policies,factory,reseed,recorder,check_chunk,absolute_deadline):
    require(tuple(policies)==METHODS,'exact original policies required')
    records=[];t0_snapshots=[]
    for index,mid in enumerate(ORDER):
        label=f'q{index+1:02d}_{mid}';env=None
        recorder.rng('before_reseed',label=label);reseed();recorder.rng('after_reseed_before_factory',label=label)
        try:
            with deadline(absolute_deadline-time.monotonic()):
                env,instruction,identity=factory(state)
                recorder.emit('environment_created',label=label,identity=identity,instruction=instruction,method_id=mid,round=index//4+1,order='AB' if index%4<2 else 'BA',position=index%2+1)
                recorder.rng('before_reset',label=label)
                obs=env.reset();last=recorder.observe(obs,env,label,'reset')
                recorder.rng('after_reset',label=label)
                obs=env.set_init_state(np.asarray(state['initial_state'],dtype=np.float64));last=recorder.observe(obs,env,label,'set_init',last)
                recorder.rng('after_set_init',label=label)
                policies[mid].reset()
                for step in range(10):
                    before=recorder.observe(obs,env,label,f'wait{step+1:02d}_before',last)
                    obs,_,_,_=env.step(list(DUMMY))
                    last=recorder.observe(obs,env,label,f'wait{step+1:02d}_after',before)
                pre=recorder.observe(obs,env,label,'prequery',last)
                recorder.rng('prequery',label=label)
                started=time.perf_counter()
                with deadline(min(60.,absolute_deadline-time.monotonic())):chunk=policies[mid](obs,instruction)
                elapsed=time.perf_counter()-started
                # Query deadline scope consumes no policy action. Outer deadline is restored explicitly.
                signal.setitimer(signal.ITIMER_REAL,max(.001,absolute_deadline-time.monotonic()))
                recorder.rng('postquery',label=label)
                post=recorder.observe(obs,env,label,'postquery',pre)
                details=check_chunk(mid,chunk)
                record=dict(label=label,method_id=mid,query_seconds=elapsed,prequery_sha256=aggregate(pre),postquery_sha256=aggregate(post),input_unchanged=aggregate(pre)==aggregate(post),per_array_difference=differences(pre,post),wait_actions_executed=10,policy_actions_executed=0,**details)
                records.append(record);t0_snapshots.append((pre,post));recorder.emit('query_record',**record)
        finally:
            if env is not None:
                with deadline(min(30.,max(.001,absolute_deadline-time.monotonic()))):env.close()
                recorder.emit('environment_closed',label=label)
    require(len(records)==12 and sum(r['wait_actions_executed'] for r in records)==120,'bounded query count mismatch')
    pairs=[]
    for left in range(0,12,2):
        a,b=records[left:left+2]
        pairs.append(dict(round=left//4+1,order='AB' if left%4==0 else 'BA',left=a['label'],right=b['label'],prequery_equal=a['prequery_sha256']==b['prequery_sha256'],postquery_equal=a['postquery_sha256']==b['postquery_sha256'],prequery_array_difference=differences(t0_snapshots[left][0],t0_snapshots[left+1][0]),postquery_array_difference=differences(t0_snapshots[left][1],t0_snapshots[left+1][1])))
    all_matches=all(x['prequery_equal'] and x['postquery_equal'] for x in pairs) and all(x['input_unchanged'] for x in records)
    return dict(query_records=records,pair_diagnostics=pairs,all_current_probe_pairs_equal=all_matches,unique_prequery_hashes=sorted({r['prequery_sha256'] for r in records}),unique_postquery_hashes=sorted({r['postquery_sha256'] for r in records}),scientific_gate='HOLD',scientific_trials_accepted=0,original_failed_200_trials_unchanged=True,retry_authorized=False)

def prepare_only(config_path):
    c=read(config_path);validate_config(c)
    for ref in c['pinned_inputs'].values():check_ref(ref)
    for name,expected in c['bundle_sources'].items():require(sha(config_path.parent/name)==expected,'candidate source differs: '+name)
    proof=validate_prefix(S/'scripts/eval_formal_selector_libero.py',config_path.parent/'original_loading_prefix.py',c['prefix_proof'])
    invocation=read(c['pinned_inputs']['original_invocation']['path'])
    require(invocation['suite']=='libero_goal' and invocation['stage']=='development' and invocation['method_ids']==list(METHODS),'original invocation scope differs')
    wrapper=load(P/'scripts/ops/formal_action_deployment_v1/wrapper.py','goal_probe_original_wrapper')
    verified=wrapper.verify(invocation,project=P)
    manifest=read(verified['args'].execution_manifest)
    require(manifest['methods']==c['methods'],'original selected checkpoint metadata changed')
    return dict(status='cpu_prepared_not_GPU_run',original_wrapper_metadata_verified=True,weights_loaded=False,sealed_values_read=False,source_proof=proof),verified,invocation

def validate_authorization(auth,c,config_path,script_path):
    require(auth['schema']=='formal_main_v2' and auth['kind']=='root_bounded_engineering_probe_authorization' and auth['status']=='approved' and auth['reviewed_by']=='root','explicit root engineering authorization required')
    require(auth['config_sha256']==sha(config_path) and auth['entrypoint_sha256']==sha(script_path),'authorization config/source mismatch')
    require(auth['root_review']!=auth['independent_review'],'independent review must differ')
    for role in ('root_review','independent_review'):
        row=read(check_ref(auth[role]));require(row['status']=='passed' and row['config_sha256']==sha(config_path) and row['entrypoint_sha256']==sha(script_path),'actual reviewed candidate identity required')
    require(auth['maximum_gpu_jobs']==1 and auth['maximum_wall_seconds']==1800 and auth['counts_against_8_GPU_slots'] is True,'allocation accounting gate missing')
    require(auth['scientific_release'] is False and auth['original_goal_failure_retained'] is True,'science gate must remain HOLD')
    return True

def run_gpu(config_path,authorization_path,authorization_sha):
    require(os.name=='posix' and re.fullmatch(r'[0-9]+',os.environ.get('SLURM_JOB_ID','')),'root-submitted server Slurm required')
    c=read(config_path);validate_config(c)
    require(sha(authorization_path)==authorization_sha,'root authorization bytes differ')
    auth=read(authorization_path);validate_authorization(auth,c,config_path,Path(__file__))
    out=Path(c['output_root']);require(not out.exists(),'existing diagnostic attempt must be preserved; no retry/resume')
    out.mkdir(parents=True,exist_ok=False);rec=Recorder(out);started=time.monotonic();ending=None;exit_code=1
    publish(out/'registered_config.json',c);publish(out/'root_authorization.json',auth)
    rec.emit('probe_begin',job_id=os.environ['SLURM_JOB_ID'],config_sha256=sha(config_path),entrypoint_sha256=sha(__file__),accepted_scientific_trials=0)
    try:
        prepared,context,inv=prepare_only(config_path)
        runtime=context['runtime'];ec=context['execution_contract'];original=context['original_plan'];args=context['args']
        legacy=load(P/'scripts/ops/formal_evaluation_adapter.py','goal_probe_accepted_legacy_adapter')
        legacy.verify_snapshot(P,S,P/inv['source_inventory'],adapter_sha256=inv['adapter_sha256'])
        with legacy.source_imports(S):
            from cti_vla.evaluation import formal_trials,future_profiling
            from cti_vla.data.initial_states import initial_state_sha256
            manifest=read(args.execution_manifest);registration=read(args.registration);regsha=legacy.signature(registration)
            formal_trials.validate_execution_manifest(manifest,registration_sha256=regsha)
            panel=formal_trials.load_formal_panel(suite='libero_goal',split='development',development_path=args.development_panel,registration_sha256=regsha)
            selected=[v for v in panel['states'] if v['task_id']==2 and v['source_state_index']==42]
            require(len(selected)==1,'exact diagnosed state missing')
            state=selected[0];require(state['task_name']==TASK and state['initial_state_sha256']==INITIAL_SHA and initial_state_sha256(state['initial_state'])==INITIAL_SHA,'state values/identity mismatch')
            publish(out/'selected_development_state.json',state)
            eval_module=legacy.private_module(S,'eval_formal_selector_libero');common=legacy.private_module(S,'eval_libero')
            expected_assets=runtime.expected_asset_identities(project_root=P,source_root=S,contract=ec['runtime_contract'],asset_contract=original['invocation'].get('downstream_asset_compatibility'))
            def runner():
                with legacy.recorded_bindings(eval_module,common,future_profiling,S,rec.emit):
                    namespace=dict(eval_module.__dict__);namespace['probe_record_rng']=rec.rng
                    prefix=config_path.parent/'original_loading_prefix.py'
                    exec(compile(prefix.read_bytes(),str(prefix),'exec'),namespace)
                    rec.rng('preload_all');loaded=namespace['execute'](args,manifest,panel,regsha);rec.rng('postload_all')
                torch=loaded['torch'];require(torch.cuda.device_count()==1 and 'L40' in torch.cuda.get_device_name(0),'exact one L40 allocation required')
                policies=loaded['policies'];require(tuple(policies)==METHODS,'loaded policy pair differs')
                from libero.libero import get_libero_path
                task=loaded['suite'].get_task(2);bddl=Path(get_libero_path('bddl_files'))/task.problem_folder/task.bddl_file
                envsource=Path(args.libero_source)/'libero/libero/envs/env_wrapper.py'
                require(sha(bddl)==c['bddl_sha256'] and sha(envsource)==c['environment_wrapper_sha256'],'task/environment source changed')
                identity=dict(runtime=common.environment_provenance(torch,torch.device('cuda:0')),node=platform.node(),source_verification=loaded['source_verification'],bddl=record_ref(bddl),environment_wrapper=record_ref(envsource),task=dict(task_id=2,task_name=task.name,problem_folder=task.problem_folder,bddl_file=task.bddl_file,language=task.language),methods=c['methods'],initial_state_sha256=INITIAL_SHA,source_state_index=42,model_loading='one frozen base and both original selected DIE checkpoints; existing runtime contexts',camera_heights=256,camera_widths=256)
                publish(out/'runtime_identity.json',identity)
                def reseed():random.seed(17);np.random.seed(17);torch.manual_seed(17)
                def factory(st):
                    require(st==state,'factory received another initial state')
                    env=loaded['OffScreenRenderEnv'](bddl_file_name=str(bddl),camera_heights=256,camera_widths=256);env.seed(0)
                    controller=[dict(class_name=type(r.controller).__module__+'.'+type(r.controller).__qualname__,config=serial(getattr(r,'controller_config',{}))) for r in env.robots]
                    return env,task.language,dict(class_name=type(env).__module__+'.'+type(env).__qualname__,underlying=type(env.env).__module__+'.'+type(env.env).__qualname__,controllers=controller,camera_names=serial(env.env.camera_names),camera_heights=serial(env.env.camera_heights),camera_widths=serial(env.env.camera_widths),control_freq=env.env.control_freq,environment_seed=0,runtime_seed=17)
                def check_chunk(mid,chunk):
                    require(isinstance(chunk,loaded['libero_runtime'].PolicyChunk),'same accepted PolicyChunk class required')
                    values=np.asarray(chunk.environment_actions);require(values.shape==(8,7) and np.isfinite(values).all(),'finite full action chunk required')
                    md=serial(dict(chunk.metadata));expected=next(x['identity'] for x in c['methods'] if x['identity']['method_id']==mid)
                    require(md.get('selector_checkpoint_sha256')==expected['checkpoint_sha256'],'query checkpoint differs')
                    indices=np.asarray(md['retained_indices']);require(indices.shape==(256,) and len(np.unique(indices))==256 and np.sum(indices<256)==128 and np.sum(indices>=256)==128,'hard retained token counts changed')
                    require(md.get('future_head_calls')==0 and md.get('policy_forward_calls')==1,'deployment path differs')
                    return dict(policy_metadata=md,environment_action_sha256=hashlib.sha256(values.tobytes()).hexdigest(),environment_actions=values.tolist(),normalized_actions=np.asarray(chunk.normalized_actions).tolist())
                loaded['unchanged']()
                result=run_fixed_queries(state=state,policies=policies,factory=factory,reseed=reseed,recorder=rec,check_chunk=check_chunk,absolute_deadline=started+c['application_deadline_seconds'])
                loaded['unchanged']()
                require(loaded['before']==loaded['verify_checkpoint_directory'](args.checkpoint,loaded['asset']) and loaded['module_parameter_sha256'](loaded['components'])==loaded['f00']['frozen_model_sha256'],'base checkpoint/parameters changed')
                return result
            with deadline(c['application_deadline_seconds']-(time.monotonic()-started)):
                result=runtime.run_with_asset_contexts(runner,project_root=P,source_root=S,contract=ec['runtime_contract'],asset_contract=original['invocation'].get('downstream_asset_compatibility'),emit=rec.emit)
            proof=runtime.verify_runtime_events(rec.events,ec['runtime_contract'],expected_asset_identities=expected_assets)
            require(proof['all_source_and_binding_contexts_restored'] is True,'accepted runtime restoration unproven')
            legacy.verify_snapshot(P,S,P/inv['source_inventory'],adapter_sha256=inv['adapter_sha256'])
        ending=dict(status='engineering_probe_completed_science_HOLD',diagnostics=result,runtime_restoration=proof,CPU_prepared=prepared,real_GPU_probe_completed=True,scientific_trials_accepted=0,sealed_values_read=False,original_200_trials_replaced=False,retry_authorized=False)
        exit_code=0
    except BaseException as exc:
        ending=dict(status='engineering_probe_failed_science_HOLD',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc(),real_GPU_probe_completed=False,scientific_trials_accepted=0,sealed_values_read=False,retry_authorized=False)
        rec.emit('probe_exception',**ending)
    finally:
        if ending is None:ending=dict(status='engineering_probe_aborted_science_HOLD',scientific_trials_accepted=0)
        ending.update(version=VERSION,exit_code=exit_code,job_id=os.environ['SLURM_JOB_ID'],wall_seconds=time.monotonic()-started,full_Slurm_allocation_to_be_charged_once=True,estimated_GPU_cost_not_substituted_for_sacct=True,arrays_written=rec.arrays_written)
        rec.emit('probe_end',status=ending['status'],exit_code=exit_code)
        ending['events_sha256']=sha(out/'events.jsonl');publish(out/'completion.json',ending)
    return exit_code

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True);parser.add_argument('--config-sha256',required=True);parser.add_argument('--run-gpu',action='store_true');parser.add_argument('--root-authorization',type=Path);parser.add_argument('--root-authorization-sha256')
    args=parser.parse_args();require(sha(args.config)==args.config_sha256,'configuration SHA mismatch')
    if args.run_gpu:
        require(args.root_authorization is not None and args.root_authorization_sha256 is not None,'separate root authorization required')
        return run_gpu(args.config,args.root_authorization,args.root_authorization_sha256)
    result,_,_=prepare_only(args.config);print(dump(result));return 0
if __name__=='__main__':raise SystemExit(main())
