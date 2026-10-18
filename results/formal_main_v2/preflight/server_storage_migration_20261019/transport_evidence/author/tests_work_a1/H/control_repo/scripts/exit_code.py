import sys
print('out')
print('err',file=sys.stderr)
raise SystemExit(23)
