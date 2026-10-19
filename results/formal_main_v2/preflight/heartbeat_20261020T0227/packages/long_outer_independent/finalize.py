"""Freeze the independent CPU/read-only evidence bundle; no runtime permission."""
import importlib.util,sys,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from xml.etree import ElementTree as ET
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/long_action_outer_audit_1827'
path=D/'audit.py'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='e9469a8031343876f959847369d764aa5990d2e74829dddbac2307edaf8b7995'
spec=importlib.util.spec_from_file_location('independent_long1827_finalizer_support',path)
a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
a.watch(__file__);a.watch(path,'e9469a8031343876f959847369d764aa5990d2e74829dddbac2307edaf8b7995')
rec=a.read('.local/long_action_outer_audit_1827/reconstruction.json','b4c0f690894632bf4811247f61445a3c9953f975f061fbd21ead9e1450c3d73e')
a.require(rec['passed_checks']==39 and rec['actual_GPU_runtime_chain_verified'] is False,'wrong reconstruction')
for p,h in rec['read_evidence_sha256'].items():a.watch(p,h)
idx=a.read('.local/long_action_outer_audit_1827/independent_index.json','795839d52918b19d26f13928fb1dce5f7459e30cc8404585b767730b5cf59fd2')
for row in idx['shards']:
 review=a.ref(row['candidate'])
 for key in ('scientific_plan','effective_plan','action_execution_contract','plan_sha256','method_ids'):
  a.require(review[key]==row[key],'per-plan independent identity mismatch '+key)
 a.require(review['actual_GPU_runtime_chain_verified'] is False and review['production_chain_complete'] is True,'scope definition')
 for key in ('scientific_plan','effective_plan','action_execution_contract'):
  a.ref(row[key]);a.watch(a.P/row[key]['path'],row[key]['sha256'])
execution=a.read('.local/long_action_outer_audit_1827/execution_a1.json')
a.require(execution['exit_code']==0,'execution failed')
a.watch('.local/long_action_outer_audit_1827/audit_a1.log',execution['log_sha256'])
xmlpath=a.watch('.local/long_action_outer_audit_1827/checks.xml')
tree=ET.fromstring(xmlpath.read_bytes())
a.require(tree.attrib['tests']=='39' and tree.attrib['failures']=='0' and tree.attrib['errors']=='0' and tree.attrib['skipped']=='0','JUnit mismatch')
author=a.read(a.AUTHOR+'/candidate_review.json','4a92de2908b1c4365d2ab7a8b4053936a69d68169029ef24eb5d9badea36b435')
archive=a.read(a.AUTHOR+'/archive_manifest.json','16543bc948950e2b1bd1279ec587cacc56037163dc655fef973ae87c65536afc')
for row in archive['files']:
 p=a.watch(row['path'],row['sha256']);a.require(p.stat().st_size==row['bytes'],'author archive byte count')
a.require(author['tests']['passed']==42 and author['tests']['failures']==author['tests']['errors']==0,'author test statement')
for key in ('command','log','xml'):a.watch(author['tests'][key]['path'],author['tests'][key]['sha256'])
at=ET.fromstring((R/author['tests']['xml']['path']).read_bytes())
suites=[at] if at.tag=='testsuite' else list(at)
a.require(sum(int(s.attrib['tests']) for s in suites)==42 and sum(int(s.attrib.get('failures','0'))+int(s.attrib.get('errors','0')) for s in suites)==0,'actual author JUnit')
spatial=a.read('results/formal_main_v2/execution/action_spatial_resume_0943/runtime_readiness.json','3e192788730bdfd97115713c332640c3b2de1f380e046ec7d045d274b9e07bb4')
component_refs=spatial['component_reviews'];covered={}
for role,reference in component_refs.items():
 comp=a.ref(reference)
 a.require(comp['kind']=='formal_downstream_action_component_independent_CPU_review' and comp['status']=='passed_CPU_review'
  and comp['component']==role and comp['blockers']==[],'wrong inherited component independent review')
 for p,h in comp['files'].items():
  a.require(p not in covered or covered[p]==h,'component source conflict');covered[p]=h
  a.watch(p,h)
for row in idx['shards']:
 review=a.ref(row['candidate'])
 for p,h in review['runtime_sources'].items():
  if p.startswith(a.PREFIX) and not p.endswith('gateway.py'):
   a.require(covered.get(p)==h,'component CPU coverage missing '+p)
