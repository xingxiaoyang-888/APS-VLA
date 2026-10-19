"""Candidate-only explicit action execution envelope; no submission or science mutation.

An inner v1 plan remains an immutable description of scientific inputs. It is
never relabelled as proof of a v2 execution. Production readiness is a separate
root artifact and is deliberately absent from this candidate builder.
"""
from __future__ import annotations
import copy
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

SCHEMA = "formal_main_v2"
VERSION = "formal-downstream-action-v1"
PREFIX = "scripts/ops/formal_action_deployment_v1/"
WRAPPER = PREFIX + "wrapper.py"
ENTRY = PREFIX + "entry.py"
CONTRACT = PREFIX + "contract.py"
RUNTIME = PREFIX + "runtime_scope.py"
GATEWAY = PREFIX + "gateway.py"
REVIEWER = PREFIX + "reviewer.py"
CONSUMER = PREFIX + "consumer.py"
EXPECTED_NEW_FILES = {WRAPPER, ENTRY, CONTRACT, RUNTIME, GATEWAY, REVIEWER, CONSUMER}
P = PurePosixPath('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
SOURCE = P / 'snapshots/formal_main_v2_run_564be0995e'
SOURCE_SHA = 'dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e'
INVENTORY = 'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
INVENTORY_SHA = '5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
ACTION_ADAPTER = 'results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py'
ACTION_SHA = 'b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185'
GPU_REFS = {
 'results/formal_main_v2/preflight/heartbeat_20261019T1347/v4_GPU_root_acceptance.json': '3ee503429d703bb9d8da5970a9e183d371defbaf86884b24ae164d6cbc7bc1e9',
 'results/formal_main_v2/engineering/action_v4_actual_independent_0547/terminal_review.json': '613489f84224eaafac36523244ac98e3b81d50624d9da7102b3d5cd1062edbbe',
}
ALLOWED_STAGES = ('development','collect','full','components')
RUNTIME_MUTABLE = {'version','entrypoint','wrapper','wrapper_sha256','support_files','watched_files','root_evidence_sha256'}
RUNTIME_ADDITIONS = {'action_execution_contract','scientific_plan','scientific_plan_sha256'}
INITIAL_METADATA = {f'configs/manifests/formal_main_v2/{suite}/initial_states/{name}' for suite in ('libero_10','libero_spatial','libero_object','libero_goal') for name in ('development.json','final_registry.json')}
FORBIDDEN_SUFFIXES = {'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.init','.pruned_init'}


def require(condition, message):
 if not condition: raise ValueError(message)


def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(8<<20),b''): h.update(block)
 return h.hexdigest()


def signature(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def relative(value):
 require(isinstance(value,str), 'Path must be a string')
 p=PurePosixPath(value)
 require(not p.is_absolute() and str(p)==value and '..' not in p.parts and ':' not in value and '\\' not in value, 'Noncanonical project path')
 require(not any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts), 'No sealed/weight input')
 require(not (set(p.suffixes)&FORBIDDEN_SUFFIXES), 'No payload input')
 require('initial_states' not in p.parts or value in INITIAL_METADATA, 'Only exact registered development or metadata-only registry input allowed')
 return value


def ref(value):
 require(isinstance(value,dict) and set(value)=={'path','sha256'}, 'Exact path/SHA reference required')
 relative(value['path']);require(bool(re.fullmatch('[0-9a-f]{64}',str(value['sha256']))),'Invalid SHA')
 return value


