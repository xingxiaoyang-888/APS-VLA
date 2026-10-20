from pathlib import Path
import base64,fcntl,hashlib,json,sys,tomllib
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');v=json.load(sys.stdin);assert set(v)=={'automation_toml_base64'};raw=base64.b64decode(v['automation_toml_base64'],validate=True);d=tomllib.loads(raw.decode());assert d['id']=='cti-vla' and d['kind']=='heartbeat' and d['status']=='ACTIVE' and d['rrule']=='RRULE:FREQ=MINUTELY;INTERVAL=60' and d['target_thread_id']=='01a1363e-5ab4-7422-b655-cc2e6f5d3ea1'
assert '72' in d['prompt'] and '3053503' in d['prompt'] and '3053518' in d['prompt'] and '禁止为填槽重启训练控制器' in d['prompt']
with (R/'results/experiment_supervisor/.writer.lock').open('r+b') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);p=R/'results/formal_main_v2/preflight/heartbeat_20261021T0225/automation_phase_update.json';record={'schema':'formal_main_v2','status':'existing_heartbeat_prompt_updated_after_training_complete','automation':d,'original_toml_sha256':hashlib.sha256(raw).hexdigest(),'schedule_preserved':True,'notification_policy_preserved':True,'project_content_written_on_Windows':False,'update_method':'Codex automation_update structured tool; existing heartbeat, no new automation','official_documentation':'https://developers.openai.com/training/walkthroughs/scheduled-tasks','utc':datetime.now(timezone.utc).isoformat()}
 with p.open('x') as f:json.dump(record,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps({'status':record['status'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
