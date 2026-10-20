from pathlib import Path
import datetime,hashlib,io,json,tarfile
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/delivery_independent_20261020T2054'
B='results/formal_main_v2/preflight/heartbeat_20261021T0454';E='results/formal_main_v2/engineering/supervision_delivery_20261020T2054'
NAMES=['Spatial588_author','Spatial588_independent','Goal_CPU_author','Goal_CPU_independent','Object_raw_root','Object_raw_independent']
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_bytes())
def ck(ok,msg):
 if not ok:raise ValueError(msg)
def ref(p):return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':h(p)}
rows=[];member_count=0
for name in NAMES:
 rp=R/B/(name+'_archive.json');r=rd(rp)
 ck(r['status']=='immutable_nonweight_package_archived' and r['state_unchanged'] and r['not_runtime_admission'] and r['GPU_jobs_added']==0,'archive status '+name)
 mp=R/r['manifest']['path'];dst=R/r['destination'];ck(h(mp)==h(dst)==r['manifest']['sha256'] and mp.read_bytes()==dst.read_bytes(),'manifest identical '+name)
 m=rd(dst);base=R/m['root'];files=m['files'];ck(len(files)==r['file_count'],'file count')
 saved=[];size=0
 for f in files:
  p=R/f['path'];rel=p.relative_to(base);q=dst.parent/rel
  ck(p.is_file() and q.is_file() and not p.is_symlink() and not q.is_symlink(),'file type')
  ck(p.stat().st_size==q.stat().st_size==f['bytes'] and h(p)==h(q)==f['sha256'],'file bytes/hash '+str(q))
  saved.append({'source':f,'archive':ref(q)});size+=f['bytes']
 ck(size==r['bytes'],'receipt bytes')
 package=None
 ip=dst.parent/'CPU_evidence_archive_index.json'
 if ip.exists():
  ix=rd(ip)
  if name=='Goal_CPU_author':ck(ix['kind']=='lossless_synthetic_CPU_evidence_archive' and ix['real_GPU_or_final_values'] is False,'synthetic author CPU only')
  else:ck(name=='Goal_CPU_independent' and ix['kind']=='independent_synthetic_CPU_evidence_archive' and ix['GPU_runs']==0 and ix['scientific_trials_added']==0,'synthetic independent CPU only')
  ar=ix['archive'];ap=dst.parent/ar['path'];ck(ap.stat().st_size==ar['bytes'] and h(ap)==ar['sha256'],'tar archive SHA')
  expected={x['path']:x for x in ix['members']};ck(len(expected)==len(ix['members']),'duplicate index')
  checks=[]
  with tarfile.open(fileobj=io.BytesIO(ap.read_bytes()),mode='r:gz') as tar:
   members=tar.getmembers();ck(len(members)==len(expected),'tar member count')
   ck({x.name for x in members}==set(expected),'tar exact names')
   for entry in members:
    ck(entry.isfile() and not Path(entry.name).is_absolute() and '..' not in Path(entry.name).parts,'tar member scope')
    raw=tar.extractfile(entry).read();x=expected[entry.name]
    ck(len(raw)==entry.size==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256'],'tar content')
    checks.append({'path':entry.name,'bytes':len(raw),'sha256':x['sha256']})
  total_raw_bytes=sum(x['bytes'] for x in checks)
  if name=='Goal_CPU_author':ck(total_raw_bytes==ix['raw_bytes'],'tar total')
  member_count+=len(checks);package={'index':ref(ip),'archive':ref(ap),'member_count':len(checks),'raw_bytes':total_raw_bytes,'members':checks,'unpacked_to_filesystem':False}
 rows.append({'name':name,'receipt':ref(rp),'manifest':ref(dst),'file_count':len(files),'files':saved,'synthetic_package':package})
author=rd(R/E/'Spatial588_author/delivery_manifest.json');ind=rd(R/E/'Spatial588_independent/delivery_manifest_original.json')
ck(author['control']['sha256']==ind['final_candidate_sha256']=='e3994a213c54b8824febe95bed2e0ca8f76b2782ddd21b5f7c5a1496f4ac3df8','spatial independently reviewed control')
ck(not author['full_production_chain_complete'] and not author['actual_P_new_invocation_verify'] and not ind['production_authorized'] and not ind['legacy12_current_action_compatibility_proven'],'Spatial gate remains closed')
goal=rd(R/E/'Goal_CPU_independent/delivery_manifest_original.json')
ck(goal['author_assertions_independently_reexecuted']==66 and goal['new_Goal_science_HOLD'] and goal['old200_HOLD'] and not goal['P_runtime_source_closure_verified'] and not goal['single_attempt_GPU_authorization_granted'],'Goal remains CPU only')
obj=rd(R/E/'Object_raw_independent/delivery_manifest_original.json')
ck(not obj['compatibility_admission'] and obj['accepted_trials']==0 and obj['original_attempts_and_costs_preserved'],'Object diagnostic not acceptance')
out={'schema':'formal_main_v2','kind':'independent_CPU_archive_delivery_review','status':'passed_exact_six_CPU_archives_no_scientific_admission','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'packages':rows,'package_count':6,'source_and_archived_file_count':sum(x['file_count'] for x in rows),'tar_members_verified':member_count,'all_private_reports_exactly_archived':True,'CPU_is_not_GPU_admission':True,'production_state_Git_or_Slurm_mutations':False,'sealed_final_values_read':False,'auditor_conflict_disclosure':'Spatial588 author also verified byte copies here; algorithm and scientific limitations are independently covered by the separate Spatial588 independent reviewer.'}
p=D/'CPU_archives_review.json'
with p.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'status':out['status'],'packages':6,'files':out['source_and_archived_file_count'],'tar_members':member_count,'report':ref(p)}))
