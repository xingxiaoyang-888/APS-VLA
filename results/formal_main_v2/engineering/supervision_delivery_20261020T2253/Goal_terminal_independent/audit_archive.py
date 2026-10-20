from pathlib import Path
from collections import Counter
import hashlib,json,tarfile,time,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R/'.local/goal_terminal_independent_20261020T2253';STAGE='results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156';AP=R/STAGE/'attempt01/observer/blob_archive_manifest.json';AH='471ce3a437018859550bba77c6b456b6c5fa8ca52477a41dc6bbf551a7e58be8';RP=R/'results/formal_main_v2/preflight/heartbeat_20261021T0653/Goal_terminal_root_review.json';RH='612766294af9462d0c21edbdcb177433a0cd1f2897b1d613ab9eb674f43bbb19';counts=Counter()
def h(p):
 v=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):v.update(b)
 return v.hexdigest()
def ck(name,ok):
 counts[name]+=1
 if not ok:raise AssertionError(name)
def out(name,v):
 p=D/name;p.open('x').write(json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2)+'\n');return {'path':str(p.relative_to(R)),'sha256':h(p)}
def main():
 ck('archive_manifest_pin',h(AP)==AH);ck('root_raw_review_pin',h(RP)==RH);arc=json.loads(AP.read_bytes());root=json.loads(RP.read_bytes());ind=json.loads((D/'raw_artifact_allowlist.json').read_bytes());terminal=json.loads((D/'terminal_review.json').read_bytes());per=json.loads((D/'per_trial_independent_reconstruction.json').read_bytes())['trials'];ck('independent_terminal_pin',h(D/'terminal_review.json')=='e48e5f5a0855c81280ea9cd4eb014aefe45c3b18d324836930b5a5ef1e1d4d61')
 ck('root_scalars_independent_match',root['GPU_seconds']==terminal['allocated_GPU_seconds']==840 and root['accepted_queries']==940 and root['executed_steps']==7302 and root['paired_inputs']==29 and root['prefix_trials']==58 and root['new_Goal_science_HOLD'] and root['old200_adopted'] is False and root['new_scientific_trials']==0 and root['final_release'] is False)
 ck('root_pertrial_independent_match',root['per_trial']==[{'ordinal':t['ordinal'],'queries':t['policy_calls'],'same_raw_actions':True,'scientific_trials_added':0,'steps':t['executed_steps'],'trial_id':t['identity']['trial_id']} for t in per])
 expected={k.removeprefix('observer/'):v for k,v in ind['files'].items() if k.startswith('observer/blobs/')};rootmap={r['path']:{'bytes':r['bytes'],'sha256':r['sha256']} for r in root['blob_allowlist']};ck('root_blob_allowlist_independent_exact',rootmap==expected and len(rootmap)==len(root['blob_allowlist'])==10741)
 ck('archive_zero_science',arc['job_id']=='3054127' and arc['new_Goal_science_HOLD'] and arc['new_scientific_trials']==0 and arc['weights_or_sealed_values'] is False and arc['final_release'] is False and arc['old200_adopted'] is False)
 ck('archive_counts',arc['blob_count']==10741 and arc['blob_bytes']==474068525 and len(arc['parts'])==15 and arc['compressed_bytes']==171376198)
 seen={};partchecks=[]
 for part in arc['parts']:
  p=R/part['path'];ck('part_path',p.is_relative_to(R/STAGE/'attempt01/observer/blob_archives') and p.resolve()==p and not p.is_symlink());ck('part_sha_and_length',h(p)==part['sha256'] and p.stat().st_size==part['compressed_bytes'])
  declared={x['path']:{'sha256':x['sha256'],'bytes':x['bytes']} for x in part['members']};ck('part_declaration_unique',len(declared)==len(part['members']))
  actual={}
  with tarfile.open(p,'r|gz') as tf:
   for member in tf:
    ck('archive_regular_allowlisted_members',member.isfile() and not member.issym() and not member.islnk() and member.name in declared and member.name in expected and member.name not in seen and member.name not in actual)
    raw=tf.extractfile(member).read();value={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)};ck('each_raw_member_exact',value==declared[member.name]==expected[member.name] and len(raw)==member.size)
    actual[member.name]=value;seen[member.name]=value
  ck('whole_part_exact',actual==declared and sum(v['bytes'] for v in actual.values())==part['uncompressed_member_bytes'])
  partchecks.append({'path':part['path'],'sha256':part['sha256'],'members':len(actual),'member_bytes':sum(v['bytes'] for v in actual.values()),'compressed_bytes':p.stat().st_size})
 ck('whole_archive_complete',seen==expected and sum(v['bytes'] for v in seen.values())==474068525 and sum(x['compressed_bytes'] for x in partchecks)==171376198)
 declaredmeta={x['relative']:x for x in root['metadata_allowlist']};ck('metadata_count',len(arc['metadata'])==len(declaredmeta)==12)
 metachecks=[]
 for m in arc['metadata']:
  declared=declaredmeta[m['relative']];ck('metadata_root_declaration',all(m[k]==declared[k] for k in ('source','relative','bytes','sha256')))
  source=Path(m['source']);dest=R/m['destination'];ck('exact_destination',dest==R/STAGE/m['relative'] and source.resolve()==source and dest.resolve()==dest and not source.is_symlink() and not dest.is_symlink());ck('metadata_exact_bytes',source.read_bytes()==dest.read_bytes() and h(dest)==m['sha256'] and dest.stat().st_size==m['bytes'])
  if m['relative'].startswith('attempt01/'):
   ck('metadata_independent_allowlist',ind['files'][m['relative'].removeprefix('attempt01/')]=={'bytes':m['bytes'],'sha256':m['sha256']})
  metachecks.append({'path':m['destination'],'sha256':m['sha256'],'bytes':m['bytes']})
 omittedzero={k:v for k,v in ind['files'].items() if k.endswith('.lock')};ck('only_empty_operational_locks_not_archived',set(omittedzero)=={'.original_run.adapter.lock','original_run/.evaluation.lock'} and all(x['bytes']==0 for x in omittedzero.values()))
 # Log warnings are preserved verbatim and not replaced with an empty log.
 err=R/STAGE/'original_logs/cti-goal-paired-input_3054127.err';logtext=err.read_text();ck('no_real_traceback', 'Traceback (most recent call last)' not in logtext)
 review={'schema':'formal_main_v2','kind':'independent_Goal_exact_raw_archive_review','status':'passed_all_raw_members_and_metadata','job_id':'3054127','blockers':[],'root_raw_review':{'path':str(RP.relative_to(R)),'sha256':RH},'root_archive_manifest':{'path':str(AP.relative_to(R)),'sha256':AH},'independent_terminal_review':{'path':str((D/'terminal_review.json').relative_to(R)),'sha256':h(D/'terminal_review.json')},'all10741blobs_verified':True,'blob_count':len(seen),'blob_bytes':sum(x['bytes'] for x in seen.values()),'compressed_bytes':sum(x['compressed_bytes'] for x in partchecks),'parts':partchecks,'metadata':metachecks,'zero_byte_operational_locks_retained_on_P_not_needed_in_Git':omittedzero,'new_Goal_science_HOLD':True,'original_goal200_HOLD':True,'final_release':False,'scientific_trials_added':0,'old_cause_identified':False,'old_failure_repaired':False,'check_count':sum(counts.values()),'checks_by_category':dict(counts),'archive_extraction_to_disk':False}
 print(json.dumps(out('archive_review.json',review)))
try:main()
except BaseException as e:out('archive_failure_'+str(time.time_ns())+'.json',{'status':'failed_independent_archive_audit','error':str(e),'traceback':traceback.format_exc(),'counts':dict(counts)});raise
