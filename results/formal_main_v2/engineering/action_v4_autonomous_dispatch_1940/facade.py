"""Restricted supervisor facade; frozen scientific submitter is never edited.

The compatibility module retains frozen supervisor __file__ only for the existing
node adapter identity anchor. Its read/write/lock/refresh names are explicitly
rebound here; this implementation is separately SHA pinned by entry.py.
"""
from contextlib import contextmanager
from pathlib import Path
import copy, hashlib, importlib.util, json, os, re, subprocess

CONTROLLER_REL='scripts/ops/formal_autonomous_training_v1/controller.py'
CONTROLLER_SHA='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
SUPERVISOR_REL='scripts/formal_supervisor.py'
SUPERVISOR_SHA='3e0786da690552356bbe2f56458fe19e88c90b4de079211dc652d655fe3c2e95'
RESERVATION={'path': 'results/formal_main_v2/preflight/action_execution_gpu_v4_slot_reservation_1940.json', 'sha256': '90ec791baeac23aeb3facc909cd95f6d7db0345ab76ed1f99c7f6f10211636a5'}
ACTIVATION={'path':'configs/experiments/formal_main_v2_autonomous_execution_activation_v2.json','sha256':'7391c3bb17c36f8b0dbce540e28714ac6f721662118ddb7338d7c0288aa0bcef'}
COORDINATOR='3034538'


def require(value,message):
    if not value: raise ValueError(message)


def load(path,name,sha):
    path=Path(path)
    require(not any(x.is_symlink() for x in (path,*path.parents)), 'module symlink')
    data=path.read_bytes(); require(hashlib.sha256(data).hexdigest()==sha,'pinned source differs: '+str(path))
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    exec(compile(data,str(path),'exec'),m.__dict__)
    return m


def exclusive_json(path,value):
    p=Path(path);require(not any(x.is_symlink() for x in (p,*p.parents)),'receipt symlink')
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as out:
        out.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode());out.flush();os.fsync(out.fileno())
    fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


