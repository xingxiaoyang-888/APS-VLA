"""Read-only proposed exact Git scope. Writes only this private audit package; never stages or commits."""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,os,subprocess,traceback,gzip,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R/'.local/final_delivery_scope_20261020T1644'
B='results/formal_main_v2/preflight/heartbeat_20261021T0044';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1644';BASE='88a0fea9b76a7f904ec0e9ce0c848b3b3413f36d'
PULLS={'20261020T170126Z_1fd1cd88b439':'f0633ec7db1a6f09aa92afb332d452e91f81c9d69c6c356bf27df45bdb338036','20261020T174830Z_45bc1fa22551':'f92b3cbe59584160b698c32b192b395284238dd8e0249151d1029f9d13c038cd','20261020T175321Z_d93105850084':'892b66bae4074e0a88712113233ea10da4c05e39cb8a8f9c014e2d34f9ff1b06'}
ALLOWED={'.json','.jsonl','.log','.out','.err','.txt','.py','.md','.yaml','.yml','.gz','.diff','.toml','.csv','.tsv'}
FORBIDDEN={'.pt','.pth','.ckpt','.safetensors','.bin','.pkl','.pickle','.pyc','.init','.npz','.npy','.h5','.hdf5'}
inputs={};candidates={};exceptions=[];covered={};missing=[];checks=0

def sha(b):return hashlib.sha256(b).hexdigest()
def ck(v,msg):
 global checks
 if not v:raise ValueError(msg)
 checks+=1
def safe(name):
 q=PurePosixPath(name);ck(not q.is_absolute() and q.as_posix()==name and '..' not in q.parts and '\\' not in name,'unsafe path '+name)
 p=R/name;ck(not any(z.is_symlink() for z in [p,*p.parents]),'symlink '+name);return p
def file_ref(name,pin=None,size=None):
 p=safe(name);ck(p.is_file(),'missing file '+name)
 st=p.stat();dig=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):dig.update(b)
 after=p.stat();ck((st.st_size,st.st_mtime_ns,st.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino),'changed input '+name)
 h=dig.hexdigest();ck(pin is None or h==pin,'input hash '+name);ck(size is None or size==st.st_size,'input size '+name)
 ref={'path':name,'sha256':h,'bytes':st.st_size};inputs[name]=ref;return ref
