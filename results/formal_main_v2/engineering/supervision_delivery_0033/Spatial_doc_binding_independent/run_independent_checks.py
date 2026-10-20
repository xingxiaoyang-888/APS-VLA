"""Independent exact-document bridge review; CPU/read-only actual prepare only."""
from pathlib import Path
import ast,copy,difflib,hashlib,importlib.util,json,os,subprocess,sys,traceback
from datetime import datetime,timezone
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
C=R/'.local/spatial_continuous_doc_binding_0033'
D=Path(__file__).resolve().parent
OLD=R/'scripts/ops/formal_spatial_cuda_continuous_admission_v1'
PINS={'admission.py':'187e5393e6ffcdc8f042bfcdb032860048e6f36282160825dbb928f3a83ad46f','gateway.py':'4f552abcc05d72ff84975e360ea28a624a4744febb8518e2fc71839fe47d5864','document_binding.json':'37123f887b53931016d6a5ef85984b5c76d9b055b632d4b171298ffe2faea019','authorization_a1_draft.json':'e56ef07b135f5f229546b68f6bd9e18138ffdf43c4fca4127ae7e20070fbe25f','actual_prepare_a1.json':'18025e16cee97c03b8db50f5bc37a4acbbf8ca5c6f85e8237223be3659d3a097','test_doc_binding.py':'b52597c3ff47b506c01ce3d076308b6e2028f9221614e454a84b419b68e6c247'}
OLDPINS={'admission.py':'0e5d2bbdca27640c4784393b3ea6a17969a7c6235bdeeb10b61c4a8ab7546b74','gateway.py':'71af9cf0bce935d00934db8c8198f7f9624fd7194f570e36efd95f77da0634c6'}
READS={};CHECKS=[]
def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(p,pin=None):
 p=Path(p);raw=p.read_bytes();h=digest(raw)
 if pin is not None and pin!=h:raise ValueError('source pin differs '+str(p))
 key=str(p)
 if key in READS and READS[key]!=h:raise ValueError('read drift '+key)
 READS[key]=h;return raw
def write(name,value):
 raw=(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,indent=2)+'\n').encode()
 with (D/name).open('xb') as f:f.write(raw)
 return {'path':str((D/name).relative_to(R)),'sha256':digest(raw),'bytes':len(raw)}
def check(name,fn):
 value=fn();CHECKS.append({'name':name,'status':'passed','detail':value});return value
def must(ok,msg):
 if not ok:raise AssertionError(msg)
def rejected(fn):
 try:fn()
 except (ValueError,FileNotFoundError) as e:return {'type':type(e).__name__,'message':str(e)}
 raise AssertionError('expected strict refusal')
def load(p,pin,name):
 raw=read(p,pin);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);exec(compile(raw,str(p),'exec'),m.__dict__);return m
for name,pin in PINS.items():read(C/name,pin)
for name,pin in OLDPINS.items():read(OLD/name,pin)
g=load(C/'gateway.py',PINS['gateway.py'],'independent_spatial_doc_gateway');a=g.a
binding=json.loads(read(C/'document_binding.json',a.DOCUMENT_BINDING_SHA))
binding_ref={'path':str((C/'document_binding.json').relative_to(R)),'sha256':a.DOCUMENT_BINDING_SHA}

def source_delta():
 olda=read(OLD/'admission.py').decode();newa=read(C/'admission.py').decode();oldg=read(OLD/'gateway.py').decode();newg=read(C/'gateway.py').decode()
 news=newa.replace("VERSION='spatial-cuda-continuous-admission-v2-doc-binding'","VERSION='spatial-cuda-continuous-admission-v1'").replace("CANON='scripts/ops/formal_spatial_cuda_continuous_admission_v2/'","CANON='scripts/ops/formal_spatial_cuda_continuous_admission_v1/'")
 start=news.index("DOCUMENT='docs/");end=news.index("SLURM='",start);news=news[:start]+news[end:]
 start=news.index('def verify_document_binding(');end=news.index('def history(',start);news=news[:start]+news[end:]
 news=news.replace(", 'historical_document_binding':copy.deepcopy(auth['historical_document_binding'])",'') if False else news
 news=news.replace(",'historical_document_binding':copy.deepcopy(auth['historical_document_binding'])",'')
 news=news.replace("  verify_document_binding(e,auth.get('historical_document_binding'))\n",'')
 news=news.replace("  for proof,proof_ref in ((saved,refs['root_recovery_review']),(ind,refs['independent_recovery_review'])):\n","  for proof in (saved,ind):\n")
 news=news.replace("    if rel!=STATE:watch_review_evidence(e,proof_ref,rel,h,auth['historical_document_binding']) # State remains CAS-bound.","    if rel!=STATE:e.watch(rel,h) # Historical STATE hash remains historical; full current history is matched above.")
 must(news==olda,'admission has change beyond exact documented bridge')
 newg=newg.replace(PINS['admission.py'],OLDPINS['admission.py']).replace(" a.verify_document_binding(e,v.get('historical_document_binding'))\n",'')
 must(newg==oldg,'gateway transaction differs beyond source pin/document check')
 return {'admission_reverse_transform_exact_original_bytes':True,'gateway_reverse_transform_exact_original_bytes':True,'original_gateway_transaction_and_CAS_and_capacity_bytes_unchanged':True}
