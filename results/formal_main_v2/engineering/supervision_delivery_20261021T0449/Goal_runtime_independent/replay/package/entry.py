"""New exact-five runtime. Independent contexts; no legacy package global changes."""
from __future__ import annotations
import argparse,copy,fcntl,hashlib,importlib.util,json,os,re,sys,time,traceback,resource
from contextlib import ExitStack,contextmanager
from datetime import datetime,timezone
from pathlib import Path
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
S=P/'snapshots/formal_main_v2_run_564be0995e'
PKG='scripts/ops/formal_goal_remaining5_gate_v1'
VERSION='goal-remaining5-prospective-single-attempt-v1'
WRAPPER=P/'scripts/ops/formal_action_deployment_v1/wrapper.py'
WSHA='d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33'
LEGACY=P/'scripts/ops/formal_evaluation_adapter.py'
LSHA='b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd'
THREADS={'OMP_NUM_THREADS':'7','OPENBLAS_NUM_THREADS':'7','MKL_NUM_THREADS':'7','TF_NUM_INTRAOP_THREADS':'7','TF_NUM_INTEROP_THREADS':'1','TOKENIZERS_PARALLELISM':'false','MUJOCO_GL':'egl','LIBERO_CONFIG_PATH':str(P/'configs/libero_runtime'),'PYTHONPATH':str(S/'src'),'PYTHONDONTWRITEBYTECODE':'1'}
RESOURCES={'partition':'L40','gres':'gpu:l40:1','cpus_per_task':7,'mem':'64G','wall_seconds':7200,'no_requeue':True,'excluded_nodes':['gpu4020']}
def scope_module():
 path=Path(__file__).parent/'scope.py'
 if hashlib.sha256(path.read_bytes()).hexdigest()!='f0a9b1d2be86ad62260c0b083822273a1089bc3cb98e4946fe0ba18e167b718b':raise ValueError('exact scope source differs before import')
 spec=importlib.util.spec_from_file_location('_exact_goal_remaining5_scope',path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
scope=scope_module();PACKAGE_FILES=scope.PACKAGE_FILES
context=scope.context
def same(a, b):
    return json.dumps(a, sort_keys=True, separators=(',', ':'), allow_nan=False) == json.dumps(b, sort_keys=True, separators=(',', ':'), allow_nan=False)

def require(ok, msg):
    if not ok:
        raise ValueError(msg)

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for raw in iter(lambda: f.read(8 << 20), b''):
            h.update(raw)
    return h.hexdigest()

def require_path(p, expected):
    p = Path(p)
    require(p == expected and p.is_absolute() and (p.resolve() == p) and (not any((x.is_symlink() for x in [p, *p.parents]))), 'exact non-link registered path required')
    return p

def read(p, pin=None):
    if pin is not None:
        require(re.fullmatch('[0-9a-f]{64}', str(pin)) and sha(p) == pin, 'file SHA differs: ' + str(p))
    return json.loads(Path(p).read_bytes())

def load(p, name, pin):
    require(sha(p) == pin, 'module SHA differs before import')
    spec = importlib.util.spec_from_file_location(name, p)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def ref(p):
    return dict(path=str(p), sha256=sha(p))

def validate_authorization(ctx, a, config_sha, manifest_sha, entry_sha):
    fixed = {'schema': 'formal_main_v2', 'kind': 'root_goal_remaining5_single_attempt_authorization', 'version': VERSION, 'status': 'approved', 'reviewed_by': 'root', 'stage_key': ctx.stage_key, 'pair_key': ctx.pair_key, 'config_sha256': config_sha, 'package_manifest_sha256': manifest_sha, 'entrypoint_sha256': entry_sha, 'maximum_gpu_jobs': 1, 'maximum_attempts': 1, 'maximum_wall_seconds': 7200, 'counts_against_8_GPU_slots': True, 'automatic_retry': False, 'scientific_release': False, 'original_goal200_HOLD': True, 'new_Goal_science_HOLD': True, 'maximum_trials': 200, 'maximum_total_control_steps': 60000, 'maximum_total_policy_queries': 7600, 'policy_watchdog_seconds': 60.0, 'raw_observation_root': str(ctx.RAW), 'root_storage_decision': ctx.storage_decision, 'root_fixed_design': {'path': ctx.root_decision['path'], 'sha256': ctx.root_decision['sha256']}, 'resources': RESOURCES, 'dispatch_record_path': str(ctx.DISPATCH), 'reservation_path': str(ctx.RESERVATION)}
    require(all((same(a.get(k), v) for k, v in fixed.items())), 'new exact Goal full200 root authorization required')
    require(set(a) == set(fixed) | {'root_review', 'independent_review', 'original_invocation'}, 'unexpected authorization fields')
    require(a['root_review'] != a['independent_review'], 'root and independent review must differ')
    require(type(a['original_invocation']) is dict and set(a['original_invocation'])=={'path','sha256'} and a['original_invocation']['path']==str(ctx.ORIGINAL) and re.fullmatch('[0-9a-f]{64}',str(a['original_invocation']['sha256'])), 'exact genuine prepared invocation reference required')
    for role in ('root', 'independent'):
        validate_review_ref(ctx, a[role + '_review'], role)

def validate_review_ref(ctx, value, role):
    require(role in ('root', 'independent') and isinstance(value, dict) and (set(value) == {'path', 'sha256'}), 'readiness reference must contain exactly path and SHA')
    require(value['path'] == str(ctx.BASE / (role + '_readiness.json')) and isinstance(value['sha256'], str) and re.fullmatch('[0-9a-f]{64}', value['sha256']), 'exact new readiness path and 64-hex SHA required before target I/O')
    return value

def check_review(ctx, value, role, manifest_sha, config_sha):
    fixed = {'schema': 'formal_main_v2', 'kind': 'goal_remaining5_single_attempt_CPU_readiness', 'status': 'passed', 'reviewed_by': role, 'version': VERSION, 'package_manifest_sha256': manifest_sha, 'config_sha256': config_sha, 'original_chain_preserved': True, 'observer_gaps_fixed': True, 'paired_input_gate_CPU_passed': True, 'pre_policy_pair_equality_gate': True, 'all_query_input_integrity_gate': True, 'original_policy_error_retained_then_halt': True, 'full200_bound_tests_passed': True, 'original_typed_raw_consumer_ready': True, 'two_root_storage_contract_verified': True, 'real_GPU_acceptance': False, 'scientific_release': False}
    require(all((same(value.get(k), v) for k, v in fixed.items())), 'complete matching CPU-only readiness required')

def validate_dispatch(ctx, d, res, a, auth_sha, job, reservation_sha):
    fixed = {'schema': 'formal_main_v2', 'kind': 'root_goal_remaining5_held_dispatch', 'status': 'held_registered_before_release', 'stage_key': ctx.stage_key, 'pair_key': ctx.pair_key, 'job_id': job, 'authorization': {'path': str(ctx.AUTH), 'sha256': auth_sha}, 'request_token': 'cti-goal-remaining5-v1:' + ctx.pair_key + ':' + auth_sha, 'capacity_limit_all_GPU_modes': 8, 'reserved_slots': 1, 'maximum_attempts': 1, 'new_submissions': 1, 'no_requeue': True, 'scientific_release': False, 'resources': RESOURCES}
    require(all((same(d.get(k), v) for k, v in fixed.items())), 'exact held ACK registration must precede release')
    require(isinstance(d.get('occupied_job_ids'), list) and len(set(d['occupied_job_ids'])) == len(d['occupied_job_ids']) <= 8 and (job in d['occupied_job_ids']), 'one registered slot within all-GPU eight limit required')
    require(re.fullmatch('[0-9a-f]{64}', str(d.get('state_after_sha256'))), 'root writer-lock/CAS snapshot identity missing')
    require(d.get('reservation') == {'path': str(ctx.RESERVATION), 'sha256': reservation_sha}, 'exact root reservation pin missing')
    rf = {'schema': 'formal_main_v2', 'kind': 'root_goal_remaining5_GPU_slot_reservation', 'status': 'approved_for_exact_remaining5_pair', 'stage_key': ctx.stage_key, 'pair_key': ctx.pair_key, 'authorization': fixed['authorization'], 'reserved_slots': 1, 'capacity_limit_all_GPU_modes': 8, 'maximum_wall_seconds': 7200, 'automatic_retry': False, 'scientific_release': False}
    require(all((same(res.get(k), v) for k, v in rf.items())), 'new full200 reservation required; old probe reservation forbidden')

def validate_prefix(ctx, inv, legacy, prefix):
    panelpath = P/'configs/manifests/formal_main_v2/libero_goal/initial_states/development.json'
    panel = read(panelpath, 'ce8e3d31ab8f7616c87dd4d4031af41825713907ac184c6ea5b01d9040985aa9')
    require(panel['suite'] == 'libero_goal' and panel['split'] == 'development', 'original development panel only')
    keys = ('trial_id', 'state_trial_id', 'task_id', 'task_name', 'source_state_index', 'initial_state_sha256', 'method')
    with legacy.source_imports(S):
        from cti_vla.evaluation import formal_trials
        actual = [{k: v for k, v in formal_trials._identity(panel, state, mid).items() if k in keys} for state in panel['states'] for mid in ctx.methods]
    require(len(prefix) == 200 and actual == [{k: row[k] for k in keys} for row in prefix], 'exact original full200 identity/order required before observer creation')
    require(len({x['state_trial_id'] for x in actual}) == 100 and all((x['task_id'] == 9 and x['source_state_index'] == 43 for x in actual[-2:])), 'fixed full200 endpoint differs')
    return dict(original_panel=ref(panelpath),panel_is_original_input_not_old_output=True, original_fixed200_identity_order=True, unique_development_states=100)

def execute(ctx, config, auth, job, package, gate):
    require(not ctx.OUTPUT.exists(), 'one attempt already exists; retry forbidden')
    read(R / ctx.storage_decision['path'], ctx.storage_decision['sha256'])
    storage = load(P / PKG / 'storage.py', 'goal_remaining5_storage', package['files'][PKG+'/storage.py'])
    storage.verify_storage(ctx)
    raw_claim = storage.claim_raw(ctx)
    runtime_log_files = redirect_runtime_output(ctx)
    ctx.OUTPUT.mkdir(parents=True, exist_ok=False)
    outer = ctx.OUTPUT / 'outer'
    outer.mkdir()
    eventpath = outer / 'events.jsonl'
    events = []
    observer = None
    result = None
    errors = []
    restored = False
    started = time.perf_counter()
    code = 1

    def emit(event, **fields):
        fixed = dict(seq=len(events), event=event, utc=datetime.now(timezone.utc).isoformat(), job_id=job, scientific_trials_added=0)
        require(all((k not in fixed or fixed[k] == v for k, v in fields.items())), 'event field collides with outer identity')
        row = dict(fields)
        row.update(fixed)
        if len(events) >= 1024:raise MetadataBoundAbort('outer event count exceeds bound; prefix retained')
        raw = bounded_json_bytes(row,65536)
        with eventpath.open('ab') as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        events.append(row)
    inv = wrapper = original_ctx = legacy = None
    original_run = original_code = None
    try:
        inv, wrapper, original_ctx, legacy = prepare_original(ctx)
        require(sha(ctx.ORIGINAL)==auth['original_invocation']['sha256'], 'root authorized exact prepared invocation differs')
        require(not list((P / 'results/formal_main_v2/adapter_invocations').glob(job + '_*')), 'prior adapter invocation for this job forbids retry')
        original_run = legacy.run
        original_code = original_run.__code__
        runtime = original_ctx['runtime']
        contract = original_ctx['execution_contract']
        original = original_ctx['original_plan']
        prefix = read(ctx.SPEC, ctx.spec_sha)['rows']
        prefix_proof = validate_prefix(ctx, inv, legacy, prefix)
        ob = load(P / PKG / 'paired_input_gate_v1.py', 'g200_paired_input_gate', package['files'][PKG + '/paired_input_gate_v1.py'])
        ad = load(P / PKG / 'ast_gate_v2.py', 'g200_paired_input_ast', package['files'][PKG + '/ast_gate_v2.py'])
        observer = ob.PairedInputGate(ctx, ctx.RAW / 'observer', allow_cpu_fixture=False, raw_observation_root=ctx.RAW)
        require(observer.allow_cpu_fixture is False and observer.sink is None, 'production observer cannot use CPU fixtures or injected sinks')
        a = copy.deepcopy(original_ctx['args'])
        before_args = copy.deepcopy(vars(a))
        a.output = ctx.OUTPUT / 'original_run'
        a.stop_after = 200
        require({k for k in vars(a) if vars(a)[k] != before_args[k]} == {'output', 'stop_after'}, 'only prospective output and explicit full200 stop may change')
        emit('engineering_start', raw_observation_claim=raw_claim, runtime_log_files=runtime_log_files, pair_key=ctx.pair_key, version=VERSION, authorization_sha256=gate['auth_sha'], package_manifest_sha256=gate['manifest_sha'], original_invocation=ref(ctx.ORIGINAL), environment={k: os.environ.get(k) for k in list(THREADS) + ['CUDA_VISIBLE_DEVICES', 'SLURM_JOB_ID', 'SLURMD_NODENAME']}, original_argument_changes={'output': str(a.output), 'stop_after': 200}, prefix_identity_proof=prefix_proof, original_adapter_run_code_sha256=legacy.code_sha(original_run), original_actions_forced=False)

        def runtime_emit(event, **fields):
            emit(event, **fields)
            if event in ('asset_metadata_compat_load_start', 'asset_metadata_compat_load_complete', 'deployment_base_load_start', 'deployment_base_load_complete', 'goal_component_load_start', 'goal_component_load_complete'):
                observer.capture('existing_loader_event:' + event)

        def scientific_runner():
            from cti_vla.evaluation import libero_runtime, formal_trials
            with ad.observer_scope(libero_runtime, formal_trials, observer, emit=emit):
                with bounded_adapter_scope(ctx,legacy,job) as metadata_guard:
                    outcome=legacy.run(a, mode='evaluate', source_root=S, source_inventory=Path(inv['source_inventory']), adapter_sha256=LSHA, resume=False)
                emit('bounded_adapter_metadata_restored',storage=metadata_guard,original_run_source_unchanged=True)
                return outcome
        with legacy.source_imports(S):
            expected_assets = runtime.expected_asset_identities(project_root=P, source_root=S, contract=contract['runtime_contract'], asset_contract=original['invocation'].get('downstream_asset_compatibility'))
            result = runtime.run_with_asset_contexts(scientific_runner, project_root=P, source_root=S, contract=contract['runtime_contract'], asset_contract=original['invocation'].get('downstream_asset_compatibility'), emit=runtime_emit)
        proof = runtime.verify_runtime_events(events, contract['runtime_contract'], expected_asset_identities=expected_assets)
        require(proof['all_source_and_binding_contexts_restored'], 'original action/component/loading context not restored')
        restored = True
        finish = observer.finish()
        require(finish['original_prefix_trials'] == 200 and finish['scientific_trials_added'] == 0 and (finish['exact_paired_t0_checks'] == 100) and (finish['runtime_context'] == 'real_environment_engineering'), 'incomplete engineering prefix')
        emit('engineering_prefix_returned', runtime_proof=proof, observer_finish=finish)
        code = 0
    except BaseException as error:
        errors.append(dict(error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc()))
        traceback.print_exception(type(error), error, error.__traceback__)
    finally:
        if legacy is not None and (legacy.run is not original_run or original_run.__code__ is not original_code):
            code = 1
            errors.append(dict(error_type='BindingIntegrity', error='original legacy run changed'))
        if inv is not None:
            try:
                require(sha(ctx.ORIGINAL) == auth['original_invocation']['sha256'] and sha(WRAPPER) == WSHA and (sha(LEGACY) == LSHA), 'original entry source changed')
                for path, pin in inv['watched_files'].items():
                    require(sha(Path(path)) == pin, 'watched original input changed')
                for path, pin in package['files'].items():
                    require(sha(P / path) == pin, 'published observer package changed')
            except BaseException as error:
                code = 1
                errors.append(dict(error_type=type(error).__name__, error=str(error)))
        archived_adapter = []
        try:
            adir = ctx.OUTPUT / 'original_run/adapter_invocations'
            adir.mkdir(parents=True, exist_ok=True)
            for src in sorted((P / 'results/formal_main_v2/adapter_invocations').glob(job + '_*')):
                require(src.is_file() and src.suffix in ('.json', '.jsonl') and (not src.is_symlink()), 'unexpected adapter artifact')
                b = src.read_bytes()
                dst = adir / src.name
                with dst.open('xb') as f:
                    f.write(b)
                require(sha(src) == sha(dst), 'adapter changed during exact archive')
                archived_adapter.append(dict(source=str(src), path=str(dst), sha256=sha(dst), bytes=len(b)))
            if code == 0:
                require(len(archived_adapter) == 2, 'exact one original adapter pair required')
        except BaseException as error:
            code = 1
            errors.append(dict(error_type=type(error).__name__, error=str(error)))
        complete = dict(schema='formal_main_v2', kind='goal_remaining5_engineering_attempt', version=VERSION, status='returned_200_prospective_pending_terminal_review' if code == 0 else 'failed_no_retry', job_id=job, exit_code=code, authorization_sha256=gate['auth_sha'], package_manifest_sha256=gate['manifest_sha'], adapter_artifacts=archived_adapter, original_runtime_restored=restored, raw_observation_root=str(ctx.RAW), raw_observation_claim=raw_claim, errors=errors, observer_failed=getattr(observer, 'dead', None), runtime_context='real_environment_engineering', last_paired_input_abort=getattr(observer, 'last_gate_abort', None), accepted_queries_retained=sum(getattr(observer, 'query_counts', {}).values()), executed_policy_steps_retained=getattr(observer, 'executed_policy_steps', 0), paired_t0_checks_retained=len(getattr(observer, 'paired_keys', set())), last_observer_abort=getattr(observer, 'last_abort', None), observer_begun=getattr(observer, 'begun', 0), observer_finished=getattr(observer, 'finished', 0), maximum_attempts=1, automatic_retry=False, original_actions_forced=False, scientific_trials_added=0, original_goal200_HOLD=True, new_Goal_science_HOLD=True, final_release=False, wall_seconds=time.perf_counter() - started, raw_event_sha256=sha(eventpath) if eventpath.exists() else None, cost_scope='Charge complete Slurm allocation once, including loading, observer I/O and failures; never scientific timing.')
        complete_raw=bounded_json_bytes(complete,8*1024*1024,indent=2)
        with (outer / 'completion.json').open('xb') as f:f.write(complete_raw)
        receipts = []
        for artifact in archived_adapter:
            if artifact['path'].endswith('.json'):
                item = read(Path(artifact['path']))
                receipts.append({'path': artifact['path'], 'status': item['status'], 'runner_status': item.get('runner_status')})
        parent = dict(schema='formal_main_v2', kind='goal_remaining5_typed_parent_receipt', execution_version=VERSION, job_id=job, wrapper_sha256=sha(ctx.ENTRY), stage_completed_claimed=False, status='returned' if code == 0 else 'failed', exit_code=code, wall_seconds=complete['wall_seconds'], source_completion_sha256=sha(outer / 'completion.json'), adapter_artifacts=archived_adapter, adapter_receipts=receipts, scientific_trials_added=0, original_goal200_HOLD=True, final_release=False)
        parent_raw=bounded_json_bytes(parent,8*1024*1024,indent=2)
        with (outer / 'typed_parent.json').open('xb') as f:f.write(parent_raw)
    return code


def validate_config(ctx,c):
 fixed={'schema':'formal_main_v2','kind':'goal_remaining5_single_attempt_configuration','version':VERSION,'pair_key':ctx.pair_key,'stage_key':ctx.stage_key,'suite':'libero_goal','seed':ctx.seed,'tokens':ctx.tokens,'method_ids':ctx.methods,'runtime_seed':17,'environment_seed':0,'maximum_trials':200,'unique_development_states':100,'wait_steps':10,'action_chunk':8,'max_control_steps':300,'maximum_attempts':1,'automatic_retry':False,'scientific_trials_added':0,'original200_HOLD':True,'new_Goal_science_HOLD':True,'historical_actions_forced':False,'resources':RESOURCES,'planned_invocation_path':str(ctx.ORIGINAL),'plans':ctx.plans,'prefix':{'path':str(ctx.SPEC),'sha256':ctx.spec_sha},'output':str(ctx.OUTPUT),'final_evaluation_enabled':False,'maximum_total_control_steps':60000,'maximum_total_policy_queries':7600,'maximum_total_wait_steps':2000,'policy_watchdog_seconds':60.0,'raw_observation_root':str(ctx.RAW),'observer_root':str(ctx.RAW/'observer'),'root_storage_decision':ctx.storage_decision,'root_fixed_design':ctx.root_decision}
 require(all(same(c.get(k),v) for k,v in fixed.items()) and set(c)==set(fixed)|{'schema_note'},'exact five-pair immutable configuration required')
def prepare_original(ctx):
 inv=read(ctx.ORIGINAL)
 require_path(ctx.ORIGINAL,ctx.ORIGINAL)
 for name,value in ctx.plans.items():
  if name=='specification':continue
  path=P/value['path'];read(path,value['sha256'])
 effective=read(P/ctx.plans['effective_plan']['path'],ctx.plans['effective_plan']['sha256'])
 require(set(inv)==set(effective['invocation'])|{'registered_utc','plan_sha256','runtime_readiness'} and {k:inv[k] for k in effective['invocation']}==effective['invocation'],'genuine prepared invocation must exactly extend pinned effective plan')
 require(inv['execution_manifest']==str(P/ctx.plans['execution_manifest']['path']) and inv['execution_manifest_sha256']==ctx.plans['execution_manifest']['sha256'],'own exact original execution manifest')
 require(inv['scientific_plan']==ctx.plans['scientific_plan'] and inv['action_execution_contract']==ctx.plans['execution_contract'],'own exact scientific/action plans')
 wrapper=load(WRAPPER,'goal_r5_original_wrapper_'+ctx.pair_key,WSHA)
 original_ctx=wrapper.verify(inv,project=P)
 legacy=load(LEGACY,'goal_r5_original_legacy_'+ctx.pair_key,LSHA)
 a=original_ctx['args']
 require(Path(a.development_panel)==P/'configs/manifests/formal_main_v2/libero_goal/initial_states/development.json','exact original input development panel, no fabricated historical output')
 require(a.policy_watchdog_seconds==60.0 and a.mode=='evaluate' and not a.resume and not a.prepare_only and Path(a.output)==Path(inv['run_root']),'original no-resume settings/watchdog')
 require(inv['suite']=='libero_goal' and inv['stage']=='development' and inv['method_ids']==ctx.methods,'exact pair method scope')
 require(not any(getattr(a,k,None) is not None for k in ('final_registry','sealed_final','release','release_sha256')),'final/sealed forbidden')
 manifest=read(Path(inv['execution_manifest']),inv['execution_manifest_sha256'])
 require([m['identity']['method_id'] for m in manifest['methods']]==ctx.methods,'own A/B loading order')
 for m in manifest['methods']:
  mid=m['identity']['method_id'];path=Path(m['checkpoint'])
  expected=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_goal')/('k'+str(ctx.tokens))/('seed'+str(ctx.seed))/mid[0]/'best.pt'
  require_path(path,expected);st=path.stat()
  require(sha(path)==m['identity']['checkpoint_sha256'] and st==path.stat(),'own selected checkpoint raw bytes')
 return inv,wrapper,original_ctx,legacy

class MetadataBoundAbort(BaseException):
 """Stop original adapter/output publication before a bounded metadata overflow."""
@contextmanager
def bounded_adapter_scope(ctx,legacy,job):
 # Only this fresh legacy module instance's I/O helpers; original run code/source,
 # values, file names and original serializer remain intact. Always restore.
 append=legacy.append;publish=legacy.publish
 seen={'append_calls':0,'publish_calls':0,'paths':{}}
 def inspect(path,value,*,is_append):
  path=Path(path)
  expected=P/'results/formal_main_v2/adapter_invocations'
  require_path(path,path)
  if path.parent!=expected or not re.fullmatch(re.escape(job)+r'_[0-9a-f]{32}[.](jsonl|json)',path.name):
   raise MetadataBoundAbort('unregistered adapter output path')
  encoded=(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,**({} if is_append else {'indent':2}))+'\n').encode('utf8')
  limit=4194304
  existing=path.stat().st_size if is_append and path.exists() else 0
  if len(encoded)+existing>limit:
   raise MetadataBoundAbort('adapter metadata prewrite 4MiB file bound exceeded; prefix retained')
  if is_append:
   seen['append_calls']+=1
   if seen['append_calls']>1024:raise MetadataBoundAbort('adapter event count exceeded')
  else:
   seen['publish_calls']+=1
   if seen['publish_calls']>1:raise MetadataBoundAbort('adapter receipt duplicate publication')
  seen['paths'][str(path)]=len(encoded)+existing
 def checked_append(path,value):
  inspect(path,value,is_append=True)
  return append(path,value)
 def checked_publish(path,value):
  inspect(path,value,is_append=False)
  return publish(path,value)
 legacy.append=checked_append;legacy.publish=checked_publish
 try:yield seen
 finally:
  intact=legacy.append is checked_append and legacy.publish is checked_publish
  legacy.append=append;legacy.publish=publish
  if not intact:raise MetadataBoundAbort('adapter bounded metadata bindings changed')

