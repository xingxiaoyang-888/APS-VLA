# OpenVLA-OFT / LIBERO setup

From the repository root, use Python 3.10 and install the package with its test dependencies. The data and policy tests read files from pinned upstream checkouts.

```bash
python -m pip install -e ".[test]"
git clone https://github.com/Lifelong-Robot-Learning/LIBERO.git external/LIBERO
git -C external/LIBERO checkout 8f1084e3132a39270c3a13ebe37270a43ece2a01
git clone https://github.com/moojink/openvla-oft.git external/openvla-oft
git -C external/openvla-oft checkout e4287e94541f459edc4feabc4e181f537cd569a8
python -m pytest -q
```

The paper's experiment entry points are `scripts/run_formal_future.py` (training), `scripts/eval_formal_selector_libero.py` (rollouts) and `scripts/profile_formal.py` (timing). Each accepts `--help`. GPU runs also require suite-specific checkpoints, the modified LIBERO RLDS data, the simulator and the registered manifests. The scripts retain the lab's storage paths and source checks for the original runs. Historical execution records and cluster setup are available in the [experiment snapshot](https://github.com/xingxiaoyang-888/APS-VLA/tree/e8176b1212d91f13608bd83240fa5cc053a8f57f).

The Python import name is `cti_vla`. Original checkpoints verify hashes for the entire `src/` tree and four entry scripts. Use the matching revision when loading them.
