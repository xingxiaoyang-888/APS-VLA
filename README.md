# CTI-VLA

Counterfactual Token Influence for Efficient Vision-Language-Action Policies.

`CTI-VLA` is the public project/paper name. The Python package and existing
server/repository paths remain `diwa`/`DIWA` for backward compatibility during
the migration.

## Current scope

- Base checkpoint: `moojink/openvla-7b-oft-finetuned-libero-spatial`
- Primary benchmark: LIBERO Spatial
- Main precision: `bf16` on `2 x A100`
- Stage A: Decision Influence Estimator (DIE) teacher-target training
- Large model weights, datasets, caches, and run outputs are intentionally excluded from Git

## Local verification

```text
python -m pytest -q
python -m compileall -q diwa tests
```

## Server bootstrap

```text
git clone https://github.com/xingxiaoyang-888/DIWA.git
cd DIWA
python -m pip install -e .
```

Download the complete fine-tuned checkpoint on the server only. Do not download a second
base OpenVLA checkpoint unless the checkpoint manifest proves that the selected repository
contains adapter-only weights. Start with a fixed LIBERO Spatial smoke/pilot subset; fetch
the full LIBERO training split only after the smoke and expansion gates pass. RoboCasa and
RoboTwin are optional later transfer/evaluation datasets and should be mounted from the
existing copies rather than copied into this repository.

See `服务器启动清单.md` for the hardware, model, data, signature, and OOM gates.
