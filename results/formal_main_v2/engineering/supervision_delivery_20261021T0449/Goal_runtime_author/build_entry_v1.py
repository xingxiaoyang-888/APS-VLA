from pathlib import Path
import ast,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_remaining5_runtime_20261021T0449';Q=D/'package';O=R/'scripts/ops/formal_goal_full200_gate_v1'
raw=(O/'entry.py').read_text()
tree=ast.parse(raw)
scoped={'validate_authorization','validate_review_ref','check_review','validate_dispatch','validate_prefix','execute'}
scope_names={'STAGE':'stage_key','BASE':'BASE','OUTPUT':'OUTPUT','ENTRY':'ENTRY','CONFIG':'CONFIG','MANIFEST':'MANIFEST','AUTH':'AUTH','DISPATCH':'DISPATCH','RESERVATION':'RESERVATION','RAW':'RAW','ORIGINAL':'ORIGINAL','PREFIX_SHA':'spec_sha','STORAGE_DECISION':'storage_decision'}
class Rebind(ast.NodeTransformer):
 def visit_Name(self,n):
  if n.id=='ctx':return ast.copy_location(ast.Name(id='original_ctx',ctx=n.ctx),n)
  if n.id in scope_names:return ast.copy_location(ast.Attribute(value=ast.Name(id='ctx',ctx=ast.Load()),attr=scope_names[n.id],ctx=n.ctx),n)
  if n.id=='ROOT_DECISION_REL':return ast.copy_location(ast.Subscript(value=ast.Attribute(value=ast.Name(id='ctx',ctx=ast.Load()),attr='root_decision',ctx=ast.Load()),slice=ast.Constant('path'),ctx=ast.Load()),n)
  if n.id=='ROOT_DECISION_SHA':return ast.copy_location(ast.Subscript(value=ast.Attribute(value=ast.Name(id='ctx',ctx=ast.Load()),attr='root_decision',ctx=ast.Load()),slice=ast.Constant('sha256'),ctx=ast.Load()),n)
  return n
 def visit_Call(self,n):
  n=self.generic_visit(n)
  if isinstance(n.func,ast.Name) and n.func.id in scoped|{'prepare_original'}:n.args.insert(0,ast.Name(id='ctx',ctx=ast.Load()))
  return n
functions=[]
for n in tree.body:
 if isinstance(n,ast.FunctionDef) and n.name in scoped:
  n=Rebind().visit(n);n.args.args.insert(0,ast.arg(arg='ctx'));ast.fix_missing_locations(n);functions.append(ast.unparse(n))
 elif isinstance(n,ast.FunctionDef) and n.name in {'same','require','sha','require_path','read','load','ref'}:
  functions.append(ast.unparse(n))
