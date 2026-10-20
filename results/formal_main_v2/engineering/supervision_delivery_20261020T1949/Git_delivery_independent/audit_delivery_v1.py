import sys,os,json,hashlib,subprocess,importlib.util,zipfile,io,datetime,collections
from pathlib import Path,PurePosixPath
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent;B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0349';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1949'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def h(p):return sha(Path(p).read_bytes())
def ref(p):p=Path(p);return {'path':p.relative_to(R).as_posix(),'sha256':h(p),'bytes':p.stat().st_size}
def put(n,x):p=D/n;p.write_text(json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False)+'\n');return ref(p)
def read_pin(p,pin):p=Path(p);assert h(p)==pin;return json.loads(p.read_text())
env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')};env['GIT_OPTIONAL_LOCKS']='0'
def git(*a):return subprocess.check_output(['git','-c','core.quotepath=false','-C',str(R),*a],env=env)
head=git('rev-parse','HEAD').decode().strip();index_before=git('ls-files','--stage','-z');status=git('status','--porcelain=v1','-z','--untracked-files=all');assert not any(x[:1] in (b'R',b'C') for x in status.split(b'\0') if x)
status_rows=[{'status':x[:2].decode(),'path':x[3:].decode()} for x in status.split(b'\0') if x];put('git_status_snapshot.json',{'head':head,'raw_sha256':sha(status),'index_sha256':sha(index_before),'GIT_OPTIONAL_LOCKS':'0','rows':status_rows})
sg=R/'scripts/ops/check_nonweight_archive_stage.py';assert h(sg)=='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6';spec=importlib.util.spec_from_file_location('_stageguard_lexical_only',sg);guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
def lexical_error(name):
 try:guard.lexical(name);return None
 except Exception as e:return str(e)
previous=R/'results/formal_main_v2/preflight/heartbeat_20261021T0225';oldguard=read_pin(previous/'git_index_guard.json','42491f666a4d5029849acd8f17f28179b33dcf31209248d9756123b775455b5e');oldCPU=read_pin(previous/'git_CPU_fixture_archive.json','e7f874aea26990d365a1a4a841c1062498d82fd6c718a9e05a6f939c385836af');oldmeta=read_pin(previous/'git_operational_metadata_archive.json','b181c31ecc68be01e88e5cf739f15f5372975b1a10fd9d5358d8a90c52de849c')
assert len(oldguard['raw_paths_restored_exactly'])==9 and len(oldCPU['files'])==48 and len(oldmeta['files'])==13
oldrefs=[ref(previous/'git_index_guard.json'),ref(previous/'git_CPU_fixture_archive.json'),ref(previous/'git_operational_metadata_archive.json')]
for x in oldrefs+[oldCPU['archive'],oldmeta['archive'],{'path':oldguard['snapshot'],'sha256':oldguard['snapshot_sha256']}]:assert sha(git('show','HEAD:'+x['path']))==x['sha256']
old_exclusions={x['path'] for x in oldguard['raw_paths_restored_exactly']+oldCPU['files']+oldmeta['files']}
put('previous_archives_exact_exclusions.json',{'prior_proofs_in_current_HEAD':True,'proofs':oldrefs,'raw_files_9':oldguard['raw_paths_restored_exactly'],'synthetic_CPU_bin_48':oldCPU['files'],'operational_metadata_13':oldmeta['files'],'recommendation':'Retain server originals and reuse existing archives/HEAD evidence. Do not re-add or rearchive these exact paths. No contents re-expanded here.'})
packages=[]
for rel,pin,target in [('.local/k64_seed23_bridges_20261020T1949/delivery_manifest.json','b7aac670e3a78a2f41179ce0b8fc1b374ff2d41a7085ea03f889e8178646bc9c','k64_source_author'),('.local/collect_terminal_independent_20261020T1949/delivery_manifest.json','806c3f40b5c34f9c37f25b4f96adec1b0504ac6ca38fd63ae5508f5a67164a5e','collect_independent')]:
 m=R/rel;v=read_pin(m,pin);base=m.parent;rows=[]
 for item in v['files']:
  src=R/item.get('source',item['path']);assert src.is_file() and not src.is_symlink();raw=src.read_bytes();assert sha(raw)==item['sha256'] and len(raw)==item['bytes'];sub=src.relative_to(base).as_posix();dst=E+'/'+target+'/'+sub;rows.append({'source':src.relative_to(R).as_posix(),'path':dst,'sha256':sha(raw),'bytes':len(raw),'stageguard_lexical_error':lexical_error(dst)})
 rows.append({'source':rel,'path':E+'/'+target+'/delivery_manifest.json','sha256':pin,'bytes':m.stat().st_size,'stageguard_lexical_error':None})
 assert not any(x['stageguard_lexical_error'] for x in rows);assert all(x['bytes']<=guard.LIMIT for x in rows)
 packages.append({'source_manifest':ref(m),'suggested_destination':E+'/'+target,'files':rows,'file_count_including_manifest':len(rows),'bytes':sum(x['bytes'] for x in rows),'needs_additional_lossless_archive':False})
