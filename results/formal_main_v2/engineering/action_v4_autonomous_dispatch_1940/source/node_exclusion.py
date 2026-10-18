"""Root-scoped SSH argv adapter; no process execution, retries, or state writes.

Only the existing formal training wrappers and action-engineering v4 wrapper
are supported. Other submission grammars fail closed. Query argv is unchanged.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import threading

VERSION = 'root-ssh-node-exclusion-v2-action-gpu-v4'
P = '/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA'
H = '/share/home/u15016/XXY_CVPR/CTI-VLA'
S = P + '/snapshots/formal_main_v2_run_564be0995e'
SOURCE_SHA = 'dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e'
SUPERVISOR_SHA = '3e0786da690552356bbe2f56458fe19e88c90b4de079211dc652d655fe3c2e95'
REGISTRATION_SHA = 'a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9'
SSH = ['ssh', '-o', 'BatchMode=yes', 'tongji-cvpr']
NODE = 'gpu4020'
GPU_STAGE = 'formal_main_v2_action_execution_compat_gpu_v4'
GPU_BASE = 'results/formal_main_v2/engineering/' + GPU_STAGE
WRAPPERS = {
    'formal': ('scripts/server/formal_main.slurm', '4e0b7b714b2d6cb0440acc145dab770c4f53a9ba561fa208931af7ce9ae364ab'),
    'object': ('scripts/server/formal_asset_main.slurm', '9d54e0486a078a8358c8443bb92db8c8096d9ac3988eff693fa69b250d97c36a'),
    'goal': ('scripts/server/formal_goal_asset_main.slurm', 'ad29920d056b95be82d0257907d2010ba1a97be9166664a65029bdfd001d896a'),
    'gpu_v4': (GPU_BASE + '/source/probe.slurm', 'e87beacdb0ff23f293c7f6009f090a614c2903a37d6ff8e4732714236e0425c0'),
}
SUBMIT_WORD = re.compile(r'(?<![A-Za-z0-9_])sbatch(?![A-Za-z0-9_])')


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def metadata_path(root, relative):
    require(type(relative) is str and '\\' not in relative, 'metadata path must be project-relative POSIX')
    p = PurePosixPath(relative)
    require(not p.is_absolute() and p.as_posix() == relative and '..' not in p.parts
            and p.suffix == '.json' and not any(x.lower() in {'test', 'sealed', 'weights', 'checkpoints'} for x in p.parts)
            and not any(x in p.name.lower() for x in ('init_state', 'initial_state', 'final_state', 'test_state')),
            'forbidden metadata path')
    result = root.joinpath(*p.parts)
    require(not any(x.is_symlink() or (getattr(x.lstat(), 'st_file_attributes', 0) & 0x400)
                    for x in (result, *result.parents) if x.exists()), 'metadata alias/reparse point')
    require(result.resolve().is_relative_to(root), 'metadata escaped project')
    return result


def read_json(root, relative, evidence, expected=None):
    data = metadata_path(root, relative).read_bytes()
    digest = sha(data)
    require(expected is None or digest == expected, 'metadata SHA mismatch: ' + relative)
    require(relative not in evidence or evidence[relative] == digest, 'metadata changed during scope: ' + relative)
    evidence[relative] = digest
    value = json.loads(data)
    require(type(value) is dict, 'metadata must be a JSON object')
    return value


def validate_request(value):
    require(type(value) is dict, 'explicit request required')
    value = json.loads(json.dumps(value, allow_nan=False))
    if value.get('kind') == 'training':
        require(set(value) == {'kind', 'suite', 'budget', 'seed', 'segment_end', 'resume'}, 'training request keys')
        require(value['suite'] in {'libero_10', 'libero_spatial', 'libero_object', 'libero_goal'}
                and type(value['budget']) is int and value['budget'] in (256, 128, 64)
                and type(value['seed']) is int and value['seed'] in (17, 23, 41)
                and type(value['segment_end']) is int and value['segment_end'] in range(500, 5001, 500)
                and type(value['resume']) is bool, 'unregistered training target')
    else:
        require(value == {'kind': 'action_execution_gpu_v4'}, 'unsupported request kind')
    return value


class _ScopedSSH:
    def __init__(self, f, request, registration_ref, audit_relative):
        self.f, self.original = f, f.SSH
        self.root = Path(f.ROOT).resolve()
        self.request = validate_request(request)
        self.owner = threading.get_ident()
        self.consumed = False
        self.evidence = {}
        require(type(self.original) is list and self.original == SSH and f.P == P and f.H == H,
                'unexpected SSH/project identity or nested scope')
        require(Path(f.__file__).resolve() == self.root / 'scripts/formal_supervisor.py'
                and sha(Path(f.__file__).read_bytes()) == SUPERVISOR_SHA, 'supervisor source changed')
        require(Path(f.STATE).resolve() == self.root / 'results/experiment_supervisor/state.json', 'state path differs')
        require(type(registration_ref) is dict and set(registration_ref) == {'path', 'sha256'}, 'registration reference')
        self.registration_ref = dict(registration_ref)
        reg = read_json(self.root, registration_ref['path'], self.evidence, registration_ref['sha256'])
        expected = dict(schema='formal_main_v2', kind='scheduler_node_exclusion_registration', version=VERSION,
                        status='reviewed_for_future_explicit_requests', server_project=P, source_root=S,
                        source_sha256=SOURCE_SHA, excluded_nodes=[NODE], automatic_retry=False,
                        existing_jobs_untouched=True, scope='future_explicit_training_and_action_gpu_v4_only')
        require(all(reg.get(k) == v for k, v in expected.items()), 'node exclusion is not root-registered')
        require(reg.get('adapter_sha256') == sha(Path(__file__).read_bytes()), 'adapter not bound by registration')
        require(reg.get('registered_wrapper_sha256') == {v[0]: v[1] for v in WRAPPERS.values()}, 'wrapper inventory differs')
        refs = reg.get('failure_evidence_sha256')
        require(type(refs) is dict and refs, 'root-reviewed failure evidence required')
        for rel, digest in refs.items():
            read_json(self.root, rel, self.evidence, digest)
        self.audit_relative = audit_relative
        require(audit_relative.startswith(('.local/', 'results/formal_main_v2/preflight/')), 'audit destination outside allowed evidence directories')
        self.audit_path = metadata_path(self.root, audit_relative)
        require(not self.audit_path.exists(), 'audit already exists; never retry automatically')

    def __add__(self, tail):
        require(type(tail) is list and len(tail) == 1 and type(tail[0]) is str, 'expected one SSH command')
        command = tail[0]
        original_argv = self.original + tail
        # Catch shell quoting/backslash spellings as well as a literal sbatch.
        # These never occur in the pinned callers, but must not bypass the gate.
        try:
            lexical_parts = shlex.split(command, posix=True)
        except ValueError:
            lexical_parts = []
        has_sbatch = SUBMIT_WORD.search(command) or any(x.rsplit('/', 1)[-1] == 'sbatch' for x in lexical_parts)
        if not has_sbatch:
            return original_argv
        require(threading.get_ident() == self.owner, 'submission from a different thread')
        require(not self.consumed, 'only one sbatch request per explicit scope')
        require(not any(c in command for c in '\r\n\0') and '--exclude' not in command,
                'multiline command or preexisting exclusion is unsupported')
        parts = shlex.split(command, posix=True)
        require(len(parts) == 7 and parts[:5] == ['cd', P, '&&', 'sbatch', '--parsable']
                and parts[5].startswith('--export='), 'not the exact registered single sbatch grammar')
        export = parts[5][len('--export='):]
        entries = export.split(',')
        require(entries[0] == 'ALL' and all(x.count('=') == 1 for x in entries[1:]), 'export syntax differs')
        env = dict(x.split('=', 1) for x in entries[1:])
        require(len(env) == len(entries)-1, 'duplicate export key')
        require(all(re.fullmatch(r'[A-Za-z0-9_./:-]+', x) for x in env.values()), 'unsafe export value')
        invocation_server = env.get('INVOCATION', '')
        require(invocation_server.startswith(P + '/results/formal_main_v2/invocations/'), 'foreign invocation')
        invrel = invocation_server[len(P)+1:]
        inv = read_json(self.root, invrel, self.evidence)
        invsha = self.evidence[invrel]
        state = read_json(self.root, 'results/experiment_supervisor/state.json', {}, None)
        pending = state.get('pending_submission')
        require(type(pending) is dict and pending.get('stage_key') == inv.get('stage_key')
                and pending.get('invocation') == invrel, 'prepared pending identity differs')
        require(inv.get('schema') == 'formal_main_v2' and inv.get('source_root') == S
                and inv.get('source_sha256') == SOURCE_SHA, 'invocation frozen source differs')
        if self.request['kind'] == 'training':
            r = self.request
            stage = f"{r['suite']}_train_k{r['budget']}_seed{r['seed']}"
            require(inv.get('stage') == 'train' and inv.get('stage_key') == stage and inv.get('suite') == r['suite']
                    and inv.get('segment_end') == r['segment_end'] and inv.get('entrypoint') == 'scripts/run_formal_future.py'
                    and inv.get('registration_sha256') == REGISTRATION_SHA, 'explicit training identity differs')
            require(re.fullmatch(re.escape('results/formal_main_v2/invocations/' + stage) + r'_attempt[0-9]{2,}\.json', invrel), 'training invocation name differs')
            argv = inv.get('argv')
            require(type(argv) is list and all(type(x) is str for x in argv), 'training argv missing')
            for flag, wanted in {'--config': S + f"/configs/experiments/formal_main_v2/{r['suite']}_k{r['budget']}_seed{r['seed']}.json",
                                 '--arm': 'both', '--stop-after-updates': str(r['segment_end'])}.items():
                require(argv.count(flag) == 1 and argv.index(flag)+1 < len(argv) and argv[argv.index(flag)+1] == wanted,
                        'training argv target differs: ' + flag)
            require(argv.count('--resume') == int(r['resume']), 'resume identity differs')
            profile = {'libero_object': 'object', 'libero_goal': 'goal'}.get(r['suite'], 'formal')
            expected_env = {'SOURCE_ROOT': S, 'INVOCATION': invocation_server}
            if profile != 'formal':
                expected_env['INVOCATION_SHA256'] = invsha
                contract = inv.get('component_compatibility' if profile == 'goal' else 'runtime_compatibility', {})
                require(contract.get('slurm') == WRAPPERS[profile][0]
                        and contract.get('files', {}).get(WRAPPERS[profile][0]) == WRAPPERS[profile][1], 'asset wrapper contract differs')
            require(pending.get('utc') == inv.get('registered_utc'), 'pending registration time differs')
        else:
            profile = 'gpu_v4'
            require(invrel == 'results/formal_main_v2/invocations/' + GPU_STAGE + '_attempt01.json'
                    and inv.get('kind') == 'bounded_action_execution_engineering_invocation'
                    and inv.get('stage') == 'engineering' and inv.get('stage_key') == GPU_STAGE
                    and inv.get('output_root') == P + '/' + GPU_BASE
                    and inv.get('wrapper_sha256') == WRAPPERS[profile][1]
                    and pending.get('status') == 'prepared_before_invocation_publication', 'v3 invocation identity differs')
            expected_env = {'INVOCATION': invocation_server, 'INVOCATION_SHA256': invsha,
                            'WRAPPER_SHA256': WRAPPERS[profile][1]}
        require(env == expected_env, 'export identity differs')
        if 'INVOCATION_SHA256' in env:
            require(pending.get('invocation_sha256') == invsha, 'pending invocation SHA differs')
        wrapper_rel, wrapper_sha = WRAPPERS[profile]
        require(sha((self.root / wrapper_rel).read_bytes()) == wrapper_sha, 'registered wrapper bytes changed')
        wrapper_server = (S if profile == 'formal' else P) + '/' + wrapper_rel
        canonical = 'cd ' + shlex.quote(P) + ' && sbatch --parsable --export=' + shlex.quote(export) + ' ' + shlex.quote(wrapper_server)
        require(command == canonical, 'noncanonical command, extra shell statement, or foreign wrapper')
        for rel, digest in self.evidence.items():
            require(sha(metadata_path(self.root, rel).read_bytes()) == digest, 'evidence changed before argv release')
        actual = command.replace(' && sbatch --parsable ', ' && sbatch --parsable --exclude=' + NODE + ' ', 1)
        actual_argv = self.original + [actual]
        event = dict(schema='formal_main_v2', kind='root_scoped_scheduler_argv_transformation', version=VERSION,
                     status='argv_prepared_not_submission_result', utc=datetime.now(timezone.utc).isoformat(),
                     node_exclusion=[NODE], request=self.request, registration=self.registration_ref,
                     invocation=invrel, invocation_sha256=invsha, pending_submission_at_transform=pending,
                     original_command=command, actual_command=actual, original_ssh_argv=original_argv,
                     actual_ssh_argv=actual_argv, shell_argv_unchanged_except_exclude=True,
                     metadata_evidence_sha256=self.evidence, supervisor_sha256=SUPERVISOR_SHA,
                     adapter_sha256=sha(Path(__file__).read_bytes()), wrapper_sha256=wrapper_sha,
                     automatic_retry=False, subprocess_executed_by_adapter=False,
                     existing_jobs_changed=False, scientific_configuration_changed=False)
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_path.open('x', encoding='utf-8', newline='\n') as out:
            out.write(json.dumps(event, ensure_ascii=False, indent=2) + '\n')
            out.flush()
            os.fsync(out.fileno())
        self.consumed = True
        return actual_argv


@contextmanager
def exclude_future_sbatch(f, *, request, registration_ref, audit_relative):
    """Wrap one root call, inside its existing capacity/repair/lock workflow.

    The caller owns submission and outcome handling. This does not retry an old
    failed stage, bypass a marker, or validate a scientific continuation gate.
    """
    original = f.SSH
    scoped = _ScopedSSH(f, request, registration_ref, audit_relative)
    f.SSH = scoped
    try:
        yield scoped
    finally:
        unchanged = f.SSH is scoped
        f.SSH = original
        require(unchanged, 'SSH binding changed inside root-only scope; restored original')