a.watch('results/formal_main_v2/control_transport/long_action_outer_independent_1827_a1.jsonl')
value=dict(schema='formal_main_v2',kind='Long16_action_outer_independent_summary',status='passed_exact_pre_execution_plan_review',
 execution_version='formal-downstream-action-v1',utc=datetime.now(timezone.utc).isoformat(),reviewed_by='train64',
 independent_index=dict(path='.local/long_action_outer_audit_1827/independent_index.json',sha256='795839d52918b19d26f13928fb1dce5f7459e30cc8404585b767730b5cf59fd2'),
 author_review=dict(path=a.AUTHOR+'/candidate_review.json',sha256='4a92de2908b1c4365d2ab7a8b4053936a69d68169029ef24eb5d9badea36b435'),
 author_archive=dict(path=a.AUTHOR+'/archive_manifest.json',sha256='16543bc948950e2b1bd1279ec587cacc56037163dc655fef973ae87c65536afc'),
 root_canonical_publication=dict(path=a.PUB,sha256=a.PINS[a.PUB]),
 independent_checks=39,independent_seconds=rec['elapsed_seconds'],author_checks=42,
 author_checks_not_reexecuted=True,actual_unfiltered_registry_rows=rec['full_registry_rows'],
 real_original_planner_comparisons=8,real_effective_conversions=8,real_inner_wrapper_P_checks=8,
 real_runtime_contract_R_P_checks=2,actual_canonical_R_P_files=24,
 exact_runtime_input_count=len(rec['all_runtime_inputs']),per_pair_trials=200,total_planned_trials=1600,
 unique_development_initial_states_per_method=100,methods=16,original_Long600_GPU_seconds=10531,
 failed_attempts_during_independent_audit=[],blocking_findings_for_exact_pre_execution_plans=[],
 source173_R_S_unchanged=True,seven_runtime_sources_R_P_unchanged=True,legacy_versions_not_relabelled=True,
 inherited_component_reviews=component_refs,inherited_GPU_job_id='3039197',actual_GPU_runtime_chain_verified=False,
 new_trials=0,new_GPU_seconds=0,checkpoint_bytes_read_by_this_audit=False,
 actual_selected_byte_identity_inherited_from_root=a.ROOTCHECK,
 production_status='PENDING_ROOT_READINESS_FULL_WRAPPER_AND_LIVE_SUBMISSION_GATES',
 root_readiness_issued=False,Slurm_queries=0,submissions=0,production_state_writes=0,
 scope_notes=[
  '8 actual full-registry plans, fixed source/provenance/method/checkpoint/panel identities and actual P dependencies reconstructed without replacing any production validator.',
  '39 independent checks are distinct from the author42. Only negative inputs are in-memory synthetic; no synthetic passed root receipt exists.',
  'Per-plan production_chain_complete denotes pre-execution integration closure only, with actual_GPU_runtime_chain_verified=false.',
  'Each nested root/independent review must explicitly match this plan refs, semantic hash and methodIDs; the minimal production validation fields alone do not protect against a cross-plan passed receipt.',
  'Fresh 16 methods do not overlap the historical six and have no legacy prefix. Full22 new-runtime coverage/O2A/freeze/final release remain outside this review.',
  'Root must still sign/readiness/publish all additional metadata, run full unchanged wrapper.verify(P), obtain own reservation and refresh all scheduler/pending/CAS/capacity gates before any single-use submit.'
 ],read_evidence_sha256=a.evidence)
result=a.emit('independent_review.json',value)
a.emit('README.md',('Long16 outer independent audit, server-only.\n\n'
 '39 independent checks passed on actual R/P inputs and original validators; author42 were checked from original evidence, not rerun. '
 'The eight shard receipts bind their own scientific/effective/contract references, plan signature and original methods. '
 'production_chain_complete describes the pre-execution integration closure only. No new GPU chain or root readiness is asserted.\n\n'
 'Root must run full wrapper.verify(P) with genuine exact readiness, then current live transaction/capacity gates. '
 'The old Long600/10531GPU seconds remain original history. Fresh16 trials are1600 plans on100shared initial states, not1600 independent states.\n\n'
 'No production writes, no Slurm calls, no weight/final-value reads. Immutable logs, sources, snapshot and receipts are included in archive_closure.json.\n').encode())
print(json.dumps(dict(independent_review=result,read_refs=len(a.evidence),per_plan_receipts=8)))
