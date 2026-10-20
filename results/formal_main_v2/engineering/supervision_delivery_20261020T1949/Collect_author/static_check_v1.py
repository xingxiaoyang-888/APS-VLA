from pathlib import Path
import ast,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/collect_terminal_20261020T1949'
p=D/'root_collect_terminal_v1.py';pin='1cd87061863737c8783e4498820d9d09929c93bc8e0427c650330baff31e1eb6';assert hashlib.sha256(p.read_bytes()).hexdigest()==pin
compile(p.read_bytes(),str(p),'exec',dont_inherit=True)
tree=ast.parse(p.read_text());calls=[x for x in ast.walk(tree) if isinstance(x,ast.Call)]
attrs=[x.func.attr for x in calls if isinstance(x.func,ast.Attribute)]
assert not set(attrs)&{'unlink','remove','rmdir','replace','rename','system','Popen'}
constants=[x.value for x in ast.walk(tree) if isinstance(x,ast.Constant) and isinstance(x.value,str)]
assert not any(x in ('sbatch','scancel','scontrol','git') for x in constants)
report={'status':'passed_static_preexecution_check','source':{'path':str(p.relative_to(R)),'sha256':pin},'compiled_without_execution':True,'root_execute_not_called':True,'root_review_consumer_not_called':True,'root_scope_read_through_original_call_chain':True,'no_new_scheduler_or_Git_mutation_calls':True,'no_added_delete_or_rename_operations':True,'not_an_end_to_end_transaction_test':True}
with (D/'root_helper_static_check.json').open('x') as f:json.dump(report,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps(report))
