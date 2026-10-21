"""Exact immutable remaining-five contexts. No old module global mutation."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,re
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
PKG='scripts/ops/formal_goal_remaining5_gate_v1'
VERSION='goal-remaining5-prospective-single-attempt-v1'
KEYS=('libero_goal_k256_seed23','libero_goal_k256_seed41','libero_goal_k64_seed17','libero_goal_k64_seed23','libero_goal_k64_seed41')
SOURCE_FILES=('scope.py','entry.py','storage.py','observer_v3.py','ast_observer_v2.py','paired_input_gate_v1.py','ast_gate_v2.py','consumer.py','run.slurm','registry.json')
PACKAGE_FILES={PKG+'/'+n for n in SOURCE_FILES}|{PKG+'/pairs/'+k+'/'+n for k in KEYS for n in ('config.json','specification.json')}
REGISTRY_SHA='41faf2c2d6ad22b527df4ca8a737687ee9667c50142156a2c96db3b0e18c6553'
def require(v,m):
 if not v:raise ValueError(m)
def pinned(path,pin):
 b=Path(path).read_bytes();require(hashlib.sha256(b).hexdigest()==pin,'exact immutable context source differs: '+str(path));return json.loads(b)
def paths(key):
 require(key in KEYS,'only five named Goal pairs')
 x='results/formal_main_v2/execution/goal_remaining5_v1/'+key
 raw=R/'results/formal_main_v2/raw_runtime/goal_remaining5_v1'/key/'attempt01'
 return dict(stage_key='goal_remaining5_v1/'+key,X=x,OUT=x+'/attempt01',BASE=P/x,OUTPUT=P/x/'attempt01',RAW=raw,RUN=x+'/attempt01/original_run')
def context(pair_key):
 require(type(pair_key) is str and pair_key in KEYS,'unknown remaining5 pair')
 registry=pinned(Path(__file__).parent/'registry.json',REGISTRY_SHA)
 require(registry['version']==VERSION and tuple(registry['pair_keys'])==KEYS and set(registry['pairs'])==set(KEYS),'exact five registry')
 slot=registry['pairs'][pair_key];c=pinned(Path(__file__).parent/'pairs'/pair_key/'config.json',slot['config_sha256'])
 tokens,seed=map(int,re.fullmatch(r'libero_goal_k(256|64)_seed(17|23|41)',pair_key).groups())
 pd=paths(pair_key);methods=['A'+str(tokens)+'_seed'+str(seed),'B'+str(tokens)+'_seed'+str(seed)]
 obj=SimpleNamespace(**pd,pair_key=pair_key,seed=seed,tokens=tokens,methods=methods,config=c,config_sha=slot['config_sha256'],spec_sha=slot['specification_sha256'],
  CONFIG=P/PKG/'pairs'/pair_key/'config.json',SPEC=P/PKG/'pairs'/pair_key/'specification.json',ENTRY=P/PKG/'entry.py',MANIFEST=P/PKG/'package_manifest.json',
  root_decision=registry['root_fixed_design'],storage_decision=registry['root_storage_decision'],
  AUTH=pd['BASE']/'root_authorization.json',DISPATCH=pd['BASE']/'held_dispatch_record.json',RESERVATION=pd['BASE']/'reservation.json',
  ORIGINAL=Path(c['planned_invocation_path']),plans=c['plans'])
 return obj
