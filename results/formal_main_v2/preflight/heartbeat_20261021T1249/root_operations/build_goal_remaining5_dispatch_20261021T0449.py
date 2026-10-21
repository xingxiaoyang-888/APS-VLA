from pathlib import Path
import ast,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_remaining5_dispatch_20261021T0449'
D.mkdir(exist_ok=False)
old=R/'scripts/ops/formal_goal_full200_dispatch_v1/dispatch.py'
source=old.read_text()
assert hashlib.sha256(old.read_bytes()).hexdigest()=='8d3e282946c300f072a13c1b4a658f92b3e25cfb3130a0ad63ab186fe6386b3c'
lines=source.splitlines()
tree=ast.parse(source)
nodes={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def block(name):
 n=nodes[name];a=min([n.lineno]+[x.lineno for x in getattr(n,'decorator_list',[])])
 return '\n'.join(lines[a-1:n.end_lineno])+'\n'
prefix='''"""Root dispatcher for the five explicitly enumerated remaining Goal pairs.
Control transaction adapted from frozen full200 dispatcher; all pair bindings are
new immutable per-instance closures. The old exclusive module is never mutated.
"""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
from contextlib import contextmanager
from types import SimpleNamespace
import argparse,copy,fcntl,hashlib,importlib.util,json,os,re,stat,subprocess,sys
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
H=R.parent
S=P/'snapshots/formal_main_v2_run_564be0995e'
BASE='scripts/ops/formal_goal_remaining5_dispatch_v1'
PROD='scripts/ops/formal_goal_remaining5_gate_v1'
STATE='results/experiment_supervisor/state.json'
EXPERIMENT='formal_main_v2'
VERSION='goal-remaining5-held-atomic-dispatch-v1'
SOURCE='dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e'
OWNER='results/formal_main_v2/autonomous_training/run_v1/owner.json'
OWNER_SHA='2ba2100d6f20e8a00f7853e193d1546b3d7c4195f174c75d54605ec504e33bc2'
LEASE='results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock'
CONTROLLER='scripts/ops/formal_autonomous_training_v1/controller.py'
CONTROLLER_SHA='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
DESIGN='results/formal_main_v2/engineering/supervision_delivery_20261021T0334/Goal_remaining5_design/design.json'
DESIGN_SHA='5c813e3a6e9429cc46ed9ab52a5543d0cf6302c5e5c1819efd11a501a2fb4e8e'
OLD_IDS=['3053440','3054127'];OLD_SECONDS=[803,840]
PAIRS={
 'libero_goal_k256_seed23':('9ad90de70f1e3fa7581efde098ef8953427ccbfd034c6eaf686cd791f4689032',256,23),
 'libero_goal_k256_seed41':('bc06dd35931c05b180758f46e9f39cec50b632b20a33b4ebfc0d2f2cc7614954',256,41),
 'libero_goal_k64_seed17':('ad5f40d8b25cba3280e85d8c05712fd6aa749f26277e015b7eaec3b405e6b8bd',64,17),
 'libero_goal_k64_seed23':('7a6254a2e2de33e4f09a072654ea08121b51c3a4e84bfb837fee13ebb3586ce9',64,23),
 'libero_goal_k64_seed41':('8336a896242eeabff2afbd37462b83a0321f016974a27a70d83ac47949f0243d',64,41)}
'''
common=['require','canonical','sha','utc','safe','relative','raw','read','ref','read_ref','immutable','record','load','controller','parse_ack','fields','argv_of','option','expected_live','validate_live_identity','shared_writer_lock','probe_lease','actual_observation']
for name in common:
 txt=block(name).replace('_goal_full200_exact_controller','_goal_remaining5_exact_controller')
 prefix+='\n'+txt
prefix+='''
def source_map(root=R):
 return {BASE+'/'+n:sha(raw(root/BASE/n)) for n in ('gateway.py','scope.json')}
def make_dispatcher(pair_key,scope_sha256):
 require(pair_key in PAIRS,'only five exact remaining Goal pairs')
 scope=read(R/BASE/'scope.json',scope_sha256)
 require(raw(P/BASE/'scope.json',scope_sha256)==raw(R/BASE/'scope.json',scope_sha256),'scope R/P differs')
 require(set(scope)=={'schema','kind','version','design','pairs','runtime_manifest_sha256','runtime_files'},'unexpected dispatch scope fields')
 require(scope['schema']==EXPERIMENT and scope['kind']=='five_exact_Goal_pairs_dispatch_scope' and scope['version']==VERSION,'wrong scope kind')
 require(scope['design']=={'path':DESIGN,'sha256':DESIGN_SHA},'root frozen design binding differs')
 design=read(R/DESIGN,DESIGN_SHA)
 actual={r['pair_key']:(r['pair_id'],r['budget'],r['seed']) for r in design['remaining_pairs']}
 require(actual==PAIRS and scope['pairs']=={k:list(v) for k,v in PAIRS.items()},'five exact pair identity differs')
 PAIR,TOKENS,TRAIN_SEED=PAIRS[pair_key]
 KEY=pair_key;STAGE='goal_remaining5_v1/'+KEY
 X='results/formal_main_v2/execution/'+STAGE
 AUTH=X+'/root_authorization.json';INV=AUTH
 ADMISSION=X+'/dispatch_admission.json';OUT=X+'/attempt01'
 RAW='results/formal_main_v2/raw_runtime/'+STAGE+'/attempt01'
 RESERVATION=X+'/reservation.json';DISPATCH=X+'/held_dispatch_record.json'
 CELL='Goal_remaining5_'+KEY
 NAME='cti-goal-r5-k'+str(TOKENS)+'s'+str(TRAIN_SEED)
 MODE='goal_remaining5_prospective'
 METHODS=[f'{a}{TOKENS}_seed{TRAIN_SEED}' for a in ('A','B')]
 RUNTIME_MANIFEST_SHA=scope['runtime_manifest_sha256'];SCOPE_SHA=scope_sha256
 require(re.fullmatch('[0-9a-f]{64}',RUNTIME_MANIFEST_SHA) is not None,'runtime manifest must be frozen; HOLD')
 RESOURCES=dict(job_name=NAME,account='p_p15016',qos='cpu-500_core-l40-8_card-a800-8_card',partition='L40',nodes=1,ntasks=1,cpus_per_task=7,gres='gpu:l40:1',mem='64G',time='02:00:00')
 RUNTIME_RESOURCES=dict(partition='L40',gres='gpu:l40:1',cpus_per_task=7,mem='64G',wall_seconds=7200,no_requeue=True,excluded_nodes=['gpu4020'])
 CONFIG_REL=PROD+'/pairs/'+KEY+'/config.json'
'''
new={}
new['runtime_package']='''def runtime_package(root=P):
 p=read(root/PROD/'package_manifest.json',RUNTIME_MANIFEST_SHA)
 require(p.get('schema')==EXPERIMENT and p.get('version')=='goal-remaining5-prospective-single-attempt-v1'
  and p.get('files')==scope['runtime_files'] and PROD+'/entry.py' in p['files'] and CONFIG_REL in p['files'],'exact five-pair runtime closure required')
 for path,pin in p['files'].items():raw(root/relative(path),pin)
 return p
'''
new['runtime_output']='''def runtime_output(value,package):
 require(value.get('status')=='passed_metadata_source_capacity_only' and value.get('stage_key')==STAGE
  and value.get('package_manifest_sha256')==RUNTIME_MANIFEST_SHA and value.get('config_sha256')==package['files'][CONFIG_REL]
  and value.get('new_GPU_submissions')==0 and value.get('actual_GPU_runtime_verified') is False
  and value.get('GPU_execution_authorized') is False and value.get('original200_HOLD') is True
  and value.get('final_release') is False,'actual P verification is source/identity/capacity only')
 require(value.get('identity',{}).get('original_fixed200_identity_order') is True
  and value.get('identity',{}).get('unique_development_states')==100,'complete original 200 identity missing')
 require(value.get('storage',{}).get('aggregate_pair_keys')==list(PAIRS)
  and value['storage'].get('no_dedup_credit') is True,'all-five conservative storage proof required')
 return value
'''
new['admission_fixed']='''def admission_fixed():
 return dict(schema=EXPERIMENT,kind='root_goal_remaining5_exact_dispatch_admission',status='approved_exactly_once',
  reviewed_by='root',version=VERSION,stage_key=STAGE,pair_key=KEY,pair_id=PAIR,method_ids=METHODS,
  training_seed=TRAIN_SEED,runtime_seed=17,environment_seed=0,
  maximum_trials=200,unique_development_states=100,maximum_control_steps=60000,maximum_policy_queries=7600,
  maximum_attempts=1,automatic_retry=False,original200_HOLD=True,final_allowed=False,
  package_manifest_sha256=RUNTIME_MANIFEST_SHA,scope_sha256=SCOPE_SHA,resources=RESOURCES)
'''
new['reconcile_runtime_metadata']='''def reconcile_runtime_metadata(e,package):
 require(Path(e.__file__).resolve()==P/PROD/'entry.py','exact published P entry required')
 value=e.verify_existing_metadata(KEY,RUNTIME_MANIFEST_SHA)
 require(value.get('status')=='passed_existing_ACK_metadata_source_only' and value.get('new_GPU_submission_allowed') is False,'reconcile metadata may not submit/claim')
 require(value.get('identity',{}).get('original_fixed200_identity_order') is True and value['identity'].get('unique_development_states')==100,'ACK scientific identity missing')
 return value
'''
new['admission']='''def admission(pin,*,reconcile_existing=False):
 require(type(reconcile_existing)is bool,'explicit original-ACK mode')
 a=read(R/ADMISSION,pin);require(raw(P/ADMISSION,pin)==raw(R/ADMISSION,pin),'admission R/P differs')
 check_admission_fields(a)
 package=runtime_package(P);require(runtime_package(R)==package,'runtime R/P differs')
 require(a.get('dispatch_files')==source_map() and a.get('runtime_files')==package['files'],'root source closures differ')
 for rel,pin in source_map().items():raw(P/rel,pin)
 auth=read_ref(R,a['authorization'],AUTH);require(raw(P/AUTH)==raw(R/AUTH),'authorization R/P differs')
 ah=sha(raw(R/AUTH));e=load(P/PROD/'entry.py',package['files'][PROD+'/entry.py'],'_goal_remaining5_'+KEY)
 ctx=e.context(KEY)
 e.validate_authorization(ctx,auth,package['files'][CONFIG_REL],RUNTIME_MANIFEST_SHA,package['files'][PROD+'/entry.py'])
 for role in ('root','independent'):
  rr=auth[role+'_review'];rel=relative(str(Path(rr['path']).relative_to(P)))
  require(raw(P/rel,rr['sha256'])==raw(R/rel,rr['sha256']),'root/runtime readiness differs')
  e.check_review(ctx,read(P/rel),role,RUNTIME_MANIFEST_SHA,package['files'][CONFIG_REL])
 ri=archive_ref(a['runtime_independent_review'])
 require(str(ri.get('status','')).startswith('passed') and ri.get('package_manifest_sha256')==RUNTIME_MANIFEST_SHA
  and ri.get('package_files')==package['files'] and ri.get('blockers')==[]
  and ri.get('reviewed_by') not in (None,'root'),'independent runtime source review missing')
 di=archive_ref(a['dispatch_independent_review'])
 require(di.get('kind')=='Goal_remaining5_atomic_dispatch_independent_review' and di.get('status')=='passed'
  and di.get('dispatch_files')==source_map() and di.get('package_manifest_sha256')==RUNTIME_MANIFEST_SHA
  and di.get('runtime_files')==package['files'] and di.get('blockers')==[]
  and di.get('review_scope')=='source_and_CPU_only' and di.get('GPU_execution_authorized') is False,'new dispatcher independent proof missing')
 capture=read_ref(R,a['actual_P_verification'])
 argv=[str(H/'venv/bin/python'),'-B',str(P/PROD/'entry.py'),'--pair-key',KEY,'--verify','--package-manifest-sha256',RUNTIME_MANIFEST_SHA]
 require(capture.get('kind')=='Goal_remaining5_actual_P_verification_capture' and capture.get('argv')==argv
  and capture.get('returncode')==0 and capture.get('runtime_files')==package['files'],'exact actual P process absent')
 prior=runtime_output(json.loads(capture['stdout']),package)
 current=reconcile_runtime_metadata(e,package) if reconcile_existing else runtime_output(e.verify_published(KEY,RUNTIME_MANIFEST_SHA,must_be_fresh=True),package)
 require(current['identity']==prior['identity'],'actual P original scientific identity differs')
 return dict(admission=a,authorization=auth,authorization_ref=ref(R,AUTH),authorization_sha256=ah,
  admission_ref=ref(R,ADMISSION),token='cti-goal-remaining5-v1:'+KEY+':'+ah,comment='cti-goal-remaining5-v1:'+KEY+':'+ah,
  invocation_bytes=raw(R/AUTH),runtime_package=package,scope=scope,sources={**source_map(),**package['files']},actual_P_current=current,reconcile_existing=reconcile_existing)
'''
new['sbatch_argv']='''def sbatch_argv(bundle):
 return ['sbatch','--hold','--parsable','--no-requeue','--exclude=gpu4020','--comment='+bundle['comment'],
  *['--'+k.replace('_','-')+'='+str(v) for k,v in RESOURCES.items()],
  '--chdir='+str(S),'--output='+str(P/'results/slurm'/(NAME+'_%j.out')),
  '--error='+str(P/'results/slurm'/(NAME+'_%j.err')),
  '--export=ALL,CTI_GOAL_REMAINING5_PAIR_KEY='+KEY+',CTI_GOAL_REMAINING5_AUTH_SHA256='+bundle['authorization_sha256'],str(P/PROD/'run.slurm')]
'''
new['duplicate']='''def duplicate(j):
 return (j.get('stage_key')==STAGE or j.get('logical_trial_id')==CELL or j.get('invocation')==AUTH
  or j.get('run_root') in (str(P/OUT),str(P/OUT/'original_run'),OUT)
  or j.get('name',j.get('job_name'))==NAME
  or str(j.get('slurm_comment','')).startswith('cti-goal-remaining5-v1:'+KEY+':')
  or (j.get('pair_id')==PAIR and j.get('mode')=='development'))
'''
new['goal_overlap']='''def goal_overlap(j):
 if j.get('pair_id')==PAIR:return True
 text=' '.join(str(j.get(k,'')) for k in ('suite','stage_key','run_root','name','job_name')).lower()
 # Unknown pair identity on another Goal job is not safe to infer.
 return 'goal' in text and not re.fullmatch('[0-9a-f]{64}',str(j.get('pair_id','')))
'''
for name in ['runtime_package','archive_ref','runtime_output','admission_fixed','check_admission_fields','reconcile_runtime_metadata','admission','sbatch_argv','duplicate','goal_overlap','validate_new_identity','job_record','reservation','normalized_projection','Native','Transaction']:
 txt=new.get(name,block(name))
 txt=txt.replace('Goal_full200_durable_pending','Goal_remaining5_durable_pending').replace('goal_full200_gateway','goal_remaining5_gateway')
 txt=txt.replace('root_goal_full200_held_dispatch','root_goal_remaining5_held_dispatch').replace('root_goal_full200_GPU_slot_reservation','root_goal_remaining5_GPU_slot_reservation').replace('approved_for_exact_full200','approved_for_exact_remaining5_pair')
 txt=txt.replace("PROD+'/config.json'","CONFIG_REL")
 txt=txt.replace('visual_tokens=256,training_seed=17','visual_tokens=TOKENS,training_seed=TRAIN_SEED,runtime_seed=17,environment_seed=0')
 txt=txt.replace("purpose='One prospective fixed Goal full200 attempt; historical200 and other Goal1000 remain HOLD pending exact terminal review'","purpose='One original fixed Goal pair from exact remaining-five scope; all results pending original raw consumer and independent terminal acceptance'")
 txt=txt.replace("e.validate_dispatch(d,reserved,self.bundle['authorization']", "e.validate_dispatch(e.context(KEY),d,reserved,self.bundle['authorization']")
 txt=txt.replace("same pair or Goal allocation occupied","same pair or unknown Goal identity occupied")
 # Reflect actual occupancy while preserving completed controller lifecycle.
 if name=='Native':
  txt=txt.replace("new=self.cas(state,expected);return new","state['autonomous_training_v1']['occupied_job_ids']=list(obs['derived']['occupied'])\n  new=self.cas(state,expected);return new")
 prefix+='\n'+''.join(' '+line+'\n' for line in txt.splitlines())
prefix+='''
 return SimpleNamespace(pair_key=KEY,pair_id=PAIR,stage=STAGE,authorization=AUTH,output=OUT,raw=RAW,
  admission=admission,admission_fixed=admission_fixed,normalized_projection=normalized_projection,
  duplicate=duplicate,goal_overlap=goal_overlap,job_record=job_record,sbatch_argv=sbatch_argv,
  parse_ack=parse_ack,Transaction=Transaction,Native=Native,runtime_output=runtime_output,
  scope=scope,source_map=source_map,resources=RESOURCES,runtime_package=runtime_package,
  reservation=reservation,validate_new_identity=validate_new_identity)

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--pair-key',choices=tuple(PAIRS),required=True)
 p.add_argument('--dispatch-sha256',required=True);p.add_argument('--scope-sha256',required=True);p.add_argument('--admission-sha256',required=True)
 m=p.add_mutually_exclusive_group();m.add_argument('--submit',action='store_true');m.add_argument('--reconcile',action='store_true')
 p.add_argument('--root-reviewed',action='store_true');a=p.parse_args(argv)
 require(Path(__file__).resolve()==R/BASE/'gateway.py' and Path.cwd().resolve()==R,'canonical root dispatcher only')
 require(sha(raw(Path(__file__)))==a.dispatch_sha256,'exact new source pin')
 require(not(a.submit or a.reconcile) or a.root_reviewed,'root reviewed exact action required')
 d=make_dispatcher(a.pair_key,a.scope_sha256)
 b=d.admission(a.admission_sha256,reconcile_existing=a.reconcile)
 print(json.dumps(d.Transaction(d.Native(b),b).run(submit=a.submit,reconcile=a.reconcile),sort_keys=True,ensure_ascii=False))
if __name__=='__main__':main()
'''
compile(prefix,str(D/'gateway.py'),'exec')
(D/'gateway.py').write_text(prefix)
(D/'source_provenance.json').write_text(json.dumps(dict(kind='candidate_source_transform_not_production',old_path=str(old.relative_to(R)),old_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),new_sha256=hashlib.sha256(prefix.encode()).hexdigest(),fixed_pair_count=5,new_explicit_closure=True,old_module_globals_mutated=False,old_gateway_modified=False,new_submit_allowed=False,rewritten_functions=list(new)),sort_keys=True,indent=2)+'\n')
print(json.dumps({'candidate':str(D/'gateway.py'),'sha256':hashlib.sha256((D/'gateway.py').read_bytes()).hexdigest(),'line_count':len(prefix.splitlines()),'production_ready':False}))
