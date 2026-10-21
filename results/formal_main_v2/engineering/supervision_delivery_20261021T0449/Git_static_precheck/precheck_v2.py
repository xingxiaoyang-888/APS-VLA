"""Read-only Git-delivery precheck of the already archived bounded-five packages.
Only this private directory receives outputs. No Git writes, Slurm, state writes,
canonical changes, tar extraction, weights, or sealed input reads are performed.
This is file/transport classification, NOT independent runtime science review.
"""
from pathlib import Path, PurePosixPath
from collections import Counter
import datetime, hashlib, importlib.util, json, os, stat, tarfile
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/git_stage_precheck_20261021T0449'
B=R/'results/formal_main_v2/preflight/heartbeat_20261021T1249'
E=R/'results/formal_main_v2/engineering/supervision_delivery_20261021T0449'
GUARD='scripts/ops/check_nonweight_archive_stage.py'
GUARD_SHA='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
INV_SHA='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
EXPECTED_MANIFESTS={
 'Goal_gateway_independent':'aca28a1d699cf1b7087bb997f9133177be55dc52b51465369a2c25f7fc8f127b',
 'Goal_gateway_root_author':'e079a02afa7b6595bd45ef2f5843897ba4b129091d3f090cdc9f5198c0c981bb',
 'Goal_metadata_independent':'ba372b5138815882f7e69098205843dc22ee8d9d109084e4d7c10c38b3ca562f',
 'Goal_plan_independent':'a78f9025ba6bf22f3485c23253efee2d3a67ee1a1248afd16920d17cd89b11c8',
 'Goal_plans_author':'321e64ca6aa130230c5949bab54b1bcd52f4ef0fec75ad70f2f4161ef1ea683e',
 'Goal_runtime_author':'1db27d51a060e87966e56fe132f9ca9cd323204bddbfb4fa4c8a0791dafbd19f',
 'Goal_runtime_independent':'928071e2b7c37369af9b4ef683b2029879b22660c448a475e82fe558be2946bf',
}
checks=[];problems=[]
def check(ok,label,detail=None):
 row={'check':label,'passed':bool(ok)}
 if detail is not None:row['detail']=detail
 checks.append(row)
 if not ok:problems.append(row)
 return bool(ok)
def sha(b):return hashlib.sha256(b).hexdigest()
def safe(p):
 assert p.is_absolute() and p.resolve()==p and all(not x.is_symlink() for x in [p,*p.parents]),str(p)
 assert p.is_file(),str(p)
 return p
def bytesof(p):
 p=safe(p);before=p.stat();raw=p.read_bytes();after=p.stat()
 assert (before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns)
 assert len(raw)==after.st_size
 return raw
def ref(p):
 data=bytesof(p)
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(data),'bytes':len(data)}
def jread(p):return json.loads(bytesof(p))
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def put(name,v):
 assert '/' not in name and name.endswith('.json')
 with (D/name).open('xb') as f:f.write(enc(v))
 return ref(D/name)
def direct_root(v):
 p=Path(v);p=p if p.is_absolute() else R/p
 assert p.resolve()==p and R/'.local' in p.parents,str(p)
 return p
assert sha(bytesof(R/GUARD))==GUARD_SHA
spec=importlib.util.spec_from_file_location('goal_r5_delivery_guard',R/GUARD);guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
assert sha(bytesof(R/INV))==INV_SHA
inv=jread(R/INV);assert len(inv['files'])==173
roots=[R,P/'snapshots/formal_main_v2_run_564be0995e',R/'snapshots/formal_main_v2_run_564be0995e']
frozen=[]
for name,expected in sorted(inv['files'].items()):
 row={'path':name,'sha256':expected,'roots':[]}
 for root in roots:
  actual=sha(bytesof(root/name));check(actual==expected,'frozen173_source_bytes',{'root':str(root),'path':name});row['roots'].append(str(root))
 frozen.append(row)
