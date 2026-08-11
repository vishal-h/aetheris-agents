import subprocess, os, json, collections, sys, re
S='/tmp/claude-1000/-home-it-sandbox-elixirws-aetheris-agents/90489c34-9e84-449e-b474-4ca763cbabb4/scratchpad'
REPOS={'agents':'/home/it/sandbox/elixirws/aetheris-agents','harness':'/home/it/sandbox/elixirws/aetheris'}
pop=json.load(open(S+'/pop.json'))
# boundary-anchored: basename must not be preceded by [A-Za-z0-9_-]
pats={p['base']: re.compile(r'(?<![A-Za-z0-9_-])'+re.escape(p['base'])) for p in pop}
by={p['base']:p for p in pop}
hits=collections.defaultdict(list)
for r,d in REPOS.items():
    out=subprocess.run(['git','log','--format=%H|%h|%ad|%s','--date=short'],cwd=d,capture_output=True,text=True).stdout.splitlines()
    for full,short,date,subj in (l.split('|',3) for l in out):
        p=subprocess.run(['git','show','--format=','--unified=0',full],cwd=d,capture_output=True,text=True).stdout
        cur=None
        for line in p.splitlines():
            if line.startswith('+++ b/'): cur=line[6:]; continue
            if not line.startswith('+') or line.startswith('+++'): continue
            body=line[1:]
            for b,rx in pats.items():
                if rx.search(body): hits[b].append((r,short,date,subj[:70],cur,body.strip()[:400]))
json.dump(hits,open(S+'/hits2.json','w'))
print("raw hit lines (boundary-anchored):",sum(len(v) for v in hits.values()),"across",len(hits),"files",file=sys.stderr)
