def execute(args, manifest, panel, registration_sha):
    from cti_vla.data.identity import file_sha256
    from cti_vla.data.formal_windows import load_formal_protocol, load_formal_windows
    from cti_vla.data.initial_states import official_task_catalog
    from cti_vla.data.formal_windows import LIBERO_REVISION
    from cti_vla.data.experiment_protocol import write_frozen_json
    from cti_vla.evaluation import formal_runtime, formal_trials, libero_runtime
    from cti_vla.evaluation.formal_acceptance import select_formal_acceptance_windows, require_formal_input_acceptance, require_formal_acceptance, module_parameter_sha256, verify_formal_operator_journal
    from cti_vla.evaluation.future_input_acceptance import verify_input_acceptance_journal
    from cti_vla.evaluation.checkpoint_manifest import load_checkpoint_manifest, verify_checkpoint_directory
    from cti_vla.evaluation.teacher_diagnostics import atomic_json, json_signature
    from cti_vla.models.abstraction.packing import PACKING_VERSION
    from cti_vla.training.formal_future import formal_source_hashes, validate_formal_training_config
    from cti_vla.training.formal_resume_acceptance import require_formal_resume_acceptance, verify_resume_journal
    project = args.project_root.resolve()
    sources = formal_source_hashes(ROOT)
    registration = read_json(args.registration)
    suite_config = registration['suites'][manifest['suite']]
    asset = load_checkpoint_manifest(args.asset_manifest)
    if file_sha256(args.asset_manifest) != suite_config['model_manifest_sha256'] or asset.revision != suite_config['model_revision'] or args.checkpoint.resolve() != Path(suite_config['model_root_server']).resolve():
        raise ValueError('formal evaluation base differs from its registered suite checkpoint')
    protocol = load_formal_protocol(args.protocol, project_root=project)
    windows = load_formal_windows(args.windows, protocol)
    suite_name = manifest['suite']
    if windows['suite'] != suite_name or args.windows.resolve() != (project / suite_config['windows']).resolve() or args.protocol.resolve() != (project / suite_config['protocol']).resolve():
        raise ValueError('formal evaluation/data suite mismatch')
    fixed = select_formal_acceptance_windows(windows, protocol)
    f00 = read_json(args.input_acceptance)
    config = dict(suite=suite_name, model_revision=asset.revision, stats_key=formal_runtime.FORMAL_SUITES[suite_name]['stats_key'])
    require_formal_input_acceptance(f00, config=config, window_manifest_sha256=file_sha256(args.windows), data_protocol_sha256=file_sha256(args.protocol), asset_manifest_sha256=file_sha256(args.asset_manifest), source_files=sources, selected_windows=fixed)
    input_journal = args.input_acceptance.parent / 'input_calls.jsonl'
    verify_input_acceptance_journal(input_journal, f00)
    resume_path = args.input_acceptance.parent / 'resume_acceptance.json'
    resume_journal = args.input_acceptance.parent / 'f03_calls.jsonl'
    resume_report = read_json(resume_path)
    primary_registration = next((p for p in registration['pairs'] if p['suite'] == suite_name and p['visual_tokens'] == 128 and (p['seed'] == 17)))
    primary_path = (project / primary_registration['path']).resolve()
    if file_sha256(primary_path) != primary_registration['sha256']:
        raise ValueError('formal primary config used by F03 differs from registration')
    require_formal_resume_acceptance(resume_report, config=read_json(primary_path), window_manifest_sha256=file_sha256(args.windows), input_acceptance_sha256=file_sha256(args.input_acceptance), source_files=sources, selected_windows=fixed[:2], frozen_model_sha256=f00['frozen_model_sha256'])
    verify_resume_journal(resume_journal, resume_report)
    watched_paths = [args.execution_manifest, args.registration, args.asset_manifest, args.protocol, args.windows, args.input_acceptance, input_journal, resume_path, resume_journal, primary_path]
    watched_paths.extend([args.development_panel] if panel['split'] == 'development' else [args.release, args.final_registry, args.sealed_final])
    policies, loaded = ({}, {})
    registered_pairs = {(p['suite'], p['visual_tokens'], p['seed']): p for p in registration['pairs']}
    f00_sha = file_sha256(args.input_acceptance)
    for row in manifest['methods']:
        identity = row['identity']
        mid = identity['method_id']
        if identity['method'] in ('dense', 'uniform'):
            actual = formal_trials.baseline_instance_identity(suite=suite_name, method=identity['method'], visual_tokens=identity['visual_tokens'], model_revision=asset.revision, frozen_model_sha256=f00['frozen_model_sha256'], source_files=sources, input_acceptance_sha256=f00_sha)
        else:
            paths = {key: resolve_project_path(project, row[key], checkpoint=key == 'checkpoint') for key in ('checkpoint', 'receipt', 'pair_config', 'f01_report')}
            watched_paths.extend(paths.values())
            pair, receipt, f01 = (read_json(paths[key]) for key in ('pair_config', 'receipt', 'f01_report'))
            validate_formal_training_config(pair)
            registered = registered_pairs[suite_name, identity['visual_tokens'], identity['training_seed']]
            if file_sha256(paths['pair_config']) != registered['sha256'] or pair != receipt['pair_config'] or paths['pair_config'] != (project / registered['path']).resolve() or (paths['checkpoint'] != (Path(registered['checkpoint_root_server']) / identity['method'] / 'best.pt').resolve()):
                raise ValueError('formal checkpoint receipt differs from frozen pair config')
            require_formal_acceptance(f01, config=pair, window_manifest_sha256=file_sha256(args.windows), input_acceptance_sha256=f00_sha, source_files=sources, selected_windows=fixed)
            if f01['frozen_model_sha256'] != f00['frozen_model_sha256']:
                raise ValueError('formal input/operator gates used different frozen VLA bytes')
            operator_journal = paths['f01_report'].parent / 'operator_calls.jsonl'
            verify_formal_operator_journal(operator_journal, f01)
            watched_paths.append(operator_journal)
            expected = dict(suite=suite_name, model_revision=asset.revision, stats_key=config['stats_key'], input_version=libero_runtime.INPUTS_VERSION, packing_version=PACKING_VERSION, visual_tokens=identity['visual_tokens'], per_camera_budgets=[identity['visual_tokens'] // 2] * 2, window_manifest_sha256=file_sha256(args.windows), input_acceptance_sha256=f00_sha, f01_report_sha256=file_sha256(paths['f01_report']), frozen_model_sha256=f00['frozen_model_sha256'], data_protocol_sha256=file_sha256(args.protocol), selection_protocol_sha256=json_signature(pair['selection']))
            probe_record_rng('before_selector_load')
            selected = formal_runtime.load_formal_selector_checkpoint(paths['checkpoint'], receipt, expected_versions=expected, expected_source_hashes=sources)
            probe_record_rng('after_selector_load')
            loaded[mid] = selected
            actual = formal_trials.selector_instance_identity(selected.provenance)
        if identity != actual:
            raise ValueError('formal execution instance differs from verified deployment identity: ' + mid)
    for budget in formal_runtime.FORMAL_BUDGETS:
        for seed in formal_runtime.FORMAL_SEEDS:
            a, b = (formal_trials.method_id(arm, budget, seed) for arm in ('A', 'B'))
            if a in loaded and b in loaded:
                formal_runtime.validate_formal_pair(loaded[a], loaded[b])
    watched = {str(p.resolve()): file_sha256(p) for p in watched_paths}

    def unchanged():
        if sources != formal_source_hashes(ROOT) or any((file_sha256(path) != sha for path, sha in watched.items())):
            raise ValueError('formal evaluation evidence/checkpoint/source bytes changed')
    source_verification = {'openvla_oft': verify_checkout(args.oft_source, libero_runtime.OFT_COMMIT), 'libero': verify_checkout(args.libero_source, LIBERO_REVISION)}
    catalog, mapping = official_task_catalog(args.libero_source, suite=suite_name)
    if panel['source'].get('revision') != LIBERO_REVISION or any((panel['source'].get(key) != value for key, value in mapping.items())):
        raise ValueError('formal panel task mapping differs from pinned LIBERO')
    if not (args.libero_config / 'config.yaml').is_file():
        raise ValueError('formal LIBERO project configuration must exist before evaluation')
    os.environ['LIBERO_CONFIG_PATH'] = str(args.libero_config.resolve())
    for p in (args.cache_directory, args.cache_directory / 'hub', args.cache_directory / 'modules'):
        p.mkdir(parents=True, exist_ok=True)
    os.environ.update(HF_HOME=str(args.cache_directory), HF_HUB_CACHE=str(args.cache_directory / 'hub'), HF_MODULES_CACHE=str(args.cache_directory / 'modules'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    import numpy as np
    import torch
    from transformers import AutoProcessor
    from cti_vla.models.openvla_oft_loader import load_openvla_oft_components
    if torch.cuda.device_count() != 1:
        raise RuntimeError('formal rollouts require exactly one allocated visible GPU')
    device = torch.device('cuda:0')
    torch.cuda.set_device(device)
    before = verify_checkpoint_directory(args.checkpoint, asset)
    probe_record_rng('before_base_load')
    components = load_openvla_oft_components(args.checkpoint, device=device, use_minimal_prismatic_compat=True)
    probe_record_rng('after_base_load')
    if module_parameter_sha256(components) != f00['frozen_model_sha256']:
        raise ValueError('formal loaded base parameters/buffers differ from F00 acceptance')
    probe_record_rng('before_processor_load')
    processor = AutoProcessor.from_pretrained(args.checkpoint, trust_remote_code=True, local_files_only=True)
    probe_record_rng('after_processor_load')
    for row in manifest['methods']:
        identity = row['identity']
        selected = loaded.get(identity['method_id'])
        if selected:
            selected.estimator.to(device)
        policies[identity['method_id']] = formal_runtime.FormalRolloutPolicy(components, processor, suite=suite_name, method=identity['method'], total_tokens=identity['visual_tokens'], selector=selected)
    from libero.libero import benchmark, get_libero_path
    from libero.libero.envs import OffScreenRenderEnv
    import libero.libero as installed_libero
    if args.libero_source.resolve() not in Path(installed_libero.__file__).resolve().parents:
        raise ValueError('formal imported LIBERO lies outside its pinned checkout')
    suite = benchmark.get_benchmark_dict()[suite_name](task_order_index=0)
    if any((suite.get_task(r['task_id']).name != r['task_name'] or catalog[r['task_id']]['task_name'] != r['task_name'] for r in panel['states'])):
        raise ValueError('formal simulator task order differs from the registered panel')
    runtime = dict(torch=torch.__version__, python=platform.python_version(), gpu=torch.cuda.get_device_name(), cuda=torch.version.cuda, numpy=np.__version__, slurm_job_id=os.environ['SLURM_JOB_ID'])
    return locals()
