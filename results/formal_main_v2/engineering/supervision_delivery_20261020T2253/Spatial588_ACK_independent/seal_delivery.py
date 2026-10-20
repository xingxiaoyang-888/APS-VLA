from pathlib import Path
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/spatial588_ack_independent_20261020T2253'
AUTH='d0143bc88b855ad9f4d6b6008e8373272d55c953d36bba88fbd8840a1090f7d5'
DG=R/'results/formal_main_v2/downstream_gateway'/AUTH
B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0653'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,b):
 p.parent.mkdir(exist_ok=True)
 with p.open('xb') as f:f.write(b)
def cp(p,name,pin=None):
 if pin is not None:assert h(p)==pin
 write(D/'raw_evidence'/name,p.read_bytes())
cp(R/'.local/reconcile_spatial588_3054201_20261020T2253.py','root_reconcile_v1_NOT_EXECUTED.py','8a4c04313d0134330b9c18663e8b98a5aa330ef7fbf9cf1654f3209c74b482ba')
cp(R/'.local/reconcile_spatial588_3054201_20261020T2253_v2.py','root_reconcile_v2_EXECUTED.py','8febf8111c1bcb71c89f05600359865d5708b2e32019295a056f5d7674f2b46f')
for name,pin in {
 'preflight.json':'77de2bf6f02d5ea8ca7629a286898105f5c0358c66e2b397717f64ea318254b1',
 'sbatch_result.json':'cba65b7776348747bc6dfa62f4b336643fac38f880e1e6a375df0dfc3b25f52f',
 'failed_transaction.json':'18897d313b1460cf14bbef535171090ff3a72bd29adf03018a65bd02ec1525ff',
 'committed.json':'952759f9c8fb1daaf46359cbf046f097233eb94d127d4f22039651da57668fbb',
 'root_reconciled_submission_observation.json':'d38314a320c4e31ab644b2f499ae09a4e78cc1b2256c2cece8e57d360ab51d6c'
}.items():cp(DG/name,name,pin)
cp(B/'state_and_document_update.json','root_state_and_document_update.json','e20926b5a6fead9d6fa64f50012450e63392ba37ba6d30c16653a92e6f8993f4')
cp(B/'final_summary.json','root_final_summary.json','f4d17e968396671b9e8072de1503133652b437e1dd9eee040f74c5d37a56b12d')
for name in [
 'spatial588_ack_independent_20261020T2253_v1.jsonl',
 'spatial588_ack_mutable_output_validation_20261020T2253_v1.jsonl',
 'spatial588_ack_independent_20261020T2253_v2.jsonl',
 'spatial588_ack_post_registration_independent_20261020T2253_v1.jsonl',
 'spatial588_ack_post_registration_independent_20261020T2253_v2.jsonl'
]:cp(R/'results/formal_main_v2/control_transport'/name,'transport_'+name)
assert h(D/'independent_review.json')=='60eb3a6e0f79f9a4943a3e6904a65a2d9f94684ff932ab923064faddd8da8568'
assert h(D/'post_registration_independent_review.json')=='62b31fedd7ace383a22610d5de7b4ee4e7b2542cd565d3c7c1efae18523e191c'
files=[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':h(p)} for p in sorted(D.rglob('*')) if p.is_file()]
out={'schema':'formal_main_v2','kind':'Spatial588_ACK_reconciliation_independent_delivery','status':'passed','file_count':len(files),'files':files,'review':{'path':(D/'post_registration_independent_review.json').relative_to(R).as_posix(),'sha256':h(D/'post_registration_independent_review.json')},'pre_reconciliation_review':{'path':(D/'independent_review.json').relative_to(R).as_posix(),'sha256':h(D/'independent_review.json')},'automatic_submission_authority':False,'new_GPU_seconds':0,'new_GPU_submissions':0,'new_Slurm_queries':0,'new_scientific_trials':0,'failed_attempts_preserved':['audit_v1: exact all-P comparison rejected legitimate append/report after unique ACK; root old helper was not executed','post_registration_audit_v1: original b66d state pin changed during root final metadata publication; v2 reconstructs exact b66d and checks precise allowed a0d4 root delta'],'validator_authorship':'191d read-only exact-output validator authored by this child, tested with 8 deliberate reject cases and separately reviewed by root before root v2 integration. No independent-author confusion.','reconciliation_scope':'Unique original ACK3054201, exact original preflight and pending, only two mutable post-submit outputs; 374 R +227 immutable P + full exact two-output identity checks; no new FrozenPlan/submit.','original_failure_retained':True,'final_release':False}
p=D/'delivery_manifest_final.json';write(p,(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
print(json.dumps({'manifest':p.relative_to(R).as_posix(),'sha256':h(p),'file_count':len(files),'bytes':sum(f['bytes'] for f in files)}))