class Facade:
    """Exactly one original execute_submit transaction, no retries or legacy refresh."""
    def __init__(self,root,controller,contract,slurm,audit_root,*,allow_writes=False):
        self.root=controller.no_links(root);self.c=controller;self.contract=contract;self.slurm=slurm
        self.state_path=self.root/'results/experiment_supervisor/state.json'
        self.audit=controller.no_links(audit_root)
        require(self.audit.is_relative_to(self.root),'audit outside project')
        self.allow_writes=allow_writes;self.locked=False;self.phase='unread';self.observation=None
        self.receipt_written=False;self.gate_jobs=None
    def attach(self):
        f=load(self.root/SUPERVISOR_REL,'_v4_supervisor_explicit_facade',SUPERVISOR_SHA)
        require(f.ROOT==self.root and f.STATE==self.state_path and f.P==self.contract.P and f.H==self.contract.H,'supervisor identity differs')
        # Explicit compatibility rebinding, not a claim these functions are frozen.
        for name in ('supervisor_lock','read','refresh','write'):setattr(f,name,getattr(self,name))
        self.module=f;return f
    @contextmanager
    def supervisor_lock(self):
        require(not self.locked and self.phase=='unread','facade cannot be reused')
        require((self.state_path.parent/'.writer.lock').is_file(),'shared writer lock missing; check-only never creates it')
        with self.c.exclusive_lock(self.state_path.parent/'.writer.lock'):
            self.locked=True
            if self.allow_writes:
                require(not self.audit.exists(),'prior dispatch audit exists; inspect, never retry')
                self.audit.mkdir(parents=True,exist_ok=False)
            try: yield
            finally: self.locked=False
    def read(self,path):
        require(self.locked and Path(path)==self.state_path and self.phase=='unread','only initial locked state read allowed')
        before=self.c.file_sha(path);value=self.c.read_json(path)
        require(self.c.file_sha(path)==before,'state changed during read')
        self.expected_sha=before;self.baseline=copy.deepcopy(value);self.phase='initial';return value
    def _reservation(self,state):
        require(state.get('pending_submission') is None and 'pending_submission' in state,'unresolved pending submission')
        control=state.get('autonomous_training_v1',{})
        require(control.get('controller_job_id')==COORDINATOR and control.get('activation')==ACTIVATION,'controller identity differs')
        require(control.get('root_submission_hold') is None,'root submission hold active')
        require(type(control.get('reserved_GPU_slots')) is int and control['reserved_GPU_slots']==1 and control.get('reservation_root_record')==RESERVATION,'dedicated one-GPU reservation missing')
        for ref in (RESERVATION,ACTIVATION):
            require(self.c.file_sha(self.root/ref['path'])==ref['sha256'],'root reservation/activation SHA differs')
        reg=self.c.read_json(self.root/RESERVATION['path'])
        require(reg.get('kind')=='root_engineering_GPU_slot_reservation' and reg.get('reserved_slots')==1 and reg.get('capacity_limit_all_GPU_modes')==8 and reg.get('controller_job_id')==COORDINATOR and reg.get('automatic_retry') is False,'reservation scope differs')
        require(reg.get('registration')==self.refs['gpu_registration'],'reservation names different experiment')
    def refresh(self,state):
        require(self.locked and self.phase=='initial' and state==self.baseline,'refresh requires unchanged locked state')
        self._reservation(state)
        jobs=state['registered_jobs']
        require(not any(j.get('stage_key')==self.contract.STAGE for j in jobs),'single-attempt stage already registered')
        snapshot=self.slurm.observe(jobs)  # ALL registered experiments, including CPU0.
        caps=self.c.capacity(jobs,snapshot,COORDINATOR)
        confirmed_cpu=[str(j['job_id']) for j in jobs if j.get('gpus')==0 and snapshot['rows'].get(str(j['job_id']),{}).get('gpus')==0]
        self.observation=dict(kind='all_registered_Slurm_observation_for_action_v4',state_sha256=self.expected_sha,
            queried_job_ids=[str(j['job_id']) for j in jobs],registered_jobs=copy.deepcopy(jobs),snapshot=snapshot,
            capacity=caps,confirmed_CPU_zero_job_ids=confirmed_cpu,reservation=RESERVATION,
            old_refresh_called=False,evidence_filtered=False,scientific_trials=0,GPU_submitted=False)
        if self.allow_writes:exclusive_json(self.audit/'scheduler_observation.json',self.observation)
        require(not caps['unknown'] and not caps['findings'],'uncertain scheduler: '+json.dumps(caps,sort_keys=True))
        require(COORDINATOR in confirmed_cpu and snapshot['rows'][COORDINATOR]['status']=='RUNNING','registered CPU controller is not confirmed running')
        require(all(j.get('experiment')=='formal_main_v2' for j in jobs if str(j['job_id']) in caps['occupied']),'active foreign experiment blocks this bounded gate')
        # Projection only adapts the old gate; complete registry/evidence stays intact.
        projection=[]
        for j in jobs:
            if j.get('experiment')!='formal_main_v2' or str(j['job_id']) in confirmed_cpu:continue
            row=copy.deepcopy(j);row['status']=snapshot['rows'][str(j['job_id'])]['status'];projection.append(row)
        active=[str(j['job_id']) for j in projection if j['status'] not in self.c.TERMINAL]
        require(set(active)==set(caps['occupied']) and len(active)==len(caps['occupied']),'capacity projection disagrees')
        self.gate_jobs=projection;self.occupied=list(caps['occupied'])
        require(state==self.baseline,'read-only refresh changed state')
        return projection
    def _expected_job(self,pending):
        k=self.contract;now=pending['utc'];jid=pending['known_job_id']
        return dict(job_id=jid,name='cti-action-exec16',experiment='formal_main_v2',mode='engineering',
            stage_key=k.STAGE,suite=None,suites=list(k.SUITES),visual_tokens=None,training_seed=17,segment_end=None,
            status='SUBMITTED',gpus=1,source_root=k.S,source_sha256=k.SOURCE_SHA,
            run_root=k.P+'/'+k.OUT+'/'+jid,invocation=k.INVOCATION,invocation_sha256=pending['invocation_sha256'],
            submitted_utc=now,maximum_attempts=1,automatic_retry=False,wall_limit_seconds=3600,
            expected_engineering_cells=16,scientific_trials=0,final_states_opened=False,
            purpose='Fixed four-suite sixteen-cell action-execution engineering acceptance; no success-rate result or automatic failed-Object-trial replay')
    def write(self,path,value):
        require(self.locked and self.allow_writes,'write outside explicit submit transaction')
        require(self.c.file_sha(self.state_path)==self.expected_sha,'state changed outside writer transaction')
        path=Path(path)
        if path!=self.state_path:
            require(self.phase=='observed' and not self.receipt_written,'unexpected job receipt write')
            job=self._expected_job(self.baseline['pending_submission'])
            require(path==self.root/(self.contract.BASE+'submissions/'+job['job_id']+'.json') and value==job,'job receipt identity differs')
            exclusive_json(path,value);self.receipt_written=True;return
        expected=copy.deepcopy(self.baseline);normalized=None
        if self.phase=='initial':
            require(self.gate_jobs is not None and len(self.occupied)<8,'unobserved/full capacity')
            pending=value.get('pending_submission',{})
            require(type(pending) is dict and set(pending)=={'stage_key','invocation','invocation_sha256','status','utc'},'prepared pending keys differ')
            require(pending['stage_key']==self.contract.STAGE and pending['invocation']==self.contract.INVOCATION and pending['status']=='prepared_before_invocation_publication' and re.fullmatch('[0-9a-f]{64}',pending['invocation_sha256']) and isinstance(pending['utc'],str),'prepared pending identity differs')
            expected['pending_submission']=copy.deepcopy(pending);next_phase='prepared'
        elif self.phase=='prepared':
            pending=value.get('pending_submission',{});new=copy.deepcopy(self.baseline['pending_submission'])
            jid=pending.get('known_job_id','')
            require(type(jid) is str and re.fullmatch('[0-9]+',jid) and jid not in {str(j['job_id']) for j in expected['registered_jobs']},'invalid/duplicate submitted ID')
            new.update(status='submitted_identifier_observed',known_job_id=jid);expected['pending_submission']=new;next_phase='observed'
        elif self.phase=='observed':
            require(self.receipt_written,'job receipt not durable')
            job=self._expected_job(self.baseline['pending_submission'])
            expected['registered_jobs'].append(job);expected['pending_submission']=None
            expected['current_round_cost']['registered_jobs']=len(self.gate_jobs)+1  # Exact original submitter output, then corrected below.
            expected['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=len(self.occupied)+1
            expected['updated_utc']=job['submitted_utc'];next_phase='committed'
            normalized=copy.deepcopy(expected)
            normalized['current_round_cost']['registered_jobs']=sum(j.get('experiment')=='formal_main_v2' for j in normalized['registered_jobs'])
            control=normalized['autonomous_training_v1'];control['reserved_GPU_slots']=0
            control['reservation_consumed_by_job']=dict(job_id=job['job_id'],reservation=RESERVATION,utc=job['submitted_utc'],reason='v4_job_durably_registered_in_same_writer_CAS_transaction')
        else:raise ValueError('unexpected state write phase')
        require(value==expected,'state change outside exact v4 transaction whitelist')
        self._reservation(self.baseline) if self.phase=='initial' else None
        out=normalized if normalized is not None else expected
        self.c.atomic_json(self.state_path,out,self.expected_sha)
        self.expected_sha=self.c.file_sha(self.state_path);self.baseline=copy.deepcopy(out);self.phase=next_phase
        exclusive_json(self.audit/('state_commit_'+next_phase+'.json'),dict(kind='action_v4_restricted_state_CAS_commit',phase=next_phase,state_sha256=self.expected_sha,
            reservation=RESERVATION,pending=out['pending_submission'],formal_registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in out['registered_jobs']),
            compatibility_projection_registered_jobs=len(self.gate_jobs),preserved_other_autonomous_fields=True))