def bounded_json_bytes(value,limit,*,indent=None):
 try:raw=(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=indent)+'\n').encode('utf-8')
 except BaseException as error:raise MetadataBoundAbort('metadata serialization failed; original prefix retained') from error
 if len(raw)>limit:raise MetadataBoundAbort('exact serialized metadata exceeds bound; original prefix retained')
 return raw

def redirect_runtime_output(ctx):
 # Independent exact files, never co-open a Slurm-daemon output file.
 resource.setrlimit(resource.RLIMIT_FSIZE,(2147483648,2147483648))
 result={}
 for fd,name in ((1,'runtime.stdout'),(2,'runtime.stderr')):
  path=ctx.RAW/name;require_path(path,path)
  handle=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  require(os.fstat(handle).st_uid==os.getuid(),'runtime log owner')
  os.dup2(handle,fd);os.close(handle);result[str(fd)]=str(path)
 return result
def _verify_sources(ctx,expected_manifest_sha):
 require(Path(__file__).resolve()==ctx.ENTRY,'verify only exact published P source')
 package=read(ctx.MANIFEST,expected_manifest_sha)
 require(package.get('schema')=='formal_main_v2' and package.get('version')==VERSION and set(package.get('files',{}))==PACKAGE_FILES,'complete exact five package closure')
 for path,pin in package['files'].items():require_path(P/path,P/path);require(sha(P/path)==pin,'published source changed')
 validate_config(ctx,read(ctx.CONFIG,ctx.config_sha))
 for key in scope.KEYS:
  c=context(key);validate_config(c,read(c.CONFIG,c.config_sha))
 decision=read(R/ctx.root_decision['path'],ctx.root_decision['sha256'])
 require(decision['status']=='fixed_five_design_adopted_runtime_and_GPU_HOLD' and decision['GPU_execution_authorized'] is False,'design cannot authorize GPU')
 read(R/ctx.storage_decision['path'],ctx.storage_decision['sha256'])
 return package
