import sys,os,json,hashlib,subprocess,importlib.util,datetime,fcntl,re
from pathlib import Path
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent;E='results/formal_main_v2/engineering/supervision_delivery_20261020T1949';sys.dont_write_bytecode=True
PIN=sys.argv[1];assert re.fullmatch('[0-9a-f]{64}',PIN)
h=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):p=Path(p);return {'path':p.relative_to(R).as_posix(),'sha256':h(p),'bytes':p.stat().st_size}
def put(n,x):
 p=D/n;raw=(json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
 with p.open('xb') as f:f.write(raw)
 return ref(p)
env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env['GIT_OPTIONAL_LOCKS']='0'
def git(*a):return subprocess.check_output(['git','-c','core.quotepath=false','-C',str(R),*a],env=env)
sg=R/'scripts/ops/check_nonweight_archive_stage.py';assert h(sg)=='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6';spec=importlib.util.spec_from_file_location('_final_file_audit_lexical',sg);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
manifest=R/'.local/k64_seed23_bridges_independent_20261020T1949/delivery_manifest.json';assert h(manifest)==PIN;v=json.loads(manifest.read_text());base=manifest.parent;rows=[]
for row in v['files']:
 p=R/row.get('source',row['path']);assert p.is_file() and not p.is_symlink() and h(p)==row['sha256'] and p.stat().st_size==row['bytes'];sub=p.relative_to(base).as_posix();dest=E+'/k64_source_independent/'+sub;g.lexical(dest);assert row['bytes']<=g.LIMIT;rows.append({'source':p.relative_to(R).as_posix(),'path':dest,'sha256':row['sha256'],'bytes':row['bytes']})
rows.append({'source':manifest.relative_to(R).as_posix(),'path':E+'/k64_source_independent/delivery_manifest.json','sha256':PIN,'bytes':manifest.stat().st_size});g.lexical(rows[-1]['path'])
package={'source_manifest':ref(manifest),'file_count_including_manifest':len(rows),'bytes':sum(x['bytes'] for x in rows),'files':rows,'needs_additional_lossless_archive':False};put('independent_package_copy_map.json',package)
old=json.loads((D/'previous_archives_exact_exclusions.json').read_text());exclusions={x['path'] for key in ['raw_files_9','synthetic_CPU_bin_48','operational_metadata_13'] for x in old[key]}
# No payloads outside the already reviewed nonweight project status list are opened.
with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
 fcntl.flock(lock,fcntl.LOCK_SH)
 head=git('rev-parse','HEAD').decode().strip();index_before=git('ls-files','--stage','-z');status=git('status','--porcelain=v1','-z','--untracked-files=all');current=[];oldrows=[];blockers=[];open_transports=[]
 for raw in status.split(b'\0'):
  if not raw:continue
  row={'status':raw[:2].decode(),'path':raw[3:].decode()};name=row['path'];p=R/name
  if name in exclusions:oldrows.append(row);continue
  try:g.lexical(name)
  except Exception as e:blockers.append({**row,'reason':str(e)});continue
  if p.is_file():
   row['bytes']=p.stat().st_size
   if row['bytes']>g.LIMIT:blockers.append({**row,'reason':'over100MiB'});continue
   if name.startswith('results/formal_main_v2/control_transport/') and name.endswith('.jsonl'):
    lines=p.read_text().splitlines();last=json.loads(lines[-1]) if lines else {}
    if last.get('event')!='control_end':open_transports.append(row);continue
   row['sha256']=h(p)
  current.append(row)
 assert git('ls-files','--stage','-z')==index_before and git('rev-parse','HEAD').decode().strip()==head
 fcntl.flock(lock,fcntl.LOCK_UN)
assert not blockers,blockers
put('final_status_candidates.json',{'head':head,'status_sha256':hashlib.sha256(status).hexdigest(),'index_sha256':hashlib.sha256(index_before).hexdigest(),'current_files':current,'previously_archived_originals_excluded':oldrows,'open_transports_excluded_until_closed':open_transports,'blockers':blockers,'read_only_snapshot_not_final_index_review':True})
npz=json.loads((D/'observation_delivery_audit.json').read_text());assert npz['status']=='approved_exact60_current_development_observation_NPZ' and npz['file_count']==60
for row in npz['files']:
 p=R/row['path'];assert h(p)==row['sha256'] and p.stat().st_size==row['bytes'];g.lexical(row['path'])
for mapname in ['candidate_package_copy_map.json','author_package_addendum.json']:
 for pack in json.loads((D/mapname).read_text())['packages']:
  for row in pack['files']:
   p=R/row['source'];assert h(p)==row['sha256'] and p.stat().st_size==row['bytes'];g.lexical(row['path'])
report={'kind':'final_Git_nonweight_file_delivery_addendum','status':'passed_final_delivery_addendum','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'new_NPZ_files_approved':60,'new_NPZ_bytes':23678640,'NPZ_scope':'Exact original development collect five-array observations only; no model or final initial-state values','blockers':[],'independent_package':{k:package[k] for k in ['source_manifest','file_count_including_manifest','bytes','needs_additional_lossless_archive']},'package_copy_maps':[ref(D/n) for n in ['candidate_package_copy_map.json','author_package_addendum.json','independent_package_copy_map.json']],'exact_NPZ_audit':ref(D/'observation_delivery_audit.json'),'existing_archived_files_do_not_restage':{'raw':9,'CPU_bin':48,'operational_metadata':13,'proof':ref(D/'previous_archives_exact_exclusions.json')},'current_status':ref(D/'final_status_candidates.json'),'open_transports_excluded_until_closed':open_transports,'stageguard':ref(sg),'new_prohibited_suffix_or_name_files':[],'new_lossless_archive_required':False,'Git_index_and_HEAD_unchanged':True,'author137_package_unchanged':True,'production_or_state_or_Git_writes':False,'final_or_GPU_validation_executed':False,'conditions':['Use exact files and SHA/bytes from maps; copy source bytes unchanged.','Force-add only the 60 exact NPZ allowlist entries, never wildcard NPZ/state payloads.','Retain the 9+48+13 original files server-side and reuse previous immutable archives.','Do not stage still-open transports; rehash metadata added after this snapshot.','Original pinned stage guard must pass against root final exact index. This file audit does not replace it.']}
a=put('final_addendum.json',report);files=[ref(p) for p in sorted(D.iterdir()) if p.is_file() and p.name!='delivery_manifest_final.json'];m=put('delivery_manifest_final.json',{'kind':'final_Git_delivery_file_audit_manifest','status':'passed_final_delivery_addendum','files':files,'file_count':len(files),'bytes':sum(x['bytes'] for x in files),'final_addendum':a,'new_NPZ_files_approved':60,'blockers':[]});print(json.dumps({'final_addendum':a,'delivery_manifest_final':m,'independent_files':len(rows),'status_files':len(current),'open_transports':len(open_transports)}))