# Read only already visible B/E files. Additions after this captured list remain out of scope.
paths=sorted([p for top in (B,E) for p in top.rglob('*') if p.is_file()])
assert len(paths)==len({str(p).casefold() for p in paths})
inventory=[];lexical_rejections=[];markdown_whitespace=[]
for p in paths:
 name=p.relative_to(R).as_posix()
 try:guard.lexical(name)
 except Exception as error:
  lexical_rejections.append({'path':name,'reason':str(error)});check(False,'existing_lexical_guard',name);continue
 check(not any(part.lower() in ('raw_runtime','blobs','weights','checkpoints','checkpoint') for part in p.relative_to(R).parts),'no_loose_raw_directory',name)
 data=bytesof(p);check(len(data)<=guard.LIMIT,'single_file_100MiB_limit',name)
 inventory.append({'path':name,'sha256':sha(data),'bytes':len(data)})
 if p.suffix=='.md':
  lines=data.splitlines()
  bad=[i for i,line in enumerate(lines,1) if line.rstrip(b' \t')!=line]
  eof_blank=len(data)-len(data.rstrip(b'\n'))>1
  if bad or eof_blank:markdown_whitespace.append({'path':name,'trailing_whitespace_lines':bad,'extra_LF_at_EOF':eof_blank})
