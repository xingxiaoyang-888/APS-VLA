"""Seal immutable private candidate delivery; no state/Git/production mutations."""
import ast,hashlib,json
from pathlib import Path
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/legacy6_typed_bridge_0927'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(n):return json.loads((D/n).read_text())
def emit(n,v):
 with (D/n).open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
for name,sha in [('build_map_v1.py','f0958f6bbdbb1b9f45894c38cf57de1b4b8753b1f06dc2da23b43ce0e21e7c20'),('check_legacy_root_v1.py','0a6200400dbf4e311ff60726158fc99fce2f9998998e75356ae92884104579d2'),('report.json','123d73d7a4e5622fd3048efc69058ce19b3d480c28f1ef33a874302b08ead508'),('equivalence_map_candidate.json','f3c7c2e3b3d4546748c4705bb8cba7f29c050470a22645215f7a894f899d3cc0'),('minimum_integration_plan.json','80b5d36e91aed9f7b31d388b4f4b458ee20b5c2a259af5720b763d12b7a7ba8b')]:assert h(D/name)==sha,name
module=ast.parse((D/'build_map_v1.py').read_text());fields={}
for node in module.body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('TOP','TRIAL'):fields[node.targets[0].id]=sorted(ast.literal_eval(node.value))
validator=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='validate_candidate')
emit('schema_contract.json',{'kind':'typed_candidate_schema_contract','format':'named exact-field Python validator, not a production admission protocol','source':{'path':(D/'build_map_v1.py').relative_to(R).as_posix(),'sha256':h(D/'build_map_v1.py')},'validator':'validate_candidate(mapping, records)','validator_line':validator.lineno,'validator_end_line':validator.end_lineno,'required_exact_fields':fields,'map_status':'candidate_not_admitted','trial_status':'conditional_evidence_not_admitted','production_admission_API_implemented':False,'root_and_independent_adoption_refs':None,'unknown_or_positive_admission_claims':'rejected','immutable_ref_policy':'mapping binds original raw files, method identities, target exact action semantics and registration; original root stays old version'})
root=read('legacy_root_recheck.json');report=read('report.json')
emit('delivery_summary.json',{'kind':'legacy600_author_candidate_delivery','status':'ready_for_root_and_independent_review_only','candidate_report_sha256':h(D/'report.json'),'candidate_map_sha256':h(D/'equivalence_map_candidate.json'),'plan_sha256':h(D/'minimum_integration_plan.json'),'new_GPU_seconds':0,'historical_GPU_seconds':10531,'new_scientific_trials':0,'CPU_recheck_and_builder_wall_seconds':root['wall_seconds']+report['CPU_wall_seconds'],'CPU_recheck_and_builder_process_seconds':root['CPU_seconds']+report['CPU_process_seconds'],'transport_preparation_failure_retained':True,'candidate_execution_failures':0,'original600_reused':False,'original600_rerun':False,'production_consumer_changed':False,'pending':'Original same controller/environment condition requires explicit source-chain sufficiency adoption; no new historical snapshot or RNG dump prerequisite.'})
files=[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':h(p)} for p in sorted(D.iterdir()) if p.is_file() and p.name!='manifest.json']
emit('manifest.json',{'schema':'formal_main_v2','kind':'author_candidate_delivery_files','directory':D.relative_to(R).as_posix(),'files':files,'no_reuse_approval':True})
print(json.dumps({'manifest':{'path':(D/'manifest.json').relative_to(R).as_posix(),'bytes':(D/'manifest.json').stat().st_size,'sha256':h(D/'manifest.json')},'file_count':len(files),'summary_sha256':h(D/'delivery_summary.json'),'schema_sha256':h(D/'schema_contract.json')}))
