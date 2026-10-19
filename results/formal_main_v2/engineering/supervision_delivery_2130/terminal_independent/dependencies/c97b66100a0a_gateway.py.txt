"""Root-only single CUDA-startup recovery. Default check is read-only."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, copy, hashlib, importlib.util, json, os, re, sys
sys.dont_write_bytecode=True
VERSION='cuda-startup-server-gateway-v1'
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
STATE='results/experiment_supervisor/state.json'
CONTROLLER='scripts/ops/formal_autonomous_training_v1/controller.py'
CONTROLLER_SHA='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
EVIDENCE_SHA='96e5e0a653c2ed884f09f7c3bf1ce19f0664c1665921a183bc351a97f5ff9d87'
ACTIVATION={'path':'configs/experiments/formal_main_v2_autonomous_execution_activation_v2.json','sha256':'7391c3bb17c36f8b0dbce540e28714ac6f721662118ddb7338d7c0288aa0bcef'}
def require(v,m):
    if not v: raise ValueError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':')).encode()+b'\n'
def load(path,name,pin):
    p=Path(path);require(not any(x.is_symlink() for x in (p,*p.parents)),'module symlink')
    raw=p.read_bytes();require(sha(raw)==pin,'module SHA differs: '+str(p))
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec)
    exec(compile(raw,str(p),'exec'),m.__dict__);return m
e=load(Path(__file__).with_name('evidence.py'),'cuda1940_evidence',EVIDENCE_SHA)
def immutable(path,raw):
    p=e.no_links(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
def record(path,value):immutable(path,canonical(value))
def intent_sha(auth):
    value=copy.deepcopy(auth);value.pop('root_reservation',None);return sha(canonical(value))
def source_files(root):
    return {Path(__file__).resolve().relative_to(root).as_posix():sha(Path(__file__).read_bytes()),
            Path(__file__).with_name('evidence.py').resolve().relative_to(root).as_posix():EVIDENCE_SHA}
def validate_authorization(root,reference):
    v=e.Evidence(root);a=v.ref(reference)
    require(a.get('schema')=='formal_main_v2' and a.get('kind')=='cuda_startup_single_recovery_authorization'
        and a.get('version')==VERSION and a.get('status')=='approved_for_exactly_one_original_target_recovery','root typed authorization required')
    jid=a.get('failed_job_id');require(jid in e.CASES,'unregistered failure')
    case=e.CASES[jid]
    require(a.get('original_target')==case[3] and type(a.get('maximum_new_attempts')) is int and a['maximum_new_attempts']==1 and a.get('automatic_retry') is False
        and a.get('resume') is True and a.get('wall_seconds')==12600 and a.get('slurm_time')=='04:00:00'
        and a.get('excluded_nodes')==['gpu4020'] and a.get('source_sha256')==e.SOURCE_SHA,'scope/target differs')
    require(a.get('control_root')==str(R) and a.get('runtime_root')==str(e.P),'server root differs')
    require(a.get('gateway_files')==source_files(root) and a.get('original_recovery_files')==e.FIVE,'implementation closure differs')
    for rel,pin in {**a['gateway_files'],**e.FIVE}.items():v.watch(rel,pin)
    require(a.get('canonical_publication')==e.PUBLICATION and a.get('node_exclusion')==e.NODE,'wrong root publication/node exclusion')
    v.ref(e.PUBLICATION);node=v.ref(e.NODE)
    require(node.get('status')=='reviewed_for_future_explicit_requests' and node.get('automatic_retry') is False,'node exclusion not approved')
    ind=v.ref(a['independent_review'])
    require(ind.get('schema')=='formal_main_v2' and ind.get('kind')=='cuda_startup_server_recovery_gateway_independent_CPU_review'
        and ind.get('status')=='passed_CPU_review','new typed independent CPU review required')
    require(all(ind.get('files',{}).get(k)==x for k,x in a['gateway_files'].items()),'independent review does not cover current source')
    require(a.get('controller_activation')==ACTIVATION and re.fullmatch('[1-9][0-9]*',a.get('controller_job_id','')),'controller identity differs')
    v.ref(ACTIVATION);v.watch(CONTROLLER,CONTROLLER_SHA)
    reservation=v.ref(a['root_reservation'])
    require(reservation.get('schema')=='formal_main_v2' and reservation.get('kind')=='root_CUDA_recovery_GPU_slot_reservation'
        and reservation.get('status')=='approved_for_named_single_recovery' and type(reservation.get('reserved_slots')) is int and reservation['reserved_slots']==1
        and reservation.get('capacity_limit_all_GPU_modes')==8 and reservation.get('controller_job_id')==a['controller_job_id']
        and reservation.get('failed_job_id')==jid and reservation.get('original_target')==case[3]
        and reservation.get('authorization_path')==reference['path'] and reservation.get('authorization_intent_sha256')==intent_sha(a)
        and reservation.get('automatic_retry') is False,'CUDA reservation ownership differs')
    require(a.get('final_release_authorized') is False and a.get('continuous5000_admission_authorized') is False,'scope expansion')
    v.ref(a['repair_record']);v.ref(a['canonical_failure_review'])
    return a,v

def capacity_gate(c,state,snapshot,a):
    require(state.get('pending_submission') is None and 'pending_submission' in state,'unresolved pending submission')
    jobs=state['registered_jobs'];ids=[str(j['job_id']) for j in jobs]
    require(len(ids)==len(set(ids)) and all(re.fullmatch('[1-9][0-9]*',x) for x in ids),'registry IDs differ/duplicate')
    require(set(snapshot['rows'])==set(ids) and set(snapshot['queue'])<=set(ids),'registered accounting missing/foreign')
    ctl=state.get('autonomous_training_v1',{})
    require(ctl.get('activation')==a['controller_activation'] and ctl.get('activation_sha256')==a['controller_activation']['sha256']
        and ctl.get('controller_job_id')==a['controller_job_id'],'different controller owns state')
    require(ctl.get('root_submission_hold') is None,'root hold active')
    require(type(ctl.get('reserved_GPU_slots')) is int and ctl['reserved_GPU_slots']==1
        and ctl.get('reservation_root_record')==a['root_reservation'],'dedicated CUDA reservation missing')
    caps=c.capacity(jobs,snapshot,a['controller_job_id'])
    require(not caps['unknown'] and not caps['findings'],'uncertain scheduler: '+json.dumps(caps,sort_keys=True))
    require(len(caps['occupied'])<8,'all eight GPU slots occupied')
    confirmed={str(j['job_id']) for j in jobs if j.get('gpus')==0 and snapshot['rows'][str(j['job_id'])]['gpus']==0}
    require(a['controller_job_id'] in confirmed and snapshot['rows'][a['controller_job_id']]['status']=='RUNNING','controller not confirmed CPU0 running')
    require(all(j.get('experiment')=='formal_main_v2' for j in jobs if str(j['job_id']) in caps['occupied']),'foreign active registered experiment')
    case=e.CASES[a['failed_job_id']];key=f'{case[0]}_k{case[1]}_seed23'
    require(key not in caps['active_pairs'],'failed pair already active')
    projection=[]
    for j in jobs:
        if str(j['job_id']) in confirmed:continue
        item=copy.deepcopy(j);row=snapshot['rows'][str(j['job_id'])]
        if item.get('experiment')=='formal_main_v2':
            item.update({k:row[k] for k in ('status','exit_code','elapsed_seconds','allocation','node')})
        projection.append(item)
    projected=[str(j['job_id']) for j in projection if j.get('experiment')=='formal_main_v2' and c.state_name(j['status']) not in c.TERMINAL]
    require(set(projected)==set(caps['occupied']),'CPU0 projection lost GPU/unknown occupancy')
    return projection,caps,sorted(confirmed)

def sbatch_argv(plan,auth,ref):
    inv=plan['invocation'];raw=canonical(inv);checksum=sha(raw)
    exports='ALL,SOURCE_ROOT='+inv['source_root']+',INVOCATION='+str(e.P/plan['invocation_relative'])
    if inv['suite']=='libero_object':exports+=',INVOCATION_SHA256='+checksum
    comment='cti-cuda-recovery-v1:'+ref['sha256']
    argv=['sbatch','--parsable','--no-requeue','--time=04:00:00','--exclude=gpu4020','--comment='+comment,'--export='+exports,plan['wrapper']]
    require(auth['original_target']==inv['segment_end'],'sbatch target differs')
    return argv,raw,checksum,comment
def parse_ack(result,existing_ids):
    require(result.returncode==0,'sbatch failed or response uncertain')
    m=re.fullmatch(r'([1-9][0-9]*)(?:;[A-Za-z0-9_.-]+)?\n?',result.stdout)
    require(m is not None,'ambiguous sbatch output')
    jid=m.group(1);require(jid not in existing_ids,'old/duplicate job ID returned')
    return jid

class Gateway:
    """Injected dependencies are for CPU tests; CLI binds only pinned modules."""
    def __init__(self,root,c,slurm,science,io,authorization,authorization_ref,auth_evidence):
        self.root=Path(root);self.c=c;self.slurm=slurm;self.science=science;self.io=io
        self.auth=authorization;self.ref=authorization_ref;self.auth_evidence=auth_evidence
        self.path=self.root/STATE
        self.audit=self.root/f"results/formal_main_v2/startup_recoveries/{authorization['failed_job_id']}/{authorization_ref['sha256']}"
    def _cas(self,state):
        self.c.atomic_json(self.path,state,self.expected)
        self.expected=self.c.file_sha(self.path)
    def _job(self,jid,plan,invsha,argv):
        inv=plan['invocation']
        j=dict(job_id=jid,name='cti-formal',experiment='formal_main_v2',mode='train',stage_key=inv['stage_key'],
            suite=inv['suite'],visual_tokens=plan['args']['budget'],training_seed=23,segment_end=inv['segment_end'],
            status='SUBMITTED',gpus=1,source_root=inv['source_root'],source_sha256=inv['source_sha256'],
            run_root=str(e.P/plan['proof']['output_relative']),invocation=plan['invocation_relative'],invocation_sha256=invsha,
            submitted_utc=inv['registered_utc'],purpose='One root-authorized original-target recovery of a retained CUDA startup failure',
            startup_recovery=dict(version=VERSION,failed_job_id=self.auth['failed_job_id'],authorization=self.ref,
                canonical_failure_review=self.auth['canonical_failure_review'],repair_record=self.auth['repair_record'],
                maximum_new_attempts=1,automatic_retry=False,actual_sbatch_argv=argv))
        if 'runtime_compatibility' in inv:j['runtime_compatibility']=copy.deepcopy(inv['runtime_compatibility'])
        return j
    def run(self,*,submit=False):
        lock=self.path.parent/'.writer.lock'
        require(lock.is_file(),'shared writer lock missing; never create/rebind it')
        with self.c.exclusive_lock(lock):
            self.expected=self.c.file_sha(self.path);state=self.c.read_json(self.path)
            require(self.c.file_sha(self.path)==self.expected,'state changed during initial read')
            baseline=copy.deepcopy(state)
            require(not self.audit.exists(),'prior recovery audit exists; inspect, never repeat')
            snapshot=self.slurm.observe(state['registered_jobs'])
            projection,caps,cpus=capacity_gate(self.c,state,snapshot,self.auth)
            plan=self.science.prepare(state,projection,self.auth)
            argv,raw,invsha,comment=sbatch_argv(plan,self.auth,self.ref)
            require(not (self.root/plan['invocation_relative']).exists(),'local invocation exists; inspect unknown publication')
            live=self.io.preflight(plan)
            self.science.e.unchanged();self.auth_evidence.unchanged()
            require(self.c.file_sha(self.path)==self.expected and state==baseline,'state changed outside writer transaction')
            # Fresh occupancy after potentially large read-only SHA work.
            fresh=self.slurm.observe(state['registered_jobs'])
            _,caps,cpus=capacity_gate(self.c,state,fresh,self.auth)
            result=dict(schema='formal_main_v2',kind='cuda_startup_recovery_preflight',version=VERSION,
                status='read_only_checks_passed_not_submitted',failed_job_id=self.auth['failed_job_id'],
                authorization=self.ref,source_sha256=e.SOURCE_SHA,original_target=self.auth['original_target'],
                state_sha256=self.expected,full_registered_jobs=state['registered_jobs'],scheduler_observation=fresh,
                capacity=caps,confirmed_CPU0=cpus,original_scientific_invocation=plan['invocation'],
                invocation_relative=plan['invocation_relative'],invocation_sha256=invsha,actual_sbatch_argv=argv,
                server_preflight=live,read_evidence_sha256={**self.science.e.hashes,**self.auth_evidence.hashes},
                retained_failed_status='FAILED',blocked_pairs_cleared=False,continuous5000_admission=False)
            if not submit:return result
            self.audit.mkdir(parents=True,exist_ok=False)
            record(self.audit/'preflight.json',result)
            pending=dict(schema='formal_main_v2',kind='cuda_startup_recovery_pending',version=VERSION,
                status='prepared_before_invocation_publication',stage_key=plan['invocation']['stage_key'],
                failed_job_id=self.auth['failed_job_id'],original_target=self.auth['original_target'],
                authorization=self.ref,invocation=plan['invocation_relative'],invocation_sha256=invsha,
                request_token=comment,actual_sbatch_argv=argv,utc=plan['invocation']['registered_utc'],retry_permitted=False,
                requested_gpus=1,audit_relative=self.audit.relative_to(self.root).as_posix())
            state['pending_submission']=pending
            self._cas(state)  # durable before any invocation publication or sbatch
            try:
                immutable(self.root/plan['invocation_relative'],raw)
                self.io.publish(plan,raw)
                self.science.e.unchanged();self.auth_evidence.unchanged()
                require(self.c.file_sha(self.path)==self.expected,'state drift before sbatch')
                answer=self.slurm.submit(argv)
                record(self.audit/'sbatch_result.json',dict(returncode=answer.returncode,stdout=answer.stdout,stderr=answer.stderr,actual_sbatch_argv=argv))
                jid=parse_ack(answer,{str(j['job_id']) for j in state['registered_jobs']})
                pending.update(status='submitted_identifier_observed',known_job_id=jid)
                self._cas(state)
                job=self._job(jid,plan,invsha,argv)
                record(self.root/f'results/formal_main_v2/submissions/{jid}.json',job)
                state['registered_jobs'].append(job);state['pending_submission']=None
                state['current_round_cost']['registered_jobs']=sum(j.get('experiment')=='formal_main_v2' for j in state['registered_jobs'])
                control=state['autonomous_training_v1'];control['reserved_GPU_slots']=0
                control.setdefault('cuda_recovery_reservations_consumed',{})[self.ref['sha256']]=dict(job_id=jid,reservation=self.auth['root_reservation'],failed_job_id=self.auth['failed_job_id'])
                tracking=state['formal_main_progress']['parallel_execution']['pair_tracking']
                case=e.CASES[self.auth['failed_job_id']];key=f'{case[0]}_k{case[1]}_seed23'
                require(key in tracking,'missing original pair tracking')
                tracking[key].update(active_job_id=jid,segment_target=self.auth['original_target'],latest_startup_recovery_review=self.auth['canonical_failure_review']['path'],latest_startup_recovery_repair=self.auth['repair_record']['path'])
                state['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=len(caps['occupied'])+1
                require(state['registered_jobs'][:-1]==baseline['registered_jobs'],'historical registry changed')
                require(control.get('blocked_pairs')==baseline['autonomous_training_v1'].get('blocked_pairs'),'failed blocks changed')
                self._cas(state)
                record(self.audit/'committed.json',dict(status='submitted_once',job=job,state_sha256=self.expected,reservation_consumed=True,retry_permitted=False,continuous5000_admission=False))
                return dict(status='submitted_once',job=job,state_sha256=self.expected)
            except BaseException as exc:
                # Do not clear pending, edit FAILED history, or resend after any uncertainty.
                try:record(self.audit/'failed_transaction.json',dict(status='stopped_no_automatic_retry',error_type=type(exc).__name__,error=str(exc),state_sha256=self.c.file_sha(self.path),retry_permitted=False))
                except BaseException:pass
                raise

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--authorization',required=True);ap.add_argument('--authorization-sha256',required=True)
    ap.add_argument('--gateway-sha256',required=True);ap.add_argument('--submit',action='store_true')
    ap.add_argument('--root-reviewed-submit',action='store_true');args=ap.parse_args()
    require(sha(Path(__file__).read_bytes())==args.gateway_sha256,'gateway SHA differs')
    require(Path.cwd().resolve()==R,'must execute from server control root')
    require(args.submit==args.root_reviewed_submit,'explicit two-part root submit confirmation required')
    ref=dict(path=args.authorization,sha256=args.authorization_sha256)
    auth,ev=validate_authorization(R,ref)
    c=load(R/CONTROLLER,'cuda1940_pinned_controller',CONTROLLER_SHA)
    run=Gateway(R,c,c.Slurm(),e.RecoveryScience(R),e.NativeIO(),auth,ref,ev)
    print(json.dumps(run.run(submit=args.submit),ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
