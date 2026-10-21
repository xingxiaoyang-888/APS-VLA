"""Exact Object correction identity and source pins; no execution authority."""
from pathlib import Path
import hashlib, importlib.util, json, re, sys
import fixed as F
PRIVATE='.local/object_single_error_production_20261020T2358'
BASE=F.BASE
VERSION='object-single-error-linked-v1'
PLAN=F.EX+'/plan.json'
INVOCATION='results/formal_main_v2/invocations/object_single_error_task08_state0049_dense_attempt01.json'
REPAIR=F.EX+'/root_repair.json'
ADOPTION=F.EX+'/root_legacy_adoption.json'
ADOPTION_SHA='c431646cbac00f461177e95361fb8d31d66c78bcfbbfc2b5c766edb8eabd6d24'
ROWS=F.EX+'/legacy599_adoption_rows.jsonl'
ROWS_SHA='ac792e8d88f251f097f3f0e110e6c32aa45dbacd103404c0189b3bebf56ccb5e'
REFERENCE='results/formal_main_v2/invocations/libero_object_development_8c843c1d4ee8383c_attempt01.json'
REFERENCE_SHA='6c5aaa313e11c67042eec51946886e1f34cdf4e0d7ed899e3dd27e429f3cfdb8'
STAGE_KEY='object_single_error_task08_state0049_dense_attempt01'
JOURNAL_ROOT='results/formal_main_v2/object_single_error_invocations'
OLD_WRAPPER='scripts/server/run_formal_downstream.py'
OLD_WRAPPER_SHA='f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24'
LEGACY='scripts/ops/formal_evaluation_adapter.py'
LEGACY_SHA='b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd'
RUNTIME='scripts/ops/formal_action_deployment_v1/runtime_scope.py'
RUNTIME_SHA='6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53'
ACTION='results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/action_adapter.py'
ACTION_SHA='b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185'
OLD_REVIEW='scripts/review_formal_downstream.py'
OLD_REVIEW_SHA='753edb55ce21fd43f85499e136a7e52093ecf9feaeafadf0f01cece8fa267202'
ACTION_REVIEW='scripts/ops/formal_action_deployment_v1/reviewer.py'
ACTION_REVIEW_SHA='9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd'
SCHEDULER='scripts/ops/formal_downstream_supervisor.py'
SCHEDULER_SHA='f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571'
HELPER='scripts/formal_execution_manifests.py'
HELPER_SHA='614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89'
RAW_KIND='Object_single_error_real_raw_reconstruction'
SOURCE_NAMES=('fixed.py','iterator.py','constants.py','adoption.py','execution.py',
              'wrapper.py','entry.py','reviewer.py','gateway_contract.py','scope.json')
DEPENDENCIES={OLD_WRAPPER:OLD_WRAPPER_SHA,LEGACY:LEGACY_SHA,RUNTIME:RUNTIME_SHA,
              ACTION:ACTION_SHA,OLD_REVIEW:OLD_REVIEW_SHA,ACTION_REVIEW:ACTION_REVIEW_SHA,
              SCHEDULER:SCHEDULER_SHA,HELPER:HELPER_SHA}
require=F.require
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def ref(root,path):
 p=F.safe(root,path);b=p.read_bytes()
 return dict(path=path,bytes=len(b),sha256=F.sha(b))
def read_ref(root,row,*,path=None):
 require(type(row) is dict and set(row)=={'path','bytes','sha256'},'complete exact reference required')
 if path is not None:require(row['path']==path,'reference outside exact role path')
 raw=F.read(root,row['path'],row['sha256'])
 require(len(raw)==row['bytes'],'reference size differs')
 return json.loads(raw)
def load(root,path,checksum):
 b=F.read(root,path,checksum)
 name='_object_linked_'+F.sig([str(root),path,checksum])[:24]
 m=sys.modules.get(name)
 if m is None:
  import types
  m=types.ModuleType(name);m.__file__=str(Path(root)/path);m.__package__=''
  sys.modules[name]=m
  try:exec(compile(b,m.__file__,'exec',dont_inherit=True),m.__dict__)
  except BaseException:sys.modules.pop(name,None);raise
 require(Path(m.__file__)==Path(root)/path,'module path collision')
 return m
def closure(directory):
 directory=Path(directory)
 return {BASE+'/'+name:digest(directory/name) for name in SOURCE_NAMES}
def verify_closure(project,descriptor):
 require(type(descriptor) is dict and set(descriptor)=={BASE+'/'+n for n in SOURCE_NAMES},'complete exact new entry/reviewer source closure required')
 for path,h in descriptor.items():F.read(project,path,h)
 for path,h in DEPENDENCIES.items():F.read(project,path,h)
 require(descriptor[BASE+'/fixed.py']=='6766626cf072e9cff149e85a785ea8e8231f30cd8cd555ac4b2c14a8ed8a5bc2'
  and descriptor[BASE+'/scope.json']==F.SCOPE_SHA,'original fixed scope changed')
 return descriptor

ADOPTION_INDEPENDENT='results/formal_main_v2/engineering/supervision_delivery_20261020T2358/Object_single_error_independent/canonical599_adoption_addendum.json'
ADOPTION_INDEPENDENT_SHA='d9d6de64311c45639a40a028e75a2697ac5cb605b892e881c50e81ab4b4e5ecf'