s='\n\n'.join(functions)+'\n'
s=s.replace('goal_full200','goal_remaining5').replace('cti-goal-full200-v1:',"cti-goal-remaining5-v1:")
s=s.replace("'cti-goal-remaining5-v1:' + auth_sha","'cti-goal-remaining5-v1:' + ctx.pair_key + ':' + auth_sha")
s=s.replace("'approved_for_exact_full200'","'approved_for_exact_remaining5_pair'")
s=s.replace("['A256_seed17', 'B256_seed17']","ctx.methods")
s=s.replace("P / PKG / 'specification.json'","ctx.SPEC")
s=s.replace("storage = load(P / PKG / 'storage.py', 'goal200_storage', STORAGE_SHA)","storage = load(P / PKG / 'storage.py', 'goal_remaining5_storage', package['files'][PKG+'/storage.py'])")
s=s.replace('storage.verify_storage()','storage.verify_storage(ctx)').replace('storage.claim_raw()','storage.claim_raw(ctx)')
s=s.replace("observer = ob.PairedInputGate(ctx.OUTPUT / 'observer',","observer = ob.PairedInputGate(ctx, ctx.RAW / 'observer',")
s=s.replace("== ISHA", "== auth['original_invocation']['sha256']")
# Exact auth carries the future genuine prepared invocation pin; no circular fake readiness.
s=s.replace("'root_review', 'independent_review'","'root_review', 'independent_review', 'original_invocation'")
needle="require(a['root_review'] != a['independent_review'], 'root and independent review must differ')"
s=s.replace(needle,needle+"\n    require(type(a['original_invocation']) is dict and set(a['original_invocation'])=={'path','sha256'} and a['original_invocation']['path']==str(ctx.ORIGINAL) and re.fullmatch('[0-9a-f]{64}',str(a['original_invocation']['sha256'])), 'exact genuine prepared invocation reference required')")
# Explicit pair on all root decisions and review/dispatch scopes.
s=s.replace("'stage_key': ctx.stage_key,","'stage_key': ctx.stage_key, 'pair_key': ctx.pair_key,")
# verify_prefix shouldn't inject unrelated pair into original input records.
s=s.replace("raw_claim = storage.claim_raw(ctx)","raw_claim = storage.claim_raw(ctx)\n    runtime_log_files = redirect_runtime_output(ctx)")
s=s.replace('inv, wrapper, original_ctx, legacy = prepare_original(ctx)','inv, wrapper, original_ctx, legacy = prepare_original(ctx)\n        require(sha(ctx.ORIGINAL)==auth[\'original_invocation\'][\'sha256\'], \'root authorized exact prepared invocation differs\')')
# The archived original adapter pair is bounded before copying; original production
# write proof is separately audited from its fixed journal schema and row limits.
s=s.replace("b = src.read_bytes()\n            dst", "b = src.read_bytes()\n            require(len(b)<=8*1024*1024, 'adapter archive file exceeds metadata budget')\n            dst")
# Clamp no data; any anomalously huge error record stops final metadata serialization.
s=s.replace("with (outer / 'completion.json').open", "require(len(json.dumps(complete,sort_keys=True,ensure_ascii=False,allow_nan=False).encode())<=8*1024*1024,'terminal completion metadata exceeds bound; raw prefix retained')\n        with (outer / 'completion.json').open")
s=s.replace("with (outer / 'typed_parent.json').open","require(len(json.dumps(parent,sort_keys=True,ensure_ascii=False,allow_nan=False).encode())<=8*1024*1024,'typed parent metadata exceeds bound; raw prefix retained')\n        with (outer / 'typed_parent.json').open")
# Ensure true original invocation lineage enters the outer before any model loading.
s=s.replace("raw_observation_claim=raw_claim, version=VERSION","raw_observation_claim=raw_claim, runtime_log_files=runtime_log_files, pair_key=ctx.pair_key, version=VERSION")
header='''"""New exact-five runtime. Independent contexts; no legacy package global changes."""
from __future__ import annotations
import argparse,copy,fcntl,hashlib,importlib.util,json,os,re,sys,time,traceback,resource
from contextlib import ExitStack
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
 spec=importlib.util.spec_from_file_location('_exact_goal_remaining5_scope',path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
scope=scope_module();PACKAGE_FILES=scope.PACKAGE_FILES
context=scope.context
'''
extra=r'''
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
 storage=load(P/PKG/'storage.py','goal_r5_verify_storage',package['files'][PKG+'/storage.py'])
 capacity=storage.verify_storage(ctx,must_be_fresh=must_be_fresh,aggregate_pair_keys=scope.KEYS)
 return {'status':'passed_metadata_source_capacity_only','stage_key':ctx.stage_key,'pair_key':ctx.pair_key,'package_manifest_sha256':manifest_sha,'config_sha256':sha(ctx.CONFIG),'original_invocation':ref(ctx.ORIGINAL),'identity':identity,'storage':capacity,'new_GPU_submissions':0,'actual_GPU_runtime_verified':False,'GPU_execution_authorized':False,'original200_HOLD':True,'final_release':False}
def verify_published(pair_key,manifest_sha,*,must_be_fresh=True):
 require(type(must_be_fresh) is bool,'explicit fresh mode')
 return _verify(context(pair_key),manifest_sha,must_be_fresh)
def verify_existing_metadata(pair_key,manifest_sha):
 # Read-only ACK reconciliation; never claims freshness or a second authorization.
 result=_verify(context(pair_key),manifest_sha,False)
 result['existing_metadata_only']=True;result['new_submission_authorized']=False
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
'''
out=header+s+'\n'+extra
ast.parse(out)
with (Q/'entry.py').open('x') as f:f.write(out)
print(json.dumps({'status':'new_context_entry_candidate_written','sha256':hashlib.sha256(out.encode()).hexdigest()}))
