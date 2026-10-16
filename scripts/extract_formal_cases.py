"""Extract preregistered final cases locally; never run policies or read states.

No cases are published until all four released, root-reviewed final runs are
complete. Missing evidence is pending; corrupted evidence is an error. Synthetic
fixtures use the same gates and require an explicit label on every output.
"""
from __future__ import annotations

import argparse
from collections import Counter
from functools import lru_cache
import hashlib
from html import escape
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SCHEMA = "formal_main_v2"
VERSION = "formal-fixed-cases-v1"
SUITES = ("libero_10", "libero_spatial", "libero_object", "libero_goal")
BUDGETS, SEEDS = (256, 128, 64), (17, 23, 41)
CATEGORIES = ("B_only_success", "A_only_success", "both_failure", "both_success")
RULE = "Within each suite/budget/seed, numeric (task_id, source_state_index) first in each category; never replace an unavailable token diagnostic."
SYNTHETIC = "SYNTHETIC — NOT EXPERIMENTAL RESULTS"
SOURCES = ("scripts/extract_formal_cases.py", "scripts/review_formal_downstream.py",
    "scripts/formal_execution_manifests.py", "scripts/ops/formal_downstream_supervisor.py",
    "scripts/analyze_formal.py", "scripts/ops/formal_evaluation_adapter.py", "scripts/server/run_formal_downstream.py")


