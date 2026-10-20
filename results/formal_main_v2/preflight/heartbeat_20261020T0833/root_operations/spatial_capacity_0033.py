from pathlib import Path
import json,hashlib,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
g=load('scripts/ops/formal_spatial_cuda_continuous_admission_v2/gateway.py','4f552abcc05d72ff84975e360ea28a624a4744febb8518e2fc71839fe47d5864','spatial0033capacity')
c=g.load(R/g.CONTROLLER,g.CONTROLLER_SHA,'spatial0033capacityctl')
d=g.load(R/g.IDENTITY,g.IDENTITY_SHA,'spatial0033capacityidentity')
ref=dict(path='configs/experiments/formal_main_v2_spatial_cuda_continuous_3043399_v2.json',sha256='1cdb14995f275d03557d86be1b565f615a005d911b994ce8c17a3d229e989411')
auth,e=g.validate_authorization(R,ref)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=c.read_json(R/g.a.STATE);before=h(R/g.a.STATE);snap=c.Slurm(timeout=45).observe(state['registered_jobs'])
 cap=c.capacity(state['registered_jobs'],snap,auth['controller_job_id'])
 assert not cap['unknown'] and not cap['findings'] and state['pending_submission'] is None
 for j in state['registered_jobs']:
  jid=str(j['job_id']);d.check_observed_identity(j,snap['rows'][jid],snap['queue'].get(jid),c.TERMINAL)
 owner=g.controller_owner(R,state,snap,auth);e.unchanged()
 reserved=state['autonomous_training_v1']['reserved_GPU_slots'];assert len(cap['occupied'])+reserved<=8
 target=R/'results/formal_main_v2/preflight/heartbeat_20261020T0833/Spatial_v2_capacity_decision.json'
 record=dict(status='ready_wait_for_next_scheduled_capacity' if len(cap['occupied'])+reserved==8 else 'spare_capacity_requires_fresh_gateway',capacity=cap,reserved=reserved,scheduler=snap,owner=owner,authorization=ref,submission_attempted=False,source_and_raw_preflight='Spatial_v2_root_publication_and_prepare.json',state_unchanged_sha256=before)
 assert h(R/g.a.STATE)==before
 with target.open('x') as f:json.dump(record,f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(dict(status=record['status'],active=len(cap['occupied']),reserved=reserved,receipt=target.relative_to(R).as_posix(),sha256=h(target))))
