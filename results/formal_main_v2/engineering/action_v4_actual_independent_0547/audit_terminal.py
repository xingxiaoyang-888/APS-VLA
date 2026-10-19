"""Independent read-only reconstruction of fixed v4 GPU engineering result."""
from pathlib import Path
import ast, collections, datetime, hashlib, json, math, os, re, struct, subprocess, traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
H=Path('/share/home/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/action_v4_actual_independent_0547'
STAGE='formal_main_v2_action_execution_compat_gpu_v4'
VERSION='action-execution-gpu-candidate-1940-v4-runtime-lifecycle'
JOB='3039197'
BASE='results/formal_main_v2/'
OUT=P/(BASE+'engineering/'+STAGE)/JOB
SRC=BASE+'engineering/'+STAGE+'/source/'
REG='configs/experiments/'+STAGE+'.json'
REG_SHA='96dea708c5efd8da465952877d41de36cbe8dd56e3c3a5b5fc256488d255f164'
PROBE_SHA='91e12f29ad39591c29cfd63912394949d1cad932bb80c8a871ed852cea32cadc'
COMP_SHA='481ff2f526504a6353b5d2d4c07f99de4bd3547229931b2b222c0ea70fdf36d7'
EVENT_SHA='54f92fbd0354bae27b95f17c5193c186cb387781f223e7af1655ea825a84459c'
LAUNCH_SHA='d0b2f96016149b76a3be79969623da7cfbbbd1c57284a6335b47646b3f0cfee2'
INV_SHA='72da0c331ade3c985290c8eb005a8e788601aeaef7a71f80d1dd267ffee4338b'
SUITES=['libero_10','libero_spatial','libero_object','libero_goal']
METHODS=['dense','uniform128','A128_seed17','B128_seed17']
PANELS={root/f'configs/manifests/formal_main_v2/{s}/initial_states/development.json' for root in (R,P) for s in SUITES}
BEST={H/f'checkpoints/formal_main_v2/{s}/k128/seed17/{a}/best.pt' for s in SUITES for a in ('A','B')}
seen={};checks=[];sizes={}
def require(value,message):
    if not value:raise AssertionError(message)
def encoded(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sig(v):return hashlib.sha256(encoded(v)).hexdigest()
def path_guard(path,*,checkpoint=False):
    raw=str(path);p=Path(path)
    require(p.is_absolute() and '..' not in p.parts and '\\' not in raw,'noncanonical path')
    require(any(p.is_relative_to(base) for base in (R,P,H/'venv')) or p in BEST,'outside allowed roots')
    require(not any('sealed' in x.lower() or x.lower() in ('test','weights') for x in p.parts),'sealed/test path')
    if checkpoint:require(p in BEST,'checkpoint not fixed selected8')
    else:
        require(not any(x.lower()=='checkpoints' for x in p.parts) and p.suffix.lower() not in
            {'.pt','.pth','.bin','.ckpt','.safetensors','.pkl','.pickle','.npz','.npy','.init','.pruned_init'},'payload path')
        require(p.suffix=='.py' or p in PANELS or not any(x in raw.lower() for x in ('init_state','initial_state','final_state','test_state')),'unregistered state path')
    require(not (p.name=='panel.json' and 'final' in p.parts),'final panel')
    require(not any(x.is_symlink() for x in (p,*p.parents)),'symlink')
    return p
def key(p):return p.relative_to(R).as_posix() if p.is_relative_to(R) else str(p)
def sha(path,pin=None,*,checkpoint=False):
    p=path_guard(path,checkpoint=checkpoint);a=p.stat();h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    z=p.stat()
    require((a.st_size,a.st_ino,a.st_mtime_ns,a.st_ctime_ns)==(z.st_size,z.st_ino,z.st_mtime_ns,z.st_ctime_ns),'hash input changed')
    value=h.hexdigest();require(pin is None or value==pin,'SHA mismatch '+str(p))
    require(key(p) not in seen or seen[key(p)]==value,'input drift '+str(p))
    seen[key(p)]=value;sizes[key(p)]=z.st_size;return value
def read(path,pin=None):
    sha(path,pin);return json.loads(Path(path).read_bytes())
def ref(row,root=R):return read(root/row['path'],row['sha256'])
def once(rows,name,suite=None):
    values=[e for e in rows if e['event']==name and (suite is None or e.get('suite')==suite)]
    require(len(values)==1,'expected one '+name+' '+str(suite));return values[0]
def finite_matrix(value,rows=8):
    require(isinstance(value,list) and len(value)==rows,'action matrix rows')
    require(all(isinstance(row,list) and len(row)==7 and all(type(x) in (float,int) and math.isfinite(x) for x in row) for row in value),'finite7D action')
def publish(name,value):
    p=D/name
    with p.open('xb') as f:f.write(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False).encode()+b'\n')
    return p
def capture(name,path,pin=None):
    sha(path,pin);raw=Path(path).read_bytes()
    with (D/'raw'/name).open('xb') as f:f.write(raw)
    require(hashlib.sha256(raw).hexdigest()==seen[key(Path(path))],'copy changed')
    sha(D/'raw'/name)
def analyze():
    (D/'raw').mkdir(exist_ok=False)
    cmd=['sacct','-j',JOB+',3034675','--parsable2','--noheader',
         '--format=JobIDRaw,JobName,State,ExitCode,ElapsedRaw,AllocTRES,NodeList,Start,End,Timelimit']
    proc=subprocess.run(cmd,text=True,capture_output=True,timeout=30)
    publish('sacct_terminal.json',{'command':cmd,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr,'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    sha(D/'sacct_terminal.json');require(proc.returncode==0,'sacct failed')
    rows={x[0]:x for line in proc.stdout.splitlines() if len(x:=line.split('|'))>=10 and '.' not in x[0]}
    require(set(rows)=={JOB,'3034675'},'parent allocations missing')
    current=rows[JOB];old=rows['3034675']
    require(current[2:5]==['COMPLETED','0:0','814'] and current[6]=='gpu4002' and current[9]=='01:00:00','unexpected terminal facts')
    require('gres/gpu:l40=1' in current[5].split(',') and 'gres/gpu=1' in current[5].split(','),'not single L40')
    require(old[2:5]==['FAILED','1:0','303'],'prior v3 failure disappeared')
    reg=read(R/REG,REG_SHA);require(reg['status']=='registered_single_attempt' and reg['attempt']==1 and reg['automatic_retry'] is False,'registration')
    require(reg['suite_order']==SUITES and reg['method_order']==METHODS and reg['limits']['cells']==16,'matrix changed')
    m=ref(reg['candidate_manifest']);require(m['suite_order']==SUITES and m['method_order']==METHODS and m['limits']==reg['limits'],'manifest matrix')
    invrel=BASE+'invocations/'+STAGE+'_attempt01.json';inv=read(R/invrel,INV_SHA)
    require(inv['manifest']==reg['candidate_manifest'] and inv['gpu_registration']==dict(path=REG,sha256=REG_SHA),'invocation refs')
    for name in ['probe.py','launcher.py','probe.slurm','submit.py','node_exclusion.py']:
        value=sha(R/(SRC+name));require(sha(P/(SRC+name))==value,'published source changed')
    require(sha(R/(SRC+'probe.py'))==PROBE_SHA,'probe pin')
    invraw=read(P/invrel,INV_SHA);require(invraw==inv,'P invocation')
    for refrow in reg['cpu_reviews'].values():
        require(ref(refrow)['status']==refrow['accepted_status'],'CPU gate identity only')
    prior=reg['prior_GPU_failure'];ref(prior['raw_independent_audit'])
    require(prior['job_id']=='3034675' and prior['GPU_seconds']==303 and prior['completed_cells']==4,'prior failed scope')
    comp=read(OUT/'completion.json',COMP_SHA);sha(OUT/'events.jsonl',EVENT_SHA)
    raw=(OUT/'events.jsonl').read_bytes();require(raw.endswith(b'\n') and len(raw)==comp['events_bytes'],'incomplete journal')
    events=[json.loads(line) for line in raw.splitlines()];require(len(events)==739,'event count')
    require(comp['status']=='captured_pending_root_review' and comp['exit_code']==0 and comp['error'] is None and comp['source_inputs_unchanged'] is True,'not successful capture')
    require(comp['events_sha256']==EVENT_SHA and comp['candidate_sha256']==PROBE_SHA and comp['manifest_sha256']==reg['candidate_manifest']['sha256'] and comp['root_registration_sha256']==REG_SHA,'completion bindings')
    for k in ('scientific_complete','final_states_opened','success_rate_computed','latency_claim','weights_copied','original_results_replaced','automatic_retry'):
        require(comp[k] is False,'unsupported claim '+k)
    for index,event in enumerate(events):
        require(event['seq']==index and event['job_id']==JOB and event['schema']=='formal_main_v2' and event['version']==VERSION,'journal identity/sequence')
        require(math.isfinite(event['elapsed_seconds']) and (index==0 or event['elapsed_seconds']>=events[index-1]['elapsed_seconds']),'journal clock')
        require(not event['event'].endswith(('_failed','_rejected')) and event['event']!='engineering_failure','runtime failure')
    require(events[0]['event']=='engineering_start' and events[-1]['event']=='engineering_end','journal endpoints')
    require(events[0]['limits']==reg['limits'] and events[0]['expected_cells']==16 and events[0]['no_retry'] is True,'journal start scope')
    require(events[-1]['exit_code']==0 and events[-1]['error'] is None and events[-1]['source_inputs_unchanged'] is True,'journal end')
    identity=read(OUT/'action_execution_identity.json');entered=once(events,'action_execution_candidate_enter')
    require(entered['identity']==identity,'scope identity')
    require(identity['ast_proof']['removed_if_count']==1 and identity['ast_proof']['other_AST_nodes_unchanged'] is True and
            identity['action_transformation']=='none; existing finite PolicyChunk passed unchanged','one-branch/no-transform identity')
    inventory=ref(m['source_inventory'])
    require(len(inventory['files'])==173 and inventory['source_sha256']==m['source_aggregate_sha256'],'inventory173')
    for rel,pin in inventory['files'].items():sha(R/rel,pin);sha(S/rel,pin)
    inputs=read(OUT/'inputs.json')
    require(inputs['manifest_sha256']==reg['candidate_manifest']['sha256'],'inputs manifest')
    full=comp['read_evidence_sha256']
    require(all(full.get(k)==v for k,v in inputs['watched_files'].items()),'initial watched subset changed')
    for path,pin in full.items():sha(path,pin)
    for path,pin in inv['watched_files'].items():sha(path,pin)
    starts=[e for e in events if e['event']=='cell_start'];ends=[e for e in events if e['event']=='cell_complete']
    fixed=[(s,meth) for s in SUITES for meth in METHODS]
    require([(e['suite'],e['method_id']) for e in starts]==fixed and [(e['suite'],e['method_id']) for e in ends]==fixed,'16 exact ordered cells')
    results=[];summary=[];counts=collections.Counter();max_abs=0.;beyond=0;checkpoint_checks=[]
    for suite in SUITES:
        sr=m['suites'][suite];panel=ref(sr['panel'])
        require(panel['suite']==suite and panel['split']=='development' and panel['environment_seed']==0,'dev panel')
        subset=[row for row in panel['states'] if row['task_id']==0];st=min(subset,key=lambda row:row['source_state_index'])
        require(st['source_state_index']==[0,3,5,7][SUITES.index(suite)] and len([r for r in subset if r['source_state_index']==st['source_state_index']])==1,'fixed task0 lowest state')
        require(sig(st)==sr['state']['row_canonical_sha256'] and len(st['initial_state'])==sr['state']['vector_length'],'state row')
        require(hashlib.sha256(struct.pack('<'+str(len(st['initial_state']))+'d',*st['initial_state'])).hexdigest()==sr['state']['initial_state_sha256'],'state array SHA')
        same_obs=[];same_rng=[]
        tr=ref(sr['training_root']);ind=ref(sr['training_independent']);selected=ref(sr['selected_server']);gate=ref(sr['acceptance_root'])
        require(all(r['status']=='passed' for r in (tr,ind,selected,gate)) and tr['completed_by_arm']=={'A':5000,'B':5000},'own training gate')
        require(ind['read_evidence_sha256'][sr['training_root']['path']]==sr['training_root']['sha256'] and selected['input_sha256'][sr['training_root']['path']]==sr['training_root']['sha256'],'root source chain')
        f00=ref(sr['acceptance']['input_acceptance.json'])
        for mi,item in enumerate(sr['methods']):
            expected=item['identity'];method=METHODS[mi];idx=fixed.index((suite,method));start=starts[idx];end=ends[idx]
            require(start['seq']<end['seq'] and (idx==0 or ends[idx-1]['seq']<start['seq']),'overlapping cells')
            require(start['identity']==expected and start['state_identity']==sr['state'] and start['environment_seed']==0 and start['runtime_seed']==17,'cell identity')
            require(expected['future_head_deployed'] is False and expected['frozen_model_sha256']==f00['frozen_model_sha256'],'future/base identity')
            same_rng.append(start['runtime_rng_sha256'])
            cell=events[start['seq']:end['seq']+1]
            require(once(cell,'environment_reset')['seq']<once(cell,'initial_state_set')['seq'],'reset/state order')
            require(once(cell,'initial_state_set')['initial_state_sha256']==sr['state']['initial_state_sha256'],'wrong state')
            controller=once(cell,'actual_controller_verified')['controller']
            ce=m['controller_expected']
            require(controller['controller_type']==ce['controller_type'] and controller['actual_use_delta']==ce['actual_use_delta']
                    and controller['limits']==ce['limits'] and controller['actual_delta_branch_enabled'] is True,'actual controller differs')
            for fun in ('scale_action','set_goal'):
                bound=controller['methods'][fun];sha(bound['path'],bound['sha256'])
                require(bound['source'] in Path(bound['path']).read_text(),'bound controller function differs')
            ps=once(cell,'policy_start');chunk=once(cell,'policy_chunk');ret=once(cell,'bounded_episode_return')
            result=end['result'];rawresult=result['raw_result']
            require(expected==result['identity']==ps['identity'] and end['controller_identity_unchanged'] is True and result['no_external_action_transform'] is True,'policy/controller identity')
            require(ret['raw_frozen_result']==rawresult and result['method_id']==method and rawresult['status']=='completed','cell result')
            require(len(rawresult['chunks'])==rawresult['policy_calls']==1 and rawresult['wait_steps']==10,'single chunk/wait')
            learned=expected['method'] in ('A','B')
            expected_counts=dict(vla_backbone=1,vision=1,action_head=1,scorer=int(learned),topk=int(learned),packing=1)
            require(chunk['observed_counts']==result['observed_counts']==expected_counts and chunk['future_head_constructed'] is False,'actual counters')
            meta=chunk['metadata'];rchunk=rawresult['chunks'][0]
            require(meta==rchunk['metadata'] and meta['schema']=='formal_main_v2' and meta['method']==expected['method'] and meta['suite']==suite,'chunk metadata')
            require(meta['policy_calls']==meta['vision_calls']==meta['packing_calls']==1 and meta['scorer_calls']==int(learned)
                    and meta['future_head_calls']==0 and meta['language_cache']=='disabled','deployment count/cache')
            tokens=expected['visual_tokens'];indices=meta['retained_indices']
            require(meta['visual_tokens']==tokens and indices==sorted(set(indices)) and len(indices)==tokens and
                    all(type(i) is int and 0<=i<512 for i in indices) and sum(i<256 for i in indices)==tokens//2,'hard packing')
            if learned:
                require(meta['selector_checkpoint_sha256']==expected['checkpoint_sha256'] and meta['training_seed']==17,'selected identity')
                receipt=ref(item['receipt']);report=ref(item['training_report'])
                pts=receipt['evaluations'];best=min(pts,key=lambda x:(x['validation_metric'],x['update']))
                require([x['update'] for x in pts]==list(range(0,5001,500)) and receipt['training_complete'] and receipt['completed_updates']==5000,'11 node training')
                require(best['update']==item['selected_update']==receipt['metadata']['update']==report['best_update'],'earliest selection')
                saved=next(x for x in selected['server_selected_checks'] if x['arm']==expected['method'])
                require(saved['path']==item['checkpoint'] and saved['sha256']==receipt['checkpoint_sha256']==report['best_checkpoint_sha256']==expected['checkpoint_sha256'],'selected proof')
                sha(item['checkpoint'],expected['checkpoint_sha256'],checkpoint=True)
                require(sizes[key(Path(item['checkpoint']))]==item['checkpoint_bytes']==saved['bytes'],'checkpoint bytes')
                checkpoint_checks.append(dict(suite=suite,arm=expected['method'],path=item['checkpoint'],sha256=expected['checkpoint_sha256'],bytes=item['checkpoint_bytes'],selected_update=item['selected_update']))
            for field in ('normalized_actions','environment_actions'):
                finite_matrix(chunk[field]);require(chunk[field]==rchunk[field],'raw original chunk differs')
            action=chunk['environment_actions'];executed=rawresult['executed_actions'];n=rawresult['control_steps']
            require(1<=n<=8 and n==result['actual_control_steps'] and executed==action[:n] and result['unexecuted_chunk_tail']==action[n:],'executed prefix')
            ss=[x for x in cell if x['event']=='environment_step_start'];se=[x for x in cell if x['event']=='environment_step_end']
            require(len(ss)==len(se)==10+n==ret['attempted_environment_steps']==ret['confirmed_environment_steps'],'environment count')
            for i,(a,b) in enumerate(zip(ss,se)):
                expected_action=[0.,0.,0.,0.,0.,0.,-1.] if i<10 else action[i-10]
                require(a['step_index']==b['step_index']==i and a['step_kind']==b['step_kind']==('wait' if i<10 else 'control')
                        and a['unchanged'] is True and encoded(a['action'])==encoded(expected_action)
                        and a['original_action_sha256']==sig(expected_action) and b['confirmed_steps']==i+1
                        and a['seq']<b['seq'] and (i==0 or se[i-1]['seq']<a['seq']),'executed original action')
            require(se[9]['seq']<ps['seq']<chunk['seq']<ss[10]['seq'] and se[-1]['seq']<ret['seq']<end['seq'],'one action boundary')
            require(ps['observation_sha256']==result['observation_sha256']==rchunk['observation_sha256'] and rchunk['control_step']==0,'current observation')
            same_obs.append(ps['observation_sha256']);counts.update(expected_counts);counts['policy']+=1;counts['wait_actions']+=10;counts['control_actions']+=n
            max_abs=max(max_abs,max(abs(x) for row in action for x in row));beyond+=sum(abs(x)>1.00001 for row in action for x in row)
            results.append(dict(suite=suite,**result));summary.append(dict(suite=suite,method=method,control_actions=n,wait_actions=10,counts=expected_counts,token_count=tokens,chunk_environment_sha256=sig(action)))
        require(len(set(same_obs))==len(set(same_rng))==1,'reset observation/RNG differs within suite')
        require(once(events,'suite_complete',suite)['models_unchanged'] is True,'base source changed')
        require(once(events,'base_load_complete',suite)['frozen_model_sha256']==f00['frozen_model_sha256'],'loaded base fingerprint')
    lifecycle=[x for x in events if x['event']=='runtime_compat_lifecycle_verified']
    require([(x['suite'],x['suite_index'],x['minimal_installed_this_load']) for x in lifecycle]==
            [(s,i,i==0) for i,s in enumerate(SUITES)],'first installer/reuse differs')
    exitrow=once(events,'action_execution_candidate_exit')
    require(exitrow['identity_sha256']==identity['identity_sha256'] and all(exitrow[k] is True for k in
        ('original_bindings_restored','scope_binding_and_code_intact','finite_shape_and_observation_helpers_intact','source_inputs_unchanged','policy_chunk_construction_intact','policy_chunk_construction_restored'))
        and exitrow['fresh_runtime_required'] is False and exitrow['runner_raised'] is False and exitrow['changed_inputs']==[],'action restoration')
    for suite in SUITES:
        meta=suite in ('libero_object','libero_goal')
        for event in ('asset_metadata_compat_enter','asset_metadata_compat_load_start','asset_metadata_compat_load_complete','asset_metadata_compat_exit'):
            require(sum(x['event']==event and x.get('suite')==suite for x in events)==int(meta),'metadata scope count')
        if meta:
            row=once(events,'asset_metadata_compat_exit',suite)
            require(all(row[k] is True for k in ('original_loader_restored','directory_verifier_unchanged','binding_intact','original_loader_code_unchanged','directory_verifier_code_unchanged','frozen_source_and_inputs_unchanged')) and
                    row['runner_raised'] is False and row['passthrough_calls']==0 and row['adapted_calls_attempted']==row['adapted_calls_completed']==1,'metadata restoration')
        goal=suite=='libero_goal'
        for event,num in [('goal_component_compat_enter',1),('goal_component_load_start',2),('goal_component_load_complete',2),('goal_component_compat_exit',1)]:
            require(sum(x['event']==event and x.get('suite')==suite for x in events)==num*int(goal),'component scope count')
    ge=once(events,'goal_component_compat_exit')
    require(all(ge[k] is True for k in ('original_loader_restored','original_function_codes_unchanged','binding_intact','torch_load_unchanged','source_inputs_unchanged','component_files_unchanged'))
            and ge['runner_raised'] is False and ge['rejected_calls']==0 and ge['component_calls_attempted']==ge['component_calls_completed']==2,'Goal restoration')
    for name in ('goal_component_load_start','goal_component_load_complete'):require([x['call_id'] for x in events if x['event']==name]==[0,1],'Goal call order')
    require(comp['result']['cells']==results and comp['result']['global_counts']==dict(policy=16,vision=16,vla_backbone=16)
            and comp['result']['actual_cells']==16 and comp['result']['total_control_steps']==counts['control_actions']==128,'completion not raw reconstructed')
    require(comp['result']['runtime']==m['runtime'],'runtime identity')
    receipt=read(P/(BASE+'job_receipts/'+JOB+'.json'),LAUNCH_SHA)
    require(receipt['job_id']==JOB and receipt['stage_key']==STAGE and receipt['invocation_sha256']==INV_SHA and receipt['exit_code']==0 and receipt['error'] is None,'launcher result')
    require(receipt['watched_inputs_verified_before'] is True and receipt['watched_inputs_verified_after'] is True and receipt['output']==str(OUT),'launcher watched/output')
    require(receipt['manifest']==inv['manifest'] and receipt['gpu_registration']==inv['gpu_registration'] and receipt['root_review']==inv['root_review'],'launcher refs')
    command=[str(H/'venv/bin/python'),'-B',str(P/(SRC+'probe.py')),'--project-root',str(P),'--source-root',str(S),
        '--manifest',reg['candidate_manifest']['path'],'--manifest-sha256',reg['candidate_manifest']['sha256'],
        '--gpu-registration',REG,'--gpu-registration-sha256',REG_SHA,'--job-id',JOB,'--script-sha256',PROBE_SHA,'--execute-gpu']
    require(receipt['command']==command and receipt['scientific_trials']==0 and receipt['final_states_opened'] is False,'launcher exact child')
    marker=read(OUT.parent/'attempt01.launcher_started.json')
    require(marker['job_id']==JOB and marker['invocation_sha256']==INV_SHA and marker['started_utc']==receipt['started_utc'],'one-shot marker')
    for name,pin in [('completion.json',COMP_SHA),('events.jsonl',EVENT_SHA),('inputs.json',None),('action_execution_identity.json',None)]:
        capture(name,OUT/name,pin)
    capture('launcher_receipt.json',P/(BASE+'job_receipts/'+JOB+'.json'),LAUNCH_SHA)
    capture('launcher_marker.json',OUT.parent/'attempt01.launcher_started.json')
    for ext in ('out','err'):capture('slurm.'+ext,P/f'results/slurm/cti-action-exec16_{JOB}.{ext}')
    sha(D/'pending_review.json','3137f0e145a916c9880381511df6435edbed8d34d685e3229e2ab376bf4ebb84')
    sha(Path(__file__))
    for p,pin in list(seen.items()):
        path=Path(p) if Path(p).is_absolute() else R/p
        sha(path,pin,checkpoint=path in BEST)
    return dict(schema='formal_main_v2',kind='action_execution_v4_actual_GPU_independent_review',
        status='passed_bounded_actual_GPU_engineering_acceptance_pending_root_integration',job_id=JOB,
        reviewed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        registration=dict(path=REG,sha256=REG_SHA),invocation_sha256=INV_SHA,
        source173_R_and_S_match=True,events=739,engineering_cells=16,unique_development_initial_states=4,
        counts=dict(counts,future_head=0),cell_results=summary,selected_checkpoint_checks=checkpoint_checks,
        current_allocation=dict(status='COMPLETED',exit_code='0:0',node='gpu4002',GPUs=1,allocated_GPU_seconds=814,time_limit='01:00:00'),
        retained_v3_failure=dict(job_id='3034675',status='FAILED',exit_code='1:0',allocated_GPU_seconds=303,completed_cells=4,required_cells=16,original_raw_audit=prior['raw_independent_audit']),
        named_v3_v4_GPU_seconds=1117,named_subtotal_is_not_all_project_or_all_historical_engineering_cost=True,
        prismatic_install_then_reuse=[True,False,False,False],all_action_metadata_component_scopes_restored=True,
        deployment_no_future_head=True,no_extra_action_transform=True,maximum_absolute_environment_action=max_abs,
        finite_environment_action_components_exceeding_old_bound=beyond,
        scientific_trials_added=0,scientific_complete=False,scientific_release_authorized=False,
        success_rate_computed=False,latency_claim=False,final_states_opened=False,weights_copied=False,
        actual_checkpoint_SHA_only=True,new_GPU_calls_by_auditor=0,
        limitations=['Only16 fixed first-chunk engineering cells on4 development states, not scientific closed-loop evaluation.',
        'No performance/speed or robustness claim. Historical Object failed trial and earlier engineering failures remain unchanged.',
        'CPU reviews bind provenance only; this conclusion derives from completed real GPU raw journal and Slurm allocation.',
        'Base parameter identities are evidenced by observed frozen code checks before/after, not reloading models in this CPU audit.',
        'Root must separately integrate this engineering result and preserve the original global final-release gate.'],
        read_evidence_sha256=seen,read_evidence_bytes=sizes)
if __name__=='__main__':
    result=analyze()
    p=publish('terminal_review.json',result)
    print(json.dumps({'status':result['status'],'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                      'counts':result['counts'],'refs':len(seen),'max_abs_action':result['maximum_absolute_environment_action'],
                      'old_bound_exceedances':result['finite_environment_action_components_exceeding_old_bound']}))
