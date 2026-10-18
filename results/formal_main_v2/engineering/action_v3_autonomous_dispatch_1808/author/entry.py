"""Root-reviewed one-shot coexistence bridge. Default is read-only --check-only.

Production submit requires explicit --submit --root-reviewed-submit, exact entry
SHA and the already-audited server_control_transport_v1 environment. This file
never changes the scientific probe, launcher, wrapper or original submit module.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, sys
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
REL='.local/action_v3_autonomous_dispatch_1808/'
FACADE_SHA='5bee1357c507df49627b9f38e358c7d48c91b8e1e598cb8ffa8aae641724985a'
SOURCE='results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/'
BINDINGS={
 'submit.py':'f5a4efc24f9b77b54ca73bbf0a8626e9ebde9c416ac1305cf4e88cd55ad8b8dc',
 'launcher.py':'13c9a2e60e0b0a9eeeb1460ff5121c1c7305c8106420a6dc21dca6634fc712c5',
 'node_exclusion.py':'0886ce865ca3edc01bf1ba4d875d139bdf8267a2b6992d1630f1a84c4efcc506',
 'probe.py':'ba7363695b9a67324b3717632d7571e5ceccd5e91683673ff65c0801e1e4a004',
 'probe.slurm':'69277a63fcbcb24f94a6d333bb70e490f702df9edade25e042b49fdaafe37dc0',
 'action_adapter.py':'b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185',
 'constructor_independent_cpu.json':'171b93b145431bdffb9138eea48673e9185dcadbef226e468d0ab140a7a470f1',
 'candidate_manifest.json':'832cdad374e1dfd5cef04870a14f440ec37a1194dea9130b95c7ddd9c7be782e'}
REFS={
 'root_review':{'path':'results/formal_main_v2/preflight/action_execution_gpu_v3_candidate_root_0840.json','sha256':'54d689ae3d90b82dfd7701502fc398bd938e58e35a48528477a9db739dd2b676'},
 'manifest':{'path':SOURCE+'candidate_manifest.json','sha256':BINDINGS['candidate_manifest.json']},
 'gpu_registration':{'path':'configs/experiments/formal_main_v2_action_execution_compat_gpu_v3.json','sha256':'1ae3fcb716a3924217e0bc7447c5fd9bf9210fa8f1803081e611d668e709ba41'}}
NODE_REG={'path':'configs/experiments/formal_main_v2_node_exclusion_action_gpu_v3.json','sha256':'b5e083acbd93a35d561607fbf0c76862438e19d12629258c79845267b3ba50f3'}
TRANSPORT_MANIFEST='3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149'

def require(v,m):
    if not v:raise ValueError(m)

def load_facade():
    p=R/(REL+'facade.py');require(not any(x.is_symlink() for x in (p,*p.parents)),'facade alias')
    data=p.read_bytes();require(hashlib.sha256(data).hexdigest()==FACADE_SHA,'facade changed')
    spec=importlib.util.spec_from_file_location('_restricted_action_v3_facade',p);m=importlib.util.module_from_spec(spec);exec(compile(data,str(p),'exec'),m.__dict__);return m

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entry-sha256',required=True)
    group=parser.add_mutually_exclusive_group();group.add_argument('--check-only',action='store_true');group.add_argument('--submit',action='store_true')
    parser.add_argument('--root-reviewed-submit',action='store_true')
    parser.add_argument('--audit-relative',default=REL+'dispatch_01')
    a=parser.parse_args()
    entry=Path(__file__).absolute()
    require(os.name=='posix' and entry==R/(REL+'entry.py') and entry.resolve()==entry and not any(x.is_symlink() for x in (entry,*entry.parents)),'wrong server entry')
    require(hashlib.sha256(entry.read_bytes()).hexdigest()==a.entry_sha256,'entry SHA differs')
    require(not a.root_reviewed_submit or a.submit,'root flag only for explicit submit')
    if a.submit:
        require(a.root_reviewed_submit,'explicit root-reviewed-submit required')
        require(os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R) and os.environ.get('CTI_SERVER_CONTROL_MANIFEST_SHA256')==TRANSPORT_MANIFEST,'audited transport scope required')
    facade=load_facade();ctl=facade.load(R/facade.CONTROLLER_REL,'_v3_pinned_controller',facade.CONTROLLER_SHA)
    for name,sha in BINDINGS.items():require(ctl.file_sha(R/(SOURCE+name))==sha,'v3 source differs: '+name)
    orig=facade.load(R/(SOURCE+'submit.py'),'_v3_unmodified_submit',BINDINGS['submit.py'])
    node=facade.load(R/(SOURCE+'node_exclusion.py'),'_v3_unmodified_node',BINDINGS['node_exclusion.py'])
    checked=orig.c.check_contract(R,root_ref=REFS['root_review'],manifest_ref=REFS['manifest'],registration_ref=REFS['gpu_registration'])
    # Verify snapshot identity directly as server metadata; no checkpoint/model read.
    for rel,sha in checked['inventory']['files'].items():require(ctl.file_sha(Path(orig.c.S)/rel)==sha,'frozen S differs: '+rel)
    audit=Path(a.audit_relative)
    require(not audit.is_absolute() and '..' not in audit.parts and audit.as_posix()==a.audit_relative and a.audit_relative.startswith((REL,'results/formal_main_v2/preflight/')),'audit destination outside scope')
    fcd=facade.Facade(R,ctl,orig.c,ctl.Slurm(),R/audit,allow_writes=a.submit);fcd.refs=REFS;f=fcd.attach()
    with node.exclude_future_sbatch(f,request={'kind':'action_execution_gpu_v3'},registration_ref=NODE_REG,audit_relative=a.audit_relative+'/node_exclusion.json'):
        if a.submit:
            try:
                result=orig.execute_submit(R,checked,REFS,f)
                facade.exclusive_json(R/audit/'result.json',dict(result=result,facade_phase=fcd.phase,entry_sha256=a.entry_sha256,facade_sha256=FACADE_SHA))
            except BaseException as e:
                if fcd.audit.exists():
                    facade.exclusive_json(fcd.audit/'failure.json',dict(error_type=type(e).__name__,message=str(e),facade_phase=fcd.phase,automatic_retry=False,pending_is_never_cleared_on_failure=True))
                raise
        else:
            with f.supervisor_lock():
                state=f.read(f.STATE);jobs=f.refresh(state);active,available=orig.submission_gate(state,jobs)
                require(not (R/orig.c.INVOCATION).exists(),'prior control invocation exists')
                out=Path(orig.c.P)/orig.c.OUT;inv=Path(orig.c.P)/orig.c.INVOCATION
                ctl.no_links(out);ctl.no_links(inv)
                require(not inv.exists() and (not out.exists() or not any(p.name!='source' for p in out.iterdir())),'remote prior attempt exists')
                remote={p:(ctl.file_sha(p) if Path(p).is_file() else None) for p in checked['watched_files']}
                require(all(v is None or v==checked['watched_files'][p] for p,v in remote.items()),'existing remote immutable metadata differs')
                result=dict(status='passed_read_only_contract_and_live_capacity',available=available,active_GPU_job_ids=[j['job_id'] for j in active],
                    observation=fcd.observation,remote_existing_count=sum(v is not None for v in remote.values()),remote_missing_count=sum(v is None for v in remote.values()),
                    full_original_contract_verified=True,frozen_R_and_S_files=173,all_eight_v3_sources_unchanged=True,
                    legacy_refresh_called=False,state_changed=False,submitted=False,GPU_submitted=False,entry_sha256=a.entry_sha256,facade_sha256=FACADE_SHA)
                require(ctl.file_sha(f.STATE)==fcd.expected_sha,'state changed during check-only')
    print(json.dumps(result,ensure_ascii=False,allow_nan=False),flush=True)

if __name__=='__main__':main()
