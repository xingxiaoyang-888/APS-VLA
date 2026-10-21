from pathlib import Path
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_bounded_diagnostic_20261020T2358'
sha=lambda b:hashlib.sha256(b).hexdigest()
old=D/'delivery_manifest_v2.json'
assert sha(old.read_bytes())=='84a3b3c3695f437b63898ed3be9e07857910940be82b8db51437376c2771ee29'
m=json.loads(old.read_text())
for name,v in m['files'].items():
 b=(D/name).read_bytes();assert len(b)==v['bytes'] and sha(b)==v['sha256']
assert (D/'prospective_full200_specification_v2.json').read_bytes()==(D/'prospective_full200_specification.json').read_bytes()
r=json.loads((D/'prospective_specification_CPU_tests_v2.json').read_text())
assert r['positive_tests']==1 and r['rejection_tests']==30 and all(x['rejected'] for x in r['negative_tests'])
note={'kind':'append_only_independent_feedback_repair','old_entrypoint':'build_prospective_specification.py','old_entrypoint_sha256':'75379ac29257a706729262873bb9e9d875dd66edabeea882c1f3ab5cd8b48e63',
 'current_entrypoint':'build_prospective_specification_v2.py','current_entrypoint_sha256':'c8f64e3ee1f4c6d07aa12e7afd2ecd75847c391987fddecdf1d14e25be96e8bf',
 'previous_gap':'CPU specification validator did not explicitly reject mutations of step/query/trial bounds, watchdog, ordered row signature or panel hash; actual frozen specification values were correct.',
 'revision':'Six fields now explicit; duplicate gate and remaining field mutations reject against entire pinned original specification. Added10negative cases including fractional numeric bound and retrospective/pass condition changes.',
 'test_counts':{'positive':1,'rejections':30},'actual_specification_SHA_unchanged':'ed0b59bd1acbdab34658f5599f4969aa745e596348bf25d230a38c978aa652ad',
 'core_analyze_source_and_real_evidence_unchanged':True,'old_files_rewritten':False,'still_CPU_specification_only':True,'independent_review_pending':True}
p=D/'validator_scope_revision.json';assert not p.exists();p.write_bytes(json.dumps(note,ensure_ascii=False,sort_keys=True,indent=2).encode()+b'\n')
name='goal_bounded_diagnostic_20261020T2358_specification02.jsonl'
b=(R/'results/formal_main_v2/control_transport'/name).read_bytes()
p=D/name;assert not p.exists();p.write_bytes(b)
files={}
for p in sorted(D.iterdir()):
 assert p.is_file() and not p.is_symlink()
 if p.name=='delivery_manifest_v3.json':raise ValueError('refuse overwrite')
 b=p.read_bytes();files[p.name]={'sha256':sha(b),'bytes':len(b)}
new={k:v for k,v in m.items() if k not in ('files','file_count')}
new.update(files=files,file_count=len(files),supersedes_delivery_manifest_sha256=sha(old.read_bytes()),
 current_CPU_specification_validator='build_prospective_specification_v2.py',
 change='Append independent-feedback validator repair and30negative author tests; all prior files retained. The actual200 specification and real diagnostic unchanged.')
p=D/'delivery_manifest_v3.json';p.write_bytes(json.dumps(new,ensure_ascii=False,sort_keys=True,indent=2).encode()+b'\n')
print(json.dumps({'path':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes()),'file_count':len(files),'original_files_unchanged':True}))
