from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,os,subprocess,sys
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0225';G=R/'scripts/ops/formal_action_deployment_posttraining_v1/gateway.py';PIN='4a11a62e817cd96523cd8f06aa0c3c71e12208f1b3a6b487799160915e59ec83'
PINS={'Spatial':('4d81461eddac21c2e847dbb374f3ef6bcc580918bc297ac30774cc2870c9f705','44f5874409a79bfa8912245baf5500a20e5a7e0c928966b7616409ed22b8b83c'),'Object':('83c82bdaa4a61695d0d35b739dde63e88144a2034b9a5f24c10553f75c9254d5','e8dc0fc0302534afa5d4895f19809ef50c4515c541315b0b40b06f525475ec5f')}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(p,raw):
 assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def save(p,v):put(p,(json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode())
def load(p,pin,name):
 assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument('--suite',choices=list(PINS),required=True);a=ap.parse_args();suite=a.suite
prefix='results/formal_main_v2/execution/'+suite.lower()+'_collect_action_v1_20261020T1825';ar={'path':prefix+'/submission_authorization.json','sha256':PINS[suite][0]}
g=load(G,PIN,'rootcollectdispatchgateway');c=load(R/g.CONTROLLER,g.CONTROLLER_SHA,'rootcollectdispatchcontroller')
post=R/('.local/spatial_object_collect_independent_20261020T1825/post_readiness/libero_'+suite.lower()+'_independent_review.json');assert h(post)==PINS[suite][1];rv=read(post)
assert rv['status']=='passed' and rv['kind']=='formal_collect_post_readiness_independent_review' and not rv['blockers'] and rv['authorization']==ar and rv['actual_full_P_wrapper_verifications']==1
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read(sp);ctl=s['autonomous_training_v1'];assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 assert ar['sha256'] not in ctl.get('downstream_reservations_consumed',{})
 assert not any((B/(suite+'_'+x)).exists() for x in ['collect_reservation.json','collect_preflight_stdout.json','collect_submit_stdout.json'])
 auth,e,plan,science,prepared=g.validate_authorization(R,ar);assert rv['effective_plan']==auth['plan'] and rv['prepared_invocation']==auth['prepared_invocation']
 projected=copy.deepcopy(s);projected['autonomous_training_v1']['reserved_GPU_slots']=1;projected['autonomous_training_v1']['reservation_root_record']=auth['root_reservation']
 snap=c.Slurm().observe(s['registered_jobs']);caps,cpus,live_projection=g.capacity_gate(c,projected,snap,auth,plan)
 g.FrozenPlan(R,auth,e,plan,science,prepared).prepare(live_projection);e.unchanged();assert h(sp)==before
 c.atomic_json(sp,projected,expected_sha=before)
 save(B/(suite+'_collect_reservation.json'),{'schema':'formal_main_v2','status':'one_slot_reserved_for_exact_authorization','authorization':ar,'post_readiness_review':{'path':str(post.relative_to(R)),'sha256':h(post)},'reservation':auth['root_reservation'],'capacity':caps,'observation':snap,'state_before':before,'state_after':h(sp),'automatic_retry':False,'utc':datetime.now(timezone.utc).isoformat()})
argv=[sys.executable,'-B',str(G),'--authorization',ar['path'],'--authorization-sha256',ar['sha256'],'--gateway-sha256',PIN]
check=subprocess.run(argv,cwd=R,capture_output=True,timeout=180)
put(B/(suite+'_collect_preflight_stdout.json'),check.stdout);put(B/(suite+'_collect_preflight_stderr.txt'),check.stderr)
assert check.returncode==0,check.stderr.decode()[-4000:]
v=json.loads(check.stdout);assert v['status']=='read_only_checks_passed_not_submitted' and len(v['capacity']['occupied'])<8
print(json.dumps({'suite':suite,'preflight':'passed','occupied_before':len(v['capacity']['occupied'])}),flush=True)
dispatch=subprocess.run(argv+['--submit','--root-reviewed-submit'],cwd=R,capture_output=True,timeout=180)
put(B/(suite+'_collect_submit_stdout.json'),dispatch.stdout);put(B/(suite+'_collect_submit_stderr.txt'),dispatch.stderr)
assert dispatch.returncode==0,dispatch.stderr.decode()[-4000:]
result=json.loads(dispatch.stdout);assert result['status']=='submitted_once'
print(json.dumps({'suite':suite,'status':result['status'],'job_id':result['job']['job_id'],'stage_key':result['job']['stage_key'],'state_sha256':result['state_sha256']}))
