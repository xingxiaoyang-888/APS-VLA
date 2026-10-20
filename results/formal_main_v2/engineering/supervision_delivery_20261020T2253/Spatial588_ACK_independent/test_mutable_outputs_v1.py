from pathlib import Path
import ast,hashlib,importlib.util,json,sys,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/spatial588_ack_independent_20261020T2253'
p=D/'validate_mutable_outputs_v1.py';assert hashlib.sha256(p.read_bytes()).hexdigest()=='191dbe411df56fc7ed7bf45d5209655d4939a10be70fd59030c17796998f199a'
s=importlib.util.spec_from_file_location('ackmut',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
pre=json.loads((R/'results/formal_main_v2/downstream_gateway/d0143bc88b855ad9f4d6b6008e8373272d55c953d36bba88fbd8840a1090f7d5/preflight.json').read_bytes())
state=hashlib.sha256((R/'results/experiment_supervisor/state.json').read_bytes()).hexdigest()
proof=m.validate_mutable_outputs(pre)
old={n:(m.R/m.REL/n).read_bytes() for n in m.PINS};new={n:(m.P/m.REL/n).read_bytes() for n in ['closed_loop_report.json','config.json','panel.json','trials.jsonl']}
m.validate_snapshots(old,new)
tests=[]
def reject(name,mutate):
 n=copy.deepcopy(new);mutate(n)
 try:m.validate_snapshots(old,n)
 except ValueError as e:tests.append({'test':name,'rejected':True,'error':str(e)})
 else:raise AssertionError(name)
reject('changed_original_prefix',lambda n:n.update({'trials.jsonl':b' '+n['trials.jsonl'][1:]}))
reject('config_changed',lambda n:n.update({'config.json':n['config.json']+b' '}))
reject('panel_changed',lambda n:n.update({'panel.json':n['panel.json']+b' '}))
reject('partial_final_json_line',lambda n:n.update({'trials.jsonl':n['trials.jsonl'][:-1]}))
def alter_row(n,fn):
 rows=[json.loads(x) for x in n['trials.jsonl'][592887:].splitlines()];fn(rows)
 n['trials.jsonl']=n['trials.jsonl'][:592887]+b''.join((json.dumps(x)+'\n').encode() for x in rows)
reject('wrong_new_invocation',lambda n:alter_row(n,lambda rows:rows[0].update(slurm_job_id='9999999')))
reject('duplicate_invocation',lambda n:alter_row(n,lambda rows:rows.append(rows[0])))
reject('wrong_trial_identity',lambda n:alter_row(n,lambda rows:rows[1].update(initial_state_sha256='0'*64)))
def alter_report(n):
 r=json.loads(n['closed_loop_report.json']);r['provenance']['runtime']['slurm_job_id']='3022743';n['closed_loop_report.json']=json.dumps(r).encode()
reject('old_or_wrong_report_owner',alter_report)
assert hashlib.sha256((R/'results/experiment_supervisor/state.json').read_bytes()).hexdigest()==state
out={'schema':'formal_main_v2','kind':'Spatial588_post_ACK_mutable_output_identity_evidence','status':'passed','validator':{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},'actual_read_only_proof':proof,'CPU_negative_tests':tests,'state_sha256_unchanged':state,'root_execution_performed':False,'new_submissions':0,'Slurm_queries':0,'scientific_results_admitted':0,'exact_mutable_absolutes':sorted(m.MUTABLE_ABSOLUTES)}
b=(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
with (D/'mutable_output_validation.json').open('xb') as f:f.write(b)
print(json.dumps({'status':'passed','validator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'proof_sha256':hashlib.sha256(b).hexdigest(),'rejection_tests':len(tests),'mutable_files':2,'original_prefix_results':12,'new_results_admitted':0}))
