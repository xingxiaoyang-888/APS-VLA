from pathlib import Path
from types import SimpleNamespace
import importlib.util,hashlib
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
D=R/".local/cuda_recovery_independent_0943"
p=D/"audit_3039258_v2.py"
assert hashlib.sha256(p.read_bytes()).hexdigest()=="029dac536286154f200a6dbd2543241eb7d95fb0e8c81ae36210e2c00ad5eab7"
spec=importlib.util.spec_from_file_location("cuda_terminal_independent_0943",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.raw(Path(__file__).relative_to(R).as_posix())
m.read(".local/cuda_recovery_independent_0943/ownership_patch_independent_review.json","edff54b1d4ff8ace87251378b882190155f7db5b26bf09bf5e360c0bec34abba")
m.read("results/formal_main_v2/preflight/heartbeat_20261019T1743/3039258_slurm_log_server_mirror.json")
m.read("results/formal_main_v2/preflight/heartbeat_20261019T1743/cuda_root_terminal.json","1d1e184202fff55263465a97d53eb7fc652339754ed0034e8050855f0d8d77c5")
m.raw('.local/cuda_recovery_independent_0943/audit_3039258.py')
m.raw('.local/cuda_recovery_independent_0943/terminal_3039258_a1.log')
m.raw('.local/cuda_recovery_independent_0943/terminal_3039258_a1_run.json')
m.raw('.local/cuda_recovery_independent_0943/run_terminal_3039258.py')
m.main(SimpleNamespace(root_review_sha256="57192346c2b8e7010538a9798d6215c5605468b0e2c68c2873a7d2ea92f48d71",pull="results/formal_main_v2/pulls/20261019T095542Z_e5d54e39d3ae/receipt.json",pull_sha256="8cf02df4314a103db61824fbf64a238994a1572757bc443682ab6d5d319be0e8"))
