"""Record the post-measurement CPU-only sorted-JSON readback correction."""
from pathlib import Path
import datetime, hashlib, json, subprocess

r=Path('F:/CTI-VLA'); out=r/'results/g1_future_long_k64_v1'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
source='src/cti_vla/evaluation/future_long_profiling.py'
inventory=json.loads((out/'source_g1_future_long_k64_v1.json').read_text(encoding='utf-8'))
profile=out/'profiling'
review=json.loads((profile/'independent_review.json').read_text(encoding='utf-8'))
assert review['status']=='passed'
summary=json.loads((out/'analysis/summary.json').read_text(encoding='utf-8'))
assert summary['status']=='analyzed'
value={
 'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'scope':'Only local offline analyze_long_profile readback; server production snapshot and all raw artifacts remain unchanged.',
 'file':source, 'frozen_production_sha256':inventory['files'][source], 'local_offline_sha256':sha(r/source),
 'failure':'Exact raw-summary recomputation rejected per_observation list order and paired_comparisons floating-point reductions after sorted-key JSON serialization.',
 'correction':'Restore observation_episodes insertion order from already validated explicit observation_ids only inside offline analysis, then perform all original exact raw-summary comparisons.',
 'raw_field_recomputation_after_correction':'all fields exactly equal original saved summary',
 'independent_numeric_review':'profiling/independent_review.json',
 'real_measurement_count':2340, 'warmup_count':260, 'new_GPU_calls_for_fix':0,
 'raw_files_unchanged':{name:sha(profile/name) for name in ('config.json','measurements.json','calls.jsonl','summary.json')},
 'regression':{'passed':18,'file':'profile_readback_cpu_checks.xml',
   'initial_fixture_failure':'New CPU fixture omitted journal identity_sha256 refresh; fixed fixture only, initial17pass1fail retained in profile_readback_cpu_checks_attempt1.xml.'},
 'training_selection_profiling_protocol_and_source_snapshot_unchanged':True,
 'test_opened':False,
}
target=out/'profile_readback_fix.json'
assert not target.exists()
target.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
# Independently verify the two downloaded exit receipts without copying weights.
names=['job_3001742.json','job_3001817.json']
P='/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/results/g1_future_long_k64_v1'
raw=subprocess.check_output(['ssh','-o','BatchMode=yes','tongji-cvpr',
    'sha256sum '+' '.join(P+'/'+n for n in names)],text=True)
remote={Path(line.split()[1]).name:line.split()[0] for line in raw.splitlines()}
assert set(remote)==set(names)
assert all(sha(out/n)==remote[n] for n in names)
(out/'exit_receipts_download.json').write_text(json.dumps({'weights_copied':False,'SHA_matches':remote},indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'offline_fix_recorded':True,'actual_analysis':'passed','exit_receipts_SHA_verified':len(names)}))
