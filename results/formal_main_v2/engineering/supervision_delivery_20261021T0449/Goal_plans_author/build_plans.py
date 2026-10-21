"""Private CPU generation of exactly five Goal development plans using original validators.
No scheduler, state writer, canonical publisher, model loader, or final-state reader.
"""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/goal_remaining5_plans_20261021T0449'
X='results/formal_main_v2/execution/goal_remaining5_v1'
ROUND='formal_main_v2'
PAIRS=((256,23),(256,41),(64,17),(64,23),(64,41))
KEYS=tuple(f'libero_goal_k{k}_seed{s}' for k,s in PAIRS)
PANEL='configs/manifests/formal_main_v2/libero_goal/initial_states/development.json'
PANEL_SHA='ce8e3d31ab8f7616c87dd4d4031af41825713907ac184c6ea5b01d9040985aa9'
DESIGN='.local/goal_remaining5_design_20261021T0334/design.json'
DESIGN_SHA='5c813e3a6e9429cc46ed9ab52a5543d0cf6302c5e5c1819efd11a501a2fb4e8e'
PINS={'scripts/formal_execution_manifests.py':'614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89',
'scripts/ops/formal_downstream_supervisor.py':'f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571',
'scripts/ops/formal_action_deployment_v1/contract.py':'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19',
'scripts/ops/formal_action_deployment_v1/runtime_scope.py':'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53'}
sys.path.insert(0,str(R/'src'))
def require(ok,msg):
 if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def encoded(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def sig(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def no_links(p):
 p=Path(p);require(p.is_absolute() and p.resolve()==p and not any(t.is_symlink() for t in [p,*p.parents]),'direct path required');return p
def private(p):
 p=no_links(p);require(D in p.parents,'writes restricted to exact private author directory');return p
def write(p,raw):
 p=private(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw)
 return dict(path=str(p.relative_to(R)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def load(rel):
 p=R/rel;require(sha(p)==PINS[rel],'original builder pin differs: '+rel)
 name='remaining5_'+p.stem;spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m

def design():
 require(sha(R/DESIGN)==DESIGN_SHA,'frozen five-pair evidence changed')
 return {x['pair_key']:x for x in json.loads((R/DESIGN).read_bytes())['remaining_pairs']}

def manifest_relative(key):
 require(key in KEYS,'only five exact Goal pairs');return X+'/'+key+'/execution_manifest.json'
def publication(p):return D/'publication'/p

def projected_helper(h,key):
 """Exact one-file read-only I/O projection for unpublished canonical manifest.
 All original scientific functions retain original globals and implementations.
 Root replay after publication does NOT need this class.
 """
 target=R/manifest_relative(key);candidate=publication(manifest_relative(key))
 class ManifestEvidence(h.Evidence):
  def path(self,v):
   p=Path(v);p=p if p.is_absolute() else self.project/p
   if p==target:
    h.Evidence.path(self,target);no_links(candidate);require(candidate.is_file(),'candidate manifest absent');return candidate
   return h.Evidence.path(self,v)
  def relative(self,p):
   if Path(p) in (target,candidate):return str(target.relative_to(R))
   return h.Evidence.relative(self,p)
  def watch(self,v):
   p=self.path(v);self.require([p]);value=sha(p);key=self.relative(p)
   require(key not in self.files or self.files[key]==value,'evidence changed during projected read');self.files[key]=value;return value
 return SimpleNamespace(**{**vars(h),'Evidence':ManifestEvidence})

def args_for(key):
 return SimpleNamespace(stage='development',source_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json',execution_manifest=manifest_relative(key),output_relative=None,freeze_directory=None,profile_panel=None,prior_review=None,collection_review=None,repair_record=None,resume=False,stop_after=None)

def validate_scope(key,manifest):
 from cti_vla.evaluation import formal_trials
 from cti_vla.evaluation.teacher_diagnostics import json_signature
 rows=design();require(key in rows,'foreign pair');target=rows[key]
 registration=json.loads((R/'configs/experiments/formal_main_v2.json').read_bytes())
 formal_trials.validate_execution_manifest(manifest,registration_sha256=json_signature(registration))
 require(manifest.get('suite')=='libero_goal' and manifest.get('split')=='development','only exact Goal development')
 require(manifest.get('environment')==dict(environment_seed=0,runtime_seed=17,wait_steps=10,action_chunk=8,max_steps=300),'fixed environment differs')
 require(manifest.get('development_panel')==PANEL and manifest.get('development_panel_sha256')==PANEL_SHA,'original development panel differs')
 require([r['identity']['method_id'] for r in manifest['methods']]==target['method_ids'],'exact A/B method order differs')
 require(set(manifest)=={'schema','kind','registration_sha256','suite','split','environment','methods','development_panel','development_panel_sha256'},'unexpected scientific manifest fields')
 for row,arm in zip(manifest['methods'],target['arms']):
  require(set(row)=={'identity','checkpoint','receipt','pair_config','f01_report'},'method row keys differ')
  identity=row['identity'];receipt=json.loads((R/arm['deployment_receipt']['path']).read_bytes())
  require(sha(R/arm['deployment_receipt']['path'])==arm['deployment_receipt']['sha256'],'own receipt changed')
  require(identity['pair_id']==target['pair_id'] and identity['training_seed']==target['seed'] and identity['visual_tokens']==target['budget'],'pair/seed/budget differs')
  require(row['checkpoint']==arm['checkpoint']['path'] and identity['checkpoint_sha256']==arm['checkpoint']['sha256'],'selected checkpoint differs')
  require(row['receipt']==arm['deployment_receipt']['path'] and row['pair_config']==target['planned_scientific_matrix_source']['path'],'foreign receipt/config')
  require(sha(R/row['pair_config'])==target['planned_scientific_matrix_source']['sha256'],'registered config changed')
  require(receipt['metadata']['update']==arm['selected_update'],'frozen selected update changed')
  require(identity['source_sha256']==arm['training_source_sha256'] and identity['config_sha256']==arm['training_config_sha256'],'training source/config changed')
  require(identity['future_head_deployed'] is False and identity['training_complete'] is True,'formal deployment flags differ')
  p=no_links(Path(row['checkpoint']));require(p.is_file() and p.stat().st_size==arm['checkpoint']['bytes'],'selected server checkpoint metadata changed since exact previous SHA verification')
 return target

def run_build():
 h=load('scripts/formal_execution_manifests.py');planner=load('scripts/ops/formal_downstream_supervisor.py');contract=load('scripts/ops/formal_action_deployment_v1/contract.py');runtime=load('scripts/ops/formal_action_deployment_v1/runtime_scope.py')
 state_raw=(R/'results/experiment_supervisor/state.json').read_bytes();state=json.loads(state_raw)
 require(state.get('pending_submission') is None and state.get('autonomous_training_v1',{}).get('pending_submission') is None,'unresolved submission')
 write(D/'build_state_snapshot.json',state_raw)
 require(sha(R/PANEL)==PANEL_SHA,'development panel SHA');panel=json.loads((R/PANEL).read_bytes())
 from cti_vla.evaluation import formal_trials
 artifacts={};pub=[]
 for key in KEYS:
  e=h.Evidence(R);sources=h.source_contract(e,h.SOURCE_INVENTORY);registration=h.registration_contract(e,h.REGISTRATION)
  target=design()[key];rows=h.suite_rows(e,registration,'libero_goal',sources,target['method_ids']);manifest=h.make_execution(registration,'libero_goal',rows,split='development');manifest.update(development_panel=PANEL,development_panel_sha256=e.watch(PANEL));validate_scope(key,manifest);e.unchanged()
  rel=manifest_relative(key);write(publication(rel),encoded(manifest))
  scientific=planner.plan(args_for(key),copy.deepcopy(state),project=R,helper=projected_helper(h,key))
  require(scientific['invocation']['prior_job_ids']==[] and scientific['invocation']['prior_allocation_cost']==[] and scientific['invocation']['prior_review'] is None,'fresh stage must have no prior invocation or cost')
  require(scientific['invocation']['source_provenance']==e.source_provenance['libero_goal'],'state versus immutable full source history differs')
  base=X+'/'+key
  def emit(name,value):
   rel=base+'/'+name;write(publication(rel),encoded(value));return dict(path=rel,sha256=sha(publication(rel)))
  mref=dict(path=rel,sha256=sha(publication(rel)))
  sr=emit('scientific_plan.json',scientific);proof=emit('source_provenance.json',scientific['invocation']['source_provenance'])
  action=dict(schema=ROUND,kind='formal_action_execution_contract',version=contract.VERSION,status='candidate_pending_root_readiness',scientific_settings_changed=False,final_evaluation_enabled=False,files={n:sha(R/n) for n in sorted(contract.EXPECTED_NEW_FILES|{contract.ACTION_ADAPTER})},runtime_contract=runtime.make_contract(project_root=R,source_root=S,suite='libero_goal',stage='development'),GPU_acceptance=contract.GPU_REFS,source_inventory=dict(path=contract.INVENTORY,sha256=contract.INVENTORY_SHA),transition=None)
  contract.validate_execution_contract(action,scientific['invocation']);runtime.validate_contract(action['runtime_contract'],project_root=R,source_root=S)
  ar=emit('execution_contract.json',action)
  effective=contract.effective_plan(scientific,scientific_plan_ref=sr,execution_contract_ref=ar,execution_contract=action);er=emit('effective_plan.json',effective);ir=emit('invocation_template.json',effective['invocation'])
  specrows=[dict(ordinal=i+1,**formal_trials._identity(panel,s,mid)) for i,(s,mid) in enumerate((s,mid) for s in panel['states'] for mid in target['method_ids'])]
  specification=dict(schema=ROUND,kind='Goal_remaining5_fixed200_trial_specification',pair_key=key,pair_id=target['pair_id'],execution_manifest=mref,panel=dict(path=PANEL,sha256=PANEL_SHA),row_count=200,unique_development_states=100,maximum_control_steps=60000,maximum_policy_queries=7600,maximum_new_attempts=1,automatic_retry=False,scientific_environment=manifest['environment'],method_identities=[r['identity'] for r in rows],rows=specrows,rows_signature_sha256=sig(specrows),production_ready=False,new_GPU_jobs_now=0,scientific_trials_added_now=0,final_release=False)
  sp=emit('specification.json',specification)
  require(len(specrows)==200 and len({r['state_trial_id'] for r in specrows})==100 and len({r['trial_id'] for r in specrows})==200,'exact fixed200 identities')
  missing=[]
  for path,pin in effective['invocation']['watched_files'].items():
   pp=Path(path)
   if not pp.exists():missing.append(dict(path=path,sha256=pin))
   else:require(sha(pp)==pin,'existing P frozen metadata/source drift: '+path)
  # Actual-P absent new inputs are declared; this routine never installs them.
  record=dict(pair_key=key,pair_id=target['pair_id'],budget=target['budget'],training_seed=target['seed'],environment_seed=0,runtime_seed=17,method_ids=target['method_ids'],execution_manifest=mref,scientific_plan=sr,effective_plan=er,execution_contract=ar,source_provenance=proof,invocation_template=ir,planned_invocation_path=scientific['invocation_relative'],panel=dict(path=PANEL,sha256=PANEL_SHA),specification=sp,original_output=str(P/scientific['output_relative']),actual_runtime_output_proposed=str(P/base/'attempt01'/'original_run'),raw_observation_root_proposed=str(R/'results/formal_main_v2/raw_runtime/goal_remaining5_v1'/key/'attempt01'),training_terminal_evidence=target['training_terminal_evidence'],selected_checkpoints=target['arms'],plan_arguments=vars(args_for(key)),original_source_bridge_required=False,source_proof='unmodified original full history reviewer passed for this own pair',missing_actual_P_inputs=missing,prepared_invocation_available=False,production_admitted=False)
  artifacts[key]=record;print(key,'original plan and action envelope passed',flush=True)
  for p in sorted((publication(base)).iterdir()):pub.append(dict(source=str(p.relative_to(R)),destination=str(p.relative_to(D/'publication')),bytes=p.stat().st_size,sha256=sha(p),install_roots=['R','P']))
  config=target['planned_scientific_matrix_source'];pub.append(dict(source=config['path'],destination=config['path'],bytes=(R/config['path']).stat().st_size,sha256=config['sha256'],install_roots=['P']))
  write(D/'pairs'/key/'builder_evidence.json',encoded(dict(files=e.files,original_modules=PINS,original_provenance_sha256=sig(e.source_provenance['libero_goal']))))
 index=dict(schema=ROUND,kind='Goal_remaining5_original_plan_candidate_index',status='CPU_original_guards_passed_pending_independent_and_root',scope=list(KEYS),pairs=artifacts,original_builders=PINS,source_design=dict(path=DESIGN,sha256=DESIGN_SHA),state_snapshot=dict(path=str((D/'build_state_snapshot.json').relative_to(R)),sha256=hashlib.sha256(state_raw).hexdigest()),canonical_publication_root=X,publication_map=pub,prepared_invocations_created=False,actual_P_verified=False,production_admitted=False,new_trials=0,new_GPU_jobs=0,final_values_read=False)
 write(D/'candidate_index.json',encoded(index));print('index',sha(D/'candidate_index.json'),flush=True)

def verify_index(index_path,expected_sha,*,canonical=False,state_override=None):
 require(sha(index_path)==expected_sha,'candidate index pin differs');index=json.loads(Path(index_path).read_bytes());require(index['scope']==list(KEYS) and set(index['pairs'])==set(KEYS),'exact five scope')
 h=load('scripts/formal_execution_manifests.py');planner=load('scripts/ops/formal_downstream_supervisor.py');contract=load('scripts/ops/formal_action_deployment_v1/contract.py')
 state=json.loads((R/index['state_snapshot']['path']).read_bytes()) if state_override is None else state_override
 require(sha(R/index['state_snapshot']['path'])==index['state_snapshot']['sha256'],'saved state changed')
 def read(ref):
  p=R/ref['path'] if canonical else publication(ref['path']);require(sha(p)==ref['sha256'],'artifact pin differs: '+ref['path']);return json.loads(p.read_bytes())
 for key in KEYS:
  item=index['pairs'][key];manifest=read(item['execution_manifest']);validate_scope(key,manifest)
  rebuilt=planner.plan(args_for(key),copy.deepcopy(state),project=R,helper=h if canonical else projected_helper(h,key));require(rebuilt==read(item['scientific_plan']),'original planner reconstruction differs')
  effective=contract.effective_plan(rebuilt,scientific_plan_ref=item['scientific_plan'],execution_contract_ref=item['execution_contract'],execution_contract=read(item['execution_contract']));require(effective==read(item['effective_plan']),'effective plan reconstruction differs')
  require(effective['invocation']==read(item['invocation_template']),'invocation template differs')
 return index

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--build',action='store_true');ap.add_argument('--verify',type=Path);ap.add_argument('--index-sha256');ap.add_argument('--canonical',action='store_true');a=ap.parse_args()
 require(a.build != (a.verify is not None),'one mode')
 if a.build:run_build()
 else:
  index=verify_index(a.verify,a.index_sha256,canonical=a.canonical);print(json.dumps(dict(status='passed_original_five_pair_rebuild',pair_count=5,actual_P_verified=False,production_admitted=False,source_state_sha256=index['state_snapshot']['sha256'])))
if __name__=='__main__':main()