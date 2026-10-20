from pathlib import Path
import hashlib,importlib.util,json,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).resolve().parent
B=R/'results/formal_main_v2/preflight/heartbeat_20261020T2330/Goal_t0_dispatch'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
pin={'held_identity.json':'b11ab37ac3a9f5b7df4ee7a45e123751731696bebf61b508fd214533f65da7db','submission_result.json':'5a0dde13a6f15e36c05dae8aa82474a34e304bcc209f29857d53714c65df5a51','pending.json':'00e8fe4d74ce7615564cbba2a1dfb4922f417ac4c6b0e75a680163d5dcfeb4e5'}
for name,h in pin.items():
 assert sha(B/name)==h
 with (D/name).open('xb') as f:f.write((B/name).read_bytes())
entry=R/'.local/goal_t0_dispatch_20261020T1530.py';assert sha(entry)=='45dc2e6483578c8f332820d03386ca0cc20f3b7736ec74ad50d2e46b4d538b5d'
spec=importlib.util.spec_from_file_location('old_root_dispatch_pure_parse',entry);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
raw=json.loads((D/'held_identity.json').read_text())['stdout'];old=m.job_fields(raw)
assert old['Partition']=='L40 AllocNode:Sid=logina04:3160037'
try:m.verify_held_or_released(old,'3050711',json.loads((D/'pending.json').read_text())['request_token'],True)
except RuntimeError as e:original_failure=str(e)
else:raise AssertionError('original parser unexpectedly accepted actual fixture')
fixed={x.group(1):x.group(2).strip() for x in re.finditer(r'(?:^|\s)([A-Za-z][A-Za-z0-9_:/]*)=(.*?)(?=\s[A-Za-z][A-Za-z0-9_:/]*=|$)',raw.strip())}
expected={'JobId':'3050711','JobName':'cti-goal-t0-probe','UserId':'u15016(10738)','GroupId':'u15016(11453)','Account':'p_p15016','Partition':'L40','JobState':'PENDING','Reason':'JobHeldUser','Requeue':'0','Restarts':'0','TimeLimit':'00:30:00','ExcNodeList':'gpu4020','NumCPUs':'7','NumTasks':'1','CPUs/Task':'7','AllocNode:Sid':'logina04:3160037','ReqB:S:C:T':'0:0:*:*','Socks/Node':'*','NtasksPerN:B:S:C':'0:0:*:*','TresPerNode':'gres:gpu:l40:1','Command':'/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/results/formal_main_v2/engineering/goal_t0_probe_20261020T1418/source/candidate.slurm','WorkDir':'/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA','Comment':json.loads((D/'pending.json').read_text())['request_token']}
assert all(fixed.get(k)==v for k,v in expected.items())
tres=dict(x.split('=',1) for x in fixed['TRES'].split(','));assert tres['gres/gpu']==tres['gres/gpu:l40']=='1' and tres['cpu']=='7' and tres['mem']=='64G'
assert fixed['TresPerNode'] not in ('gres/gpu:l40:1','gres/gpu:1')
report=dict(status='confirmed_parser_compatibility_failure_resource_request_correct',kind='independent_actual_held_ACK_diagnosis',original_dispatch_source_sha256=sha(entry),job_id='3050711',actual_inputs=pin,original_parser_failure=original_failure,original_misparsed_partition=old['Partition'],new_pure_parser_fields=fixed,exact_checks=len(expected)+5,resource_request_correct=True,original_CPU_review_limitation='201 fake-Slurm checks did not cover this actual site field-key syntax or colon GPU TRES value; the original review was CPU-only and is not evidence of successful actual dispatch.',existing_ACK_held=True,actual_Slurm_operations_by_auditor=0,new_submission_authorized=False,required_next_step='Root exact-ID/token reconciliation then one release, through separately reviewed no-sbatch helper; preserve original pending and cost evidence.')
put(D/'independent_real_format_diagnosis.json',report);print(json.dumps({'path':str(D/'independent_real_format_diagnosis.json'),'sha256':sha(D/'independent_real_format_diagnosis.json'),'checks':report['exact_checks']}))
