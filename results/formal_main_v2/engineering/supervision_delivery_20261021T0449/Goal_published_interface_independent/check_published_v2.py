"""Read-only exact R/P publication and actual capture integration review; no GPU."""
from pathlib import Path
import sys,json,hashlib,importlib.util,datetime,collections,copy,traceback,ast
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/goal_remaining5_published_integration_20261021T0449'
B='results/formal_main_v2/preflight/heartbeat_20261021T1249/'
PKG='scripts/ops/formal_goal_remaining5_gate_v1'
M='200dcef220601fd26565bb48106856612853739f486f8374ef91a4967e60692f'
KEYS=['libero_goal_k256_seed23','libero_goal_k256_seed41','libero_goal_k64_seed17','libero_goal_k64_seed23','libero_goal_k64_seed41']
PINS={
 B+'Goal_remaining5_prepared_invocations.json':'45a1fe173f83597a8181f5129a5354bbdf0f49143743eac96de2dff8a418e578',
 B+'Goal_remaining5_runtime_publication.json':'00b108d9042996a887ea4d840bde91f54364da0f6c277cecfe5a8c5830cff17b',
 B+'Goal_remaining5_actual_P_index.json':'7e449e03818eda3402871b49cf952941f7590318cf640cd32cac96c2ba1f6fad',
 '.local/goal_remaining5_plans_20261021T0449/v2/candidate_index.json':'638ec6f36339aa3a43a78266a60c58427aa40f22979f442cd740432962a28d3f',
 PKG+'/package_manifest.json':M,
 'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json':'5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926',
 '.local/publish_goal_remaining5_runtime_20261021T0449.py':'5eb3b8d12a65c9a80542d9eeb529f83281d2d8e9a8c0b8adaa5d92a96ce630ef'}
CHECKS=[]
REJECTIONS=[]
def need(ok,msg):
 if not ok: raise ValueError(msg)
 CHECKS.append(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def data(path,pin=None,size=None):
 p=Path(path)
 need(p.is_absolute() and p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]),'canonical nonlink '+str(p))
 before=p.stat();raw=p.read_bytes();after=p.stat()
 need((before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns),'stable bytes '+str(p))
 if pin:need(sha(raw)==pin,'pinned SHA '+str(p))
 if size is not None:need(len(raw)==size,'exact bytes '+str(p))
 return raw
