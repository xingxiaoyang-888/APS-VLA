"""Independent Object256s23 bridge audit. Private CPU-only, never submits."""
from pathlib import Path
from types import SimpleNamespace
import sys,os,json,hashlib,copy,ast,importlib.util,contextlib,io,traceback,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/object_bridge_independent_20261020T1644'
E=R/'results/formal_main_v2/engineering/supervision_delivery_20261020T1530/Object_source_bridge_candidate'
OLD='.local/object256s23_consumer_candidate_20261020T1530'
MAN='results/formal_main_v2/execution/object256seed23_source_bridge_v1_20261020T1530/libero_object_k256_seed23_development.json'
MAN_SHA='5f2bdcac8752c0cd06ad8dcb67114920b642db1415f6a88e1335d6c9f10fb028'
PRE='scripts/ops/formal_action_deployment_v1/'
PINS={'scripts/server/run_formal_downstream.py':'f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24',PRE+'contract.py':'efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19',PRE+'runtime_scope.py':'6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53',PRE+'wrapper.py':'d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33',PRE+'entry.py':'2cdb69923146cbffcaaec555b970d03efbce0c9b9f74e3b743a2ce67a21aae19',PRE+'gateway.py':'8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a',PRE+'reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd',PRE+'consumer.py':'16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'}
READS={};CHECKS=[];NEG=[];events=[]
sys.dont_write_bytecode=True;sys.path[:0]=[str(R/'src'),str(R/'scripts')]
def guard(event,args):
 if event.startswith(('subprocess.','socket.')) or event in ('os.system','os.posix_spawn','os.fork'):raise RuntimeError('Independent audit forbids process/network/Slurm')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0])).absolute();mode=args[1];flags=args[2] or 0
  if p.suffix.lower() in {'.pt','.pth','.bin','.safetensors','.ckpt','.pkl','.pickle','.init','.pruned_init','.npz','.h5','.hdf5'} or any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts):raise RuntimeError('Forbidden checkpoint/data/value access '+str(p))
  writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if writing and not p.is_relative_to(D):raise RuntimeError('Private write only '+str(p))
sys.addaudithook(guard)
def h(b):return hashlib.sha256(b).hexdigest()
def check(v,n):
 CHECKS.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def read(p,pin=None):
 p=Path(p);p=p if p.is_absolute() else R/p;b=p.read_bytes();sh=h(b)
 check(pin is None or sh==pin,'input exact SHA '+str(p.relative_to(R) if p.is_relative_to(R) else p))
 key=str(p);check(key not in READS or READS[key]==sh,'input stable '+key);READS[key]=sh;return b
