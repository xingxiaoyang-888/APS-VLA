from pathlib import Path
import hashlib,json,importlib.util,datetime
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent;E='results/formal_main_v2/engineering/supervision_delivery_20261020T1949'
h=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):p=Path(p);return {'path':p.relative_to(R).as_posix(),'sha256':h(p),'bytes':p.stat().st_size}
def put(n,x):p=D/n;p.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n');return ref(p)
p=R/'scripts/ops/check_nonweight_archive_stage.py';assert h(p)=='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6';spec=importlib.util.spec_from_file_location('_stage_names_only',p);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
packs=[]
for rel,pin,target in [('.local/collect_terminal_20261020T1949/collect_delivery_manifest.json','897889f47bc402209b73bda69b09401f4174210cf8dedeb0ec929ae16df8e91a','collect_author'),('.local/collect_terminal_20261020T1949/development_gateway/delivery_manifest.json','e369bbc9e597c0a80fd4f541b6f6b2d67d17b3eda321ae728e2e87e821980c5e','development_gateway_author')]:
 m=R/rel;assert h(m)==pin;v=json.loads(m.read_text());base=m.parent;rows=[]
 for row in v['files']:
  p=R/row.get('source',row['path']);assert not p.is_symlink();assert h(p)==row['sha256'] and p.stat().st_size==row['bytes'];sub=p.relative_to(base).as_posix();dest=E+'/'+target+'/'+sub;g.lexical(dest);assert row['bytes']<g.LIMIT;rows.append({'source':p.relative_to(R).as_posix(),'path':dest,'sha256':row['sha256'],'bytes':row['bytes']})
 dest=E+'/'+target+'/'+m.name;g.lexical(dest);rows.append({'source':rel,'path':dest,'sha256':pin,'bytes':m.stat().st_size});packs.append({'source_manifest':ref(m),'file_count_including_manifest':len(rows),'bytes':sum(x['bytes'] for x in rows),'needs_additional_lossless_archive':False,'files':rows})
a=put('author_package_addendum.json',{'status':'passed_exact_author_package_delivery_only','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'packages':packs,'stageguard':ref(R/'scripts/ops/check_nonweight_archive_stage.py'),'code_execution_or_science_validation_claimed':False,'Git_state_or_production_writes':False,'independent_bridge_final_package_pending':True})
files=[ref(p) for p in sorted(D.iterdir()) if p.is_file() and p.name!='delivery_manifest_v2.json'];m=put('delivery_manifest_v2.json',{'status':'current_files_verified_independent_final_addendum_pending','files':files,'file_count':len(files),'bytes':sum(x['bytes'] for x in files),'author_addendum':a});print(json.dumps({'author_addendum':a,'delivery_manifest_v2':m}))
