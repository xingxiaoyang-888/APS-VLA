from pathlib import Path
import argparse,base64,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
URL='https://github.com/xingxiaoyang-888/DIWA.git'
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--operation',choices=('check','push'),required=True)
 args=ap.parse_args()
 assert os.name=='posix'
 assert str(ROOT)=='/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo'
 assert subprocess.check_output(['git','-C',str(ROOT),'remote','get-url','origin'],text=True).strip()==URL
 value=json.load(sys.stdin)
 assert isinstance(value.get('username'),str) and isinstance(value.get('password'),str)
 auth=base64.b64encode((value['username']+':'+value['password']).encode()).decode()
 env={k:v for k,v in os.environ.items() if not k.startswith(('GIT_TRACE','GCM_TRACE','GIT_CONFIG_')) and k!='GIT_CURL_VERBOSE'}
 env.update(GIT_TERMINAL_PROMPT='0',GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='http.https://github.com/xingxiaoyang-888/DIWA.git.extraheader',GIT_CONFIG_VALUE_0='AUTHORIZATION: basic '+auth,GIT_CONFIG_KEY_1='credential.helper',GIT_CONFIG_VALUE_1='')
 def run(argv):
  r=subprocess.run(['git','-C',str(ROOT),*argv],capture_output=True,text=True,env=env)
  if r.returncode:
   err=r.stderr
   for secret in (value['password'],auth):err=err.replace(secret,'[redacted]')
   raise RuntimeError(err)
  return r.stdout
 before=run(['ls-remote','origin','refs/heads/main']).split()[0]
 local=run(['rev-parse','HEAD']).strip()
 if args.operation=='push':
  assert subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',before,local],capture_output=True).returncode==0,'Remote advanced; reconcile before a non-force push'
  run(['push','--porcelain','origin','HEAD:refs/heads/main'])
 after=run(['ls-remote','origin','refs/heads/main']).split()[0]
 if args.operation=='push':assert after==local
 print(json.dumps(dict(operation=args.operation,local_head=local,remote_head_before=before,remote_head_after=after,credentials_persisted=False)))
if __name__=='__main__':main()
