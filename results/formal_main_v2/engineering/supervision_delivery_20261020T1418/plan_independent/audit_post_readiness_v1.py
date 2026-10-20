"""Actual P wrapper read-only closure after genuine root readiness publication."""
import importlib.util,hashlib,json,sys,time
from pathlib import Path
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
SRC=R/'.local/devplans_independent_20261020T1418/audit_plans_v1.py'
assert hashlib.sha256(SRC.read_bytes()).hexdigest()=='2748f3457b12be89230961cbb126ff4186eff8e5edfcd039c2a35569c8023510'
sp=importlib.util.spec_from_file_location('post_audit_shared',SRC);u=importlib.util.module_from_spec(sp);sys.modules[sp.name]=u;sp.loader.exec_module(u)
def main():
 start=time.perf_counter();cpu=time.process_time();root_path,root_sha,prior_sha,author_sha=sys.argv[1:5]
 u.need(root_path.startswith('results/formal_main_v2/preflight/heartbeat_20261020T2218/'),'Wrong root index scope')
 index=u.js(root_path,root_sha)
 u.need(str(index['status']).startswith('passed') and index['actual_full_P_wrapper_verifications']==3 and index['actual_GPU_runtime_chain_verified'] is False,'Root actual P verification required')
 prior=u.js(u.D/'independent_index.json',prior_sha)
 author=u.js(u.A/'candidate_review.json',author_sha);pins=author['source_files']
 wrapper=u.load(u.PREFIX+'wrapper.py',pins[u.PREFIX+'wrapper.py'],u.P)
 gateway=u.load(u.PREFIX+'gateway.py',pins[u.PREFIX+'gateway.py'])
 shards=index.get('shards',index.get('plans'));u.need(isinstance(shards,list) and len(shards)==3,'Exact three root shard refs required')
 results=[]
 for p in prior['plans']:
  matches=[]
  for shard in shards:
   a=u.js(shard['authorization']['path'],shard['authorization']['sha256'])
   if a['plan']==p['effective_plan']:matches.append((shard,a))
  u.need(len(matches)==1,'Ambiguous exact plan authorization')
  shard,authorization=matches[0]
  a,e,plan,science,prepared=gateway.validate_authorization(u.R,shard['authorization'])
  u.need(a==authorization and a['plan']==p['effective_plan'] and a['scientific_plan']==p['scientific_plan'] and a['prepared_invocation']==shard['prepared_invocation'] and a['runtime_readiness']==shard['readiness'],'Authorization references differ')
  ready=u.js(shard['readiness']['path'],shard['readiness']['sha256'])
  indref={'path':p['canonical_path'],'sha256':p['candidate']['sha256']}
  u.need(ready['independent_review']==indref and ready['effective_plan']==p['effective_plan'] and ready['scientific_plan']==p['scientific_plan'] and ready['action_execution_contract']==p['action_execution_contract'] and ready['plan_sha256']==p['plan_sha256'],'Readiness must bind reviewed exact plans')
  u.need(ready['method_ids']==p['methods'] and ready['expected_trials']==p['expected_trials'] and ready['allowed_stages']==['development'],'Readiness methods/stage differ')
  for role in ('root_review','independent_review'):
   rref=ready[role];review=u.js(rref['path'],rref['sha256'])
   u.need(review['status']=='passed' and review['scientific_plan']==p['scientific_plan'] and review['effective_plan']==p['effective_plan'] and review['action_execution_contract']==p['action_execution_contract'] and review['plan_sha256']==p['plan_sha256'] and review['method_ids']==p['methods'] and review['production_chain_complete'] is True,'Per-plan review binding incomplete')
   u.read(u.P/rref['path'],rref['sha256'])
  for rr in [shard['readiness'],p['scientific_plan'],p['effective_plan'],p['action_execution_contract']]:u.read(u.P/rr['path'],rr['sha256'])
  for name,sha in ready['runtime_publication_files'].items():u.read(name,sha);u.read(u.P/name,sha)
  root_check_ref=shard.get('root_check',shard.get('root_pre_execution'));u.need(root_check_ref is not None,'Exact root pre-execution ref absent')
  check=u.js(root_check_ref['path'],root_check_ref['sha256'])
  u.need(str(check['status']).startswith('passed') and check['full_P_wrapper_verify'] is True and check['actual_GPU_runtime_chain_verified'] is False and check['authorization']==shard['authorization'] and check['readiness']==shard['readiness'] and check['prepared_invocation']==shard['prepared_invocation'] and check['method_ids']==p['methods'] and check['plan_sha256']==p['plan_sha256'],'Root verification differs from exact deployment')
  checked=wrapper.verify(prepared,project=u.P)
  u.need(checked['effective_plan']==plan and checked['original_plan']==science and checked['readiness']==ready,'Actual P wrapper reconstructed different objects')
  u.need(checked['args'].mode=='evaluate' and plan['invocation']['suite']==p['suite'] and plan['invocation']['method_ids']==p['methods'] and not plan['invocation']['resume'],'Actual wrapper changed scientific scope')
  for name,sha in e.hashes.items():u.read(name,sha)
  results.append({'group_key':p['group_key'],'suite':p['suite'],'budget':p['budget'],'seed':p['seed'],'methods':p['methods'],'expected_trials':p['expected_trials'],'unique_initial_states':100,'authorization':shard['authorization'],'root_pre_execution':root_check_ref,'readiness':shard['readiness'],'prepared_invocation':shard['prepared_invocation'],'root_review':ready['root_review'],'independent_review':indref,'reservation':a['root_reservation'],'scientific_plan':p['scientific_plan'],'effective_plan':p['effective_plan'],'action_execution_contract':p['action_execution_contract'],'plan_sha256':p['plan_sha256'],'actual_full_P_wrapper_verified':True,'original_gateway_static_authorization_verified':True,'actual_GPU_runtime_chain_verified':False})
 for path,sha in u.READS.items():u.need(u.digest(path)==sha,'Evidence changed during post-readiness audit')
 u.dump('post_readiness/read_evidence_sha256.json',u.READS)
 report=u.dump('post_readiness/post_readiness_independent_review.json',{'schema':'formal_main_v2','kind':'nonLong_exact_post_readiness_independent_review','status':'passed','reviewer':u.REVIEWER,'source':u.ref(Path(__file__)),'root_index':{'path':root_path,'sha256':root_sha},'independent_plan_index':u.ref(u.D/'independent_index.json'),'actual_full_P_wrapper_verifications':3,'actual_GPU_runtime_chain_verified':False,'new_GPU_seconds':0,'new_trials':0,'Slurm_submissions':0,'scientific_settings_changed':False,'state_Git_Slurm_modified':False,'final_release':False,'O2A_enabled':False,'plans':results,'remaining_submission_gate':'Root exact gateway must freshly check current controller owner/lease, pending token, registered jobs and <=8 GPU total, then consume one-use reservation. This audit itself submits nothing.','CPU_wall_seconds':time.perf_counter()-start,'CPU_process_seconds':time.process_time()-cpu,'prepared_invocation_delivery_boundary':'Original gateway publishes prepared bytes at plan.invocation_relative only during submission. This CPU verifier consumes exact root prepared bytes and validates all actual P prerequisites without fabricating a submitted invocation.','blockers':[]})
 files=[{'path':p.relative_to(u.R).as_posix(),'bytes':p.stat().st_size,'sha256':u.digest(p)} for p in sorted(u.D.rglob('*')) if p.is_file() and p.name!='final_manifest.json']
 manifest=u.dump('final_manifest.json',{'schema':'formal_main_v2','kind':'nonLong_development_plan_and_actual_P_verification_delivery','reviewer':u.REVIEWER,'files':files,'production_modified':False})
 print(json.dumps({'status':'passed','post_review':report,'manifest':manifest}))
if __name__=='__main__':
 try:main()
 except BaseException as err:
  u.dump('post_readiness/failure_v1.json',{'error_type':type(err).__name__,'error':str(err),'traceback':u.traceback.format_exc(),'production_modified':False,'new_GPU_seconds':0});raise