def read_ref(root, value):
 ref(value); root=Path(root).resolve(); p=root/value['path']
 require(p.resolve()==p and p.is_file(),'Noncanonical or missing evidence')
 require(digest(p)==value['sha256'],'Evidence SHA mismatch: '+value['path'])
 return json.loads(p.read_text(encoding='utf-8'),parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON')))


def validate_inner(plan):
 require(isinstance(plan,dict) and plan.get('schema')==SCHEMA and plan.get('kind')=='formal_downstream_plan','Original scientific plan required')
 require(plan.get('plan_sha256')==signature({k:v for k,v in plan.items() if k!='plan_sha256'}),'Original plan signature mismatch')
 inv=plan['invocation']
 require(inv.get('version')=='formal-downstream-root-v1' and inv.get('kind')=='formal_downstream_invocation','Original v1 scientific plan required')
 require(inv.get('stage') in ALLOWED_STAGES, 'Candidate never permits final evaluation')
 require(inv.get('source_root')==str(SOURCE) and inv.get('source_sha256')==SOURCE_SHA,'Frozen source identity mismatch')
 require(inv.get('scientific_settings_changed') is False and inv.get('final_values_read_locally') is False,'Science/final invariant missing')
 require(type(inv.get('resume')) is bool,'Explicit resume flag required')
 require(inv.get('source_inventory_sha256')==INVENTORY_SHA,'Source inventory mismatch')
 require(plan.get('output_relative')==str(PurePosixPath(inv['run_root']).relative_to(P)),'Output projection mismatch')
 relative(plan['output_relative']);relative(plan['invocation_relative'])
 argv=inv.get('argv');require(isinstance(argv,list) and argv and all(isinstance(x,str) for x in argv),'Original argv required')
 require('--sealed-final' not in argv and '--final-registry' not in argv and '--release' not in argv,'Final flags forbidden')
 return inv


def validate_execution_contract(contract, inner):
 required={'schema','kind','version','status','scientific_settings_changed','final_evaluation_enabled','files','runtime_contract','GPU_acceptance','source_inventory','transition'}
 require(isinstance(contract,dict) and set(contract)==required,'Execution contract fields differ')
 require(contract['schema']==SCHEMA and contract['kind']=='formal_action_execution_contract' and contract['version']==VERSION,'Execution version mismatch')
 require(contract['status']=='candidate_pending_root_readiness' and contract['scientific_settings_changed'] is False and contract['final_evaluation_enabled'] is False,'Candidate cannot self-authorize')
 require(contract['GPU_acceptance']==GPU_REFS,'GPU acceptance references differ')
 require(contract['source_inventory']=={'path':INVENTORY,'sha256':INVENTORY_SHA},'Frozen inventory differs')
 files=contract['files'];require(isinstance(files,dict),'Explicit support files required')
 require(set(files)==EXPECTED_NEW_FILES|{ACTION_ADAPTER},'Exact seven-file runtime/reviewer/consumer implementation plus original action adapter required')
 require(files.get(ACTION_ADAPTER)==ACTION_SHA,'Original action adapter bytes required')
 for name,sha in files.items(): ref({'path':name,'sha256':sha})
 runtime=contract['runtime_contract']; require(isinstance(runtime,dict) and bool(runtime),'Runtime scope contract required')
 require(all(runtime.get(k)==inner[k] for k in ('suite','stage','source_root','source_sha256')),'Runtime scope belongs to another scientific suite/stage/source')
 transition=contract['transition']
 if inner['resume']:
  ref(transition);require(transition['path'].startswith('results/formal_main_v2/'),'Explicit action-version transition must be an immutable result')
 else: require(transition is None,'Fresh invocation cannot claim a resume transition')
 return contract


def execution_dependencies(execution_contract):
 files=dict(execution_contract['files'])
 dependencies=execution_contract['runtime_contract'].get('dependencies',{})
 require(isinstance(dependencies,dict),'Runtime dependencies must be explicit')
 for name,checksum in dependencies.items():
  ref({'path':name,'sha256':checksum})
  require(name not in files or files[name]==checksum,'Conflicting runtime dependencies')
  files[name]=checksum
 return files


def effective_plan(original, *, scientific_plan_ref, execution_contract_ref, execution_contract):
 """Build a proposal only; never write files or invoke validators/submission."""
 inner=validate_inner(original);ref(scientific_plan_ref);ref(execution_contract_ref)
 validate_execution_contract(execution_contract,inner)
 effective=copy.deepcopy(original);inv=effective['invocation']
 files=execution_dependencies(execution_contract)
 for path,checksum in files.items():
  require(path not in inv['support_files'] or inv['support_files'][path]==checksum,'Conflicting original support')
 inv.update(version=VERSION,entrypoint=ENTRY,wrapper=WRAPPER,wrapper_sha256=files[WRAPPER],
  support_files={**inv['support_files'],**files},action_execution_contract=copy.deepcopy(execution_contract_ref),
  scientific_plan=copy.deepcopy(scientific_plan_ref),scientific_plan_sha256=scientific_plan_ref['sha256'])
 refs={**files,**GPU_REFS,INVENTORY:INVENTORY_SHA,scientific_plan_ref['path']:scientific_plan_ref['sha256'],execution_contract_ref['path']:execution_contract_ref['sha256']}
 if execution_contract['transition']: refs[execution_contract['transition']['path']]=execution_contract['transition']['sha256']
 for name,checksum in refs.items():
  remote=str(P/relative(name))
  require(remote not in inv['watched_files'] or inv['watched_files'][remote]==checksum,'Conflicting original runtime watch')
  require(name not in inv['root_evidence_sha256'] or inv['root_evidence_sha256'][name]==checksum,'Conflicting original root evidence')
  inv['watched_files'][remote]=checksum;inv['root_evidence_sha256'][name]=checksum
  effective['publish_files'][name]=checksum
 effective['plan_sha256']=signature({k:v for k,v in effective.items() if k!='plan_sha256'})
 validate_effective(original,effective,scientific_plan_ref=scientific_plan_ref,execution_contract_ref=execution_contract_ref,execution_contract=execution_contract)
 return effective


def validate_effective(original,effective,*,scientific_plan_ref,execution_contract_ref,execution_contract):
 inner=validate_inner(original);outer=effective['invocation'];ref(scientific_plan_ref);ref(execution_contract_ref)
 validate_execution_contract(execution_contract,inner)
 require(set(effective)==set(original),'New plan must not hide additional behavior')
 for key in original:
  if key not in ('invocation','publish_files','plan_sha256'):require(effective[key]==original[key],'Scientific/resource plan changed: '+key)
 require(set(outer)==set(inner)|RUNTIME_ADDITIONS,'Runtime invocation field set mismatch')
 for key,value in inner.items():
  if key not in RUNTIME_MUTABLE:require(outer[key]==value,'Scientific invocation changed: '+key)
 files=execution_dependencies(execution_contract)
 require(outer['version']==VERSION and outer['entrypoint']==ENTRY and outer['wrapper']==WRAPPER and outer['wrapper_sha256']==files[WRAPPER],'Actual outer execution identity missing')
 require(outer['scientific_plan']==scientific_plan_ref and outer['scientific_plan_sha256']==scientific_plan_ref['sha256'],'Inner plan provenance mismatch')
 require(outer['action_execution_contract']==execution_contract_ref,'Execution contract reference mismatch')
 require(outer['support_files']=={**inner['support_files'],**files},'Runtime support set mismatch')
 additions={**files,**GPU_REFS,INVENTORY:INVENTORY_SHA,scientific_plan_ref['path']:scientific_plan_ref['sha256'],execution_contract_ref['path']:execution_contract_ref['sha256']}
 if execution_contract['transition']:additions[execution_contract['transition']['path']]=execution_contract['transition']['sha256']
 require(outer['watched_files']=={**inner['watched_files'],**{str(P/k):v for k,v in additions.items()}},'Watch set differs')
 require(outer['root_evidence_sha256']=={**inner['root_evidence_sha256'],**additions},'Root evidence set differs')
 require(effective['publish_files']=={**original['publish_files'],**additions},'Publish set differs')
 require(effective['plan_sha256']==signature({k:v for k,v in effective.items() if k!='plan_sha256'}),'Effective plan signature mismatch')
 return True


def validate_transition(transition, original, *, root, execution_contract=None):
 inv=validate_inner(original)
 require(inv['resume'] is True,'Transition is only for existing raw ledger')
 prior=read_ref(root,{'path':inv['prior_review'],'sha256':inv['root_evidence_sha256'][inv['prior_review']]})
 prior_version=prior.get('execution_version','formal-downstream-root-v1')
 require(prior_version in ('formal-downstream-root-v1',VERSION),'Unknown prior execution version')
 if prior_version==VERSION:
  require(isinstance(execution_contract,dict),'Same-version continuation needs explicit current action contract')
  old_contract=read_ref(root,prior.get('action_execution_contract'))
  require(old_contract.get('version')==VERSION and old_contract.get('files',{}).get(ACTION_ADAPTER)==ACTION_SHA,'Prior action implementation differs')
  previous={k:v for k,v in old_contract['runtime_contract'].items() if k!='stage'}
  current={k:v for k,v in execution_contract['runtime_contract'].items() if k!='stage'}
  require(previous==current,'Same-version continuation changed action semantics')
 expected={'schema':SCHEMA,'kind':'formal_action_runtime_transition','status':'root_reviewed','from_version':prior_version,'to_version':VERSION,
  'stage_key':inv['stage_key'],'run_root':inv['run_root'],'execution_manifest_sha256':inv['execution_manifest_sha256'],
  'prior_job_ids':inv['prior_job_ids'],'prior_review':inv['prior_review'],'terminal_trials_repeated':False,'prior_outcomes_replaced':False,'new_trial_ids_only':True}
 require(all(transition.get(k)==v for k,v in expected.items()),'Explicit compatible-version transition differs')
 require(isinstance(transition.get('files'),dict),'Original prefix/config/panel receipt required')
 output=str(PurePosixPath(inv['run_root']).relative_to(P))
 required={output+'/'+n for n in ('trials.jsonl','closed_loop_report.json','config.json','panel.json')}
 require(required.issubset(transition['files']),'Transition omits original ledger identity')
 for name,checksum in transition['files'].items():
  require(prior.get('files',{}).get(name)==checksum and digest(Path(root)/relative(name))==checksum,'Prior raw evidence changed')
 ref(transition.get('independent_review'))
 independent=read_ref(root,transition['independent_review'])
 require(independent.get('kind')=='formal_action_runtime_transition_review' and independent.get('status')=='passed' and independent.get('review_role')=='independent', 'Independent transition review is required')
 require(independent.get('stage_key')==inv['stage_key'] and independent.get('files')==transition['files'] and independent.get('prior_review')==inv['prior_review'], 'Independent transition evidence mismatch')
 require(independent.get('from_version')==expected['from_version'] and independent.get('to_version')==VERSION, 'Independent transition version mismatch')
 return True