put('candidate_package_copy_map.json',{'status':'exact_byte_copy_recommendation_only','packages':packages,'not_copied_here':True,'independent_bridge_package_pending':'.local/k64_seed23_bridges_independent_20261020T1949/delivery_manifest.json'})
allowpath=B/'collect_terminal/observation_npz_delivery_allowlist.json';allow=read_pin(allowpath,'9de3a6b37fbdf6c25ee3cd782426107d732c3c6626571125445b5d954181681a');assert len(allow['files'])==60 and allow['sealed_values'] is False and allow['weights'] is False;assert allow['new_scientific_trials']==0
import numpy as np
headers=[];provenance={};npzrows=[]
for suite,jid in [('libero_spatial','3053503'),('libero_object','3053518')]:
 base=R/f'results/formal_main_v2/{suite}/downstream/collect/648ce4233e78353e/attempt01';panel=json.loads((base/'panel.json').read_text());cfg=json.loads((base/'config.json').read_text());assert panel['split']=='development' and panel['test_opened'] is False and cfg['test_opened'] is False;assert cfg['slurm_job_id']==jid and cfg['manifest']['split']=='development'
 dev=R/cfg['manifest']['development_panel'];assert dev.name=='development.json' and h(dev)==cfg['manifest']['development_panel_sha256'];dv=json.loads(dev.read_text());assert dv['split']=='development';minimum={i:min(s['source_state_index'] for s in dv['states'] if s['task_id']==i) for i in range(10)}
 task_refs={}
 for item in panel['episodes']:
  q=base/item['receipt']['path'];assert h(q)==item['receipt']['sha256'];v=json.loads(q.read_text());assert v['split']=='development' and v['test_opened'] is False;assert v['state']['source_state_index']==minimum[item['task_id']];task_refs[item['task_id']]=(q,v)
 provenance[suite]={'job_id':jid,'panel':ref(base/'panel.json'),'config':ref(base/'config.json'),'development_panel_ref_only':ref(dev),'task_receipts':[ref(q) for q,v in task_refs.values()],'final_state_files_opened':False}
 for row in [x for x in allow['files'] if x['suite']==suite]:
  q=R/row['path'];assert q.parent.parent==base and q.suffix=='.npz' and lexical_error(row['path']) is None;raw=q.read_bytes();assert sha(raw)==row['sha256'] and len(raw)==row['bytes'];receipt,v=task_refs[row['task_id']];o=next(x for x in v['observations'] if x['phase']==row['phase']);assert q==receipt.parent/o['arrays']['path'];assert o['arrays']['sha256']==row['sha256'];assert o['control_step']==row['control_step'];assert v['state']['source_state_index']==row['source_state_index'];assert row['job_id']==jid
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   assert len(z.infolist())==5 and not z.comment;assert set(z.namelist())=={k+'.npy' for k in row['arrays']}
   info={}
   for zi in z.infolist():
    assert not zi.is_dir() and '/' not in zi.filename and not zi.flag_bits&1
    with z.open(zi) as f:
     version=np.lib.format.read_magic(f);shape,fortran,dtype=np.lib.format._read_array_header(f,version);offset=f.tell()
    name=zi.filename[:-4];expected=row['arrays'][name];assert not dtype.hasobject and str(dtype)==expected['dtype'] and list(shape)==expected['shape'];assert zi.file_size-offset==int(np.prod(shape))*dtype.itemsize
    info[name]={'shape':list(shape),'dtype':str(dtype),'fortran_order':fortran,'npy_bytes':zi.file_size,'header_bytes':offset}
  assert set(info)=={'agentview_image','robot0_eye_in_hand_image','robot0_eef_pos','robot0_eef_quat','robot0_gripper_qpos'};headers.append({'path':row['path'],'arrays':info});npzrows.append({**row,'classification':'current_development_dense_collection_observation_only','array_payload_loaded':False,'final_state_values':False,'weights':False})