class PendingEvidence(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


@lru_cache(maxsize=None)
def load(name):
    spec = importlib.util.spec_from_file_location("fixed_cases_" + Path(name).stem, ROOT / name)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def checked_path(project, value):
    raw = Path(value)
    path = (Path(project) / raw).absolute() if not raw.is_absolute() else raw.absolute()
    require(path.resolve() == path and Path(project).resolve() in path.parents, "Case paths must be direct project descendants")
    parts = path.relative_to(project).parts
    require(not any("sealed" in p.lower() or p.lower() in ("weights", "checkpoints") for p in parts)
        and path.suffix.lower() not in (".pt", ".pth", ".bin", ".ckpt", ".safetensors", ".pkl", ".pickle", ".init", ".pruned_init")
        and path.name.lower() != "init_states_test.json"
        and not (path.name == "panel.json" and "final" in parts), "Case extraction cannot access weights or final state values")
    return path


def read_ref(evidence, ref, label):
    if not isinstance(ref, dict) or not ref.get("path") or not ref.get("sha256"):
        raise PendingEvidence(label + ": missing SHA-bound reference")
    require(re.fullmatch(r"[0-9a-f]{64}", ref["sha256"]) is not None, "Invalid evidence SHA256: " + label)
    value = ref["path"]
    require(isinstance(value, str) and not PurePosixPath(value).is_absolute() and ".." not in PurePosixPath(value).parts
        and str(PurePosixPath(value)) == value and ":" not in value and "\\" not in value,
        "Evidence references must use canonical project-relative paths")
    path = checked_path(evidence.project, ref["path"])
    require(path.suffix == ".json", "Only JSON metadata references are accepted")
    if not path.is_file():
        raise PendingEvidence(label + ": missing file")
    require(evidence.watch(path) == ref["sha256"], "Evidence SHA256 mismatch: " + label)
    return evidence.read(path)


def locate_lines(path):
    """Preserve the exact original UTF-8 bytes, LF, one-based line and byte offset."""
    offset = 0
    with Path(path).open("rb") as stream:
        for index, raw in enumerate(stream, 1):
            require(raw.endswith(b"\n") and raw.strip(), "Incomplete/empty JSONL tail retained without repair")
            row = json.loads(raw, parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Nonfinite JSON: " + x)))
            require(isinstance(row, dict), "Trial event must be an object")
            yield row, dict(line=index, byte_offset=offset, bytes=len(raw), line_sha256=hashlib.sha256(raw).hexdigest())
            offset += len(raw)


def category(a, b):
    require(type(a) is bool and type(b) is bool, "Success must be boolean")
    return ("both_success" if a else "B_only_success") if b else ("A_only_success" if a else "both_failure")


def select_pair(states, outcomes, *, suite, budget, seed):
    """Pure fixed selection; no diagnostic availability may influence its order."""
    selected, counts = {}, Counter()
    for state in sorted(states, key=lambda s: (s["task_id"], s["source_state_index"])):
        require(type(state["task_id"]) is int and type(state["source_state_index"]) is int, "Numeric task/index required")
        a, b = (outcomes.get(state["trial_id"] + f":{arm}{budget}_seed{seed}") for arm in ("A", "B"))
        if a is None or b is None:
            raise PendingEvidence("Incomplete A/B pair: " + state["trial_id"])
        label = category(a["success"], b["success"])
        counts[label] += 1
        selected.setdefault(label, dict(state={k: state[k] for k in ("trial_id", "task_id", "task_name", "source_state_index", "initial_state_sha256")}, A=a, B=b))
    return [dict(case_id=f"{suite}_k{budget}_seed{seed}_{label}", suite=suite, visual_tokens=budget, seed=seed,
        category=label, status="present" if label in selected else "missing", candidate_count=counts[label],
        selection=selected.get(label), token_comparison=None) for label in CATEGORIES]


def compare_first(a, b, budget):
    """Diagnostic only. Do not search later matching chunks or replace the case."""
    result = dict(status="unavailable", scope="First control_step=0 observation only; later closed-loop inputs can diverge",
        action_difference=None, teacher_or_demo_action_error=None)
    first = []
    for arm, row in (("A", a), ("B", b)):
        chunks = row.get("chunks")
        if not isinstance(chunks, list) or not chunks or not isinstance(chunks[0], dict):
            return {**result, "reason": arm + "_first_chunk_missing_or_invalid"}
        chunk = chunks[0]
        if type(chunk.get("control_step")) is not int or chunk["control_step"] != 0:
            return {**result, "reason": arm + "_first_chunk_not_control_step_zero"}
        observed = chunk.get("observation_sha256")
        if not isinstance(observed, str) or not re.fullmatch(r"[0-9a-f]{64}", observed):
            return {**result, "reason": arm + "_first_observation_hash_invalid"}
        kept = chunk.get("metadata", {}).get("retained_indices") if isinstance(chunk.get("metadata"), dict) else None
        if (not isinstance(kept, list) or len(kept) != budget or any(type(i) is not int or not 0 <= i < 512 for i in kept)
                or kept != sorted(set(kept)) or sum(i < 256 for i in kept) != budget // 2):
            return {**result, "reason": arm + "_first_token_set_invalid"}
        first.append(chunk)
    left, right = first
    if left["observation_sha256"] != right["observation_sha256"]:
        return {**result, "reason": "first_observation_hash_mismatch", "A_observation_sha256": left["observation_sha256"],
            "B_observation_sha256": right["observation_sha256"]}
    aset, bset = (set(c["metadata"]["retained_indices"]) for c in first)
    cameras = []
    for camera, name in enumerate(("agentview", "wrist")):
        lo, hi = camera * 256, (camera + 1) * 256
        aa, bb = ({i - lo for i in kept if lo <= i < hi} for kept in (aset, bset))
        cameras.append(dict(camera_id=camera, name=name, common=sorted(aa & bb), A_only=sorted(aa - bb), B_only=sorted(bb - aa),
            intersection_over_budget=len(aa & bb) / (budget // 2), jaccard=len(aa & bb) / len(aa | bb)))
    result.update(status="available", observation_sha256=left["observation_sha256"], A_retained_indices=sorted(aset),
        B_retained_indices=sorted(bset), intersection_over_budget=len(aset & bset) / budget,
        jaccard=len(aset & bset) / len(aset | bset), cameras=cameras)
    actions = [c.get("normalized_actions") for c in first]
    valid = all(isinstance(x, list) and len(x) == 8 and all(isinstance(r, list) and len(r) == 7 and
        all(type(v) in (int, float) and math.isfinite(v) for v in r) for r in x) for x in actions)
    if valid:
        result["action_difference"] = dict(metric="mean_absolute_A_minus_B_normalized_chunk8", value=sum(
            abs(x - y) for ra, rb in zip(*actions) for x, y in zip(ra, rb)) / 56,
            interpretation="A/B output difference on this same input; not teacher/demo error or latency")
    return result


def verified_inputs(project, spec, *, synthetic):
    """Reuse the actual release, E04 consumer and complete root audit producer."""
    from cti_vla.data.formal_initial_states import validate_formal_final_registry
    from cti_vla.evaluation.formal_trials import expected_method_ids, validate_final_release, validate_execution_manifest
    helper, scheduler, reviewer = (load(p) for p in ("scripts/formal_execution_manifests.py",
        "scripts/ops/formal_downstream_supervisor.py", "scripts/review_formal_downstream.py"))
    evidence = helper.Evidence(project)
    require(spec.get("schema") == SCHEMA and spec.get("kind") == "formal_fixed_case_inputs", "Wrong case input schema")
    require(spec.get("synthetic", False) is synthetic, "Synthetic input requires matching explicit --synthetic")
    for name in ("registration", "source_inventory", "supervisor_state", "global_freeze", "root_release"):
        if not spec.get(name):
            raise PendingEvidence(name + ": not supplied")
    require(spec["registration"]["path"] == scheduler.REGISTRATION and spec["source_inventory"]["path"] == scheduler.SOURCE_INVENTORY,
        "Use the registered formal configuration and frozen173-file inventory")
    registration = read_ref(evidence, spec["registration"], "registration")
    helper.registration_contract(evidence, scheduler.REGISTRATION)
    read_ref(evidence, spec["source_inventory"], "source_inventory")
    scheduler.check_source(evidence, helper, scheduler.SOURCE_INVENTORY)
    matrix = read_ref(evidence, spec["global_freeze"], "global_freeze")
    directory = PurePosixPath(spec["global_freeze"]["path"]).parent
    require(PurePosixPath(spec["global_freeze"]["path"]).name == "global_freeze.json"
        and spec["root_release"]["path"] == str(directory / "root_release.json"), "Use the same immutable global freeze/release directory")
    helper.release_global(evidence, registration, str(directory), release=False)
    release = read_ref(evidence, spec["root_release"], "root_release")
    validate_final_release(release, matrix, registration_sha256=scheduler.signature(registration))
    # Final registry, reviews and trial paths are not followed before release.
    refs = spec.get("final_reviews", {})
    require(isinstance(refs, dict), "This interface requires one final root review per suite")
    if set(refs) != set(SUITES):
        raise PendingEvidence("All four final root reviews are required; no partial case selection")
    require(all(isinstance(ref, dict) for ref in refs.values()), "Multiple final runs per suite are not combined by this interface")
    state = read_ref(evidence, spec["supervisor_state"], "supervisor_state")
    jobs = scheduler.formal_jobs(state)
    runs, registries = {}, {}
    for suite in SUITES:
        reference = refs[suite]
        saved = read_ref(evidence, reference, suite + ":root_review")
        checked = scheduler.require_root_review(evidence, reference["path"], jobs, expected_stage="final")
        if not checked["scientific_complete"]:
            raise PendingEvidence(suite + ": root review reports incomplete final work")
        rebuilt = reviewer.review(checked["job_id"], checked["pull_receipt"], project=project, state=state, scheduler=scheduler, helper=helper)
        # Wall-clock audit timestamps and the state snapshot's evidence identity
        # can differ. Scientific rows, history, accounting and producer identity cannot.
        for key, value in rebuilt.items():
            if key not in ("reviewed_utc", "evidence_sha256", "audit_source_sha256"):
                require(saved.get(key) == value, "Saved root review differs from reconstructed evidence: " + key)
        require(rebuilt["scientific_complete"] and rebuilt["expected_trials"] == 8800 and rebuilt["completed_trials"] == 8800,
            "Each suite needs all400 final states and22 methods")
        for name, checksum in rebuilt["evidence_sha256"].items():
            checked_path(project, name)
            require(evidence.watch(name) == checksum, "Reconstructed root evidence changed")
        output = reviewer.remote_relative(checked["run_root"], scheduler)
        config = evidence.read(output + "/config.json")
        manifest = config["manifest"]
        mids = validate_execution_manifest(manifest, registration_sha256=scheduler.signature(registration))
        require(manifest.get("suite") == suite and manifest.get("split") == "final" and mids == expected_method_ids()
            and manifest.get("global_freeze") == matrix and manifest.get("release") == release, "Final run differs from the complete released matrix")
        registry_path = registration["suites"][suite]["initial_states_root"] + "/final_registry.json"
        checked_path(project, registry_path)
        require(evidence.watch(registry_path) == matrix["suites"][suite]["final_registry_sha256"], "Final identity index changed")
        registry = evidence.read(registry_path)
        validate_formal_final_registry(registry)
        require(registry["suite"] == suite and not any("initial_state" in row for row in registry["states"]), "Only final identity metadata is accepted")
        registries[suite] = registry
        ledger = output + "/trials.jsonl"
        require(checked["verified_files"].get(ledger) == evidence.watch(ledger), "Trial ledger is not SHA-pulled root evidence")
        runs[suite] = dict(trials=ledger, trials_sha256=evidence.watch(ledger), run_signature=checked["run_signature"],
            review=reference, release=spec["root_release"], source_sha256=checked["source_sha256"],
            identities={r["identity"]["method_id"]: r["identity"] for r in manifest["methods"]},
            job_ids=rebuilt["raw_invocation_job_ids"], cost=rebuilt["cost"], root_audit_source_sha256=saved["audit_source_sha256"],
            repeated_audit_source_sha256=rebuilt["audit_source_sha256"])
    evidence.unchanged()
    return evidence, registries, runs


def extract_outcomes(evidence, registry, run):
    from cti_vla.evaluation.formal_trials import _identity
    expected = {r["trial_id"]: r for state in registry["states"] for mid in run["identities"] for r in [_identity(registry, state, mid)]}
    outcomes, starts, current_job = {}, {}, None
    path = evidence.path(run["trials"])
    for row, locator in locate_lines(path):
        require(row.get("run_signature") == run["run_signature"], "Mixed raw run signature")
        if row.get("event") == "invocation":
            current_job = str(row.get("slurm_job_id"))
            require(current_job in run["job_ids"], "Unreviewed trial allocation")
            continue
        tid = row.get("trial_id")
        require(current_job is not None and tid in expected and all(row.get(k) == v for k, v in expected[tid].items()), "Raw final trial identity differs")
        if row["event"] == "start":
            require(tid not in outcomes and starts.get(tid, {}).get("job_id") != current_job, "Duplicate terminal/start trial")
            starts[tid] = {**locator, "job_id": current_job}
        elif row["event"] == "result":
            require(tid in starts, "Result lacks its original start")
            start = starts.pop(tid)
            if row["status"] == "infrastructure_error":
                continue
            require(row["status"] in ("completed", "policy_error") and type(row.get("success")) is bool and tid not in outcomes,
                "Invalid/duplicate scientific outcome")
            identity = run["identities"][row["method"]]
            outcomes[tid] = {k: row[k] for k in ("trial_id", "state_trial_id", "method", "status", "success", "termination", "control_steps", "policy_calls")}
            outcomes[tid].update(identity=identity, trace=dict(path=run["trials"], file_sha256=run["trials_sha256"],
                result=locator, start=start, job_id=current_job, run_signature=run["run_signature"], root_review=run["review"],
                root_release=run["release"], source_sha256=run["source_sha256"]))
        else:
            require(row["event"] == "cleanup_error", "Unknown raw trial event")
    if set(outcomes) != set(expected):
        raise PendingEvidence("Incomplete final trial cells; no cases generated")
    require(len(outcomes) == 8800, "Final suite must contain8800 unique outcome cells")
    return outcomes


def hydrate_cases(evidence, cases, runs):
    targets = {c["selection"][arm]["trial_id"]: c["selection"][arm]["trace"] for c in cases if c["status"] == "present" for arm in ("A", "B")}
    selected = {}
    for run in runs.values():
        wanted = {tid: trace for tid, trace in targets.items() if trace["path"] == run["trials"]}
        for row, loc in locate_lines(evidence.path(run["trials"])):
            tid = row.get("trial_id")
            if row.get("event") == "result" and tid in wanted and loc == wanted[tid]["result"]:
                # Keep only one chunk for at most288 selected terminal results.
                selected[tid] = {"chunks": row.get("chunks", [])[:1] if isinstance(row.get("chunks"), list) else None}
        require(all(tid in selected for tid in wanted), "Selected original result line changed or disappeared")
    for case in cases:
        if case["status"] == "present":
            case["token_comparison"] = compare_first(*(selected[case["selection"][arm]["trial_id"]] for arm in ("A", "B")), case["visual_tokens"])


def svg(case, *, synthetic):
    require(case["token_comparison"]["status"] == "available", "Unavailable tokens must not be drawn as an empty mask")
    title = (SYNTHETIC + " | " if synthetic else "") + case["case_id"]
    content = [f'<svg xmlns="http://www.w3.org/2000/svg" width="680" height="370" viewBox="0 0 680 370">',
        f'<title>{escape(title)}</title>', '<rect width="680" height="370" fill="white"/>',
        f'<text x="12" y="14" font-size="10">{escape(SYNTHETIC if synthetic else "Released formal final diagnostic")}</text>',
        f'<text x="12" y="28" font-size="11">{escape(case["case_id"])}</text>',
        '<text x="12" y="42" font-size="10">Patch positions only. Same first observation; no RGB reconstruction.</text>']
    colors = {"common": "#5863b8", "A_only": "#d88a25", "B_only": "#18876e"}
    for camera in case["token_comparison"]["cameras"]:
        origin = 16 + camera["camera_id"] * 336
        content.append(f'<text x="{origin}" y="56" font-size="13">{camera["name"]}: 16 x 16</text>')
        sets = {label: set(camera[label]) for label in colors}
        for index in range(256):
            label = next((k for k, values in sets.items() if index in values), "neither")
            content.append(f'<rect data-camera="{camera["camera_id"]}" data-patch="{index}" data-selection="{label}" '
                f'x="{origin + index % 16 * 18}" y="{66 + index // 16 * 16}" width="17" height="15" fill="{colors.get(label, "#eeeeee")}"/>')
    for i, (label, color) in enumerate(colors.items()):
        content.append(f'<rect x="{16 + i * 210}" y="340" width="12" height="12" fill="{color}"/>'
            f'<text x="{33 + i * 210}" y="351" font-size="12">{label}</text>')
    return "\n".join(content + ["</svg>", ""])


def markdown(payload):
    lines = ["# " + (SYNTHETIC if payload["synthetic"] else "Formal fixed diagnostic cases"), "", RULE, "",
        "Only released, root-reviewed final outcomes. Position grids compare the first identical observation; later inputs may diverge.",
        "A/B action difference is not teacher/demo action error. No RGB/video, policy replay or new GPU cost.", ""]
    for case in payload["cases"]:
        lines += ["## " + case["case_id"], "", f'Category candidates: {case["candidate_count"]}. Status: **{case["status"]}**.', ""]
        if case["status"] == "missing":
            lines += ["No pair in this category among the complete400 final initial states.", ""]
            continue
        selected, comparison = case["selection"], case["token_comparison"]
        state = selected["state"]
        lines += [f'Task {state["task_id"]}, source index {state["source_state_index"]}; task: {state["task_name"]}.', ""]
        for arm in ("A", "B"):
            row = selected[arm]; trace = row["trace"]
            lines += [f'- {arm}: success={row["success"]}, status={row["status"]}, termination={row["termination"]}, control steps={row["control_steps"]}. '
                f'Trial `{row["trial_id"]}`; job `{trace["job_id"]}`; source `{trace["path"]}` line {trace["result"]["line"]}.']
        lines += [""]
        if comparison["status"] != "available":
            lines += ["Token comparison unavailable: `" + comparison["reason"] + "`. The selected case is retained.", ""]
        else:
            lines += [f'First observation SHA256: `{comparison["observation_sha256"]}`. Intersection/budget={comparison["intersection_over_budget"]:.4f}; Jaccard={comparison["jaccard"]:.4f}.', "",
                f'![Two-view token positions](grids/{case["case_id"]}.svg)', ""]
    return "\n".join(lines)


def extract(inputs, output, *, project=ROOT, synthetic=False):
    project = Path(project).resolve()
    output = checked_path(project, output)
    require(not output.exists(), "Output directory must be new; never overwrite case artifacts")
    require((output.name.startswith("synthetic") if synthetic else
        (project / "results" / SCHEMA / "cases") in output.parents), "Use a new formal cases directory, or an explicitly named synthetic directory")
    inputs = checked_path(project, inputs)
    require(inputs.suffix == ".json", "Case input must be JSON metadata")
    source_hashes = {name: digest(ROOT / name) for name in SOURCES}
    input_sha = digest(inputs)
    spec = json.loads(inputs.read_text(encoding="utf-8"))
    helper = load("scripts/formal_execution_manifests.py")
    try:
        evidence, registries, runs = verified_inputs(project, spec, synthetic=synthetic)
        outcomes = {s: extract_outcomes(evidence, registries[s], runs[s]) for s in SUITES}
        cases = [case for suite in SUITES for budget in BUDGETS for seed in SEEDS
            for case in select_pair(registries[suite]["states"], outcomes[suite], suite=suite, budget=budget, seed=seed)]
        require(len(cases) == 144, "Fixed144 case slots required")
        hydrate_cases(evidence, cases, runs)
        evidence.unchanged()
        require(digest(inputs) == input_sha and source_hashes == {name: digest(ROOT / name) for name in SOURCES}, "Input/source changed during extraction")
    except (PendingEvidence, helper.MissingEvidence, FileNotFoundError) as exc:
        return dict(schema=SCHEMA, version=VERSION, status="pending", synthetic=synthetic, cases_written=False, missing=[str(exc)])
    payload = dict(schema=SCHEMA, kind="fixed_final_cases", version=VERSION, status="complete", synthetic=synthetic,
        watermark=SYNTHETIC if synthetic else None, selection_rule=RULE, groups=36, slots=144, final_trials=35200,
        unique_initial_states=1600, present=sum(c["status"] == "present" for c in cases),
        missing=sum(c["status"] == "missing" for c in cases), cases=cases,
        evidence=dict(input={"path": inputs.relative_to(project).as_posix(), "sha256": input_sha},
            files_sha256=dict(sorted(evidence.files.items())), source_sha256=source_hashes,
            final_reviews={s: runs[s]["review"] for s in SUITES}, root_release=spec["root_release"],
            historical_final_allocation_cost={s: runs[s]["cost"] for s in SUITES},
            note="Existing reviewed allocations only; this diagnostic introduces no policy evaluation or GPU cost."),
        weights_read=False, final_state_values_read=False, gpu_calls=0)
    outputs = {"cases.json": (json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode(), "cases.md": markdown(payload).encode()}
    outputs.update({"grids/" + c["case_id"] + ".svg": svg(c, synthetic=synthetic).encode() for c in cases
        if c["status"] == "present" and c["token_comparison"]["status"] == "available"})
    receipt = dict(schema=SCHEMA, kind="fixed_case_extraction_receipt", version=VERSION, status="complete", synthetic=synthetic,
        watermark=payload["watermark"], inputs=payload["evidence"], outputs_sha256={name: hashlib.sha256(data).hexdigest() for name, data in outputs.items()},
        slots=144, weights_read=False, final_state_values_read=False, gpu_calls=0)
    evidence.unchanged()
    require(digest(inputs) == input_sha and source_hashes == {name: digest(ROOT / name) for name in SOURCES}, "Evidence/source changed before publication")
    output.mkdir(parents=True, exist_ok=False)
    # Receipt is last. Interrupted directories are retained and never reused.
    for name, data in outputs.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
    with (output / "case_receipt.json").open("xb") as stream:
        stream.write((json.dumps(receipt, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode())
    return dict(schema=SCHEMA, status="complete", synthetic=synthetic, cases_written=True, output=str(output),
        slots=144, present=payload["present"], missing=payload["missing"], gpu_calls=0)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--project-root", default=str(ROOT))
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args(argv)
    result = extract(args.inputs, args.output, project=args.project_root, synthetic=args.synthetic)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