check(not lexical_rejections,'all_current_archived_path_names_lexically_allowed')
inventory_by={v['path']:v for v in inventory};covered=set();packages=[];tar_summaries=[]
for package,pin in EXPECTED_MANIFESTS.items():
 base=E/package;mf=base/'delivery_manifest_original.json'
 if not mf.exists():mf=base/'delivery_manifest.json'
 check(sha(bytesof(mf))==pin,'delivery_manifest_exact_pin',package)
 m=jread(mf);rows=m['files'];check(m.get('file_count',len(rows))==len(rows),'delivery_manifest_file_count',package)
 source=direct_root(m.get('source_root',m.get('root',m.get('private_source_root'))))
 names=[];destmap={};sourcemap={}
 for row in rows:
  given=Path(row['path'])
  if given.is_absolute():src=given
  elif given.parts[0]=='.local':src=R/given
  else:src=source/given
  assert source in src.parents and src.resolve()==src
  rel=src.relative_to(source);dst=base/rel
  assert base in dst.parents
  a=bytesof(src);b=bytesof(dst)
  check(a==b and sha(b)==row['sha256'] and len(b)==row['bytes'],'source_archive_bytes_equal',str(dst.relative_to(R)))
  names.append(rel.as_posix());destmap[str(dst.relative_to(R))]={'source':str(src.relative_to(R)),'destination':str(dst.relative_to(R)),'sha256':sha(b),'bytes':len(b)}
  sourcemap[str(src.relative_to(R))]=destmap[str(dst.relative_to(R))]
  covered.add(str(dst.relative_to(R)))
 check(len(names)==len(set(names))==len({n.casefold() for n in names}),'manifest_unique_no_alias',package)
 mp=base/'source_map.json'
 if mp.exists():
  sm=jread(mp);smrows=sm['files']
  check(len(smrows)==len(rows),'source_map_same_count',package)
  check({x['destination']:x for x in smrows}==destmap,'source_map_exact_all_rows',package)
  check(sm.get('original_manifest_sha256',sm.get('source_manifest',{}).get('sha256'))==pin,'source_map_manifest_pin',package)
 original=source/'delivery_manifest.json'
 if package=='Goal_gateway_root_author':
  check(m.get('kind')=='root_gateway_candidate_history' and not original.exists(),'root_generated_gateway_manifest_distinct_from_copied_manifests',package)
 else:
  check(bytesof(original)==bytesof(mf),'original_manifest_byte_identical',package)
 packages.append({'name':package,'manifest':ref(mf),'source_root':str(source),'member_count':len(rows),'mapped_files':list(destmap.values()),'source_map':ref(mp) if mp.exists() else None})
 for arc in m.get('CPU_archives',[]):
  ap=base/arc['archive_path'];ip=base/arc['members_path']
  check(sha(bytesof(ap))==arc['archive_sha256'] and ap.stat().st_size==arc['archive_bytes'],'CPU_tar_archive_ref',str(ap.relative_to(R)))
  check(sha(bytesof(ip))==arc['members_sha256'],'CPU_tar_manifest_ref',str(ip.relative_to(R)))
  mm=jread(ip);mmrows=mm['files'];source_cpu=direct_root(mm['source_root'])
  check(source in source_cpu.parents,'CPU_tar_source_under_author_or_auditor_private_root',str(ip.relative_to(R)))
  check(mm.get('synthetic_not_scientific') is True or mm.get('CPU_fixture_only') is True,'CPU_tar_explicit_synthetic_classification',str(ip.relative_to(R)))
  byname={r['path']:r for r in mmrows}
  assert len(byname)==len(mmrows)==mm['file_count']==arc['file_count']
  assert len({n.casefold() for n in byname})==len(byname)
  streamed=[];total=0;binary=[];suffixes=Counter()
  with tarfile.open(ap,'r|gz') as tf:
   for member in tf:
    n=member.name;pp=PurePosixPath(n)
    assert member.isfile() and not pp.is_absolute() and str(pp)==n and '..' not in pp.parts and '\\' not in n
    assert n in byname and n not in streamed
    assert not any(x.lower() in ('weights','checkpoints','checkpoint','test') or 'sealed' in x.lower() for x in pp.parts),n
    row=byname[n];assert member.size==row['bytes'] and member.size<=128*1024*1024
    h=hashlib.sha256();size=0
    f=tf.extractfile(member)
    while True:
     block=f.read(1024*1024)
     if not block:break
     size+=len(block);h.update(block)
    assert size==row['bytes'] and h.hexdigest()==row['sha256'],n
    # The retained CPU file remains byte-identical; no extraction creates raw data.
    original_data=bytesof(source_cpu/n)
    assert len(original_data)==size and sha(original_data)==row['sha256'],n
    if pp.suffix=='.bin':
     assert size<=36,n
     assert any(v in pp.parts for v in ('blobs','CPU_raw_observations','physical_raw_CPU_fixture')),n
     binary.append({'path':n,'bytes':size,'sha256':row['sha256']})
    else:
     assert pp.suffix.lower() not in guard.WEIGHT_SUFFIXES,n
    suffixes[pp.suffix]+=1;streamed.append(n);total+=size
  check(set(streamed)==set(byname) and len(streamed)==len(byname),'CPU_tar_complete_no_extra_duplicate_member',str(ap.relative_to(R)))
  expected_bytes=arc.get('uncompressed_bytes',arc.get('original_bytes'));check(total==expected_bytes,'CPU_tar_total_bytes',str(ap.relative_to(R)))
  tar_summaries.append({'archive':ref(ap),'member_manifest':ref(ip),'source_root':str(source_cpu),'file_count':len(streamed),'uncompressed_bytes':total,'all_members_sha_bytes_verified':True,'all_retained_private_members_equal':True,'suffix_counts':dict(suffixes),'binary_member_count':len(binary),'max_binary_bytes':max([x['bytes'] for x in binary],default=0),'binary_class':'small synthetic observation/simulator fixtures only; never loose Git payload','scientific_reexecution':False})
# This original single-item source_map has a distinct intentionally small schema.
identity_map=E/'Goal_identity_baseline/source_map.json';im=jread(identity_map)
for key in ('original','published'):
 row=im[key];data=bytesof(R/row['path']);check(sha(data)==row['sha256'] and len(data)==row['bytes'],'identity_baseline_source_map_ref',key)
check(bytesof(R/im['original']['path'])==bytesof(R/im['published']['path']),'identity_baseline_exact_copy')
covered.add(im['published']['path'])
# Guard boundary tests are pure filename predicates, no protected payload is opened.
negative=['results/formal_main_v2/raw_runtime/example/blob.bin','results/checkpoint/model.pt','results/sealed/metadata.json','results/final_state_before.json','results/example/state.init','results/initial_states/development.json']
positive=['results/formal_main_v2/preflight/x/supervisor_snapshot_before.json','results/example/CPU_fixture.tar.gz','scripts/ops/final_state_source.py']
for n in negative:
 try:guard.lexical(n);ok=False
 except guard.StageError:ok=True
 check(ok,'unchanged_lexical_rejects_known_bad_payload',n)