assert len(npzrows)==60 and len({x['path'] for x in npzrows})==60 and sum(x['bytes'] for x in npzrows)==23678640
npzref=put('observation_delivery_audit.json',{'status':'approved_exact60_current_development_observation_NPZ','allowlist':ref(allowpath),'files':npzrows,'array_headers':headers,'provenance':provenance,'file_count':60,'bytes':23678640,'numeric_array_values_materialized':False,'sealed_final_files_opened':False,'weights_read':False,'scientific_trial_count_change':0,'latency_measurement_claimed':False,'recommendation':'If ignored by Git, force-add only these 60 exact allowlisted path/SHA/bytes after final staging review; never wildcard *.npz or initial_states. Original stageguard remains unchanged.'})
new=[];known=[];problems=[]
for row in status_rows:
 name=row['path'];q=R/name
 if name in old_exclusions:known.append(row);continue
 e=lexical_error(name);r={**row,'stageguard_lexical_error':e}
 if q.is_file():r.update(sha256=h(q),bytes=q.stat().st_size)
 if e or r.get('bytes',0)>guard.LIMIT:problems.append(r)
 new.append(r)
put('new_status_candidates.json',{'head':head,'status_sha256':sha(status),'candidates':new,'old_originals_excluded':known,'lexical_or_size_problems':problems,'advisory_snapshot_not_final_staging_authorization':True})
assert git('ls-files','--stage','-z')==index_before and git('rev-parse','HEAD').decode().strip()==head
report={'kind':'read_only_Git_delivery_audit','status':'passed_current_packages_and_observation_allowlist_pending_later_packages','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':head,'stageguard':ref(sg),'Git_commands_read_only':True,'Git_index_and_HEAD_unchanged':True,'project_files_or_state_modified':False,'current_status_count':len(status_rows),'existing_archived_originals_in_status':len(known),'previous_raw_archive_count':9,'previous_synthetic_bin_archive_count':48,'previous_operational_metadata_archive_count':13,'new_current_status_candidates':len(new),'new_lexical_or_size_problem_count':len(problems),'packages':[{'source_manifest':x['source_manifest'],'file_count_including_manifest':x['file_count_including_manifest'],'bytes':x['bytes'],'needs_additional_lossless_archive':x['needs_additional_lossless_archive']} for x in packages],'observation_audit':npzref,'new_NPZ_files_approved':60,'new_NPZ_bytes':23678640,'independent_bridge_package_final_manifest':'pending; later addendum required','runtime_or_final_science_validation_executed':False,'private_audit_output_only':True}
rr=put('audit.json',report);files=[ref(p) for p in sorted(D.iterdir()) if p.is_file() and p.name!='delivery_manifest.json'];mr=put('delivery_manifest.json',{'kind':'Git_delivery_file_audit_package','status':'current_scope_complete_later_packages_pending','files':files,'file_count':len(files),'bytes':sum(x['bytes'] for x in files),'audit':rr});print(json.dumps({'audit':rr,'delivery_manifest':mr,'status_count':len(status_rows),'new_problem_count':len(problems),'new_observations':60}))