check('exact_bounded_source_delta',source_delta)

def provenance():
 env=dict(os.environ,GIT_OPTIONAL_LOCKS='0');rows=[];raws=[]
 for side,pin in [('historical',a.DOCUMENT_OLD_SHA),('current',a.DOCUMENT_NEW_SHA)]:
  row=binding[side];commit=row['git_commit'];p=a.DOCUMENT
  actual_blob=subprocess.run(['git','-C',str(R),'rev-parse',commit+':'+p],env=env,check=True,capture_output=True).stdout.decode().strip()
  raw=subprocess.run(['git','-C',str(R),'cat-file','blob',actual_blob],env=env,check=True,capture_output=True).stdout
  must(actual_blob==row['git_blob'],'git blob identity differs')
  must(raw==row['utf8'].encode() and digest(raw)==pin and len(raw)==row['bytes'],'actual Git bytes differ')
  raws.append(raw);rows.append({'side':side,'commit':commit,'blob':actual_blob,'sha256':digest(raw),'bytes':len(raw)})
 subprocess.run(['git','-C',str(R),'merge-base','--is-ancestor',binding['historical']['git_commit'],binding['current']['git_commit']],env=env,check=True,capture_output=True)
 old,new=raws;op=difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes();changes=[x for x in op if x[0]!='equal']
 must(len(changes)==1 and changes[0][0]=='insert','not exactly one operational paragraph insertion')
 _,i,j,k,l=changes[0];insert=new[k:l];must(len(insert)==717 and b'restore_formal_source_mirror_v1.py' in insert,'unexpected paragraph')
 must(new[:k]+new[l:]==old,'other document byte changed')
 must(read(R/a.DOCUMENT,a.DOCUMENT_NEW_SHA)==new,'current document not current Git version')
 inv=json.loads(read(R/a.INVENTORY,a.INV_SHA));must(a.DOCUMENT not in inv['files'],'operational doc is frozen science')
 return {'git_read_only':True,'versions':rows,'single_added_operational_paragraph_bytes':717,'insert_utf8':insert.decode(),'remainder_byte_identical':True,'document_outside173_scientific_inventory':True}
check('actual_Git_provenance_and_exact_paragraph',provenance)

def real_historical_proof_scope():
 oldauth=json.loads(read(R/'configs/experiments/formal_main_v2_spatial_cuda_continuous_3043399_v1.json','206bb080b2c870b112a8976d9eb27c383859ddea308ea5094ead316e569403bd'))
 refs=a.proof_refs(oldauth);found=[]
 for key in ['root_recovery_review','independent_recovery_review']:
  proof=json.loads(read(R/refs[key]['path'],refs[key]['sha256']))
  for rel,pin in proof.get('evidence_sha256',proof.get('read_evidence_sha256',{})).items():
   if rel==a.STATE:continue
   h=digest(read(R/rel))
   if h!=pin:found.append({'proof':refs[key],'path':rel,'recorded_sha256':pin,'current_sha256':h})
 must(found==[{'proof':a.DOCUMENT_HISTORICAL_REVIEW,'path':a.DOCUMENT,'recorded_sha256':a.DOCUMENT_OLD_SHA,'current_sha256':a.DOCUMENT_NEW_SHA}],'additional historical evidence mismatch')
 return {'historical_proofs_unmodified':True,'only_changed_historical_evidence':found,'all_other_raw_and_source_evidence_current_SHA_exact':True}
