"""Passive CPU-array/RNG/simulator observer; engineering evidence only.

No simulator, policy, rendering, seeding, RNG draws, or CUDA initialization is
performed here. Native RNG get_state APIs only read already-existing generators.
Copies and disk I/O necessarily perturb wall-clock timing. Missing passive data
is explicitly recorded, not recovered by calling a simulator update/getter.
"""
from __future__ import annotations
from collections import OrderedDict
import hashlib
import json
from pathlib import Path
import random
import sys
import time
from types import SimpleNamespace
import numpy as np

VERSION = 'goal-prefix58-passive-observer-v1'
OBS_KEYS = ('agentview_image', 'robot0_eye_in_hand_image', 'robot0_eef_pos',
            'robot0_eef_quat', 'robot0_gripper_qpos')
SIM_FIELDS = ('qpos', 'qvel', 'act', 'ctrl', 'qacc_warmstart', 'mocap_pos', 'mocap_quat')
IDENTITY_KEYS = ('trial_id', 'state_trial_id', 'task_id', 'task_name',
                 'source_state_index', 'initial_state_sha256', 'method')

class ObserverAbort(BaseException):
    """Fail-stop outside the original Exception-only policy/environment handler."""

def require(ok, message):
    if not ok:
        raise ObserverAbort(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def jbytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode()

def plain(value):
    if value is None or type(value) in (str, bool, int, float):
        return value
    if type(value) in (dict, OrderedDict):
        return {str(k): plain(v) for k, v in value.items()}
    if type(value) in (tuple, list):
        return [plain(v) for v in value]
    if type(value) is np.ndarray:
        return dict(dtype=str(value.dtype), shape=list(value.shape),
                    bytes_hex=value.tobytes(order='C').hex())
    if isinstance(value, np.generic):
        return plain(value.item())
    raise ObserverAbort('unsupported RNG value; no opaque serialization')

def own_dict(obj):
    if obj is None:
        return {}
    try:
        value = object.__getattribute__(obj, '__dict__')
    except (AttributeError, TypeError):
        return {}
    return value if type(value) is dict else {}

def array_copy(value):
    require(type(value) is np.ndarray, 'only exact ndarray arrays are copied')
    require(not value.dtype.hasobject, 'object arrays are forbidden')
    raw = value.tobytes(order='C')
    meta = dict(dtype=str(value.dtype), dtype_descr=plain(value.dtype.descr),
                shape=list(value.shape), strides=list(value.strides),
                c_contiguous=bool(value.flags.c_contiguous),
                f_contiguous=bool(value.flags.f_contiguous),
                writeable=bool(value.flags.writeable), bytes=len(raw), sha256=sha(raw))
    return meta, raw

def object_guard(value, *, depth=0):
    """Compare exact builtin structure/ndarray bytes and identities; no callbacks."""
    require(depth <= 12, 'object guard depth exceeded')
    if value is None or type(value) in (str, int, float, bool):
        return (type(value).__name__, value)
    if type(value) is np.ndarray:
        meta, raw = array_copy(value)
        return ('ndarray', id(value), value.__array_interface__['data'][0], meta)
    if isinstance(value, np.generic):
        return ('numpy_scalar', str(value.dtype), value.tobytes().hex())
    if type(value) in (dict, OrderedDict):
        require(all(type(k) in (str, int) for k in value), 'unreadable mapping keys')
        return (type(value).__name__, id(value),
                [(k, object_guard(v, depth=depth+1)) for k, v in value.items()])
    if type(value) in (tuple, list):
        return (type(value).__name__, id(value),
                [object_guard(v, depth=depth+1) for v in value])
    # PolicyChunk's own dictionary is data only. No class/property/custom getter.
    cls = type(value)
    if cls.__module__ == 'cti_vla.evaluation.libero_runtime' and cls.__name__ == 'PolicyChunk':
        return ('PolicyChunk', id(value), object_guard(own_dict(value), depth=depth+1))
    return ('opaque_identity_only', cls.__module__, cls.__qualname__, id(value))

def _generator_state(generator):
    # torch.Generator.get_state returns a CPU byte Tensor. Never call cpu(),
    # cuda.get_rng_state*(), current_device(), synchronize(), or lazy_init().
    state = generator.get_state()
    require(state.device.type == 'cpu' and str(state.dtype) == 'torch.uint8',
            'RNG reader returned a non-CPU byte state')
    arr = state.numpy()
    require(type(arr) is np.ndarray, 'RNG Tensor did not expose an exact CPU array')
    return dict(bytes_hex=arr.tobytes().hex(), shape=list(arr.shape), dtype=str(arr.dtype))

def global_rng():
    result = dict(python=plain(random.getstate()), numpy=plain(np.random.get_state()))
    torch = sys.modules.get('torch')
    if torch is None:
        result['torch'] = {'missing': 'not imported; observer does not import it'}
        return result
    data = torch.__dict__
    generator = data.get('default_generator')
    result['torch_cpu'] = (_generator_state(generator) if generator is not None else
                          {'missing': 'no existing default CPU generator'})
    cuda = sys.modules.get('torch.cuda')
    if cuda is None or cuda.__dict__.get('_initialized') is not True:
        result['torch_cuda'] = {'missing': 'CUDA not initialized; no initialization requested'}
    else:
        generators = cuda.__dict__.get('default_generators')
        if type(generators) is not tuple or not generators:
            result['torch_cuda'] = {'missing': 'no existing CUDA generator tuple'}
        else:
            result['torch_cuda'] = [_generator_state(g) for g in generators]
    return result

def passive_environment(env, *, allow_cpu_fixture=False):
    """Direct dictionaries -> existing native MjData fields; no env/sim methods."""
    if env is None:
        return {'missing': 'environment unavailable at this marker'}, {}
    outer = own_dict(env)
    inner = outer.get('env')
    data = own_dict(inner) if inner is not None else outer
    sim = data.get('sim')
    wrapped = own_dict(sim).get('data')
    native = own_dict(wrapped).get('_data')
    if allow_cpu_fixture and type(wrapped) is SimpleNamespace:
        native = wrapped
    cls = type(native)
    native_ok = cls.__module__ == 'mujoco._structs' and cls.__name__ == 'MjData'
    fixture_ok = allow_cpu_fixture and cls is SimpleNamespace
    meta, payloads = {}, {}
    if native_ok or fixture_ok:
        meta['native_type'] = cls.__module__ + '.' + cls.__name__
        values = {}
        for name in SIM_FIELDS:
            try:
                v = own_dict(native).get(name) if fixture_ok else getattr(native, name)
                if type(v) is not np.ndarray:
                    values[name] = {'missing': 'no exact native ndarray'}
                    continue
                m, raw = array_copy(v); values[name] = m; payloads['sim.' + name] = (m, raw)
            except AttributeError:
                values[name] = {'missing': 'native descriptor absent'}
        try:
            t = own_dict(native).get('time') if fixture_ok else native.time
            values['time'] = float(t) if type(t) in (int, float) else {'missing': 'no native numeric time'}
        except AttributeError:
            values['time'] = {'missing': 'native time descriptor absent'}
        meta['fields'] = values
    else:
        meta['missing'] = 'unsupported passive env.env.sim.data._data route; no fallback getter'
        meta['observed_type'] = cls.__module__ + '.' + cls.__name__
    env_rng = {}
    for level_name, level in (('wrapper', outer), ('inner', data)):
        for name, value in level.items():
            if type(value) is np.random.RandomState:
                env_rng[level_name+'.'+name] = {'type': 'RandomState', 'state': plain(value.get_state())}
            elif type(value) is np.random.Generator:
                env_rng[level_name+'.'+name] = {'type': 'Generator', 'state': plain(value.bit_generator.state)}
    meta['environment_rng'] = env_rng or {'missing': 'no direct NumPy RNG object in env dictionaries'}
    scalars = {}
    for name in ('timestep', 'cur_time', 'done', 'hard_reset', 'deterministic_reset'):
        value = data.get(name)
        if type(value) in (bool, int, float, str):
            scalars[name] = value
    meta['direct_environment_scalars'] = scalars
    return meta, payloads

class PassiveObserver:
    def __init__(self, output, prefix_rows, *, allow_cpu_fixture=False, sink=None):
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=False)
        self.blobs = self.output / 'blobs'; self.blobs.mkdir()
        self.journal = self.output / 'events.jsonl'
        self.prefix = [{k: row[k] for k in IDENTITY_KEYS} for row in prefix_rows]
        require(len(self.prefix) == 58 and len({r['trial_id'] for r in self.prefix}) == 58,
                'exact original 58 unique trial identities required')
        self.allow_cpu_fixture = allow_cpu_fixture
        require(sink is None or allow_cpu_fixture, 'injected sink is CPU fixture only')
        self.sink = sink
        self.event_count = 0; self.begun = 0; self.finished = 0
        self.current = None; self.dead = False; self.t0 = {}
        self.started_ns = time.monotonic_ns()

    def _blob(self, raw, suffix):
        key = sha(raw); path = self.blobs / (key + suffix)
        if path.exists():
            require(path.is_file() and sha(path.read_bytes()) == key, 'existing observer blob changed')
        else:
            with path.open('xb') as f: f.write(raw)
        return {'path': 'blobs/' + path.name, 'sha256': key, 'bytes': len(raw)}

    def _append(self, event):
        if self.sink is not None: self.sink(event)
        with self.journal.open('ab') as f: f.write(jbytes(event)+b'\n')

    def capture(self, phase, env=None, observation=None, *, control_step=None, wait_steps=None, chunk=None):
        require(not self.dead, 'observer is failed; no retry')
        if control_step is not None and control_step != 0:
            return
        started = time.monotonic_ns()
        rng_before = global_rng()
        obj_before = object_guard((observation, chunk))
        sim_before, sim_payloads = passive_environment(env, allow_cpu_fixture=self.allow_cpu_fixture)
        try:
            event = dict(version=VERSION, event_index=self.event_count+1, phase=phase,
                         ordinal=self.begun if self.current else None,
                         trial_identity=self.current, control_step=control_step, wait_steps=wait_steps,
                         elapsed_ns_before_capture=started-self.started_ns,
                         timing_boundary='observer outside original policy perf_counter interval',
                         scientific_trials_added=0)
            arrays = {}; aggregate = hashlib.sha256()
            if observation is None:
                event['observation_missing'] = 'no returned observation exists at this marker'
            else:
                require(type(observation) in (dict, OrderedDict), 'unreadable observation mapping')
                require(all(k in observation for k in OBS_KEYS), 'required five observation arrays missing')
                for key in OBS_KEYS:
                    m, raw = array_copy(observation[key])
                    aggregate.update(key.encode()); aggregate.update(m['dtype'].encode())
                    aggregate.update(str(tuple(m['shape'])).encode()); aggregate.update(raw)
                    arrays[key] = {**m, 'blob': self._blob(raw, '.bin')}
                event['observation_sha256'] = aggregate.hexdigest()
            event['observation_arrays'] = arrays
            event['sim'] = sim_before
            event['sim_array_blobs'] = {k: self._blob(raw, '.bin') for k, (m, raw) in sim_payloads.items()}
            event['global_rng'] = self._blob(jbytes(rng_before), '.rng.json')
            # I/O and CPU-only injected negative-test sink are inside the invariant guards.
            event['observer_capture_ns_before_guard'] = time.monotonic_ns()-started
            if self.sink is not None: self.sink(event)
            sim_after, _ = passive_environment(env, allow_cpu_fixture=self.allow_cpu_fixture)
            obj_after = object_guard((observation, chunk)); rng_after = global_rng()
            # Tuple constructed for the guard is ephemeral; its container id is ignored.
            require(obj_before[2] == obj_after[2], 'observer changed input/returned object identity or bytes')
            require(sim_before == sim_after, 'observer changed passive simulator or environment RNG state')
            require(rng_before == rng_after, 'observer changed global RNG state')
            event['invariants'] = dict(object_identity_and_bytes_unchanged=True,
                                      passive_sim_and_environment_rng_unchanged=True,
                                      global_rng_unchanged=True)
            # Do not call the test sink twice.
            with self.journal.open('ab') as f: f.write(jbytes(event)+b'\n')
            require(global_rng() == rng_after, 'observer journal write changed RNG')
            require(object_guard((observation, chunk))[2] == obj_after[2], 'observer journal write changed inputs')
            self.event_count += 1
            if phase in ('t0_query_before', 't0_query_after'):
                require(self.current is not None, 't0 marker outside an active trial')
                self.t0.setdefault(self.current['trial_id'], {})[phase] = event.get('observation_sha256')
        except BaseException as error:
            self.dead = True
            failure = dict(event='observer_abort', phase=phase, ordinal=self.begun,
                           error_type=type(error).__name__, error=str(error), automatic_retry=False,
                           scientific_trials_added=0)
            with self.journal.open('ab') as f: f.write(jbytes(failure)+b'\n')
            if isinstance(error, ObserverAbort): raise
            raise ObserverAbort(str(error)) from error

    def trial_begin(self, identity, state):
        require(not self.dead and self.current is None and self.begun == self.finished,
                'overlapping or failed trial; no replay')
        require(self.begun < 58, 'trial 59 forbidden')
        actual = {k: identity[k] for k in IDENTITY_KEYS}
        require(actual == self.prefix[self.begun], 'fixed original prefix/order/identity mismatch')
        require(identity.get('environment_seed') == 0 and identity.get('runtime_seed') == 17
                and identity.get('wait_steps') == 10 and identity.get('action_chunk_size') == 8,
                'original environment/runtime settings differ')
        require(state['initial_state_sha256'] == actual['initial_state_sha256'], 'state identity changed')
        self.current = actual; self.begun += 1
        self.capture('trial_begin_before_reseed')

    def trial_end(self, row, ledger):
        require(self.current is not None and all(row[k] == v for k, v in self.current.items()),
                'terminal identity differs')
        # Preserve original outcome in the original ledger, but never use success for admission.
        require(row['status'] == 'completed', 'policy/environment exception: stop once without retry')
        require(not any(r.get('event') == 'cleanup_error' and r.get('trial_id') == row['trial_id']
                        for r in ledger.events), 'environment cleanup exception: stop without retry')
        markers = self.t0.get(row['trial_id'], {})
        require(set(markers) == {'t0_query_before','t0_query_after'}, 'missing original t0 query markers')
        require(row['chunks'] and row['chunks'][0]['control_step'] == 0,
                'missing original t0 chunk')
        require(markers['t0_query_after'] == row['chunks'][0]['observation_sha256'],
                'observer postquery hash differs from original ledger hash')
        event = dict(event='trial_end', ordinal=self.begun, trial_identity=self.current,
                     status=row['status'], control_steps=row['control_steps'],
                     policy_calls=row['policy_calls'], wait_steps=row['wait_steps'],
                     t0_hashes=markers, success_not_used_for_admission=True,
                     scientific_trials_added=0)
        self._append(event)
        self.finished += 1; self.current = None

    def finish(self):
        require(not self.dead and self.current is None and self.begun == self.finished == 58,
                'partial/failed prefix is not a complete engineering attempt')
        self.capture('original_runner_returned')
        return dict(version=VERSION, status='returned_58_engineering_trials_only',
                    original_prefix_trials=58, unique_development_states=29,
                    observer_events=self.event_count, scientific_trials_added=0,
                    GPU_acceptance_inferred=False, Goal_scientific_HOLD_unchanged=True,
                    event_sha256=sha(self.journal.read_bytes()))
