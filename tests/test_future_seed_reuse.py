"""Synthetic CPU provenance/cold-start tests; no engineering gate is produced."""
import ast
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation import future_seed_reuse as reuse
from cti_vla.evaluation.future_input_acceptance import INPUT_ACCEPTANCE_VERSION, select_input_windows
from cti_vla.evaluation.libero_runtime import INPUTS_VERSION, ACTION_VERSION
from cti_vla.evaluation.teacher_diagnostics import json_signature
from cti_vla.models.abstraction.packing import PACKING_VERSION


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    return path


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    root=tmp_path; source=root/"current"; parent_source=root/"parent"
    runner="\n".join(f"def {name}():\n    return 'unchanged'\n" for name in reuse.PROTECTED_FUNCTIONS)
    for directory in (source,parent_source):
        (directory/"scripts").mkdir(parents=True)
        (directory/reuse.RUNNER).write_text(runner,encoding="utf-8")
        (directory/"src/cti_vla/training").mkdir(parents=True)
        (directory/"src/cti_vla/training/future_auxiliary.py").write_text("LOSS = 'same'\n")
    (source/reuse.RUNNER).write_text(runner+"\ndef run():\n    return 'new guard'\n",encoding="utf-8")
    added=source/reuse.REUSE_SOURCE;added.parent.mkdir(parents=True);added.write_text("# synthetic reuse guard\n")
    verifier=source/"scripts/verify_long_inputs.py";verifier.write_text("# unchanged verifier\n")
    original=reuse.source_hashes(parent_source)
    parent_config={"suite":"libero_10","seed":17,"run_id":"g1_future_long_v1","model_revision":"synthetic-base",
                   "future":{"horizon":8,"weight_B":.1}}
    config={**parent_config,"seed":23,"run_id":"g1_future_long_seed23_v1"}
    target_path=put(source/"configs/experiments/g1_future_long_seed23_v1.json",config)
    protocol=SimpleNamespace(payload={"suite":"libero_10","task_catalog":[{"task_id":t,"instruction":f"task{t}"} for t in (0,3,5)]})
    windows=[{"window_id":f"w{i:03}","episode_id":f"e{i//3:03}","start_step":i%3,
              "split":"train" if i<90 else "validation","task_name":f"task{(0,3,5)[i%3]}"} for i in range(150)]
    manifest={"suite":"libero_10","windows":windows}
    from cti_vla.data import long_future_windows
    monkeypatch.setattr(long_future_windows,"load_long_future_protocol",lambda *a,**k:protocol)
    monkeypatch.setattr(long_future_windows,"load_future_windows",lambda *a,**k:manifest)
    paths={"config":put(root/"parent_config.json",parent_config),"windows":put(root/"windows.json",manifest),
        "protocol":put(root/"protocol.json",protocol.payload),"asset_manifest":put(root/"asset.json",{"model":"same"}),
        "runner":parent_source/reuse.RUNNER}
    fixed={"config":"configs/experiments/g1_future_long_v1.json","windows":"configs/manifests/long_future_v1/windows.json",
           "protocol":"configs/manifests/long_future_v1/protocol.json","asset_manifest":"configs/assets/openvla_oft_libero_long.json"}
    inv={**original,**{v:file_sha256(paths[k]) for k,v in fixed.items()},"scripts/verify_long_inputs.py":file_sha256(verifier)}
    for rel in ("configs/assets/libero_long_rlds.json","configs/experiments/g1_future_long_data_v1.json"):
        inv[rel]=file_sha256(put(source/rel,{"fixed":"synthetic"}))
    paths["source_inventory"]=put(root/"inventory.json",{"files":inv,"source_sha256":hashlib.sha256(json.dumps(inv,sort_keys=True).encode()).hexdigest()})
    selected=select_input_windows(manifest,protocol)
    journal=[]
    for row in selected:
        for kind in ("official_dense","shared_dense"):
            call=len(journal)//2; meta={"call_id":call,"window_id":row["window_id"],"kind":kind,"job_id":"synthetic"}
            journal.extend([{"event":"start",**meta},{"event":"complete",**meta,"seconds":.1}])
    paths["input_journal"]=root/"calls.jsonl";paths["input_journal"].write_text("\n".join(json.dumps(x) for x in journal))
    flags={k:True for k in ("pixels_equal","prompt_equal","raw_camera_bridge_equal","native_physical_equal",
        "action_postprocess_equal","gripper_equal","demonstration_normalization_valid","passed")}
    f00={"stage":"G1-F00-input-parity","status":"passed","execution":"real_frozen_openvla_l40","version":INPUT_ACCEPTANCE_VERSION,
        "suite":"libero_10","stats_key":"libero_10_no_noops","model_revision":"synthetic-base","config_sha256":json_signature(parent_config),
        "window_manifest_sha256":file_sha256(paths["windows"]),"protocol_sha256":file_sha256(paths["protocol"]),
        "asset_manifest_sha256":file_sha256(paths["asset_manifest"]),"source_files":original,"verification_script_sha256":file_sha256(verifier),
        "input_version":INPUTS_VERSION,"action_version":ACTION_VERSION,"packing_version":PACKING_VERSION,"checkpoint_unchanged":True,
        "test_opened":False,"policy_sample_forwards":6,"vision_forwards":6,"policy_attempts":6,"job_id":"synthetic",
        "calls_jsonl_sha256":file_sha256(paths["input_journal"]),"dataset_statistics_sha256":"d"*64,
        "observations":[{"window":r,"proprio_max_abs_error":0,"dense_max_abs_error":0,**flags} for r in selected]}
    paths["input_acceptance"]=put(root/"input.json",f00)
    f01={"stage":"G1-F01","status":"passed","execution":"real_frozen_openvla_l40","suite":"libero_10",
        "config_sha256":json_signature(parent_config),"window_manifest_sha256":file_sha256(paths["windows"]),"model_revision":"synthetic-base",
        "stats_key":"libero_10_no_noops","input_acceptance_sha256":file_sha256(paths["input_acceptance"]),
        "input_version":INPUTS_VERSION,"packing_version":PACKING_VERSION,"source_files":original,"job_id":"synthetic",
        "checks":{k:True for k in ("time_alignment","no_future_leakage","action_gradient_to_die","future_gradient_to_die",
            "vla_parameters_unchanged","hard128_packing","dense_differentiable_parity","official_input_action_parity")}}
    paths["f01_acceptance"]=put(root/"f01.json",f01)
    paths["f01_finalization"]=put(root/"finalization.json",{"status":"verified","checkpoint_unchanged":True,"result_status":"passed",
        "result_sha256":file_sha256(paths["f01_acceptance"]),"job_id":"synthetic"})
    producer={"source_files":original,"asset_manifest_sha256":file_sha256(paths["asset_manifest"]),"model_revision":"synthetic-base","dataset_statistics_sha256":"d"*64}
    index=[]
    for row in windows:
        identity={"window":row,"config_sha256":file_sha256(paths["config"]),"window_manifest_sha256":file_sha256(paths["windows"]),"producer":producer}
        index.append({"path":str(root/"features"/(row["window_id"]+".pt")),"identity":identity,"cache_sha256":hashlib.sha256(b"tensor").hexdigest(),"cache_bytes":6,
                      "window_alignment_validated":True,"future_target_detached":True,"checkpoint_normalization":True})
    paths["cache_index"]=put(root/"index.json",index)
    logical={**fixed,"source_inventory":"results/g1_future_long/source_g1_future_long_v1.json","cache_index":"results/g1_future_long_v1/training/cache_index.json",
        "input_acceptance":"results/g1_future_long_v1/inputs/input_acceptance.json","input_journal":"results/g1_future_long_v1/inputs/calls.jsonl",
        "f01_acceptance":"results/g1_future_long_v1/acceptance/f01_acceptance.json","f01_finalization":"results/g1_future_long_v1/acceptance/acceptance_finalization.json"}
    exp=put(source/"configs/experiments/g1_future_long_multiseed_v1.json",{"new_configs":{"23":{"path":target_path.relative_to(source).as_posix(),"sha256":file_sha256(target_path)}},
        "frozen_evidence_sha256":{v:file_sha256(paths[k]) for k,v in logical.items()}})
    reg={"schema":reuse.SCHEMA,"allowed_config_changes":["seed","run_id"],"target_seed":23,"target_run_id":config["run_id"],
        "target_config_identity_sha256":json_signature(config),"target_source_files":reuse.source_hashes(source),"experiment_registration_sha256":file_sha256(exp),
        "parent_files":{k:{"path":p.relative_to(root).as_posix(),"sha256":file_sha256(p)} for k,p in paths.items()},
        "parent_runner_module_structure_sha256":reuse.module_structure_hash(paths["runner"]),
        "protected_runner_functions":reuse.function_hashes(paths["runner"])}
    path=put(root/"reuse.json",reg)
    return SimpleNamespace(root=root,source=source,path=path,config=config,reg=reg,paths=paths,index=index)