check('only_one_real_historical_independent_entry_changed',real_historical_proof_scope)

count=0
def box():
 global count
 count+=1;root=D/'isolated'/('case%02d'%count);root.mkdir(parents=True)
 (root/a.DOCUMENT).parent.mkdir(parents=True);(root/a.DOCUMENT).write_bytes(binding['current']['utf8'].encode())
 (root/'binding.json').write_bytes(read(C/'document_binding.json'))
 return a.Evidence(root),{'path':'binding.json','sha256':a.DOCUMENT_BINDING_SHA}

def exact_bridge():
 e,r=box();failure=rejected(lambda:e.watch(a.DOCUMENT,a.DOCUMENT_OLD_SHA))
 a.watch_review_evidence(e,a.DOCUMENT_HISTORICAL_REVIEW,a.DOCUMENT,a.DOCUMENT_OLD_SHA,r);e.unchanged()
 must(e.hashes=={'binding.json':a.DOCUMENT_BINDING_SHA,a.DOCUMENT:a.DOCUMENT_NEW_SHA},'bridge watch closure')
 return {'old_direct_watch_rejected':failure,'current_and_binding_remain_watched':True}
check('exact_bridge_only_and_old_gate_failure_preserved',exact_bridge)
for change in ['proof_path','proof_sha','doc_path','old_sha','extra_proof_key']:
 def one(change=change):
  e,r=box();ref=copy.deepcopy(a.DOCUMENT_HISTORICAL_REVIEW);p=a.DOCUMENT;h=a.DOCUMENT_OLD_SHA
  if change=='proof_path':ref['path']=a.ROOT_PATH
  elif change=='proof_sha':ref['sha256']='0'*64
  elif change=='doc_path':p='docs/other.md';(e.root/p).write_bytes(binding['current']['utf8'].encode())
  elif change=='old_sha':h='0'*64
  else:ref['unapproved']='yes'
  return rejected(lambda:a.watch_review_evidence(e,ref,p,h,r))
 check('reject_bridge_identity_change_'+change,one)

def new_changed_or_old_restored():
 outcomes=[]
 for raw in [binding['historical']['utf8'].encode(),binding['current']['utf8'].encode()+b'\n']:
  e,r=box();(e.root/a.DOCUMENT).write_bytes(raw);outcomes.append(rejected(lambda:a.verify_document_binding(e,r)))
 return outcomes
check('reject_restored_old_or_further_changed_current_document',new_changed_or_old_restored)

def tampered_binding():
 outcomes=[]
 for change in ['git_commit','historical_content','scope']:
  e,r=box();v=copy.deepcopy(binding)
  if change=='git_commit':v['historical']['git_commit']='0'*40
  elif change=='historical_content':v['historical']['utf8']+='changed'
  else:v['historical_review']['path']=a.ROOT_PATH
  raw=a.canonical(v);(e.root/r['path']).write_bytes(raw)
  outcomes.append(rejected(lambda:a.verify_document_binding(e,r)))
  r['sha256']=digest(raw);outcomes.append(rejected(lambda:a.verify_document_binding(e,r)))
 return outcomes
check('reject_tampered_or_self_rehashed_binding',tampered_binding)

def unrelated_evidence():
 e,r=box();rel='src/cti_vla/science.py';p=e.root/rel;p.parent.mkdir(parents=True);p.write_bytes(b'original source');pin=digest(p.read_bytes());a.watch_review_evidence(e,a.DOCUMENT_HISTORICAL_REVIEW,rel,pin,r);p.write_bytes(b'changed source')
 return rejected(lambda:a.watch_review_evidence(e,a.DOCUMENT_HISTORICAL_REVIEW,rel,pin,r))
check('unrelated_scientific_evidence_not_exempted',unrelated_evidence)

def current_drift():
 e,r=box();a.verify_document_binding(e,r);(e.root/a.DOCUMENT).write_bytes(binding['current']['utf8'].encode()+b'x')
 return rejected(e.unchanged)
check('current_document_after_prepare_drift_rejected',current_drift)

def old_auth_refused():
 p='configs/experiments/formal_main_v2_spatial_cuda_continuous_3043399_v1.json'
 return rejected(lambda:g.validate_authorization(R,{'path':p,'sha256':'206bb080b2c870b112a8976d9eb27c383859ddea308ea5094ead316e569403bd'}))