def rd(name,pin=None):file_ref(name,pin);return json.loads((R/name).read_bytes())
def put(name,v):
 p=D/name;p.parent.mkdir(exist_ok=True,parents=True);b=(json.dumps(v,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
def add(name,pin,source,category,size=None):
 rr=file_ref(name,pin,size);p=Path(name)
 ck(p.suffix.lower() in ALLOWED and p.suffix.lower() not in FORBIDDEN,'forbidden type '+name)
 ck(not any(x.lower() in ['weights','checkpoints','test','final','sealed'] or 'sealed' in x.lower() for x in p.parts),'forbidden path '+name)
 ck(rr['bytes']<100*(1<<20),'oversize selected '+name)
 if name.startswith(B+'/') or name.startswith(E+'/'):
  covered[name]={'file':rr,'source':source,'coverage':'existing root helper recursive B/E scope'};return
 if name not in candidates:candidates[name]={**rr,'category':category,'sources':[]}
 ck(candidates[name]['sha256']==rr['sha256'],'conflicting scope '+name)
 if source not in candidates[name]['sources']:candidates[name]['sources'].append(source)
def refs(value):
 if isinstance(value,dict):
  if isinstance(value.get('path'),str) and isinstance(value.get('sha256'),str) and len(value['sha256'])==64:yield value
  for v in value.values():yield from refs(v)
 elif isinstance(value,list):
  for v in value:yield from refs(v)
def git(*args,input=None):
 env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
 return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,env=env,input=input,capture_output=True,check=True)
start=time.monotonic()
try:
 ck(git('rev-parse','HEAD').stdout.decode().strip()==BASE,'HEAD advanced; regenerate scope')
 ck(not git('diff','--cached','--name-only').stdout,'index already staged; not scope preparation baseline')
 archive_name=B+'/last_training_lossless_archive.json';ar=rd(archive_name,'16ac8b6220b883e31777609d5ee85dd2674235bde811f08b9d6abdb0753a6914');aref=inputs[archive_name]
 ck(ar['status']=='packed_verified_originals_retained' and len(ar['raw'])==9,'archive receipt9')
 raw={x['path']:x for x in ar['raw']};sn=ar['snapshot'];snap=rd(sn['path'],sn['sha256']);ck(sn['sha256']=='1ec87a42055015a0d0ea5e059d913d3d1de0d7be0870b023a81f7ee774976509','archive exact snapshot')
 ck({x['path'] for x in snap['files']}==set(raw),'raw snapshot mapping9')
 add(sn['path'],sn['sha256'],{'type':'root_archive_receipt','reference':aref},'lossless_archive_snapshot',sn['bytes'])
 chunks=set();objects=set()
 for row in snap['files']:
  file_ref(row['path'],row['sha256'],row['bytes']);ck(raw[row['path']]=={k:row[k] for k in ['path','sha256','bytes']},'raw9 map exact')
  mr=row['manifest'];m=rd(mr['path'],mr['sha256']);ck(m['original_sha256']==row['sha256'] and m['original_bytes']==row['bytes'],'object source exact')
  add(mr['path'],mr['sha256'],{'type':'lossless_snapshot_member','reference':sn,'raw':raw[row['path']]},'lossless_archive_object',mr['bytes']);objects.add(mr['path'])
  reconstructed=hashlib.sha256();n=0
  for ch in m['chunks']:
   add(ch['path'],ch['compressed_sha256'],{'type':'lossless_object_chunk','reference':mr,'index':ch['index']},'lossless_archive_chunk',ch['compressed_bytes']);chunks.add(ch['path'])
   b=gzip.decompress((R/ch['path']).read_bytes());ck(len(b)==ch['raw_bytes'] and sha(b)==ch['raw_sha256'] and ch['offset']==n,'lossless raw chunk');reconstructed.update(b);n+=len(b)
  ck(n==row['bytes'] and reconstructed.hexdigest()==row['sha256'],'lossless full raw reconstruction')
  exceptions.append({'path':row['path'],'sha256':row['sha256'],'bytes':row['bytes'],'reason':'raw original excluded from Git; exact lossless archive reconstruction verified','archive_snapshot':sn,'archive_object':mr})
 ck(len(objects)==9 and len(chunks)==39,'archive9objects39chunks')
 rawignore=git('check-ignore','--stdin',input=('\n'.join(sorted(raw))+'\n').encode()).stdout.decode().splitlines();ck(set(rawignore)==set(raw),'all9 raw ignored')
 pull_files=set()
 for d,pin in PULLS.items():
  name='results/formal_main_v2/pulls/'+d+'/receipt.json';pull=rd(name,pin);pr=inputs[name]
  ck(pull['status']=='verified_nonweight_snapshot' and pull['weights_copied'] is False and pull['sealed_initial_states_copied'] is False,'real nonweight pull')
  add(name,pin,{'type':'exact_root_supplied_original_pull','reference':pr},'original_pull_receipt')
  before='results/formal_main_v2/pulls/'+d+'/inventory_before.json';after=before.replace('inventory_before','inventory_after');iv=rd(before,pull['inventory_sha256']);av=rd(after)
  ck(iv==av,'stable pull inventory');add(before,pull['inventory_sha256'],{'type':'pull_inventory','reference':pr},'original_pull_inventory');add(after,inputs[after]['sha256'],{'type':'pull_inventory','reference':pr},'original_pull_inventory')
  by={x['relative']:x for x in iv['files']};ck(len(by)==len(iv['files']),'unique inventory')
  for row in pull['files']:
   rr=row['relative'];ck(row['path']==str(P/rr) and row['local_path']==str(R/rr),'pull exact paths')
   ck(by[rr]['sha256']==row['sha256'] and by[rr]['bytes']==row['bytes'],'pull bound inventory row');file_ref(rr,row['sha256'],row['bytes']);pull_files.add(rr)
   if rr in raw:continue
   category='registered_slurm_log' if row['kind']=='slurm_log' else 'registered_job_receipt' if row['kind']=='job_receipt' else 'completed_development_raw' if '/downstream/development/' in rr else 'completed_training_nonweight'
   add(rr,row['sha256'],{'type':'original_stable_nonweight_pull','reference':pr,'job_ids':row['job_ids'],'kind':row['kind']},category,row['bytes'])
 # Exact root reviews already published; this does not republish private audit candidates.
 for jid in ['3043813','3044844','3050870','3050890','3050901','3050916']:
  name=B+'/'+jid+'_root_terminal.json';root=rd(name);rr=root['root_review'];add(rr['path'],rr['sha256'],{'type':'original_root_terminal_receipt','reference':inputs[name]},'original_root_review')
 # Archive-shape evidence for the pending canonical independent copies; never invent publication.
 for suite,jid,src,pin in [('libero_goal','3043813',E+'/last_two_training_independent/goal/3043813_independent_review.json','d23ddb4a0636c3da92293ea766a099bbf62dabff6b8379c17d07af73dfb1d670'),('libero_object','3044844',E+'/last_two_training_independent/object/independent_review.json','9d357b032ae9c8c3d1aa4f901875eec4ef4fca7c2912805c52e114813e3b2150')]:
  source=file_ref(src,pin);name='results/formal_main_v2/'+suite+'/k64/seed23/training/segment_reviews/'+jid+'_independent.json'
  if (R/name).is_file():add(name,pin,{'type':'root_published_exact_independent_copy','source_archive':source},'canonical_independent_training_review')
  else:missing.append({'path':name,'expected_sha256':pin,'source_archive':source,'status':'await_root_publication_after_separate_post_audit','root_may_append_exactly_after_publishing':True})
 # Explicit root source-only/static/readiness publication chain for Object23 new control layer.
 prefix='results/formal_main_v2/execution/object256seed23_source_control_v1_20261020T1644/'
 anchors=[(B+'/Object_source_publication.json','104aba5206c8d8c917dab63f2491161460e38dce7eef97c3729ee4aeda67201a'),(B+'/Object_static_plan_publication.json','06a98ba334a64761e795d0c6fea74feae5e769571f1c4c0bea1473812fac2a9a'),(B+'/Object_runtime_readiness_root.json','4a9ae0aa406884ba7ee3d2f29799ff26186b19e42c4b1359de498df3cb400233'),(B+'/Object256s23_reservation_activation.json','a57ed6af5489fe255ed2777e0b8c13800360cb62a23542b9963beadebdccb93d')]
 for name,pin in anchors:
  data=rd(name,pin);anchor=inputs[name]
  for rr in refs(data):
   if rr['path'].startswith((prefix,'scripts/ops/formal_object256s23_source_bridge_v1/')):add(rr['path'],rr['sha256'],{'type':'exact_root_publication_reference','reference':anchor},'Object23_published_control_metadata',rr.get('bytes'))
 readiness=rd(prefix+'runtime_readiness.json');rr=readiness['root_review'];add(rr['path'],rr['sha256'],{'type':'actual_root_readiness_role','reference':inputs[prefix+'runtime_readiness.json']},'Object23_published_control_metadata')
 recname=B+'/libero_object_k256_seed23_3052166_pending_reconciliation.json';recon=rd(recname);rec=inputs[recname];ck(recon['status']=='exact_original_ACK_job_reconciled' and recon['new_submissions']==0,'exact existing ACK reconciliation')
 job=recon['job'];ck(job['job_id']=='3052166','unique reconciled job');add(job['invocation'],job['invocation_sha256'],{'type':'exact_root_reconciled_job','reference':rec},'Object23_registered_invocation')
 gateway='results/formal_main_v2/downstream_gateway/'+job['downstream_gateway']['authorization']['sha256']+'/'
 for key in ['original_ACK','original_failure','original_preflight']:
  rr=recon[key];add(rr['path'],rr['sha256'],{'type':'exact_root_reconciliation_original_evidence','reference':rec,'role':key},'Object23_gateway_transaction')
 committed=rd(gateway+'committed.json');ck(committed['job']['job_id']=='3052166' and committed['root_reconciliation']=={'path':recname,'sha256':rec['sha256']},'committed reconciliation')
 add(gateway+'committed.json',inputs[gateway+'committed.json']['sha256'],{'type':'exact_registered_commit_for_root_reconciliation','reference':rec},'Object23_gateway_transaction')
 ob=rd(gateway+'submitted_job_observation.json');ck(ob['job_id']=='3052166' and ob['request_token']==job['downstream_gateway']['request_token'],'registered exact token observation');add(gateway+'submitted_job_observation.json',inputs[gateway+'submitted_job_observation.json']['sha256'],{'type':'exact_token_observation_for_root_reconciliation','reference':rec},'Object23_gateway_transaction')
 subname='results/formal_main_v2/submissions/3052166.json';sub=rd(subname);ck(sub==committed['job'],'submission equals root reconciled committed job');add(subname,inputs[subname]['sha256'],{'type':'exact_root_reconciled_committed_job_copy','reference':inputs[gateway+'committed.json']},'Object23_registration_receipt')
 # Read exactly the root-named machine directory, retaining machine/independent distinction.
 mn='results/formal_main_v2/autonomous_training/run_v1/reviews/libero_goal_k64_seed23_2f71f57773be4dc38b46df6b6b9f4462'
 state_b=(R/'results/experiment_supervisor/state.json').read_bytes();st=json.loads(state_b);auto=st['autonomous_training_v1']['completed_pairs']['libero_goal_k64_seed23']
 auto_ref=put('machine_owner_state_excerpt.json',{'kind':'read_only_owner_excerpt','state_sha256_at_read':sha(state_b),'machine_pair':auto,'not_an_independent_training_acceptance':True})
 output=auto['machine_output'];ck(output['path']==mn+'/outcome.json','machine owner exact output');out=rd(output['path'],output['sha256']);ck(out['completed_by_arm']=={'A':5000,'B':5000} and out['pair_key']=='libero_goal_k64_seed23','machine exactpair')
 actual={p.name for p in (R/mn).iterdir() if p.is_file()};ck(actual=={'execution.json','machine_review.json','outcome.json','request.json','selected_server_hashes.json','stdout.log','stderr.log'},'exact machine7files')
 erefs={x['path']:x['sha256'] for x in auto['evidence_refs'] if x['path'].startswith(mn+'/')};ex=rd(mn+'/execution.json');req=rd(mn+'/request.json',erefs[mn+'/request.json']);ck(req['job_id']=='3043813' and req['pair_key']=='libero_goal_k64_seed23' and ex['returncode']==0 and ex['slurm_submitted'] is False,'machine execution exact identity')
 tr='results/formal_main_v2/control_transport/auto_96d57de15bb44012824e1ac146a4e9f8.jsonl';tb=(R/tr).read_bytes();last=json.loads(tb.splitlines()[-1]);ck(last['event']=='control_end' and last['returncode']==0,'machine closed original transport')
 for name in sorted(actual):
  rel=mn+'/'+name;rr=file_ref(rel,erefs.get(rel));add(rel,rr['sha256'],{'type':'root_named_machine_execution_directory','owner_snapshot':auto_ref,'machine_output':output,'execution':inputs[mn+'/execution.json'],'original_closed_transport':file_ref(tr),'root_signature_claimed':False},'Goal23_machine_execution',rr['bytes'])
 ignore_exceptions=[{'line':'!/'+mn+'/'+name,'file':file_ref(mn+'/'+name),'reason':'Root explicitly approved preserving exact immutable stdout/stderr; do not broaden *.log exclusion'} for name in ['stdout.log','stderr.log']]
 # Source inventory remains unchanged; closure metadata is not a weight or final-state read.
 inv=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');ck(len(inv['files'])==173,'frozen source173')
 for n,pin in inv['files'].items():file_ref(n,pin)
 current=git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split('\0');classified={};unbound=[];closed=[];opened=[]
 builtin={'.gitignore','results/experiment_supervisor/state.json',*[f'docs/{n}.md' for n in ['实验进度','完整实验计划','正式主实验规划','正式主实验阶段结论','正式自动连续训练执行登记','正式下游阻塞登记_20261020T1644']],*[f'results/formal_main_v2/libero_goal/k64/seed41/training/segment_reviews/{n}' for n in ['3043877.json','3043877_independent.json']]}
 for line in current:
  if not line:continue
  name=line[3:];category=None
  if name in candidates:category='candidate_additional_exact'
  elif name.startswith((B+'/',E+'/')):category='root_helper_existing_recursive_B_E'
  elif name in builtin:category='root_helper_existing_exact'
  elif name.startswith('results/formal_main_v2/autonomous_training/run_v1/events/'):category='root_helper_existing_locked_event_index'
  elif name=='results/formal_main_v2/autonomous_training/run_v1/activation/controller_3034538.out':category='excluded_live_controller'
  elif name.startswith('results/formal_main_v2/control_transport/'):
   text=(R/name).read_bytes();rows=[json.loads(x) for x in text.splitlines()]
   if rows and rows[-1].get('event')=='control_end':category='root_helper_closed_transport';closed.append(file_ref(name))
   else:category='excluded_open_transport';opened.append(name)
  else:unbound.append({'status':line[:2],'path':name,'reason':'No source from this bounded candidate. Root must separately bind, append, or deliberately exclude.'})
  if category:classified[name]=category
 source_summary=Counter(x['category'] for x in candidates.values())
 note={'schema':'formal_main_v2','status':'independent_candidate_scope_not_root_authorization','baseline':BASE,'additional_exact':[candidates[n] for n in sorted(candidates)],'exact_gitignore_exceptions':ignore_exceptions,'root_archive_guard_snapshot':sn,'raw_exclude_all9':list(raw.values()),'already_covered_B_E_references':list(covered.values()),'pending_exact_root_publications':missing,'unbound_changes_requiring_separate_root_scope':unbound,'category_summary':dict(source_summary),'candidate_files':len(candidates),'candidate_bytes':sum(x['bytes'] for x in candidates.values()),'original_pull_files_deduplicated':len(pull_files),'lossless_archive_verified':{'originals':9,'objects':len(objects),'compressed_chunks':len(chunks),'original_bytes':sum(x['bytes'] for x in raw.values()),'in_memory_complete_reconstruction_sha256_matches':True},'exclusions':exceptions,'changes_classification':classified,'open_transports_excluded':opened,'closed_transport_refs_handled_by_existing_root_helper':closed,'snapshot_counts_are_not_scientific_state_acceptance':True,'future_post_integration_archive_requires_root_separate_append':True,'Git_index_commit_push_mutated':False,'canonical_state_Slurm_mutated':False,'weights_or_sealed_values_read':False,'source173_unchanged':True,'GIT_OPTIONAL_LOCKS':'0','checks':checks,'CPU_wall_seconds':time.monotonic()-start,'created_utc':datetime.now(timezone.utc).isoformat()}
 result=put('additional_exact_candidate_v2.json',note);put('scope_input_refs_v2.json',inputs)
 print(json.dumps({'candidate':result,'files':len(candidates),'bytes':note['candidate_bytes'],'classes':dict(source_summary),'pending':missing,'unbound':unbound,'checks':checks}))
except BaseException as e:
 f=put('scope_failure_v2.json',{'status':'failed','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'input_refs':inputs,'checks':checks});print(json.dumps(f));raise