for n in positive:
 guard.lexical(n);check(True,'unchanged_lexical_accepts_allowed_name',n)
known_lexical_limitations=[]
for n in ['results/formal_main_v2/raw_runtime/example/events.jsonl','results/example/observer/blobs/random.rng.json']:
 guard.lexical(n);known_lexical_limitations.append(n)
# Immutable files in the captured snapshot must still have their initial exact bytes.
for row in inventory:
 data=bytesof(R/row['path']);check(sha(data)==row['sha256'] and len(data)==row['bytes'],'captured_archived_file_unchanged',row['path'])
for row in frozen:
 check(sha(bytesof(R/row['path']))==row['sha256'],'frozen173_R_end_pin',row['path'])
put('captured_inventory.json',{'schema':'formal_main_v2','kind':'read_only_B_E_archive_snapshot','captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':inventory,'file_count':len(inventory),'is_final_required_list':False,'later_additions_not_in_scope':True})
put('manifest_mapping_review.json',{'schema':'formal_main_v2','packages':packages,'package_count':len(packages),'unmanifested_operational_files_needing_final_explicit_allowlist':[row for row in inventory if row['path'] not in covered],'note':'These are captured bytes, not automatic stage approval. Their root publication/observation receipts must be explicitly selected in the final required list.'})
put('CPU_tar_member_review.json',{'schema':'formal_main_v2','archives':tar_summaries,'archive_count':len(tar_summaries),'total_members':sum(x['file_count'] for x in tar_summaries),'total_uncompressed_bytes':sum(x['uncompressed_bytes'] for x in tar_summaries),'tar_extracted':False,'scientific_CPU_tests_rerun':False,'classification_scope':'Byte identity plus exact synthetic CPU provenance and bounded tiny fixture blobs; no independent audit of author runtime algorithm.'})
report={'schema':'formal_main_v2','kind':'bounded_Git_archive_static_precheck','status':'passed_current_archive_precheck_pending_final_required' if not problems else 'rejected_current_archive_precheck','review_scope':'Current B/E archived bytes, manifest/source maps, tar exact members/classification, frozen sources and unchanged filename guard. Not independent scientific audit of the reviewer-authored runtime.','reviewed_by':'goal_cpu_gate_2054_Git_scope_only','guard':ref(R/GUARD),'frozen_inventory':ref(R/INV),'source173_verified':not any(not x['passed'] and x['check'].startswith('frozen173') for x in checks),'source_roots':[str(x) for x in roots],'file_count':len(inventory),'package_count':len(packages),'archive_count':len(tar_summaries),'lexical_rejections':lexical_rejections,'markdown_whitespace_findings':markdown_whitespace,'lexical_limitations_need_explicit_exclusion':known_lexical_limitations,'final_required_list_checked':False,'Git_index_read_or_written':False,'Git_commit_or_push':False,'state_or_production_written':False,'Slurm_queries_or_submissions':0,'sealed_or_weight_payloads_read':False,'final_release':False,'blockers':problems,'pending':['Final required list must be unique (including casefold), non-self-referencing, exact path/SHA/bytes, with all additions explicitly reviewed.','Do not stage any loose raw_runtime or observer/blobs member, including .rng.json; existing lexical guard alone is insufficient.','Goal30 design, future submission evidence, final snapshot and further archive additions are not covered unless present in captured_inventory.json.','Run unchanged original nonweight index/restore/frozen173 guard only after root has staged the exact final list; this static precheck does not substitute for that.'],'checks':checks,'check_count':len(checks)}
put('independent_precheck.json',report)
print(json.dumps({'status':report['status'],'checks':len(checks),'blockers':len(problems),'files':len(inventory),'packages':len(packages),'CPU_archives':len(tar_summaries),'CPU_members':sum(x['file_count'] for x in tar_summaries),'whitespace_findings':markdown_whitespace,'report':ref(D/'independent_precheck.json')},ensure_ascii=False))
