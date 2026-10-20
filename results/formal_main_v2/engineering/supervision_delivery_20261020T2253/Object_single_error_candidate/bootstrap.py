from pathlib import Path
import hashlib,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/object_single_error_candidate_20261020T2253'
sys.path.insert(0,str(D));sys.path.insert(0,str(R/'src'))
import fixed as F
import iterator
from cti_vla.evaluation import formal_trials
try:
 inputs=F.load_inputs(formal_trials)
 raw=json.dumps(inputs['scope'],ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
 with (D/'scope.json').open('xb') as f:f.write(raw)
 original,derived,proof=iterator.derive_loop(formal_trials,(R/F.LOOP).read_bytes())
 with (D/'iterator_derivation.json').open('x') as f:json.dump(proof,f,ensure_ascii=False,indent=2,sort_keys=True)
 print(json.dumps({'scope_sha256':F.sig(inputs['scope']),'scope_file_sha256':F.sha(raw),'source173_verified':True,'original_count':len(inputs['results']),'derivation':proof},ensure_ascii=False))
except BaseException as e:
 with (D/'bootstrap_failure.json').open('x') as f:json.dump({'error':str(e),'traceback':traceback.format_exc(),'GPU_seconds':0},f,indent=2)
 raise
