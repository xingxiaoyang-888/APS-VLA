"""CPU-only suite/gate regression tests; no Long images, model or gate produced."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation import future_input_acceptance as inputs_contract
from cti_vla.evaluation.future_runtime import (make_future_checkpoint_metadata, make_future_deployment_receipt,
    load_future_selector_checkpoint, require_future_f01)
from cti_vla.evaluation.libero_runtime import INPUTS_VERSION, ACTION_VERSION
from cti_vla.evaluation.teacher_diagnostics import json_signature
from cti_vla.models.abstraction.packing import PACKING_VERSION
from test_future_runtime import checkpoint_fixture
from test_future_auxiliary import cpu_threads, example

ROOT = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location("synthetic_long_" + name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def long_config():
    return json.loads((ROOT / "configs/experiments/g1_future_long_v1.json").read_text(encoding="utf-8"))


def long_fixture(tmp_path):
    path, saved, old, expected, sources = checkpoint_fixture(tmp_path)
    common = {**old["pair_config"], "suite": "libero_10", "stats_key": "libero_10_no_noops"}
    training = {**common, "arm": "A"}
    metadata = make_future_checkpoint_metadata(arm="A", seed=17, scorer_dimensions=common["scorer_dimensions"],
        training_config=training, pair_config=common, window_manifest_sha256="b"*64,
        model_revision="synthetic-base", stats_key=common["stats_key"], training_source_files=sources,
        update=25, validation_metric=.1, input_acceptance_sha256="e"*64)
    torch.save({**metadata, "estimator_state_dict": saved["estimator_state_dict"]}, path)
    receipt = make_future_deployment_receipt(path, metadata, training_config=training, pair_config=common,
        f01_report_sha256="c"*64, planned_updates=100, completed_updates=100, evaluations=old["evaluations"])
    expected.update(suite="libero_10", stats_key=common["stats_key"], input_acceptance_sha256="e"*64)
    return path, receipt, expected, sources


def test_long_checkpoint_requires_explicit_suite_and_own_input_receipt(tmp_path):
    path, receipt, expected, sources = long_fixture(tmp_path)
    loaded = load_future_selector_checkpoint(path, receipt, expected_versions=expected, expected_source_hashes=sources)
    assert loaded.provenance["suite"] == "libero_10"
    assert loaded.provenance["future_head_deployed"] is False
    for key in ("suite", "input_acceptance_sha256"):
        missing = {k:v for k,v in expected.items() if k != key}
        with pytest.raises(ValueError):
            load_future_selector_checkpoint(path, receipt, expected_versions=missing, expected_source_hashes=sources)


def test_legacy_spatial_checkpoint_cannot_enter_long_even_if_other_fields_match(tmp_path):
    path, saved, receipt, expected, sources = checkpoint_fixture(tmp_path)
    assert "suite" not in saved and "suite" not in receipt["metadata"]
    load_future_selector_checkpoint(path, receipt, expected_versions=expected, expected_source_hashes=sources)
    with pytest.raises(ValueError, match="suite"):
        load_future_selector_checkpoint(path, receipt, expected_versions={**expected, "suite":"libero_10"}, expected_source_hashes=sources)


def f01(suite="libero_10"):
    return dict(stage="G1-F01", status="passed", execution="real_frozen_openvla_l40", suite=suite,
        config_sha256="a"*64, window_manifest_sha256="b"*64, model_revision="synthetic-base",
        stats_key="libero_10_no_noops", input_acceptance_sha256="e"*64,
        input_version=INPUTS_VERSION, packing_version=PACKING_VERSION,
        checks={k:True for k in ("time_alignment", "no_future_leakage", "action_gradient_to_die",
            "future_gradient_to_die", "vla_parameters_unchanged", "hard128_packing",
            "dense_differentiable_parity", "official_input_action_parity")})


@pytest.mark.parametrize("change", ["suite", "missing_suite", "stats", "receipt", "missing_receipt", "parity"])
def test_long_f01_rejects_cross_suite_or_incomplete_bootstrap(change):
    report=f01(); kwargs=dict(pair_id="a"*64,window_manifest_sha256="b"*64,model_revision="synthetic-base",
                             suite="libero_10",input_acceptance_sha256="e"*64)
    require_future_f01(report, **kwargs)
    if change=="suite":report["suite"]="libero_spatial"
    elif change=="missing_suite":report.pop("suite")
    elif change=="stats":report["stats_key"]="libero_spatial_no_noops"
    elif change=="receipt":report["input_acceptance_sha256"]="f"*64
    elif change=="missing_receipt":report.pop("input_acceptance_sha256")
    else:report["checks"].pop("official_input_action_parity")
    with pytest.raises(ValueError):require_future_f01(report, **kwargs)


@pytest.mark.parametrize("change", [None,"default_suite","default_stats","spatial_stats","spatial_asset","revision","seed","budget","lambda","horizon"])
def test_real_long_registration_has_no_implicit_spatial_fallback(change):
    runner=script("run_g1_future");config=long_config()
    args=SimpleNamespace(suite="libero_10",stats_key="libero_10_no_noops")
    asset=SimpleNamespace(repository="moojink/openvla-7b-oft-finetuned-libero-10",revision=config["model_revision"])
    if change=="default_suite":del args.suite
    elif change=="default_stats":del args.stats_key
    elif change=="spatial_stats":config["stats_key"]="libero_spatial_no_noops"
    elif change=="spatial_asset":asset.repository="moojink/openvla-7b-oft-finetuned-libero-spatial"
    elif change=="revision":asset.revision="other"
    elif change=="seed":config["seed"]=23
    elif change=="budget":config["tokens_per_camera"]=128
    elif change=="lambda":config["future"]["weight_B"]=.2
    elif change=="horizon":config["future"]["horizon"]=16
    if change is None:assert runner.resolve_suite(args,config,asset)=="libero_10"
    else:
        with pytest.raises(ValueError):runner.resolve_suite(args,config,asset)


def panel():
    catalog=[dict(task_id=t,instruction=f"task {t}") for t in (0,3,5)]
    protocol=SimpleNamespace(payload=dict(suite="libero_10",task_catalog=catalog))
    rows=[dict(window_id=f"{t}-{ep}-{step}",episode_id=f"episode{ep}",start_step=step,
               split="train",task_name=f"task {t}") for t in (0,3,5) for ep in (2,1) for step in (8,0)]
    return dict(suite="libero_10",windows=rows),protocol


def test_fixed_acceptance_panel_uses_metadata_not_outcomes_and_excludes_validation():
    manifest,protocol=panel()
    manifest["windows"].insert(0,dict(manifest["windows"][0],split="validation",episode_id="episode0"))
    chosen=inputs_contract.select_input_windows(manifest,protocol)
    assert [r["window_id"] for r in chosen]==["0-1-0","3-1-0","5-1-0"]
    manifest["windows"].reverse()
    assert inputs_contract.select_input_windows(manifest,protocol)==chosen
    manifest["suite"]="libero_spatial"
    with pytest.raises(ValueError):inputs_contract.select_input_windows(manifest,protocol)


def input_report(tmp_path):
    manifest,protocol=panel();selected=inputs_contract.select_input_windows(manifest,protocol);config=long_config()
    kw=dict(config=config,window_manifest_sha256="b"*64,protocol_sha256="c"*64,
        asset_manifest_sha256="d"*64,source_files={"synthetic.py":"e"*64},
        verification_script_sha256="f"*64,selected_windows=selected)
    flags=("pixels_equal","prompt_equal","raw_camera_bridge_equal","native_physical_equal",
           "action_postprocess_equal","gripper_equal","demonstration_normalization_valid","passed")
    report={**{k:v for k,v in kw.items() if k not in ("config","selected_windows")},
        "stage":"G1-F00-input-parity","status":"passed","execution":"real_frozen_openvla_l40",
        "version":inputs_contract.INPUT_ACCEPTANCE_VERSION,"suite":"libero_10","stats_key":"libero_10_no_noops",
        "model_revision":config["model_revision"],"config_sha256":json_signature(config),
        "input_version":INPUTS_VERSION,"action_version":ACTION_VERSION,"packing_version":PACKING_VERSION,
        "checkpoint_unchanged":True,"test_opened":False,"policy_sample_forwards":6,"vision_forwards":6,"policy_attempts":6,
        "job_id":"synthetic-no-GPU","observations":[dict(window=w,proprio_max_abs_error=0.,dense_max_abs_error=0.,**{f:True for f in flags}) for w in selected]}
    events=[]
    for w in selected:
        for kind in ("official_dense","shared_dense"):
            meta=dict(call_id=len(events)//2,window_id=w["window_id"],kind=kind,job_id=report["job_id"])
            events.extend([dict(event="start",**meta),dict(event="complete",seconds=.01,**meta)])
    path=tmp_path/"synthetic_calls.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in events)+"\n",encoding="utf-8")
    report["calls_jsonl_sha256"]=file_sha256(path)
    return report,kw,path,events


@pytest.mark.parametrize("change", [None,"source","config","model","stage","window","pixels","nan","tolerance","unfinished"])
def test_input_receipt_is_bound_to_exact_source_and_complete_three_frame_parity(tmp_path,change):
    report,kw,path,events=input_report(tmp_path)
    inputs_contract.require_long_input_acceptance(report,**kw)
    inputs_contract.verify_input_acceptance_journal(path,report)
    if change is None:return
    if change=="source":report["source_files"]={"synthetic.py":"0"*64}
    elif change=="config":report["config_sha256"]="0"*64
    elif change=="model":report["model_revision"]="spatial"
    elif change=="stage":report["stage"]="G0"
    elif change=="window":report["observations"][0]["window"]={**report["observations"][0]["window"],"split":"validation"}
    elif change=="pixels":report["observations"][0]["pixels_equal"]=False
    elif change=="nan":report["observations"][0]["dense_max_abs_error"]=float("nan")
    elif change=="tolerance":report["observations"][0]["dense_max_abs_error"] = .003
    elif change=="unfinished":report["policy_attempts"]=7
    with pytest.raises(ValueError):inputs_contract.require_long_input_acceptance(report,**kw)


@pytest.mark.parametrize("change",["missing_completion","duplicate_kind","wrong_window","wrong_job","wrong_sha"])
def test_input_gate_cannot_use_incomplete_or_misattributed_query_journal(tmp_path,change):
    report,kw,path,events=input_report(tmp_path)
    if change=="missing_completion":events.pop()
    elif change=="duplicate_kind":events[2]["kind"]=events[3]["kind"]="official_dense"
    elif change=="wrong_window":events[0]["window_id"]=events[1]["window_id"]="other"
    elif change=="wrong_job":events[0]["job_id"]=events[1]["job_id"]="other"
    path.write_text("\n".join(json.dumps(e) for e in events)+"\n",encoding="utf-8")
    report["calls_jsonl_sha256"]="0"*64 if change=="wrong_sha" else file_sha256(path)
    with pytest.raises(ValueError):inputs_contract.verify_input_acceptance_journal(path,report)


def test_long_input_cli_rejects_spatial_before_model_loading(monkeypatch):
    module=script("verify_long_inputs")
    # Public interface must require explicit paths/suite. No GPU execution here.
    assert callable(module.verify_one) and callable(module.run)
    runner=module.training_runner()
    args=SimpleNamespace(suite="libero_spatial",stats_key="libero_10_no_noops")
    with pytest.raises(ValueError,match="suite"):
        runner.resolve_suite(args,long_config(),SimpleNamespace(repository="unused",revision="unused"))


@pytest.mark.parametrize("fault", [None, "proprio", "camera", "native_physical", "dense"])
def test_long_verify_one_exercises_public_interface_and_shared_real_packing_on_cpu(example,monkeypatch,fault):
    """Actual shared token policy, small frozen toy VLA; image functions stubbed.

    This checks runner interfaces/failure paths, not real OFT/TF equivalence.
    No acceptance report is written or presented as a real-model gate.
    """
    from io import BytesIO
    import numpy as np
    from PIL import Image
    from cti_vla.evaluation import libero_runtime as runtime
    module=script("verify_long_inputs")
    stats={"q01":[-1.]*7,"q99":[1.]*7,"min":[-1.]*7,"max":[1.]*7,"mask":[True]*6+[False]}
    prop_stats={"q01":[-1.]*8,"q99":[1.]*8,"mask":[True]*8}
    example.vla.norm_stats={"libero_10_no_noops":{"action":stats,"proprio":prop_stats}}
    ids,attention=example.batch.input_ids[:1],example.batch.attention_mask[:1]
    visual=example.batch.conditions.visual[:1]
    image=Image.fromarray(np.arange(48,dtype=np.uint8).reshape(4,4,3));buffer=BytesIO();image.save(buffer,format="PNG")
    raw_actions=np.linspace(-.8,.8,56,dtype=np.float32).reshape(8,7);raw_actions[:,-1]=np.arange(8)%2
    episode=SimpleNamespace(images=[buffer.getvalue()],wrist_images=[buffer.getvalue()],
        proprio=np.zeros((1,8),dtype=np.float32),instructions=["pick the object"],actions=raw_actions)
    def normalize(p,s):return runtime.normalize_eval_proprio(p,s)
    def processor(prompt,img,return_tensors):
        return {"input_ids":ids.clone(),"attention_mask":attention.clone(),
                "pixel_values":torch.tensor(np.asarray(img).mean(),dtype=torch.float32).reshape(1,1)}
    pixels=torch.cat([processor("",image,"")["pixel_values"]]*2,dim=1)
    actualprop=normalize(episode.proprio[0],prop_stats)
    prepared=dict(pixel_values=pixels,input_ids=ids,attention_mask=attention,
        normalized_proprio=torch.tensor(actualprop,dtype=torch.float32)[None],normalized_proprio_numpy=actualprop)
    monkeypatch.setattr(runtime,"prepare_rlds_eval_inputs",lambda *a,**kw:prepared)
    monkeypatch.setattr(runtime,"process_camera",lambda raw:Image.fromarray(raw[::-1,::-1].copy()))
    def unnormalize(n,key):
        return np.where(np.array(stats["mask"]),.5*(np.asarray(n)+1)*(np.array(stats["q99"])-stats["q01"]+1e-8)+stats["q01"],n)
    example.vla._unnormalize_actions=unnormalize
    example.vla._process_vision_features=lambda *a:visual
    public_calls=[]
    def predict_action(**kw):
        public_calls.append(kw)
        assert kw["unnorm_key"]=="libero_10_no_noops" and kw["use_film"] is False
        normalized=example.teacher.forward_from_full_tokens(visual,torch.tensor(kw["proprio"],dtype=torch.float32)[None],
            input_ids=kw["input_ids"],attention_mask=kw["attention_mask"])
        physical=unnormalize(normalized.float().numpy()[0],kw["unnorm_key"])
        if fault=="native_physical":physical=physical+.1
        if fault=="dense":normalized=normalized+.01
        return physical,normalized
    example.vla.predict_action=predict_action
    components=SimpleNamespace(vla=example.vla,action_head=SimpleNamespace(predict_action=lambda hidden:hidden),
                               proprio_projector=example.teacher.proprio_projector)
    reference={"center_crop_image":lambda im:Image.fromarray(np.asarray(im)),
        "resize_image_for_policy":lambda im,size:np.asarray(im),
        "get_libero_image":lambda obs:obs["agentview_image"][::-1,::-1],
        "get_libero_wrist_image":lambda obs:obs["robot0_eye_in_hand_image"][::-1,::-1],
        "normalize_proprio":normalize,"normalize_gripper_action":lambda a,binarize:np.array(a,copy=True),
        "invert_gripper_action":runtime.postprocess_actions}
    if fault=="proprio":reference["normalize_proprio"]=lambda p,s:normalize(p,s)+.1
    if fault=="camera":reference["get_libero_image"]=lambda obs:obs["agentview_image"]
    queries=[]
    def query(kind,fn):queries.append(kind);return fn()
    window=dict(start_step=0,action_start=0,action_stop_exclusive=8,window_id="synthetic-window")
    if fault is None:
        row=module.verify_one(episode,window,components,processor,example.teacher,reference,
            stats_key="libero_10_no_noops",query=query)
        assert row["passed"] and row["dense_max_abs_error"]==0
        assert row["demonstration_inverse_max_abs_error"] < 1e-5
        assert len(public_calls)==1 and queries==["official_dense","shared_dense"]
    else:
        with pytest.raises(RuntimeError):
            module.verify_one(episode,window,components,processor,example.teacher,reference,
                stats_key="libero_10_no_noops",query=query)
        if fault in ("proprio","camera"):assert queries==[]
