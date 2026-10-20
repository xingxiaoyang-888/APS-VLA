from pathlib import Path
import json,hashlib
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/dispatch_independent_20261020T1530/final'
h=lambda b:hashlib.sha256(b).hexdigest()
j=R/'results/formal_main_v2/control_transport/final_summary_independent_20261020T1530_v1.jsonl'
b=j.read_bytes();lines=[json.loads(x) for x in b.splitlines()]
assert lines[-1]['event']=='control_end' and lines[-1]['returncode']==0 and lines[-1]['source173_and_entrypoint_unchanged'] is True
p=D/'transport';p.mkdir(exist_ok=False)
with (p/j.name).open('xb') as f:f.write(b)
files={x.relative_to(D).as_posix():{'sha256':h(x.read_bytes()),'bytes':x.stat().st_size} for x in sorted(D.rglob('*')) if x.is_file()}
assert 'delivery_manifest.json' not in files
old='f5e19f81c7b074f02598283b1b98a73c9a5050f716db75234e4ca1b1243a90e4'
assert h((D.parent/'delivery_manifest.json').read_bytes())==old
out={'schema':'formal_main_v2','kind':'independent_final_summary_crosscheck_delivery','status':'passed','private_root':D.as_posix(),'prior_dispatch_manifest_untouched_sha256':old,'files':files,'file_count':len(files),'total_bytes':sum(v['bytes'] for v in files.values()),'report':{'path':'.local/dispatch_independent_20261020T1530/final/independent_review.json','sha256':h((D/'independent_review.json').read_bytes())},'closed_transport_source':{'path':j.relative_to(R).as_posix(),'sha256':h(b)},'source173_and_entrypoint_unchanged_confirmed_by_closed_transport':True,'source_and_reconstruction_and_all_errors_preserved':True,'production_writes':0,'new_GPU_jobs':0}
v=(json.dumps(out,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
with (D/'delivery_manifest.json').open('xb') as f:f.write(v)
print(json.dumps({'manifest':str(D/'delivery_manifest.json'),'sha256':h(v),'file_count':len(files),'total_bytes':out['total_bytes']}))
