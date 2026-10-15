"""Read-only local review of completed Long64 seed17/23/41 training evidence.

Not part of the frozen producer snapshot. No GPU, cache tensor or checkpoint
loading. Both reviews are written only after every requested check succeeds.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cti_vla.evaluation.future_runtime import _metadata, _validate_receipt
from cti_vla.evaluation.future_budget_reuse import SCHEMA, require_budget_f01
from cti_vla.evaluation.teacher_diagnostics import json_signature

ROUND = "g1_future_long_k64_v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite_tree(value, context):
    if isinstance(value, float):
        require(math.isfinite(value), f"nonfinite number in {context}")
    elif isinstance(value, dict):
        for key, item in value.items():
            finite_tree(item, f"{context}.{key}")
    elif isinstance(value, list):
        for item in value:
            finite_tree(item, context)


def read(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    finite_tree(value, str(path))
    return value


def events(path):
    require(Path(path).is_file(), f"missing durable events: {path}")
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]
    finite_tree(rows, str(path))
    return rows


def same_number(a, b, context, tolerance=1e-12):
    require(math.isclose(a, b, rel_tol=tolerance, abs_tol=tolerance), context)


def review_seed(root, seed, inventory, experiment, parent, initials):
    run = root / f"results/{ROUND}/seed{seed}"
    training = run / "training"
    required = [training / name for name in ("training_summary.json", "train_finalization.json",
        "training_order.json", "cache_index.json", "input_cache_reuse_receipt.json", "same_budget_f01_receipt.json",
        "registered_config.json", "registered_windows.json")]
    require(all(p.is_file() for p in required), f"seed{seed}: completed training evidence missing")
    submission = read(run / "submission_train.json")
    job_id = submission["job_id"]
    require(isinstance(job_id, str) and job_id.isdigit() and submission["source_sha256"] == inventory["source_sha256"],
            "unregistered job or source snapshot")
    config_path = root / experiment["new_configs"][str(seed)]["path"]
    require(sha(config_path) == experiment["new_configs"][str(seed)]["sha256"], "target config changed")
    config = read(config_path)
    require(config["seed"] == seed and config["run_id"] == f"g1_future_long_k64_seed{seed}_v1" and config["tokens_per_camera"] == 32, "wrong target seed/budget")
    require({k:v for k,v in config.items() if k not in ("seed", "run_id", "tokens_per_camera")} ==
            {k:v for k,v in parent["config"].items() if k not in ("seed", "run_id", "tokens_per_camera")}, "non-seed/budget configuration change")
    require(read(training / "registered_config.json") == config, "registered configuration differs")
    require(read(training / "registered_windows.json") == parent["windows"], "data panel changed")
    registration_path = run / "budget_reuse_registration.json"
    registration = read(registration_path)
    require(submission["registration_sha256"] == registration["experiment_registration_sha256"] ==
            sha(root / f"configs/experiments/{ROUND}.json"), "submitted experiment registration changed")
    require(submission["training_seed"] == seed and submission["mode"] == "train" and submission["experiment"] == ROUND, "submission is not this training run")
    require(registration["schema"] == SCHEMA and registration["allowed_config_changes"] == ["seed", "run_id", "tokens_per_camera"], "wrong budget-cache reuse schema")
    require(registration["target_seed"] == seed and registration["target_config_identity_sha256"] == json_signature(config), "reuse target differs")
    sources = registration["target_source_files"]
    require(all(inventory["files"].get(k) == digest == sha(root / k) for k,digest in sources.items()), "producer source differs from frozen inventory")
    receipt = read(training / "input_cache_reuse_receipt.json")
    require(receipt["status"] == "verified_input_cache_reuse_new64_F01_required" and receipt["new_GPU_calls"] == 0 and
            receipt["inherited_old128_F01"] is False and receipt["tokens_per_camera"] == 32, "inheritance misrepresented")
    require(receipt["registration_sha256"] == sha(registration_path) and receipt["parent_files"] == registration["parent_files"], "inheritance not bound to original registration")
    require(receipt["parent_input_acceptance_sha256"] == parent["input_sha"] and receipt["target_seed"] == seed and
            receipt["target_run_id"] == config["run_id"] and receipt["target_config_identity_sha256"] == json_signature(config) and
            receipt["target_source_files"] == sources, "parent/target input-cache identity mismatch")
    gate = require_budget_f01(parent["f01_path"], config=config, source_root=root,
        window_manifest_sha256=parent["windows_sha"], input_acceptance_sha256=parent["input_sha"])
    require(read(training / "same_budget_f01_receipt.json") == gate["receipt"], "new64 F01 or same-budget seed inheritance changed")
    # The old producer/cache bytes remain the identity; no relabeling to new seed.
    require(sha(training / "cache_index.json") == parent["cache_sha"], "reused cache index changed")
    require(not (training / "cost_events.jsonl").exists() or not (training / "cost_events.jsonl").read_bytes().strip(), "new cache production is forbidden")
    cache = read(training / "cache_index.json")
    train = [e["identity"]["window"] for e in cache if e["identity"]["window"]["split"] == "train"]
    validation = [e["identity"]["window"] for e in cache if e["identity"]["window"]["split"] == "validation"]
    require(len(train) == 90 and len(validation) == 60 and len(cache) == 150, "wrong cache counts")
    require(not {r["episode_id"] for r in train} & {r["episode_id"] for r in validation}, "episode split overlap")
    order = read(training / "training_order.json")
    rng = random.Random(seed); flat = []
    while len(flat) < 800:
        epoch = list(range(90)); rng.shuffle(epoch); flat.extend(epoch)
    expected_order = [[train[j]["window_id"] for j in flat[u*8:(u+1)*8]] for u in range(100)]
    require(order["seed"] == seed and order["updates"] == expected_order and order["order_sha256"] == json_signature(expected_order), "seeded800-sample schedule mismatch")
    require(order["initial_scorer_sha256"] == initials[seed], "initial state identity mismatch")
    require(order["order_sha256"] == parent["old_reports"][seed]["sample_order_sha256"], "64/128 matched-seed data order changed")
    final = read(training / "train_finalization.json")
    total = read(training / "training_summary.json")
    require(final["status"] == "verified" and final["checkpoint_unchanged"] is True and final["job_id"] == job_id and
            final["result_status"] == "completed" and final["result_sha256"] == sha(training / "training_summary.json"), "training finalization mismatch")
    require(final["checkpoint"] == parent["finalization"]["checkpoint"], "base checkpoint changed")
    arm_metrics, costs, initial_rows, best_rows, ends_by_arm = {}, {}, {}, {}, {}
    for arm in ("A", "B"):
        arm_dir = training / arm
        report = read(arm_dir / "training_report.json")
        deployment = read(arm_dir / "deployment_receipt.json")
        metadata = _metadata(deployment["metadata"])
        _validate_receipt(deployment, metadata)
        require(total["arms"][arm] == report and report["status"] == "completed" and report["arm"] == arm, "arm report completion mismatch")
        require(report["training_updates_completed"] == 100 and report["attempt_start_update"] == 1 and report["job_id"] == job_id, "not a fresh100-update run")
        require(report["initial_scorer_sha256"] == initials[seed] and report["sample_order_sha256"] == order["order_sha256"], "A/B initialization/order differ")
        require(report["source_files"] == sources and report["config_sha256"] == json_signature({**config,"arm":arm}) and
                report["window_manifest_sha256"] == parent["windows_sha"], "arm source/config/data mismatch")
        require(report["suite"] == "libero_10" and report["input_acceptance_sha256"] == parent["input_sha"] and
                report["f01_report_sha256"] == parent["f01_sha"], "wrong inherited engineering parent")
        require(report["vla_parameters_unchanged"] is True and report["vla_parameter_sha256"] == parent["f01"]["vla_parameter_sha256"], "VLA parameter bytes changed")
        expected_path = experiment["new_configs"][str(seed)]["checkpoint_root_server"] + f"/{arm}/best.pt"
        require(report["best_checkpoint"] == expected_path and report["best_checkpoint_sha256"] == deployment["checkpoint_sha256"], "wrong new checkpoint reference")
        require(deployment["pair_config"] == config and deployment["training_config"] == {**config,"arm":arm} and
                metadata["seed"] == seed and metadata["arm"] == arm and metadata["training_source_files"] == sources and
                metadata["input_acceptance_sha256"] == parent["input_sha"] and deployment["f01_report_sha256"] == parent["f01_sha"], "deployment receipt identity mismatch")
        require(metadata["visual_tokens"] == 64 and metadata["per_camera_budgets"] == [32, 32], "deployment checkpoint is not trained64 budget")
        require(report["future_head_parameters"] == (0 if arm == "A" else 277248), "unexpected future training head")
        rows = events(arm_dir / "cost_events.jsonl")
        require(len(rows) == 200, "missing/repeated update event")
        ends = []
        for update in range(1,101):
            start,end = rows[(update-1)*2:update*2]
            require(start["event"] == "update_start" and end["event"] == "update_end" and start["update"] == end["update"] == update and
                    start["job_id"] == end["job_id"] == job_id and start["window_ids"] == expected_order[update-1] and
                    end["forward_backward_samples"] == 8, "update sample/cost ledger mismatch")
            require(all(end[k] >= 0 for k in ("loss","action_loss","teacher_l1","demonstration_l1","seconds","grad_norm")), "invalid update values")
            same_number(end["alpha"], .1+.95*(1+math.cos(math.pi*(update-1)/99)), "alpha schedule differs")
            same_number(end["action_loss"], .5*(end["teacher_l1"]+end["demonstration_l1"]), "action loss differs", 1e-7)
            same_number(end["loss"], end["action_loss"]+(.1*end["future_mse"] if arm=="B" else 0), "future loss weight differs", 1e-7)
            ends.append(end)
        ends_by_arm[arm] = ends
        evaluations = []; validated = {}
        for update in (0,25,50,75,100):
            value = read(arm_dir / f"validation_{update:04d}.json")
            require(value["update"] == update and value["arm"] == arm and value["windows"] == 60 and
                    [r["window"] for r in value["observations"]] == validation, "validation panel identity differs")
            for row in value["observations"]:
                ids = row["retained_indices"]
                require(ids == sorted(set(ids)) and len(ids)==64 and sum(i<256 for i in ids)==32 and min(ids)>=0 and max(ids)<512,
                        "hard64 camera budget/order invalid")
                require(np.asarray(row["normalized_actions"]).shape == (8,7), "action chunk shape invalid")
                require(row["teacher_l1"]>=0 and row["demonstration_l1"]>=0, "negative L1")
            same_number(value["validation_metric"], np.mean([r["teacher_l1"] for r in value["observations"]]), "validation teacher mean")
            same_number(value["demonstration_l1"], np.mean([r["demonstration_l1"] for r in value["observations"]]), "validation GT mean")
            same_number(value["teacher_l1_p95"], np.percentile([r["teacher_l1"] for r in value["observations"]],95), "validation p95")
            if arm=="B":
                for key in ("future_mse","future_zero_visual_mse","future_reversed_action_mse"):
                    require(all(r[key]>=0 for r in value["observations"]), "negative future MSE")
                    same_number(value[key], np.mean([r[key] for r in value["observations"]]), "future diagnostic mean")
            evaluations.append({"update":update,"validation_metric":value["validation_metric"]});validated[update]=value
        require(report["evaluations"] == evaluations == deployment["evaluations"], "validation history differs")
        best = min(evaluations,key=lambda r:(r["validation_metric"],r["update"]))
        require(report["best_update"] == metadata["update"] == best["update"] and
                report["best_validation_metric"] == metadata["validation_metric"] == best["validation_metric"], "earliest-best rule violated")
        initial_rows[arm]=validated[0]["observations"];best_rows[arm]=validated[best["update"]]["observations"]
        arm_metrics[arm]={"best_update":best["update"],"teacher_l1":best["validation_metric"],
            "demonstration_l1":validated[best["update"]]["demonstration_l1"], "best_checkpoint_sha256":report["best_checkpoint_sha256"],
            "future_mse":validated[best["update"]].get("future_mse")}
        costs[arm]={"update_pairs":100,"forward_backward_samples":800,"saved_validation_calls":300,
            "update_seconds":sum(e["seconds"] for e in ends),"validation_seconds":sum(v["seconds"] for v in validated.values()),
            "wall_seconds_this_attempt":report["wall_seconds_this_attempt"]}
    require(initial_rows["A"] == [{k:v for k,v in r.items() if not k.startswith("future_")} for r in initial_rows["B"]], "A/B initial behavior differs")
    for key in ("action_loss","teacher_l1","demonstration_l1"):
        same_number(ends_by_arm["A"][0][key],ends_by_arm["B"][0][key],"first pre-update action losses differ")
    accounting=read(root/f"results/{ROUND}/slurm_accounting.json")
    jobs=[r for r in accounting["jobs"] if r["job_id"]==job_id]
    require(len(jobs)==1 and jobs[0]["state"]=="COMPLETED" and jobs[0]["exit_code"]=="0:0" and
            jobs[0]["allocated_gpus"]==1 and jobs[0]["elapsed_seconds"]>0 and jobs[0]["scope"]=="train" and
            jobs[0]["training_seed"]==seed, "completed new-job billing required")
    costs.update({"new_job_id":job_id,"allocated_gpu_seconds":jobs[0]["elapsed_seconds"],
        "allocated_gpu_hours":jobs[0]["elapsed_seconds"]/3600,"new_cache_teacher_forwards":0,"new_vision_backbone_forwards":0,
        "source_derived_logical_action_forwards":2200,"shared_parent_cache_forwards_not_recharged":150,
        "scope":"Only this registered training job. The separate new64 F01, collection/eval/profile and any failed allocations belong to round total accounting. Parent128 cache cost is not charged again. Nested timers are not added to allocation cost."})
    intersections=[len(set(a["retained_indices"])&set(b["retained_indices"])) for a,b in zip(best_rows["A"],best_rows["B"])]
    files={p.relative_to(root).as_posix():sha(p) for p in sorted(training.rglob('*')) if p.is_file() and p.name!='independent_review.json'}
    for path in (registration_path,run/"submission_train.json",config_path):files[path.relative_to(root).as_posix()]=sha(path)
    # Billing is copied explicitly so later addition of closed-loop rows cannot
    # silently change this review's accounting scope.
    costs["slurm_accounting_row"] = jobs[0]
    return {"schema":"long64-g1f-training-independent-review-v1","status":"passed","training_seed":seed,"job_id":job_id,
        "reviewed_utc":datetime.now(timezone.utc).isoformat(),"source_snapshot_identity_sha256":inventory["source_sha256"],
        "scope":"Completed training evidence only; not a new F01 measurement, closed-loop result or permission to expand experiments.",
        "checks":{"matched100updates800samples":True,"fresh_seed_initialization":True,"same_seed_AB_initialization_order":True,
            "all_three_reference_seed_initialization_hashes_distinct":True,"earliest_best_validation_rule":True,"new_checkpoint_receipt_identity":True,
            "old_input_cache_identity_new64_engineering_gate":True,"no_cache_reproduction_events":True,"frozen_VLA_parameter_SHA":True,
            "all_numeric_values_finite":True,"only_registered_new_job_in_cost":True},
        "initial_scorer_sha256_by_seed":{str(k):v for k,v in initials.items()},"sample_order_sha256":order["order_sha256"],
        "arms":arm_metrics,"mean_best_hard_intersection_over64":float(np.mean(intersections)/64),"cost":costs,
        "evidence_sha256":files,"review_script_sha256":sha(Path(__file__)),
        "limitations":["Local non-weight evidence review; server-only cache/checkpoint tensors are not reloaded or rehashed locally.",
            "Base/cache immutability derives from completed frozen producer checks and exact receipts, with source/config identities rechecked here.",
            "Teacher/GT arrays are absent locally: reported per-window L1 values are reaggregated, not independently recalculated from references.",
            "Offline results are development-set descriptions, not paired closed-loop evidence."]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--seed',type=int,choices=(17,23,41),action='append',help='Review a completed seed independently; omit for all three')
    parser.add_argument('--check-only',action='store_true',help='Require completed evidence but do not write reviews')
    args=parser.parse_args();root=args.root.resolve();new=root/f'results/{ROUND}'
    selected=list(dict.fromkeys(args.seed or (17,23,41)))
    inventory_path=new/f'source_{ROUND}.json'
    inventory=read(inventory_path)
    require(inventory['source_sha256']==hashlib.sha256(json.dumps(inventory['files'],sort_keys=True).encode()).hexdigest(),'wrong frozen source identity')
    experiment_path=root/f'configs/experiments/{ROUND}.json'
    experiment=read(experiment_path)
    require(inventory['files'][experiment_path.relative_to(root).as_posix()]==sha(experiment_path),'experiment was not frozen in source snapshot')
    for relative,digest in experiment['frozen_evidence_sha256'].items():
        require(sha(root/relative)==digest,'parent preregistered evidence changed: '+relative)
    parent_root=root/'results/g1_future_long_v1'
    f01_path=new/'acceptance/f01_acceptance.json'
    parent={'config':read(root/'configs/experiments/g1_future_long_v1.json'),
        'windows':read(root/'configs/manifests/long_future_v1/windows.json'),
        'windows_sha':sha(root/'configs/manifests/long_future_v1/windows.json'),
        'cache_sha':sha(parent_root/'training/cache_index.json'),
        'f01_path':f01_path,'f01':read(f01_path),'f01_sha':sha(f01_path),
        'input_sha':sha(parent_root/'inputs/input_acceptance.json'),'finalization':read(new/'acceptance/acceptance_finalization.json'),
        'old_reports':{}}
    initials={};historical_checkpoint_digests=[]
    for seed in (17,23,41):
        old=parent_root if seed==17 else root/f'results/g1_future_long_multiseed_v1/seed{seed}'
        reports=[read(old/f'training/{arm}/training_report.json') for arm in ('A','B')]
        require(reports[0]['initial_scorer_sha256']==reports[1]['initial_scorer_sha256'],'old matched seed reference invalid')
        parent['old_reports'][seed]=reports[0]
        initials[seed]=reports[0]['initial_scorer_sha256']
        historical_checkpoint_digests.extend(r['best_checkpoint_sha256'] for r in reports)
    require(len(set(initials.values()))==3,'registered seed initializations are not distinct')
    actual_available=[]
    for seed in (17,23,41):
        order_path=new/f'seed{seed}/training/training_order.json'
        if order_path.is_file():
            require(read(order_path)['initial_scorer_sha256']==initials[seed],'actual new seed initialization differs from matching fresh reference')
            actual_available.append(seed)
    reviews=[review_seed(root,s,inventory,experiment,parent,initials) for s in selected]
    checkpoint_digests=[r['arms'][arm]['best_checkpoint_sha256'] for r in reviews for arm in ('A','B')]
    require(len(set(checkpoint_digests))==2*len(selected) and not set(checkpoint_digests)&set(historical_checkpoint_digests),
            'new checkpoint digest duplicates another seed/arm or an old128 checkpoint')
    for review in reviews:
        review['actual_new_initializations_verified']=actual_available
        review['checks']['all_three_actual_initializations_available']=len(actual_available)==3
        for path in (inventory_path,experiment_path,f01_path,new/'acceptance/acceptance_finalization.json'):
            review['evidence_sha256'][path.relative_to(root).as_posix()]=sha(path)
        require(all(sha(root/p)==digest for p,digest in review['evidence_sha256'].items()),'evidence changed during review')
    if not args.check_only:
        outputs=[new/f"seed{r['training_seed']}/training/independent_review.json" for r in reviews]
        for path,review in zip(outputs,reviews):
            if path.exists():
                old=read(path)
                require(old['status']=='passed' and old['job_id']==review['job_id'] and old['evidence_sha256']==review['evidence_sha256']
                        and old['arms']==review['arms'] and old['review_script_sha256']==review['review_script_sha256'],
                        'existing review changed; retain it and investigate instead of overwriting')
                continue
            temporary=path.with_suffix('.json.tmp')
            require(not temporary.exists(),'unfinished review temporary file exists')
            temporary.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temporary.replace(path)
        if set(selected)=={17,23,41}:
            summary={'schema':'long64-training-three-seed-review-v1','status':'passed','seeds':[17,23,41],
                'all_three_actual_initializations_available':len(actual_available)==3,
                'initial_scorer_sha256_by_seed':{str(k):v for k,v in initials.items()},
                'total_updates':600,'total_forward_backward_samples':4800,
                'reviews':{str(s):{'path':f'seed{s}/training/independent_review.json',
                    'sha256':sha(new/f'seed{s}/training/independent_review.json')} for s in (17,23,41)},
                'new_training_allocated_gpu_seconds':sum(r['cost']['allocated_gpu_seconds'] for r in reviews),
                'source_snapshot_identity_sha256':inventory['source_sha256'],'review_script_sha256':sha(Path(__file__)),
                'reviewed_utc':datetime.now(timezone.utc).isoformat()}
            summary_path=new/'training_independent_review.json'
            require(not summary_path.exists(),'existing three-seed review must not be overwritten')
            summary_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'passed','reviews_written':not args.check_only,'seeds':[r['training_seed'] for r in reviews],
        'summary':[{k:r[k] for k in ('training_seed','job_id','arms','cost')} for r in reviews]},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