def rd(p,pin=None):return json.loads(read(p,pin))
def write(n,v):
 p=D/n;p.parent.mkdir(parents=True,exist_ok=True);b=v if isinstance(v,bytes) else (json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':h(b),'bytes':len(b)}
def load(p,pin=None,name=None):
 p=Path(p);p=p if p.is_absolute() else R/p;b=read(p,pin);name=name or 'ind_object23_'+p.stem
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;exec(compile(b,str(p),'exec'),m.__dict__);return m
class Evidence:
 def __init__(self):self.project=self.root=R;self.files={};self.hashes=self.files;self.forbidden_paths=set()
 def path(self,n):
  p=Path(n);p=p if p.is_absolute() else R/p
  check('..' not in p.parts and p.resolve()==p.absolute() and p.is_relative_to(R),'safe evidence path '+str(n));return p
 def watch(self,n):
  p=self.path(n);b=read(p);key=p.relative_to(R).as_posix();self.files[key]=h(b);return h(b)
 def read(self,n):p=self.path(n);self.watch(p);return json.loads(p.read_bytes())
 def relative(self,n):return self.path(n).relative_to(R).as_posix()
 def unchanged(self):
  for n,pin in list(self.files.items()):check(h((R/n).read_bytes())==pin,'evidence unchanged '+n)
def negative(name,fn,contains=None):
 try:fn()
 except (ValueError,KeyError,TypeError,AssertionError) as e:
  check(contains is None or contains in str(e),name+' expected rejection reason')
  NEG.append({'name':name,'passed':True,'type':type(e).__name__,'message':str(e)});return
 except Exception as e:raise AssertionError(name+' unexpected exception '+repr(e))
 raise AssertionError(name+' admitted malformed CPU input')
def capture(name,fn):
 buff=io.StringIO()
 with contextlib.redirect_stdout(buff),contextlib.redirect_stderr(buff):out=fn()
 write('logs/'+name+'.log',buff.getvalue().encode());return out

def main():
 t0=time.monotonic()
 delivery=rd(E/'delivery_manifest.json','06319a5f4fb7dc7b1d26741436ee6b4997f23e5d2016de23890f630cb6183d3f')
 check(delivery['file_count']==39 and delivery['GPU_runs']==0 and delivery['status']=='sealed_not_admitted','archived author delivery scope')
 for row in delivery['files']:
  rel=Path(row['path']).relative_to(OLD);b=read(E/rel,row['sha256']);check(len(b)==row['bytes'],'archive member length '+str(rel))
 bridge=load(E/'bridge_v2.py','8785b42fe62dd513f796871875547c894de972516ac9762ad60a89d3df9a7c8e')
 p=bridge.policy();read(E/'policy_v1.json',bridge.POLICY_SHA256)
 for key,ref in p['references'].items():read(ref['path'],ref['sha256'])
 inventory=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 check(len(inventory['files'])==173,'source inventory173')
 for base in (R,S):
  for rel,pin in inventory['files'].items():read(base/rel,pin)
 base_factory=load(p['references']['original_factory']['path'],p['references']['original_factory']['sha256'])
 registration=rd('configs/experiments/formal_main_v2.json');manifest=rd(MAN,MAN_SHA);read(P/MAN,MAN_SHA)
 pair=rd(p['pair']['path'],p['pair']['sha256']);read(P/p['pair']['path'],p['pair']['sha256'])
 methods=manifest['methods'];docs={k:rd(p['references'][ref]['path'],p['references'][ref]['sha256']) for k,ref in [('saved','final_root'),('independent','final_independent'),('recovery_root','recovery_root'),('recovery_independent','recovery_independent'),('failure','failure'),('recovery_authorization','recovery_authorization'),('continuous_authorization','continuous_authorization')]}
 jobs=docs['saved']['registered_pair_jobs_at_review'];scope={'suite':'libero_object','pair':p['pair'],'method_rows':methods,'relevant':jobs}
 check(bridge.scope_guard(p,**scope) is None,'exact registered scope accepted')
 check(bridge.validate_documents(p,**docs)=={'3039258','3042627'},'real original source documents accepted')
 check(sum(p['allocation_seconds'].values())==58917 and p['allocation_seconds']['3028460']==84,'all three source allocations billed')
 selected=rd(p['references']['selected_server']['path'],p['references']['selected_server']['sha256'])
 check(selected['status']=='verified_actual_server_bytes' and selected['job_id']=='3042627','prior root selected-byte evidence identity')
 for ck in selected['checks']:check(ck['sha256']==p['selected_checkpoints'][ck['arm']]['sha256'] and ck['selected_update']==5000,'selected server identity agrees '+ck['arm'])
 failed=next(j for j in jobs if j['job_id']=='3028460')
 verifier=load(p['references']['failure_verifier']['path'],p['references']['failure_verifier']['sha256'])
 ev=Evidence();failure=verifier.require_saved(ev,job=failed,saved=docs['failure']);ev.unchanged();check(failure==docs['failure'],'original raw failure verifier rebuilt unchanged')
 check(failure['current_allocation_new_updates']==failure['current_allocation_arm_initializations']==0 and failure['failure_phase']=='before_VLA_from_pretrained_and_train_formal_arm','failure before VLA/training and no initialization')
 for key,value in [('elapsed_seconds',0),('status','COMPLETED'),('source_sha256','0'*64),('invocation_sha256','0'*64),('segment_end',1000)]:
  altered=copy.deepcopy(failed);altered[key]=value
  negative('original raw failure rejects '+key,lambda a=altered:verifier.require_saved(Evidence(),job=a,saved=docs['failure']))
 for name,change in [
 ('wrong suite',lambda x:x.update(suite='libero_goal')),
 ('wrong seed',lambda x:x['pair'].update(seed=17)),
 ('wrong budget',lambda x:x['pair'].update(visual_tokens=128)),
 ('reversed AB',lambda x:x['method_rows'].reverse()),
 ('missing B',lambda x:x['method_rows'].pop()),
 ('missing failed allocation',lambda x:x['relevant'].pop(0)),
 ('duplicate allocation',lambda x:x['relevant'].append(copy.deepcopy(x['relevant'][0]))),
 ('failed cost omitted',lambda x:x['relevant'][0].update(elapsed_seconds=0)),
 ('failed promoted success',lambda x:x['relevant'][0].update(status='COMPLETED',exit_code='0:0')),
 ('different checkpoint',lambda x:x['method_rows'][0]['identity'].update(checkpoint_sha256='0'*64)),
 ('different run root',lambda x:x['relevant'][1].update(run_root='/wrong')),
 ('2GPU allocation',lambda x:x['relevant'][1].update(gpus=2))]:
  v=copy.deepcopy(scope);change(v);negative('scope '+name,lambda v=v:bridge.scope_guard(p,**v))
 for name,change in [
 ('normal metadata for failed',lambda x:x['saved']['runtime_compatibility_history'].update({'3028460':x['saved']['runtime_compatibility_history']['3039258']})),
 ('missing successful metadata',lambda x:x['saved']['runtime_compatibility_history'].pop('3039258')),
 ('missing failure history',lambda x:x['saved']['startup_failure_history'].clear()),
 ('missing failure cost',lambda x:x['saved'].update(pair_allocated_gpu_seconds=58833)),
 ('missing independent final',lambda x:x['independent'].update(status='pending')),
 ('independent root swap',lambda x:x['independent']['root_review'].update(sha256='0'*64)),
 ('false failure reconstruction',lambda x:x['independent'].update(historical_failure_preserved_and_rebuilt=False)),
 ('AB order differs',lambda x:x['independent'].update(same_AB_initialization_and_full40000_order=False)),
 ('source173 differs',lambda x:x['independent'].update(all173_R_S_and_mirror_match=False)),
 ('cost missing allocation',lambda x:x['independent']['cost']['allocations'].pop(0)),
 ('double failure cost',lambda x:x['independent']['cost'].update(retained_failed_GPU_seconds=168)),
 ('recovery onlyA',lambda x:x['recovery_root'].update(completed_by_arm={'A':500,'B':0})),
 ('recovery independent pending',lambda x:x['recovery_independent'].update(status='pending')),
 ('failed sample claimed',lambda x:x['failure'].update(completed_by_arm={'A':1,'B':0})),
 ('wrong recovery target',lambda x:x['recovery_authorization'].update(original_target=1000)),
 ('different recovery job',lambda x:x['continuous_authorization'].update(recovery_job_id='3050711')),
 ('missing selected B',lambda x:x['independent']['actual_checkpoint_hashes'].pop()),
 ('checkpoint substituted',lambda x:x['independent']['actual_checkpoint_hashes'][0]['best'].update(sha256='0'*64)),
 ('chosen update substituted',lambda x:x['independent']['actual_checkpoint_hashes'][0].update(selected_update=4500))]:
  v=copy.deepcopy(docs);change(v);negative('documents '+name,lambda v=v:bridge.validate_documents(p,**v))
 facade=bridge.auditor(Evidence());orig_source=read(p['references']['original_consumer']['path'],p['references']['original_consumer']['sha256']).decode();derived=bridge.derived_source(orig_source)
 original_ast=ast.parse(orig_source);derived_ast=ast.parse(derived)
 check(len(original_ast.body)==len(derived_ast.body),'derived module retains same top-level definitions')
 changed=[]
 for a,b in zip(original_ast.body,derived_ast.body):
  if ast.dump(a,include_attributes=False)!=ast.dump(b,include_attributes=False):changed.append(getattr(a,'name',type(a).__name__))
 check(changed==['_root_pull','_pair_source'],'only pull ownership and pair allocation history functions differ')
 for name in ['review_source_provenance','_source_scope','review_suite_acceptance','downstream_contract','_execution_inputs','review_invocation','_original_adapter']:
  a=next(x for x in original_ast.body if getattr(x,'name',None)==name);b=next(x for x in derived_ast.body if getattr(x,'name',None)==name);check(ast.dump(a)==ast.dump(b),'original scientific/consumer AST unchanged '+name)
 write('source_derivation.diff',facade.source_diff.encode())
 negative('changed source replacement count',lambda:bridge.derived_source(orig_source.replace('    ids = {j["job_id"] for j in relevant}\n','    ids = set()\n')))
 original_factory_before=base_factory.source_review_module
 args=lambda output:['--project-root',str(R),'development','--suite','libero_object','--methods','A256_seed23','B256_seed23','--source-inventory','results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','--output',(D/output).relative_to(R).as_posix()]
 rc=capture('original_factory_expected_rejection',lambda:base_factory.main(args('original_rejected.json')))
 check(rc==2 and 'metadata history does not cover every allocation' in (D/'logs/original_factory_expected_rejection.log').read_text(),'original full factory still rejects historic failure under normal metadata assumption')
 factory,planner=bridge.control_modules(base_factory.Evidence(R))
 rc=capture('bridge_factory',lambda:factory.main(args('development.json')));check(rc==0,'real original factory passes via explicit bridge only')
 generated=rd(D/'development.json');check(generated==manifest and h((D/'development.json').read_bytes())==MAN_SHA,'scientific manifest byte-identical to preregistered candidate')
 proof=rd(D/'development.json.evidence.json')['source_provenance']
 check(base_factory.source_review_module is original_factory_before,'original factory module binding untouched')
 check(proof['version']==bridge.VERSION and proof['startup_failure_source_bridge']['normal_metadata_fabricated'] is False,'explicit source bridge version, no fabricated metadata')
 check(proof['helper_sha256']==h((E/'bridge_v2.py').read_bytes()),'proof binds archived exact bridge bytes')
 rows=manifest['methods'];alljobs=proof['registered_source_jobs'];kwargs={'registration':registration,'suite':'libero_object','inventory':inventory,'method_rows':rows,'jobs':alljobs}
 independent_consumer=bridge.auditor(base_factory.Evidence(R))
 reconstructed=independent_consumer.derived.review_source_provenance(base_factory.Evidence(R),**kwargs)
 check(reconstructed==proof,'original derived consumer independently rebuilds same explicit provenance proof')
 write('reconstructed_source_provenance.json',reconstructed)
 negative('unmodified original consumer still rejects',lambda:independent_consumer.original.review_source_provenance(base_factory.Evidence(R),**kwargs),'metadata history does not cover every allocation')
 for field,val in [('method_id','A128_seed23'),('frozen_model_sha256','0'*64),('future_head_deployed',True),('training_complete',False)]:
  v=copy.deepcopy(kwargs);v['method_rows'][0]['identity'][field]=val
  negative('full original consumer rejects changed '+field,lambda v=v:independent_consumer.review_source_provenance(base_factory.Evidence(R),**v))
 # Development-only invocation fence must reject before any terminal receipt access.
 negative('final invocation prohibited',lambda:independent_consumer.review_invocation(Evidence(),job={'suite':'libero_object','mode':'final'},invocation={'method_ids':p['method_ids']}),'development-only')
 negative('other pair invocation prohibited',lambda:independent_consumer.review_invocation(Evidence(),job={'suite':'libero_object','mode':'development'},invocation={'method_ids':['A256_seed41','B256_seed41']}),'pair differs')
 # Fresh atomic state read is only a CPU planning snapshot, never root authorization.
 state_raw=(R/'results/experiment_supervisor/state.json').read_bytes();state=json.loads(state_raw)
 state_ref=write('state_read_only_snapshot.json',state_raw)
 planargs={'stage':'development','source_inventory':'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','execution_manifest':MAN,'output_relative':None,'freeze_directory':None,'profile_panel':None,'prior_review':None,'collection_review':None,'repair_record':None,'resume':False,'stop_after':None}
 for label,change in [('final plan',{'stage':'final'}),('resume plan',{'resume':True}),('shortened plan',{'stop_after':1})]:
  a={**planargs,**change};negative(label,lambda a=a:planner.plan(SimpleNamespace(**a),state,project=R,helper=factory),'first complete development only')
 science=planner.plan(SimpleNamespace(**planargs),copy.deepcopy(state),project=R,helper=factory);science_ref=write('scientific_plan.json',science);inv=science['invocation']
 check(inv['method_ids']==p['method_ids'] and inv['prior_job_ids']==[] and not inv['resume'],'first200 exact AB pair only')
 for rel in [science['output_relative'],science['invocation_relative']]:check(not (R/rel).exists() and not (P/rel).exists(),'no preexisting output/invocation '+rel)
 check(not any(j.get('mode')=='development' and set(j.get('method_ids',[]))&set(p['method_ids']) and j.get('suite')=='libero_object' for j in state['registered_jobs']),'no registered duplicate Object256s23 development')
 oldplanner=load('scripts/ops/formal_downstream_supervisor.py','f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571')
 negative('production gateway original planner remains unintegrated',lambda:oldplanner.plan(SimpleNamespace(**planargs),copy.deepcopy(state),project=R),'metadata history does not cover every allocation')
 oldwrapper=load(P/'scripts/server/run_formal_downstream.py',PINS['scripts/server/run_formal_downstream.py'])
 checked=oldwrapper.verify(inv);check(checked.mode=='evaluate','actual P original wrapper verify succeeds metadata only')
 runtime=load(R/(PRE+'runtime_scope.py'),PINS[PRE+'runtime_scope.py'])
 contract=runtime.make_contract(project_root=R,source_root=S,suite='libero_object',stage='development')
 check(contract==runtime.make_contract(project_root=P,source_root=S,suite='libero_object',stage='development'),'R/P runtime contracts identical')
 for root in (R,P):
  for name,pin in runtime.validate_contract(contract,project_root=root,source_root=S).items():read(name,pin)
 assets=runtime.expected_asset_identities(project_root=P,source_root=S,contract=contract,asset_contract=inv['downstream_asset_compatibility'])
 write('runtime_metadata_identities.json',assets);write('runtime_contract.json',contract)
 c=load(R/(PRE+'contract.py'),PINS[PRE+'contract.py']);files={n:PINS[n] for n in c.EXPECTED_NEW_FILES};files[c.ACTION_ADAPTER]=c.ACTION_SHA
 action={'schema':c.SCHEMA,'kind':'formal_action_execution_contract','version':c.VERSION,'status':'candidate_pending_root_readiness','scientific_settings_changed':False,'final_evaluation_enabled':False,'files':files,'runtime_contract':contract,'GPU_acceptance':c.GPU_REFS,'source_inventory':{'path':c.INVENTORY,'sha256':c.INVENTORY_SHA},'transition':None}
 ar=write('execution_contract.json',action);effective=c.effective_plan(science,scientific_plan_ref=science_ref,execution_contract_ref=ar,execution_contract=action);write('effective_plan_private.json',effective)
 newwrapper=load(P/(PRE+'wrapper.py'),PINS[PRE+'wrapper.py'])
 negative('actual new P wrapper requires true root readiness',lambda:newwrapper.verify(effective['invocation'],project=P),'Exact path/SHA reference required')
 panel=rd(manifest['development_panel'],manifest['development_panel_sha256']);write('development_panel_shape.json',{'top_keys':list(panel),'suite':panel['suite'],'panel_sha256':manifest['development_panel_sha256']})
 check(manifest['environment']=={'environment_seed':0,'runtime_seed':17,'wait_steps':10,'action_chunk':8,'max_steps':280},'original Object environment kept')
 check([row['identity']['method_id'] for row in rows]==['A256_seed23','B256_seed23'] and all(not row['identity']['future_head_deployed'] for row in rows),'deploy current-input only fixed AB checkpoint identities')
 for name,pin in inv['root_evidence_sha256'].items():read(R/name,pin)
 for path,pin in list(READS.items()):check(h(Path(path).read_bytes())==pin,'all read evidence stable at exit '+path)
 write('plan_arguments.json',planargs);write('checks.json',CHECKS);write('negative_cases.json',NEG);write('input_hashes.json',READS)
 report={'schema':'formal_main_v2','kind':'independent_Object256_seed23_source_bridge_candidate_review','status':'passed_CPU_source_bridge_pending_explicit_root_integration','entrypoint_sha256':h((E/'bridge_v2.py').read_bytes()),'bridge_path':(E/'bridge_v2.py').relative_to(R).as_posix(),'policy_sha256':bridge.POLICY_SHA256,'candidate_manifest_sha256':'06319a5f4fb7dc7b1d26741436ee6b4997f23e5d2016de23890f630cb6183d3f','source_bridge_code_blockers':[],
 'production_admission_blockers':['Current production gateway still uses original planner; it correctly rejects this source history. Versioned exact bridge integration and independent gateway re-plan review are required.','Production terminal source consumer must reconstruct the same explicit bridge proof, path, SHA and policy; original invocation/trial/adapter validators must remain active.','Canonical full plan and true root/independent readiness, checkpoint byte checks at original runtime, and fresh locked/CAS duplicate/capacity authorization are still required.'],
 'checks':len(CHECKS),'negative_cases':len(NEG),'all_checks_passed':True,'source173_R_S_unchanged':True,'original_factory_and_consumer_unchanged':True,'bounded_source_changed_functions':changed,'failed_allocation_rebuilt_by_original_verifier':True,'retained_failed_GPU_seconds':84,'all_pair_GPU_seconds':58917,'failed_job':'3028460','successful_jobs':['3039258','3042627'],'new_GPU_seconds':0,'new_GPU_jobs':0,'Slurm_calls':0,'production_state_or_Git_writes':False,'checkpoint_or_final_values_opened':False,'scientific_settings_changed':False,'normal_metadata_fabricated':False,'scientific_manifest_byte_identical':True,'shared_teacher_data_init_order_and_selected_checkpoints':'original pinned root+independent and raw source consumer revalidated; no new training recomputation claimed','actual_P_original_wrapper_metadata_verified':True,'actual_P_runtime_metadata_verified':True,'new_action_wrapper_without_readiness_rejected':True,'terminal_GPU_receipt_verified':False,'production_gateway_ready':False,'production_terminal_consumer_ready':False,'final_release':False,'planned_development_trials':200,'development_unique_initial_states':100,'state_snapshot':state_ref,'state_snapshot_is_authorization':False,'CPU_wall_seconds':time.monotonic()-t0,
 'minimal_runtime_acceptance':['After explicit versioned integration and CPU gateway/consumer tests, root must rebuild canonical scientific/effective plans at their final paths, sign real P readiness and recheck exact checkpoint hashes through original runtime.','No new model-method GPU acceptance is justified by this source-only bridge: original Object256 acceptance and exact frozen execution remain. If root requires a new engineering launch, bound it separately to current development observations, zero scientific trial acceptance, no final access; do not silently run a policy smoke or new panel.','Only then a single registered existing Object256s23 A/B development200 job is allowed; its real original adapter/trial consumers plus independent terminal audit must pass before counting any result. Failure retains costs and stops, no automatic retry.'],
 'limitations':['CPU source and metadata acceptance is not GPU execution or root admission.','Current bridge proof includes its archived location; moving to a canonical production path requires regenerating all source proofs and plans.','Training evidence is inherited from exact original root and independent receipts and consumer checks, not claimed as a fresh independent5000-step re-audit.']}
 write('independent_review.json',report)
 print(json.dumps({k:report[k] for k in ['status','checks','negative_cases','source_bridge_code_blockers','new_GPU_jobs','CPU_wall_seconds']}))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  write('failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'checks':CHECKS,'negative_cases':NEG,'input_hashes':READS,'production_writes':False,'new_GPU_jobs':0});raise