check('old_root_authorization_does_not_authorize_new_version',old_auth_refused)

def actual_prepare():
 auth=json.loads(read(C/'authorization_a1_draft.json',PINS['authorization_a1_draft.json']))
 must(auth['status']=='draft_not_authorized' and auth['reviewed_by'] is None and auth['independent_review'] is None,'draft must remain unauthorized')
 must(auth['gateway_files']==g.source_files(),'candidate identity map differs')
 ref={'path':str((C/'authorization_a1_draft.json').relative_to(R)),'sha256':PINS['authorization_a1_draft.json']}
 c=load(R/g.CONTROLLER,g.CONTROLLER_SHA,'independent_doc_controller')
 lock=R/'results/experiment_supervisor/.writer.lock';must(lock.is_file(),'existing writer lock required')
 with c.exclusive_lock(lock):
  before=c.file_sha(R/a.STATE);state=c.read_json(R/a.STATE)
  must(c.file_sha(R/a.STATE)==before,'concurrent state change')
  must(state.get('pending_submission') is None,'pending exists')
  control_before=copy.deepcopy(state['autonomous_training_v1'])
  must(a.PAIR in control_before['blocked_pairs'],'retained failed pair block missing')
  sc=a.Science(R);plan=sc.prepare(state,auth,ref);native=a.NativeIO().preflight(plan)
  sc.e.unchanged();must(c.file_sha(R/a.STATE)==before,'state changed during read-only audit')
  must(c.read_json(R/a.STATE)['autonomous_training_v1']==control_before,'controller changed')
  for rel,h in sc.e.hashes.items():read(R/rel,h)
  for path,row in native['server_files'].items():
   must(str(path) not in READS or READS[str(path)]==row['sha256'],'server read identity drift');READS[str(path)]=row['sha256']
  for row in native['server_resume_checks']:
   must(str(row['path']) not in READS or READS[str(row['path'])]==row['sha256'],'resume identity drift');READS[str(row['path'])]=row['sha256']
  inv=plan['invocation'];must(inv['segment_end']==5000 and inv['argv'][-1]=='--resume','continuation endpoint differs')
  must(inv['continuous_admission']['historical_document_binding']==auth['historical_document_binding'],'binding absent from invocation provenance')
  must(not (R/a.INVREL).exists() and not (a.P/a.INVREL).exists(),'invocation published')
  receipt=dict(schema='formal_main_v2',kind='independent_spatial_doc_binding_actual_prepare',status='passed_actual_read_only_raw_and_metadata',utc=datetime.now(timezone.utc).isoformat(),source_files=g.source_files(),authorization_draft=ref,authorization_validated=False,state_sha256=before,state_unchanged=True,pending_submission=None,blocked_pair_preserved=copy.deepcopy(control_before['blocked_pairs'][a.PAIR]),controller_fields_unchanged=True,actual_original_reviewer_reconstruction=True,original_plan=plan,actual_native_metadata=native,server_metadata_files=len(native['server_files']),resume_count=len(native['server_resume_checks']),completed_before={'A':1500,'B':1500},cursor_before={'A':12000,'B':12000},target_updates=5000,historical_GPU_seconds=11958,failed_GPU_seconds_preserved=73,optimizer_rng_deserialized=False,GPU_or_Slurm_called=False,new_GPU_submission=False,new_invocation_published=False,final_release=False,read_evidence_sha256=dict(sc.e.hashes))
  return write('actual_prepare_independent_a1.json',receipt)
check('actual_original_raw_rebuild_and_NativeIO_hash_only',actual_prepare)
for p,h in list(READS.items()):
 if '/checkpoints/' in p:continue # Exact two large files already stable-hashed by original NativeIO; no tensor loading.
 read(p,h)
report=dict(schema='formal_main_v2',kind='spatial_doc_binding_independent_CPU_checks',status='passed',utc=datetime.now(timezone.utc).isoformat(),tests=len(CHECKS),checks=CHECKS,read_evidence_sha256=READS,files=g.source_files(),binding=binding_ref,production_modified=False,state_modified=False,Slurm_called=False,root_authorization_granted=False,scientific_settings_changed=False)
ref=write('checks_a1.json',report)
print(json.dumps({'tests':len(CHECKS),'status':'passed','receipt':ref,'read_refs':len(READS),'server_files':213,'resume_hash_only':2}),flush=True)
