from pathlib import Path
import json,hashlib
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
D=R/".local/goal_remaining5_dispatch_20261021T0449"
def sha(b): return hashlib.sha256(b).hexdigest()
def read(rel,pin):
 b=(R/rel).read_bytes();assert sha(b)==pin,rel;return json.loads(b)
m=read(".local/goal_remaining5_runtime_20261021T0449/package/package_manifest.json","200dcef220601fd26565bb48106856612853739f486f8374ef91a4967e60692f")
dr="results/formal_main_v2/engineering/supervision_delivery_20261021T0334/Goal_remaining5_design/design.json"
ds="5c813e3a6e9429cc46ed9ab52a5543d0cf6302c5e5c1819efd11a501a2fb4e8e"
design=read(dr,ds)
assert sha((D/"gateway_v3.py").read_bytes())=="45003c082efc508249e9ba41aac15639be7c4188d9517ee1717e71f563448f9b"
s=dict(schema="formal_main_v2",kind="five_exact_Goal_pairs_dispatch_scope",version="goal-remaining5-held-atomic-dispatch-v1",design=dict(path=dr,sha256=ds),pairs={x["pair_key"]:[x["pair_id"],x["budget"],x["seed"]] for x in design["remaining_pairs"]},runtime_manifest_sha256="200dcef220601fd26565bb48106856612853739f486f8374ef91a4967e60692f",runtime_files=m["files"])
b=(json.dumps(s,sort_keys=True,indent=2)+"\n").encode()
with (D/"scope.json").open("xb") as f:f.write(b)
print(json.dumps(dict(path=str((D/"scope.json").relative_to(R)),sha256=sha(b),bytes=len(b))))