def load(b):
    return reuse.load_long_seed_reuse(b.path,config=b.config,project_root=b.root,source_root=b.source)


def test_inherits_original_pair_identity_without_claiming_new_F01(bundle):
    c=load(bundle)
    assert c.parent_pair_id!=json_signature(bundle.config)
    assert c.receipt["status"]=="verified_inheritance_not_new_F01"
    assert c.receipt["new_engineering_GPU_calls"]==0
    assert len(c.cache_index)==150


@pytest.mark.parametrize("change",["loss","unapproved_seed","parent_evidence","cache_self_repin","current_loss_source","protected_runner","unregistered_source","runner_global"])
def test_seed_only_reuse_rejects_substantive_or_unpinned_changes(bundle,change):
    b=bundle
    if change=="loss":b.config["future"]["weight_B"]=.2
    elif change=="unapproved_seed":b.config["seed"]=42
    elif change in ("parent_evidence","cache_self_repin"):
        index=deepcopy(b.index);index[0]["cache_sha256"]="e"*64;put(b.paths["cache_index"],index)
        if change=="cache_self_repin":
            b.reg["parent_files"]["cache_index"]["sha256"]=file_sha256(b.paths["cache_index"]);put(b.path,b.reg)
    else:
        target=b.source/("src/cti_vla/training/future_auxiliary.py" if change=="current_loss_source" else reuse.RUNNER)
        if change=="protected_runner":target.write_text(target.read_text().replace("return 'unchanged'","return 'different'",1))
        elif change=="current_loss_source":target.write_text("LOSS = 'changed'\n")
        elif change=="runner_global":target.write_text(target.read_text()+"\nNEW_GLOBAL = 'different'\n")
        else:(b.source/"src/extra.py").write_text("# unreviewed\n")
        b.reg["target_source_files"]=reuse.source_hashes(b.source);put(b.path,b.reg)
    with pytest.raises(ValueError):load(b)


