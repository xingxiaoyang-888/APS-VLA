from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/object_terminal_independent_20261021T0334'
B='results/formal_main_v2/preflight/heartbeat_20261021T1134'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size)
def save(name,blob):
 p=D/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(blob)
def js(name,value):save(name,(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
review=D/'independent_review.json'
assert sha(review)=='2e3b0c6c5253e0c4c612daa3d6d27860a315af585b462407896786737f847faf'
v=json.loads(review.read_bytes())
assert v['status']=='passed' and v['blockers']==[] and len(v['checks'])==v['check_count']==41 and v['CPU_guard_negative_tests']==46
assert sha(D/'original_consumer_reconstructed.json')=='07b9c955b5e625dd4cd48fdf0ab8224b0e8d0e8d035190d4cd9d250ae25543d1'
assert sha(R/'results/experiment_supervisor/state.json')=='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa'
external=[]
for name,source,pin in [
 ('reviewed_terminal_pull_bridge.py','.local/object_terminal_pull_bridge_20261021T0334/bridge.py','191745c8b7bcd82a165849ce8680a990da4f5de53d3204f9cdbb51f598cc7e49'),
 ('original_root_review_failure.json',B+'/Object_original_terminal_review_failure.json','c9e652dcb68bb2def299bbe9c2dbb48bedaf8c5c94df7d75fcf172436c4e2fdd')]:
 p=R/source;assert sha(p)==pin;save(name,p.read_bytes());external.append(dict(copied_to=name,original=ref(p)))
for short in ('object_terminal_raw_independent','object_terminal_typed_P_independent','object_terminal_original_review_diagnosis','object_terminal_amplitude_diagnostic_correction','object_terminal_bridge_consumer_independent'):
 source='results/formal_main_v2/control_transport/'+short+'_20261021T0334.jsonl';p=R/source
 rows=[json.loads(x) for x in p.read_bytes().splitlines()]
 assert rows and all(isinstance(x,dict) for x in rows)
 dest='transport/'+p.name;save(dest,p.read_bytes());external.append(dict(copied_to=dest,original=ref(p)))
js('copied_evidence_sources.json',dict(schema='formal_main_v2',kind='Object3054409_independent_exact_original_evidence_copies',files=external))
readme='''# Object3054409 independent terminal review

The final result is independent_review.json: status passed, no blockers, 41 final reconstruction checks and 46 exact metadata supplement rejection cases. The earlier full raw precheck has 2004 checks and remains separately recorded. These are actual read-only server reconstructions, with no new Slurm query, submission, state write, canonical change, or Git operation.

The unchanged canonical reviewer and consumer were each executed against all real terminal evidence. Both reconstruct exactly the root terminal receipt SHA 07b9c955b5e625dd4cd48fdf0ab8224b0e8d0e8d035190d4cd9d250ae25543d1. Reproduction requires the original frozen S import context and the exact root-authored bridge SHA 191745c8b7bcd82a165849ce8680a990da4f5de53d3204f9cdbb51f598cc7e49. The bridge preserves all original nine-file pull checks before adding only four SHA/size/job/path-bound typed journals. All 13 actual P/R files were independently compared. The local bridge copy is archival source, not an installed replacement entry.

Two unassisted canonical failures are preserved: the first imported the identical frozen source through R rather than the actual S filename, which changes marshal(code, 2) code identity; with S explicitly preloaded the next failure identified the original candidate projection's omission of four actual, already-pulled typed journals. The supplement is scoped and its original function binding is restored. No runtime, original full600 guard, configuration, checkpoint, or scientific result was altered to obtain review success.

The new completed attempt is the same logical failed cell, with 19 original chunks, 19 policy calls and 145 control actions; exact original queue/controller evidence was reconstructed. The logical view has 599 explicitly adopted legacy results plus one current result: 600 cells, 521 successes and 79 negative outcomes, 100 initial states and 10 tasks. All 601 historical attempts remain, including the original policy_error. The unchanged new native report remains incomplete at 1/600; no fake ledger rows were inserted. GPU accounting is 6713 legacy seconds plus 326 new seconds, 7039 total across four unique allocations, not a second addition to the global ledger.

logical_view_diagnostics.json preserves an audit metadata error: its optional exceedance diagnostic used 1.05. logical_view_diagnostics_v2.json explicitly corrects this to the actual frozen old guard 1.00001. The new eighth call at step56 has one environment action component 1.010742197890625; the original failed eighth-call payload was not logged and remains unknown. The recorded first seven calls match, but no unrecorded action is invented and no causal claim substitutes for the new raw result.

The in-memory negative fixtures isolate metadata guard semantics; they are never production ledger/pull evidence. Full real review and consume run separately without fixture substitution. Source/state preservation, raw evidence, diagnostic correction, original failures, source scripts and the five completed transport logs are all included in this manifest. Root acceptance and final release are separate; this package itself grants neither. The sealed final evaluation remains closed.
'''
save('README.md',readme.encode())
rows=[]
for p in sorted(D.rglob('*')):
 if not p.is_file():continue
 assert p.resolve()==p and not p.is_symlink()
 assert p.suffix in {'.json','.jsonl','.py','.md'}
 rows.append(dict(path=str(p.relative_to(D)),sha256=sha(p),bytes=p.stat().st_size))
manifest=dict(schema='formal_main_v2',kind='Object3054409_terminal_independent_delivery',status='passed',reviewed_by='independent',source_root=str(D),file_count=len(rows),files=rows,review=ref(review),scope='Actual original terminal reviewer/consumer reconstruction with exact four-journal metadata supplement; no production changes or acceptance by this agent.',new_GPU_submissions=0,new_Slurm_queries=0,state_writes=False,Git_writes=False,final_release=False,utc=datetime.now(timezone.utc).isoformat())
js('delivery_manifest.json',manifest)
print(json.dumps(dict(status='sealed',file_count=len(rows),manifest=ref(D/'delivery_manifest.json'),review=ref(review))))
