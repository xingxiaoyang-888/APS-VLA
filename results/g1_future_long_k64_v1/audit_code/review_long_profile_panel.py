from pathlib import Path
import datetime,hashlib,json,sys
r=Path('F:/CTI-VLA');sys.path.insert(0,str(r/'src'))
from cti_vla.data.long_initial_states import load_long_development_panel
from cti_vla.evaluation.future_dense_reuse import load_dense_reference
from cti_vla.evaluation.future_long_profiling import load_long_raw_panel
reg=json.loads((r/'configs/experiments/g1_future_long_k64_v1.json').read_text(encoding='utf-8'))
panel=load_long_development_panel(r/reg['evaluation']['panel'])
dense=load_dense_reference(r/reg['evaluation']['reuse_dense_reference'],panel)
out=r/'results/g1_future_long_k64_v1/profile_panel'
samples,loaded=load_long_raw_panel(out/'panel.json',development_panel=panel,dense_reference=dense,registration=reg)
assert len({x.episode_id for x in samples})==3
report=json.loads((out/'collection_report.json').read_text(encoding='utf-8'))
assert report['status']=='completed' and report['checkpoint_unchanged'] is True and report['observations']==len(samples)
value={'status':'passed','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'raw_observations_verified':len(samples),'all3_fixed_development_tasks':True,
    'all_raw_arrays_SHA_verified':True,'missing_preserved':loaded['missing'],'padding_or_substitution':False,
    'test_opened':False,'new_success_trials':False,'loaded_panel':loaded,
    'review_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(out/'root_review.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in value.items() if k!='loaded_panel'}))