def test_cache_requires_original_receipt_and_actual_bytes_not_just_new_hash(bundle):
    c=load(bundle);e=c.cache_index[0];path=Path(e["path"]);path.parent.mkdir()
    path.write_bytes(b"tensor");put(path.with_suffix(".json"),{k:v for k,v in e.items() if k!="path"})
    one=replace(c,cache_index=[e]);assert reuse.verify_reused_cache(one,path.parent)==[e]
    path.write_bytes(b"forged")
    with pytest.raises(ValueError,match="changed"):reuse.verify_reused_cache(one,path.parent)
    path.write_bytes(b"tensor");receipt=json.loads(path.with_suffix(".json").read_text());receipt["future_target_detached"]=False;put(path.with_suffix(".json"),receipt)
    with pytest.raises(ValueError,match="changed"):reuse.verify_reused_cache(one,path.parent)


def test_new_seed_cannot_resume_or_reuse_a_nonempty_output(tmp_path):
    out,weights=tmp_path/"new_output",tmp_path/"new_weights"
    reuse.require_fresh_seed_destinations(out,weights)
    weights.mkdir();(weights/"resume.pt").write_bytes(b"old")
    with pytest.raises(ValueError,match="resume"):reuse.require_fresh_seed_destinations(out,weights)


def test_explicit_CLI_cannot_point_to_other_parent_evidence(bundle):
    with pytest.raises(ValueError,match="explicit CLI"):
        reuse.load_long_seed_reuse(bundle.path,config=bundle.config,project_root=bundle.root,source_root=bundle.source,
                                  expected_paths={"f01_acceptance":bundle.paths["input_acceptance"]})