def _verify(ctx,manifest_sha,must_be_fresh):
 package=_verify_sources(ctx,manifest_sha)
 inv,wrapper,original_ctx,legacy=prepare_original(ctx)
 prefix=read(ctx.SPEC,ctx.spec_sha)['rows'];identity=validate_prefix(ctx,inv,legacy,prefix)
 if must_be_fresh:
  storage=load(P/PKG/'storage.py','goal_r5_verify_storage',package['files'][PKG+'/storage.py'])
  capacity=storage.verify_storage(ctx,must_be_fresh=True,aggregate_pair_keys=scope.KEYS)
 else:
  capacity={'status':'not_rechecked_existing_ACK_source_identity_only','fresh_submission_capacity_verified':False,'new_storage_paths_created':False,'new_submission_authorized':False}

 return {'status':'passed_metadata_source_capacity_only','stage_key':ctx.stage_key,'pair_key':ctx.pair_key,'package_manifest_sha256':manifest_sha,'config_sha256':sha(ctx.CONFIG),'original_invocation':ref(ctx.ORIGINAL),'identity':identity,'storage':capacity,'new_GPU_submissions':0,'actual_GPU_runtime_verified':False,'GPU_execution_authorized':False,'original200_HOLD':True,'final_release':False}
def verify_published(pair_key,manifest_sha,*,must_be_fresh=True):
 require(type(must_be_fresh) is bool,'explicit fresh mode')
 return _verify(context(pair_key),manifest_sha,must_be_fresh)
