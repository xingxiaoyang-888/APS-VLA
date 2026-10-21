from pathlib import Path
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_bounded_diagnostic_20261020T2358'
sha=lambda b:hashlib.sha256(b).hexdigest()
old=D/'delivery_manifest.json'
assert sha(old.read_bytes())=='d5e0391fd7b10a1fac8ecdf0198c1abcaab5375894b80dee37c86638273477bf'
m=json.loads(old.read_text())
for name,v in m['files'].items():
 b=(D/name).read_bytes();assert len(b)==v['bytes'] and sha(b)==v['sha256']
r=json.loads((D/'execution_report.json').read_text())
assert r['check_count']==1234 and len(r['checks'])==1235 and all(x['passed'] for x in r['checks'])
assert r['checks'][-1]=={'check':'new private output execution_report.json','passed':True}
note={'kind':'append_only_metadata_count_clarification','original_report_sha256':sha((D/'execution_report.json').read_bytes()),
 'recorded_integer_check_count':1234,'actual_check_rows_and_final_console':1235,'all_rows_passed':True,
 'extra_last_check':'new private output execution_report.json',
 'cause':'The integer was evaluated before out() added its own output-path check; the checks list reference included that last passed row.',
 'scientific_evidence_changed':False,'old_files_rewritten':False,'independent_review_required':True,
 'preferred_reporting':'1235 recorded passed check rows (1234 preceding output-path check); 14 classifier cases; prospective specification1positive20negative.'}
p=D/'count_metadata_clarification.json';assert not p.exists();p.write_bytes(json.dumps(note,ensure_ascii=False,sort_keys=True,indent=2).encode()+b'\n')
files={}
for p in sorted(D.iterdir()):
 assert p.is_file() and not p.is_symlink()
 if p.name=='delivery_manifest_v2.json':raise ValueError('refuse overwrite')
 b=p.read_bytes();files[p.name]={'sha256':sha(b),'bytes':len(b)}
new={k:v for k,v in m.items() if k not in ('files','file_count')}
new.update(files=files,file_count=len(files),supersedes_delivery_manifest_sha256=sha(old.read_bytes()),
 change='Only append metadata count clarification; original20 files and manifest remain immutable.')
p=D/'delivery_manifest_v2.json';p.write_bytes(json.dumps(new,ensure_ascii=False,sort_keys=True,indent=2).encode()+b'\n')
print(json.dumps({'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes()),'file_count':len(files),'original20_unchanged':True}))
