from pathlib import Path
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(n):p=R/n;return dict(path=n,sha256=h(p),bytes=p.stat().st_size)
def read(n,pin):assert h(R/n)==pin;return json.loads((R/n).read_bytes())
candidate='.local/final_delivery_scope_20261020T1644/additional_exact_candidate_v2.json'
d=read(candidate,'f5257769fc3f6dde3c2694e456b41730472cecdb92d3785cf3cdf3adff20187d')
assert d['status']=='independent_candidate_scope_not_root_authorization' and d['unbound_changes_requiring_separate_root_scope']==[] and d['source173_unchanged']
rows={}
for x in d['additional_exact']:
 assert h(R/x['path'])==x['sha256'] and (R/x['path']).stat().st_size==x['bytes']
 assert x['path'] not in rows;rows[x['path']]=x
for x in d['pending_exact_root_publications']:
 assert h(R/x['path'])==x['expected_sha256']
 assert h(R/x['source_archive']['path'])==x['expected_sha256']
 rows[x['path']]=dict(**ref(x['path']),category='root_published_independent_training_receipt',sources=[x['source_archive']])
n='results/formal_main_v2/downstream_reviews/four64_20261020T1644_independent.json'
assert h(R/n)=='d3170418334cc545bd760472463a7e165a44b233393b81dff76f5eea72c397ce'
rows[n]=dict(**ref(n),category='root_published_four_development_independent',sources=[ref('results/formal_main_v2/engineering/supervision_delivery_20261020T1644/four_development_independent/independent_review.json')])
exceptions=[]
for x in d['exact_gitignore_exceptions']:
 n=x['file']['path'];assert n in rows and rows[n]['sha256']==x['file']['sha256'] and x['line']=='!/'+n
 exceptions.append(n)
assert len(rows)==239 and len(exceptions)==2
raw={x['path'] for x in d['raw_exclude_all9']};assert len(raw)==9 and not raw.intersection(rows)
x=dict(status='root_reviewed_delivery_scope',independent_candidate=ref(candidate),independent_archival=ref('results/formal_main_v2/preflight/heartbeat_20261021T0044/final_delivery_scope_package_delivery.json'),additional_exact=list(rows.values()),exact_gitignore_exceptions=exceptions,raw_originals_excluded=list(sorted(raw)),root_appended_published_independent_receipts=3,source173_unchanged=True,sealed_values_read=False)
p=R/'.local/root_delivery_scope_20261020T1644.json';assert not p.exists();p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+chr(10))
print(json.dumps(dict(scope=ref(p.relative_to(R).as_posix()),files=len(rows))))
