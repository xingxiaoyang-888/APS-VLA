"""UNEXECUTED root-only SERVER integration candidate for the reviewed v3 candidate.

Required caller assertion (--root-approve-cpu-registration): the human-authorized
root coordinator has actually reviewed this script, the exact independent CPU
receipt, the node exclusion scope and the new single-attempt GPU registration.
This script records that caller's decision; it is not an independent reviewer.
No GPU success, release, SSH/upload, Slurm, state mutation or Git action occurs.

Example, only after root has made those decisions:
  python -B .local/action_execution_gpu_v3_root_integration_server_v1.py \
    --entry-sha256 <reviewed server entry SHA> \
    --independent-review <new-v3-raw-independent.json> \
    --independent-sha256 <exact-SHA> --root-approve-cpu-registration

All destinations must be absent. A partial/error result is retained for manual
root inspection; this script has no overwrite, retry or resume option.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
RUNTIME_ROOT = '/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA'
SNAPSHOT_ROOT = RUNTIME_ROOT + '/snapshots/formal_main_v2_run_564be0995e'
INSTALLED_ENTRY = '.local/action_execution_gpu_v3_root_integration_server_v1.py'
CANDIDATE_ENTRY = Path('/share/home/u15016/XXY_CVPR/CTI-VLA/storage_migration_candidates/action_gpu_v3_server_entry_v1/entry.py')
MIGRATION_BINDINGS = {
    'SERVER_WORKSPACE.md': 'fe43ae998a45bc749b3de1acbb8841d5b413962b59b05f62284e3f503a9baf62',
    'docs/服务器工作区与GitHub同步.md': 'a871dbefb420ac06ad4818fbf85116ae9db243839911afff999ebf9b49e83854',
    '.local/action_execution_gpu_v3_root_integration_0840.py': '135f454e645b0f73c636b53487acd4b7324b5638f38b901eb2fda207dbc85862',
}
sys.dont_write_bytecode = True
BASE = 'results/formal_main_v2/'
CANDIDATE = '.local/action_execution_gpu_v3_0840/'
STAGE = 'formal_main_v2_action_execution_compat_gpu_v3'
SOURCE = BASE + 'engineering/' + STAGE + '/source/'
AUTHOR_INPUT = CANDIDATE + 'candidate_review.json'
AUTHOR_SHA = '6d1014cdf837e9f391a08a5ee8a6bc43ed0a6b4c8ca8477f8a98c768c67cbf8a'
INDEPENDENT_SHA = '82167dfb3b61b1267ba537c45bc49d51b63e3ce5a437bc51bb0cf864638fc935'
AUTHOR = BASE + 'preflight/action_execution_gpu_v3_candidate_author_0840.json'
AUDIT = BASE + 'preflight/action_execution_gpu_v3_registration_independent_0840.json'
TYPED = BASE + 'preflight/action_execution_gpu_v3_candidate_independent_0840.json'
REVIEW = BASE + 'preflight/action_execution_gpu_v3_candidate_root_0840.json'
REG = 'configs/experiments/' + STAGE + '.json'
NODE = 'configs/experiments/formal_main_v2_node_exclusion_action_gpu_v3.json'
CHECK = BASE + 'preflight/action_execution_gpu_v3_server_check_only_v1.json'
SCRIPT_ARCHIVE = BASE + 'preflight/action_execution_gpu_v3_root_integration_server_v1.py.txt'
INVENTORY = BASE + 'source/formal_main_v2_run_564be0995e.json'
INVENTORY_SHA = '5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
EXPECTED = {
    'probe.py': ('ba7363695b9a67324b3717632d7571e5ceccd5e91683673ff65c0801e1e4a004', 47596),
    'launcher.py': ('13c9a2e60e0b0a9eeeb1460ff5121c1c7305c8106420a6dc21dca6634fc712c5', 21963),
    'probe.slurm': ('69277a63fcbcb24f94a6d333bb70e490f702df9edade25e042b49fdaafe37dc0', 2653),
    'submit.py': ('f5a4efc24f9b77b54ca73bbf0a8626e9ebde9c416ac1305cf4e88cd55ad8b8dc', 12803),
    'action_adapter.py': ('b8a1632e1a67d75d56f3866345b07634b8efae4fc4c1f2928feea64cb3728185', 24228),
    'constructor_independent_cpu.json': ('171b93b145431bdffb9138eea48673e9185dcadbef226e468d0ab140a7a470f1', 39458),
    'node_exclusion.py': ('0886ce865ca3edc01bf1ba4d875d139bdf8267a2b6992d1630f1a84c4efcc506', 14757),
    'candidate_manifest.json': ('832cdad374e1dfd5cef04870a14f440ec37a1194dea9130b95c7ddd9c7be782e', 75668),
}
INDEPENDENT_TYPE = dict(schema='formal_main_v2',
    kind='action_execution_GPU_v3_candidate_independent_CPU_review',
    version='action-execution-gpu-v3-independent-0840-v1',
    status='passed_CPU_independent_candidate_pending_publication_root_registration_and_GPU')
PANELS = frozenset('configs/manifests/formal_main_v2/' + suite + '/initial_states/development.json'
    for suite in ('libero_10', 'libero_spatial', 'libero_object', 'libero_goal'))
SYNTHETIC_STATE = CANDIDATE + 'pytest_a1/synthetic_v3_CPU_only0/results/experiment_supervisor/state.json'
seen = {}


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe(relative, *, synthetic=False):
    require(type(relative) is str and relative and '\\' not in relative and ':' not in relative, 'invalid project path')
    p = PurePosixPath(relative)
    require(not p.is_absolute() and p.as_posix() == relative and '..' not in p.parts, 'noncanonical project path')
    parts = [part.lower() for part in p.parts]
    source = p.suffix == '.py' and p.parts[0] in {'src','scripts','tests'}
    state_name = any(stem in part for part in parts for stem in ('init_state','initial_state','final_state','test_state'))
    require(not any('sealed' in part or part in {'weights','checkpoints','test','final'} for part in parts)
        and 'final_registry' not in relative.lower()
        and p.suffix.lower() not in {'.pt','.pth','.bin','.ckpt','.safetensors','.npz','.npy','.pkl','.pickle','.init','.pruned_init'}
        and (not state_name or source or relative in PANELS)
        and p.name.lower() != 'panel.json'
        and (p.name.lower() != 'state.json' or (synthetic and relative == SYNTHETIC_STATE)),
        'forbidden state/weight/evidence path: ' + relative)
    path = ROOT / relative
    require(path.resolve().is_relative_to(ROOT.resolve()) and path.resolve() == path.absolute(), 'path escape/alias')
    require(not any(x.is_symlink() or (getattr(x.lstat(),'st_file_attributes',0) & 0x400)
        for x in (path,*path.parents) if x.exists()), 'symlink/reparse path')
    return path


def read_bytes(relative, expected=None, *, synthetic=False):
    data = safe(relative,synthetic=synthetic).read_bytes()
    value = digest(data)
    require(expected is None or value == expected, 'evidence SHA differs: ' + relative)
    require(relative not in seen or seen[relative] == value, 'evidence changed during reads: ' + relative)
    seen[relative] = value
    return data


def read(relative, expected=None, **kwargs):
    return json.loads(read_bytes(relative,expected,**kwargs))


def encoded(value):
    return (json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()


def ref(relative, data=None):
    data = read_bytes(relative) if data is None else data
    return dict(path=relative,sha256=digest(data))


def check_evidence_map(value, *, exact_known_synthetic=False):
    require(type(value) is dict and value, 'missing evidence mapping')
    for path, checksum in value.items():
        require(type(checksum) is str and re.fullmatch('[0-9a-f]{64}',checksum), 'invalid evidence SHA')
        read_bytes(path,checksum,synthetic=exact_known_synthetic and path==SYNTHETIC_STATE)


def load_pinned_launcher(data):
    path = safe(CANDIDATE+'launcher.py')
    spec=importlib.util.spec_from_file_location('_root_v3_integration_contract',path)
    module=importlib.util.module_from_spec(spec)
    # Execute only already SHA-verified local launcher bytes, with no main().
    exec(compile(data,str(path),'exec'),module.__dict__)
    return module



def server_workspace_contract(*, validate_only, entry_sha256):
    """Only control storage moves; fixed runtime/science identities do not."""
    expected_root = Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
    require(os.name == 'posix' and ROOT == expected_root
        and ROOT.is_absolute() and ROOT.resolve() == ROOT.absolute(), 'wrong server control root')
    require(not any(p.is_symlink() for p in (ROOT, *ROOT.parents)), 'server control root alias')
    actual = Path(__file__).absolute()
    require(actual.resolve() == actual and not any(p.is_symlink() for p in (actual, *actual.parents)),
        'entry path alias')
    allowed = {ROOT / INSTALLED_ENTRY}
    if validate_only:
        allowed.add(CANDIDATE_ENTRY)
    require(actual in allowed, 'publication requires the reviewed installed R entry')
    require(type(entry_sha256) is str and re.fullmatch('[0-9a-f]{64}', entry_sha256)
        and digest(actual.read_bytes()) == entry_sha256, 'reviewed entry SHA differs')
    for relative, checksum in MIGRATION_BINDINGS.items():
        read_bytes(relative, checksum)
    return dict(schema='formal_main_v2', kind='explicit_server_control_workspace_migration',
        version='action-gpu-v3-server-entry-v1', control_root=str(ROOT),
        runtime_root=RUNTIME_ROOT, frozen_source_root=SNAPSHOT_ROOT,
        entrypoint_relative=INSTALLED_ENTRY, entrypoint_sha256=entry_sha256,
        execution_path=str(actual), evidence_sha256=dict(MIGRATION_BINDINGS),
        original_root_contract='F:/CTI-VLA',
        control_storage_only=True, scientific_source_or_GPU_contract_changed=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--independent-review',required=True)
    parser.add_argument('--independent-sha256',required=True)
    parser.add_argument('--entry-sha256',required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--validate-only',action='store_true')
    mode.add_argument('--root-approve-cpu-registration',action='store_true')
    args=parser.parse_args()
    migration=server_workspace_contract(validate_only=args.validate_only,entry_sha256=args.entry_sha256)
    require(args.validate_only or args.root_approve_cpu_registration, 'explicit root decision is required')
    require(args.independent_sha256 == INDEPENDENT_SHA, 'not the final reviewed v3 independent bytes')
    script_data=Path(__file__).read_bytes()
    if not args.validate_only:
        seen[INSTALLED_ENTRY]=digest(script_data)
    author=read(AUTHOR_INPUT,AUTHOR_SHA)
    require(author.get('schema')=='formal_main_v2'
        and author.get('kind')=='unsubmitted_GPU_v3_constructor_identity_repair_candidate_CPU_review'
        and author.get('status')=='passed_author_CPU_candidate_pending_independent_root_registration_and_GPU'
        and author['tests']['passed']==22 and author['tests']['failed']==0
        and author['production_published'] is False and author['root_registration_created'] is False,
        'wrong author candidate proof')
    require(author['read_evidence_sha256']==author['evidence_sha256'], 'author maps differ')
    check_evidence_map(author['evidence_sha256'],exact_known_synthetic=True)
    audit_bytes=read_bytes(args.independent_review,args.independent_sha256)
    audit=json.loads(audit_bytes)
    require(all(audit.get(k)==v for k,v in INDEPENDENT_TYPE.items()), 'not the reviewed v3 independent CPU receipt')
    require(audit.get('blockers',[])==[], 'independent blockers remain')
    require(audit.get('read_evidence_sha256')==audit.get('evidence_sha256'), 'independent maps differ')
    independent_map=audit.get('evidence_sha256')
    require(type(independent_map) is dict and independent_map.get(AUTHOR_INPUT)==AUTHOR_SHA, 'independent did not bind exact author')
    for name,(checksum,length) in EXPECTED.items():
        require(independent_map.get(CANDIDATE+name)==checksum, 'independent omitted candidate file: '+name)
        require(len(read_bytes(CANDIDATE+name,checksum))==length, 'candidate byte count differs: '+name)
    check_evidence_map(independent_map,exact_known_synthetic=True)
    inventory=read(INVENTORY,INVENTORY_SHA)
    require(len(inventory['files'])==173, 'frozen inventory size differs')
    check_evidence_map(inventory['files'])
    plan=read(CANDIDATE+'publication_plan.json')
    require(plan['stage_key']==STAGE and len(plan['files'])==8, 'publication plan differs')
    expected_rows={SOURCE+name:dict(source=CANDIDATE+name,path=SOURCE+name,sha256=checksum,bytes=length)
                   for name,(checksum,length) in EXPECTED.items()}
    require({row['path']:row for row in plan['files']}==expected_rows, 'not the exact eight static files')
    generated={SOURCE+name:read_bytes(CANDIDATE+name,checksum) for name,(checksum,_) in EXPECTED.items()}
    generated.update({AUTHOR:read_bytes(AUTHOR_INPUT,AUTHOR_SHA),AUDIT:audit_bytes,SCRIPT_ARCHIVE:script_data})
    c=load_pinned_launcher(generated[SOURCE+'launcher.py'])
    require(c.STAGE==STAGE and c.INVENTORY_SHA==INVENTORY_SHA
        and c.SOURCE_SHA==inventory['source_sha256']
        and c.P==RUNTIME_ROOT and c.S==SNAPSHOT_ROOT
        and inventory['source_root_server']==SNAPSHOT_ROOT, 'launcher frozen identity')
    manifest=json.loads(generated[SOURCE+'candidate_manifest.json'])
    constructor_ref=manifest['constructor_server_cpu']
    constructor=read(constructor_ref['path'],constructor_ref['sha256'])
    require(constructor_ref['sha256']=='15ba7a1dae8326a03d30f255282d176b5ac173be6491ad66014ea4fa84f5fc80'
        and constructor['exit_code']==0 and json.loads(constructor['stdout'])['checks_passed']==16, 'server311 CPU proof differs')
    reg=read(CANDIDATE+'gpu_registration.template.json')
    require(reg['status']=='pending_root_acceptance' and reg['gpu_submission_authorized'] is False, 'registration template already approved')
    prior=reg['prior_GPU_failure']
    require(prior['job_id']=='3030159' and prior['status']=='FAILED' and prior['GPU_seconds']==85, 'old GPU failure removed')
    check_evidence_map(prior['files_sha256'])
    root_template=read(CANDIDATE+'root_review.template.json')
    typed=read(CANDIDATE+'independent_review.template.json')
    require(typed['status']=='pending_independent_review' and typed['draft_only'] is True, 'independent template already approved')
    now=datetime.now(timezone.utc).isoformat()
    files=root_template['candidate_files']
    identity=root_template['candidate_identity']
    for item in files.values():
        require(item['path'] in generated and digest(generated[item['path']])==item['sha256'], 'candidate projection source differs')
    typed.update(status='passed_CPU_independent_review_pending_registered_GPU',draft_only=False,
        derivation_kind='root_adopted_typed_projection_of_exact_new_v3_independent_CPU_receipt',
        projection_prepared_by='root',projection_prepared_utc=now,
        underlying_independent_review=ref(AUDIT,audit_bytes),underlying_independent_type=INDEPENDENT_TYPE,
        independent_checks_rerun_by_projection=0,root_adoption=True,
        limitations=['Typed projection preserves the new independent receipt; it does not invent a test run or GPU result.'])
    typed.pop('intended_status_after_real_review',None)
    typed['evidence_sha256'].update({AUDIT:digest(audit_bytes),AUTHOR:AUTHOR_SHA})
    generated[TYPED]=encoded(typed)
    reg['cpu_reviews']['candidate_independent']['sha256']=digest(generated[TYPED])
    reg.update(status='registered_single_attempt',gpu_submission_authorized=True)

    node=read(CANDIDATE+'node_exclusion_registration.template.json')
    require(node['status']=='pending_root_acceptance' and node['adapter_path']==SOURCE+'node_exclusion.py'
        and node['adapter_sha256']==EXPECTED['node_exclusion.py'][0], 'wrong node policy template')
    for path,checksum in node['failure_evidence_sha256'].items(): read_bytes(path,checksum)
    for path,checksum in node['registered_wrapper_sha256'].items():
        require(digest(generated[path] if path in generated else read_bytes(path,checksum))==checksum, 'node wrapper differs')
    node.update(status='reviewed_for_future_explicit_requests',root_approved_utc=now,root_approved_by='root',
        independent_review=ref(AUDIT,audit_bytes),root_adoption_source=ref(SCRIPT_ARCHIVE,script_data),
        applied_to_existing_jobs=False,placement_scope_note='Only an explicitly requested new v3 engineering submission may use this new capability; no cancellation or automatic retry.')
    generated[NODE]=encoded(node)
    root_review=copy.deepcopy(root_template)
    require(root_review['status']=='pending_root_review' and root_review['draft_only'] is True, 'root template already approved')
    root_review.update(status='passed_CPU_root_review_pending_registered_GPU',draft_only=False,
        root_approved=True,reviewed_by='root',reviewed_utc=now,
        root_decision_basis='Caller explicitly supplied --root-approve-cpu-registration after reading the exact candidate and independent evidence.',
        candidate_independent_review=ref(TYPED,generated[TYPED]),
        original_independent_review=ref(AUDIT,audit_bytes),author_review=ref(AUTHOR,generated[AUTHOR]),
        root_integration_source=ref(SCRIPT_ARCHIVE,script_data),node_exclusion_registration=ref(NODE,generated[NODE]),
        dispatch_contract=c.DISPATCH,gpu_registration_path=REG,gpu_registration_intent_sha256=c.registration_intent(reg),
        actual_GPU_acceptance_pending=True,scientific_release=False,root_CPU_tests_rerun=0,
        server_workspace_migration=migration,
        registered_prior_GPU_failure_seconds=85,healthy_jobs_modified=False,
        caller_assertions=['The exact new v3 independent review is accepted.',
            'CPU engineering identity and fixed16 registration are approved; this is not actual GPU acceptance.',
            'The new exact node exclusion capability is approved; future submission still needs a free slot and all original transaction gates.'])
    root_review.pop('intended_status_after_real_review',None)
    root_review['evidence_sha256'].update({path:digest(data) for path,data in generated.items()})
    root_review['evidence_sha256'].update(MIGRATION_BINDINGS)
    root_review['evidence_sha256'].update(prior['files_sha256'])
    root_review['evidence_sha256'].update(node['failure_evidence_sha256'])
    previous_node=node['previous_registration']
    read_bytes(previous_node['path'],previous_node['sha256'])
    root_review['evidence_sha256'][previous_node['path']]=previous_node['sha256']
    for name in ('prior_transport_failure','prior_no_publication_evidence'):
        item=reg[name];read_bytes(item['path'],item['sha256']);root_review['evidence_sha256'][item['path']]=item['sha256']
    # Construct exactly the original launcher's P/S closure. Never put the
    # current root receipt or GPU registration in its own hash dependency map.
    rows={}
    def need(relative,checksum,server=None):
        c.lexical_relative(relative);c.valid_sha(checksum)
        require(relative not in {REVIEW,REG}, 'hash-cycle dependency')
        data=generated[relative] if relative in generated else read_bytes(relative,checksum)
        require(digest(data)==checksum, 'closure bytes differ: '+relative)
        server=server or c.P+'/'+relative
        row=dict(path=relative,server=server,sha256=checksum,bytes=len(data))
        require(server not in rows or rows[server]==row, 'contradictory closure destination')
        rows[server]=row
    for rel,checksum in inventory['files'].items(): need(rel,checksum,c.S+'/'+rel)
    for mapping in (manifest['read_evidence_sha256'],root_review['evidence_sha256']):
        for rel,checksum in mapping.items(): need(rel,checksum)
    for receipt in (typed,root_review):
        for item in receipt['candidate_files'].values(): need(item['path'],item['sha256'])
    for name,item in reg['cpu_reviews'].items():
        if name!='root_acceptance': need(item['path'],item['sha256'])
    for rel,checksum in ((INVENTORY,INVENTORY_SHA),(reg['candidate_manifest']['path'],reg['candidate_manifest']['sha256']),
        (c.ENTRY,reg['entrypoint']['sha256']),(c.ADAPTER,c.ADAPTER_SHA),(c.SUPERVISOR,c.SUPERVISOR_SHA)):
        need(rel,checksum)
    def visit(value):
        if isinstance(value,dict):
            if 'path' in value and 'sha256' in value and not str(value['path']).startswith('/'):
                need(value['path'],value['sha256'])
            for child in value.values(): visit(child)
        elif isinstance(value,list):
            for child in value: visit(child)
    visit(manifest)
    for row in manifest['suites'].values():
        for contract in row['compatibility'].values():
            for rel,checksum in contract['files'].items(): need(rel,checksum)
    root_review['deployment_files']=[rows[key] for key in sorted(rows)]
    generated[REVIEW]=encoded(root_review)
    reg['cpu_reviews']['root_acceptance']['sha256']=digest(generated[REVIEW])
    require(c.registration_intent(reg)==root_review['gpu_registration_intent_sha256'], 'root SHA introduced a cycle')
    generated[REG]=encoded(reg)
    # All checks and final bytes are prepared before the first publication.
    for rel in (*generated,CHECK):
        require(not safe(rel).exists(), 'destination already exists; manual inspection required: '+rel)
    for rel,checksum in seen.items():
        require(digest(safe(rel,synthetic=rel==SYNTHETIC_STATE).read_bytes())==checksum, 'input drift before publication: '+rel)
    if args.validate_only:
        # Prepared root declarations remain in memory, never become evidence.
        # This mode neither publishes nor invokes even the check-only child.
        print(json.dumps(dict(
            status='validated_server_candidate_no_publication_root_decision_pending',
            control_root=str(ROOT), runtime_root=RUNTIME_ROOT, stage_key=STAGE,
            candidate_files=8, frozen_source_files=173,
            planned_publications=len(generated), deployment_files=len(rows),
            deployment_mapping=[rows[key] for key in sorted(rows)],
            original_independent_sha256=args.independent_sha256,
            migration=migration, read_evidence_sha256=dict(seen),
            root_approval_recorded=False, files_written=0, subprocess_calls=0,
            SSH_calls=0, Slurm_submissions=0, GPU_seconds=0,
            actual_GPU_acceptance=False, scientific_release=False)))
        return
    for rel,data in generated.items():
        path=safe(rel);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data);stream.flush();os.fsync(stream.fileno())
        require(path.read_bytes()==data, 'published bytes differ: '+rel)
    # This is the only subprocess. --check-only never imports the supervisor or
    # calls a transport; the submitter and sibling launcher remain pinned.
    command=[sys.executable,'-B',str(safe(SOURCE+'submit.py')),'--project-root',str(ROOT),
        '--root-review',REVIEW,'--root-review-sha256',digest(generated[REVIEW]),
        '--manifest',reg['candidate_manifest']['path'],'--manifest-sha256',reg['candidate_manifest']['sha256'],
        '--gpu-registration',REG,'--gpu-registration-sha256',digest(generated[REG]),'--check-only']
    run=subprocess.run(command,cwd=ROOT,capture_output=True)
    publication={rel:dict(sha256=digest(data),bytes=len(data)) for rel,data in generated.items()}
    unchanged=all(safe(rel).read_bytes()==data for rel,data in generated.items())
    frozen_unchanged=all(digest(safe(rel).read_bytes())==checksum for rel,checksum in inventory['files'].items())
    result=dict(schema='formal_main_v2',kind='root_v3_GPU_registration_actual_server_check_only',
        checked_utc=datetime.now(timezone.utc).isoformat(),command=command,exit_code=run.returncode,
        stdout=run.stdout.decode(errors='replace'),stderr=run.stderr.decode(errors='replace'),
        root_review=ref(REVIEW,generated[REVIEW]),registration=ref(REG,generated[REG]),
        node_registration=ref(NODE,generated[NODE]),published=publication,
        published_bytes_unchanged=unchanged,source173_unchanged=frozen_unchanged,
        read_evidence_sha256=seen,root_approval_flag=args.root_approve_cpu_registration,
        server_workspace_migration=migration,
        SSH_calls=0,Slurm_submissions=0,GPU_seconds=0,GPU_submitted=False,scientific_release=False,
        final_states_opened=False,actual_GPU_acceptance='pending_single_future_registered_attempt')
    with safe(CHECK).open('xb') as stream:
        stream.write(encoded(result));stream.flush();os.fsync(stream.fileno())
    print(json.dumps(dict(check=ref(CHECK),exit_code=run.returncode,root_review=result['root_review'],
        registration=result['registration'],node_registration=result['node_registration'],GPU_submitted=False)))
    require(run.returncode==0 and unchanged and frozen_unchanged, 'check-only or immutable byte verification failed; preserve outputs, do not submit')


if __name__=='__main__':
    main()
