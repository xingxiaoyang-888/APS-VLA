"""Record a pure JSON ordering diagnostic without changing measured evidence."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tarfile

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'src'))
from cti_vla.evaluation.future_long_profiling import summarize_long_profile

read=lambda p: json.loads(Path(p).read_text(encoding='utf8'))
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
directory=root/'results/g1_future_long_k64_v1/profiling'
path=directory/'independent_review.json'
review=read(path)
assert review['status']=='passed'
for key,name in [('config_sha256','config.json'),('measurements_sha256','measurements.json'),
                 ('journal_sha256','calls.jsonl'),('summary_sha256','summary.json')]:
    assert review[key]==sha(directory/name)
source_relative='src/cti_vla/evaluation/future_long_profiling.py'
archive_path=root/'.local/g1_future_long_k64_v1.tar.gz'
with tarfile.open(archive_path,'r:gz') as archive:
    original=archive.extractfile(source_relative).read()
inventory=read(root/'results/g1_future_long_k64_v1/source_g1_future_long_k64_v1.json')
assert hashlib.sha256(original).hexdigest()==inventory['files'][source_relative]
original_tree=ast.parse(original.decode('utf8'))
current_tree=ast.parse((root/source_relative).read_text(encoding='utf8'))
extract=lambda tree: ast.dump(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='summarize_long_profile'),include_attributes=False)
assert extract(original_tree)==extract(current_tree)
measurement=read(directory/'measurements.json')
saved=read(directory/'summary.json')
raw_rebuild=summarize_long_profile(measurement)
differences=[key for key,value in raw_rebuild.items() if saved.get(key)!=value]
assert set(differences)=={'per_observation','paired_comparisons'}
pair_original={(r['treatment'],r['reference']):r for r in saved['paired_comparisons']}
pair_reloaded={(r['treatment'],r['reference']):r for r in raw_rebuild['paired_comparisons']}
numeric_keys=('speedup_ratio_of_means','ratio_of_medians','mean_paired_difference_ms')
max_abs={field:max(abs(pair_original[pair][field]-pair_reloaded[pair][field]) for pair in pair_original)
         for field in numeric_keys}
restored=deepcopy(measurement)
restored['observation_episodes']={oid:restored['observation_episodes'][oid] for oid in restored['observation_ids']}
reordered=summarize_long_profile(restored)
assert all(saved[key]==value for key,value in reordered.items())
backup=directory/'independent_review_before_serialization_note.json'
if not backup.exists():
    backup.write_bytes(path.read_bytes())
review['serialization_roundtrip_diagnostic']={
    'recorded_utc':datetime.now(timezone.utc).isoformat(),
    'amendment_script_sha256':sha(__file__),
    'initial_independent_review_sha256':sha(backup),
    'raw_measurement_files_unchanged':True,
    'summarize_function_AST_equals_executed_frozen_source':True,
    'fields_affected_by_mapping_order':differences,
    'per_observation_effect':'List ordering only; compare rows by method and observation_id.',
    'paired_comparisons_effect':'Floating reduction ordering only; source measurements and pairing identities are identical.',
    'paired_comparison_max_abs_roundtrip_difference':max_abs,
    'restore_mapping_order_from_observation_ids_all_summary_fields_exactly_equal':True,
    'original_independent_tolerance_recalculation_remains_passed':True,
    'no_GPU_rerun_or_measurement_edit':True}
path.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
target=root/'results/g1_future_long_k64_v1/audit_code/amend_long_profile_serialization_review.py'
target.write_bytes(Path(__file__).read_bytes())
assert sha(target)==review['serialization_roundtrip_diagnostic']['amendment_script_sha256']
print(json.dumps({'status':'passed','affected_fields':differences,'max_abs_roundtrip_difference':max_abs,
    'restore_explicit_observation_order_exact_match':True,'original_measurement_files_unchanged':True}))