def read(path,pin=None,size=None):return json.loads(data(path,pin,size))
def ref(path):b=data(path);return {'path':str(Path(path).relative_to(R)),'bytes':len(b),'sha256':sha(b)}
def put(name,obj):
 raw=(json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
 with (D/name).open('xb') as f:f.write(raw)
 return {'path':str((D/name).relative_to(R)),'bytes':len(raw),'sha256':sha(raw)}
def load(path,pin,name):
 data(path,pin);spec=importlib.util.spec_from_file_location(name,path)
 module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
def reject(label,fn):
 try:fn()
 except (ValueError,AssertionError,KeyError,TypeError,IndexError) as e:
  REJECTIONS.append({'label':label,'error_type':type(e).__name__,'message':str(e)[:240]});return
 raise ValueError('negative unexpectedly accepted: '+label)
def capacity(s,key):
 need(s['version']=='goal-remaining5-dual-root-budget-v1' and s['aggregate_pair_keys']==KEYS,'exact five storage scope')
 for name in ['no_dedup_credit','no_expected_release_credit','exclusive_claim_required_at_execution','filesystem_space_can_change_after_check','quota_not_proven']:
  need(s[name] is True,'storage '+name)
 need(s['new_storage_paths_created'] is False,'capture did not create storage')
 need(s['raw_upper_bytes']==19871439680 and s['local_upper_bytes']==1003782144,'fixed raw upper byte budgets')
 need(s['R_required_per_pair']==20945181504 and s['P_required_per_pair']==1137999872,'per-pair storage margins')
 need(s['R_aggregate_required']==5*s['R_required_per_pair'] and s['P_aggregate_required']==5*s['P_required_per_pair'],'five aggregate sums')
 expected={}
 for k in KEYS:
  expected[str(R/'results/formal_main_v2/raw_runtime/goal_remaining5_v1'/k/'attempt01')]=s['R_required_per_pair']
  expected[str(P/'results/formal_main_v2/execution/goal_remaining5_v1'/k/'attempt01')]=s['P_required_per_pair']
 rows=s['all_paths'];need(len(rows)==10 and {x['path']:x['required_bytes'] for x in rows}==expected,'all ten exact reserved roots')
 devices={}
 for x in rows:
  need(x['symlink'] is False and x['writable'] is True and x['owner_uid']==10738,'captured owner and path safety')
  need(x['free_bytes']>=x['required_bytes']>0,'captured per-path capacity')
  ds=devices.setdefault(x['st_dev'],{'required_bytes':0,'free_bytes':x['free_bytes'],'st_dev':x['st_dev']})
  ds['required_bytes']+=x['required_bytes'];ds['free_bytes']=min(ds['free_bytes'],x['free_bytes'])
 need(sorted(devices.values(),key=lambda x:x['st_dev'])==sorted(s['filesystem_checks'],key=lambda x:x['st_dev']),'filesystem grouping from complete rows')
 need(all(x['free_bytes']>=x['required_bytes'] for x in devices.values()),'captured aggregate filesystem free bytes')
 need(s['raw']==next(x for x in rows if x['path']==str(R/'results/formal_main_v2/raw_runtime/goal_remaining5_v1'/key/'attempt01')),'own raw captured row')
 need(s['local']==next(x for x in rows if x['path']==str(P/'results/formal_main_v2/execution/goal_remaining5_v1'/key/'attempt01')),'own output captured row')
 return list(devices.values())
def check_capture(cap,key,manifest,iref,identity):
 need(cap['schema']=='formal_main_v2' and cap['kind']=='Goal_remaining5_actual_P_verification_capture' and cap['pair_key']==key,'capture identity '+key)
 need(cap['argv']==['/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python','-B',str(P/PKG/'entry.py'),'--pair-key',key,'--verify','--package-manifest-sha256',M],'actual P exact argv '+key)
 need(cap['returncode']==0 and cap['stderr']=='' and cap['runtime_files']==manifest['files'],'capture exit and complete source map '+key)
 need(cap['new_GPU_submissions']==0 and cap['real_GPU_acceptance'] is False,'capture not GPU acceptance '+key)
 need(datetime.datetime.fromisoformat(cap['started_utc'])<datetime.datetime.fromisoformat(cap['completed_utc']),'capture UTC interval '+key)
 out=json.loads(cap['stdout'])
 need(out['status']=='passed_metadata_source_capacity_only' and out['pair_key']==key and out['stage_key']=='goal_remaining5_v1/'+key,'actual verifier scope/status '+key)
 need(out['package_manifest_sha256']==M and out['config_sha256']==manifest['files'][PKG+'/pairs/'+key+'/config.json'],'actual verifier package/config '+key)
 need(out['original_invocation']=={'path':str(P/iref['path']),'sha256':iref['sha256']},'actual verifier genuine original invocation '+key)
 need(out['identity']==identity,'actual captured identity equals independent original source rebuild '+key)
 for field in ['GPU_execution_authorized','actual_GPU_runtime_verified','final_release']:need(out[field] is False,'no admission '+field)
 need(out['new_GPU_submissions']==0 and out['original200_HOLD'] is True,'source-only actual verification')
 return out,capacity(out['storage'],key)
def main():
 started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 before=sha(data(R/'results/experiment_supervisor/state.json'))
 inputs={rel:read(R/rel,pin) for rel,pin in PINS.items() if not rel.endswith('.py')}
 helper=data(R/'.local/publish_goal_remaining5_runtime_20261021T0449.py',PINS['.local/publish_goal_remaining5_runtime_20261021T0449.py']).decode()
 # Static inspection of exact published root helper; it is NOT executed here.
 tree=ast.parse(helper)
 need(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='flock' for n in ast.walk(tree)),'publication helper holds fcntl writer lock')
 need("results/experiment_supervisor/.writer.lock" in helper and '==ST' in helper and 'assert not (root/rel).exists()' in helper,'helper exact writer lock/CAS/nonoverwrite')
 need('os.fsync(f.fileno())' in helper and 'with p.open("xb")' in helper,'helper exclusive fsync publication')
 manifest=inputs[PKG+'/package_manifest.json'];need(manifest['pair_keys']==KEYS and len(manifest['files'])==20,'20 source package and five pairs')
 pub=inputs[B+'Goal_remaining5_runtime_publication.json']
 need(pub['kind']=='root_exact_remaining5_source_publication' and pub['new_GPU_submissions']==0 and pub['package_manifest_sha256']==M,'source-only root publication')
 expected={**manifest['files'],PKG+'/package_manifest.json':M,'scripts/ops/formal_goal_remaining5_dispatch_v1/gateway.py':'45003c082efc508249e9ba41aac15639be7c4188d9517ee1717e71f563448f9b','scripts/ops/formal_goal_remaining5_dispatch_v1/scope.json':'f44e8cf97e0a9456782ea57ffeb4c4f39e47058b51c320b3947c73bd1a6cf27b'}
 need(len(pub['source_rows'])==23 and {x['path']:x['sha256'] for x in pub['source_rows']}==expected,'23 exact publication items')
 for row in pub['source_rows']:
  need(row['destinations']==['R','P'],'exact two publication roots')
  original=data(R/row['source'],row['sha256'],row['bytes'])
  for root in [R,P]:need(data(root/row['path'],row['sha256'],row['bytes'])==original,'source to published bytes '+str(root/row['path']))
 src=inputs['results/formal_main_v2/source/formal_main_v2_run_564be0995e.json']
 need(len(src['files'])==173,'173 frozen input files')
 for rel,h in src['files'].items():
  if isinstance(h,dict):h=h['sha256']
  for root in [R,S]:data(root/rel,h)
 idx=inputs['.local/goal_remaining5_plans_20261021T0449/v2/candidate_index.json']
 prep=inputs[B+'Goal_remaining5_prepared_invocations.json']
 need(len(prep['publication_map'])==10 and len(prep['original_invocations'])==5,'five prepared invocations/ten metadata publications')
 for row in prep['publication_map']:
  original=data(R/row['source'],row['sha256'])
  for root in [R,P]:need(data(root/row['destination'],row['sha256'])==original,'prepared canonical R/P bytes')
 # Only verifies published bytes, not a self-independent review of the authored science.
 need(idx['scope']==KEYS,'author index exact scope')
 for row in idx['publication_map']:
  for tag in row['install_roots']:data({'R':R,'P':P}[tag]/row['destination'],row['sha256'],row['bytes'])
 captures=inputs[B+'Goal_remaining5_actual_P_index.json']
 need(captures['status']=='five_actual_P_verifications_passed_source_identity_capacity_only' and len(captures['captures'])==5 and captures['new_GPU_submissions']==0,'five actual captures')
 wrapper=load(P/'scripts/ops/formal_action_deployment_v1/wrapper.py','d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33','integration_actual_original_wrapper')
 entry=load(P/PKG/'entry.py',manifest['files'][PKG+'/entry.py'],'integration_actual_new_entry')
 legacy=load(P/'scripts/ops/formal_evaluation_adapter.py','b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd','integration_actual_legacy_adapter')
 results=[]
 for key,iref,cref in zip(KEYS,prep['original_invocations'],captures['captures']):
  pair=idx['pairs'][key];need(iref['path']==pair['planned_invocation_path'],'own planned invocation path '+key)
  inv=read(P/iref['path'],iref['sha256'])
  ctx=wrapper.verify(inv,project=P)
  need(ctx['effective_plan']['invocation']=={k:inv[k] for k in ctx['effective_plan']['invocation']},'original wrapper actual effective equality '+key)
  need(inv['suite']=='libero_goal' and inv['stage']=='development' and inv['method_ids']==pair['method_ids'],'original invocation exact pair '+key)
  need(inv['scientific_plan']==pair['scientific_plan'] and inv['action_execution_contract']==pair['execution_contract'],'own original plan references '+key)
  a=ctx['args'];env=read(Path(inv['execution_manifest']),inv['execution_manifest_sha256'])['environment'];need(env==dict(action_chunk=8,environment_seed=0,max_steps=300,runtime_seed=17,wait_steps=10) and not a.resume and not a.prepare_only,'original manifest runtime/environment seeds and fresh scope '+key)
  for role in ['root_review','independent_review']:
   r=ctx['readiness'][role]
   need(data(P/r['path'],r['sha256'])==data(R/r['path'],r['sha256']),'actual R/P '+role+' '+key)
  scope=entry.context(key)
  spec=read(scope.SPEC,scope.spec_sha)
  identity=entry.validate_prefix(scope,inv,legacy,spec['rows'])
  cap=read(R/cref['path'],cref['sha256'],cref['bytes'])
  out,grouping=check_capture(cap,key,manifest,iref,identity)
  reject('foreign capture argv '+key,lambda cap=cap:check_capture({**cap,'argv':cap['argv'][:-1]+['0'*64]},key,manifest,iref,identity))
  bad=copy.deepcopy(cap);x=json.loads(bad['stdout']);x['original_invocation']['sha256']='0'*64;bad['stdout']=json.dumps(x)
  reject('changed actual invocation '+key,lambda bad=bad:check_capture(bad,key,manifest,iref,identity))
  bads=copy.deepcopy(out['storage']);bads['filesystem_checks'][0]['required_bytes']-=1
  reject('under-accounted shared filesystem '+key,lambda s=bads:capacity(s,key))
  bads=copy.deepcopy(out['storage']);bads['all_paths']=bads['all_paths'][:-1]
  reject('missing fifth pair output '+key,lambda s=bads:capacity(s,key))
  badrows=copy.deepcopy(spec['rows']);badrows[0],badrows[1]=badrows[1],badrows[0]
  reject('actual runtime identity order '+key,lambda rows=badrows:entry.validate_prefix(scope,inv,legacy,rows))
  results.append({'pair_key':key,'original_invocation':iref,'actual_P_capture':cref,'original_wrapper_verify':'passed_actual_P_module_unchanged','actual_identity_rebuilt':identity,'filesystem_recomputed':grouping,'runtime_seed':env['runtime_seed'],'environment_seed':env['environment_seed'],'original_method_ids':inv['method_ids'],'root_review':ctx['readiness']['root_review'],'independent_review':ctx['readiness']['independent_review']})
 after=sha(data(R/'results/experiment_supervisor/state.json'))
 need(before==after,'observed state stable during read-only integration review')
 report={'schema':'formal_main_v2','kind':'Goal_remaining5_actual_publication_integration_review','status':'passed_metadata_source_interfaces_only','reviewed_by':'spatial588_recovery_author_2054','review_scope':'actual_publication_original_wrapper_and_capture_interfaces_only','own_plan_authorship_disclosed':True,'independent_scientific_plan_review_claimed':False,'actual_new_P_process_rerun_by_this_reviewer':False,'root_actual_P_captures_reviewed':True,'original_wrapper_actual_P_verify_count':5,'new_runtime_actual_identity_rebuild_count':5,'published_source_count':23,'frozen173_R_and_S_verified':True,'input_pins':PINS,'state_sha256_observed_before':before,'state_sha256_observed_after':after,'source_publication_helper_static_review':'exact writer lock/CAS/nonoverwrite/fsync; captures use P verify argv after publication; no execution by this reviewer','capture_capacity_scope':'captured actual metadata at each timestamp, recomputed by shared filesystem; not a guarantee of future free space or quota','weight_files_rehashed_by_this_review':0,'new_GPU_submissions':0,'GPU_execution_authorized':False,'new_scientific_trials':0,'scientific_results_accepted':0,'final_values_read':False,'final_release':False,'checks':len(CHECKS),'negative_checks':len(REJECTIONS),'blockers':[],'required_after_review':['root exact authorization and current native gateway admission','fresh capacity and all-mode scheduler identity checks at submission','full raw terminal consumers and independent scientific acceptance after any future run'],'pairs':results,'negative_results':REJECTIONS,'started_utc':started,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 rr=put('integration_review.json',report)
 readme='# Published Goal remaining-five interface review\n\nThis package reviews actual R/P source publication, genuine prepared original invocations and the saved root-executed actual P metadata captures. The reviewer authored the five plans, so this is not an independent scientific-plan review. Five unchanged actual-P original-wrapper validators and the new runtime full-200 identity validator were executed read-only; the new actual-P process captures were checked rather than rerun. No model inference, weights rehash, scheduler action, canonical/state/Git write or final value read occurred. Captured capacity is not future capacity or quota proof. GPU authorization and scientific acceptance remain separate.\n\nThe original read-only review helper stopped on a mistaken Namespace seed field assumption; the retained failure precedes scientific execution. The v2 helper reads the exact original execution manifest environment instead. Run check_published_v2.py via the exact server-control transport entry SHA. All outputs use exclusive creation; preserve this package and choose a new private directory for a new review. Parent archives the transport journal separately after completion.\n'
 with (D/'README.md').open('x') as f:f.write(readme)
 manifest={'schema':'formal_main_v2','root':str(D.relative_to(R)),'file_count':5,'files':[ref(D/name) for name in ['check_published.py','failed_review.json','check_published_v2.py','integration_review.json','README.md']],'GPU_execution_authorized':False,'review_scope':report['review_scope']}
 mr=put('delivery_manifest.json',manifest)
 print(json.dumps({'status':report['status'],'checks':len(CHECKS),'negative_checks':len(REJECTIONS),'review':rr,'manifest':mr}))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  put('failed_review_v2.json',{'schema':'formal_main_v2','status':'failed','exception':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'checks_so_far':len(CHECKS),'GPU_execution_authorized':False});raise