def verify_existing_metadata(pair_key,manifest_sha):
 # Read-only ACK reconciliation; never claims freshness or a second authorization.
 result=_verify(context(pair_key),manifest_sha,False)
 result['status']='passed_existing_ACK_metadata_source_only';result['existing_metadata_only']=True;result['new_submission_authorized']=False;result['new_GPU_submission_allowed']=False
 return result
def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pair-key',required=True,choices=scope.KEYS);parser.add_argument('--authorization',type=Path);parser.add_argument('--authorization-sha256');parser.add_argument('--verify',action='store_true');parser.add_argument('--package-manifest-sha256');args=parser.parse_args(argv)
 ctx=context(args.pair_key)
 if args.verify:
  require(args.authorization is None and args.authorization_sha256 is None and re.fullmatch('[0-9a-f]{64}',str(args.package_manifest_sha256)),'verify exact package pin only')
  print(json.dumps(verify_published(args.pair_key,args.package_manifest_sha256),sort_keys=True));return 0
 require(args.authorization is not None and args.authorization_sha256 is not None and args.package_manifest_sha256 is None,'execute exact root authorization')
 require(os.name=='posix' and Path(__file__).resolve()==ctx.ENTRY,'exact published entry only')
 job=os.environ.get('SLURM_JOB_ID','');require(re.fullmatch('[1-9][0-9]*',job),'one Slurm job')
 require(os.environ.get('CTI_GOAL_REMAINING5_PAIR_KEY')==ctx.pair_key and os.environ.get('CTI_GOAL_REMAINING5_AUTH_SHA256')==args.authorization_sha256,'exact scheduler pair/auth selection')
 require_path(args.authorization,ctx.AUTH);require(os.environ.get('SLURM_RESTART_COUNT','0')=='0','no restart')
 require(all(os.environ.get(k)==v for k,v in THREADS.items()) and os.environ.get('SLURM_CPUS_PER_TASK')=='7' and os.environ.get('SLURMD_NODENAME')!='gpu4020','original environment/resources')
 manifest_sha=sha(ctx.MANIFEST);package=_verify_sources(ctx,manifest_sha)
 config=read(ctx.CONFIG);auth=read(ctx.AUTH,args.authorization_sha256)
 validate_authorization(ctx,auth,sha(ctx.CONFIG),manifest_sha,sha(ctx.ENTRY))
 for role in ('root','independent'):
  review=validate_review_ref(ctx,auth[role+'_review'],role)
  check_review(ctx,read(Path(review['path']),review['sha256']),role,manifest_sha,sha(ctx.CONFIG))
 require_path(ctx.DISPATCH,ctx.DISPATCH);require_path(ctx.RESERVATION,ctx.RESERVATION)
 validate_dispatch(ctx,read(ctx.DISPATCH),read(ctx.RESERVATION),auth,args.authorization_sha256,job,sha(ctx.RESERVATION))
 inv=read(ctx.ORIGINAL,auth['original_invocation']['sha256'])
 with ExitStack() as stack:
  names=[inv['stage_key'],*[f"{inv['suite']}_{inv['stage']}_{mid}" for mid in inv['method_ids']]]
  require(len(names)==len(set(names)),'unique original stage/method locks')
  for name in sorted(names):
   require(re.fullmatch('[A-Za-z0-9_-]+',name),'safe original lock key')
   path=P/'results/formal_main_v2/stage_locks'/(name+'.lock');f=stack.enter_context(path.open('a'));fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  return execute(ctx,config,auth,job,package,{'auth_sha':args.authorization_sha256,'manifest_sha':manifest_sha})
if __name__=='__main__':raise SystemExit(main())
