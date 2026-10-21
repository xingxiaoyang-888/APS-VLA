from pathlib import Path
import importlib.util,sys,hashlib,json
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('transport_preflight_receipt',p); c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert hashlib.sha256((R/'results/experiment_supervisor/state.json').read_bytes()).hexdigest()=='40e7b58265a49ef61b8a02a793d3ce96c22bb84c93eae14a0b6bcf196ffd221a'
 assert not (R/'results/formal_main_v2/control_transport/commit_delivery_20261020T2358.jsonl').exists()
 out=R/'results/formal_main_v2/preflight/heartbeat_20261021T0758/commit_transport_argument_correction.json'
 value={'status':'pre_entrypoint_argument_rejected_no_mutation','utc':datetime.now(timezone.utc).isoformat(),'incorrect_bundle_argument':'3726e3249403e3afa1d4fd1688b0dbce540e28714ac6f721662118ddb7338d7c0288aa0bcef','correct_bundle_argument':'3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149','error':'ValueError: bundle SHA missing','rejected_at':'server_transport.verify_bundle before audit and entrypoint','entrypoint_executed':False,'GPU_jobs_added':0,'state_unchanged':True,'note':'Root command transcription error; rerun only with exact existing reviewed transport bundle pin.'}
 with out.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'status':value['status'],'receipt':str(out.relative_to(R)),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
