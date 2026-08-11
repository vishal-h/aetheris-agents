import subprocess,json,re,collections,sys
S='/tmp/claude-1000/-home-it-sandbox-elixirws-aetheris-agents/90489c34-9e84-449e-b474-4ca763cbabb4/scratchpad'
REPOS={'agents':'/home/it/sandbox/elixirws/aetheris-agents','harness':'/home/it/sandbox/elixirws/aetheris'}
pop=json.load(open(S+'/pop.json')); by={p['base']:p for p in pop}
uniq=json.load(open(S+'/uniq.json'))
W=re.compile(r"[a-z0-9]+")
def sh(text,n=8):
    w=W.findall(text.lower())
    for i in range(len(w)-n+1): yield ' '.join(w[i:i+n])
Q=collections.defaultdict(list)
for r,d in REPOS.items():
    for full,short,date,subj in (l.split('|',3) for l in subprocess.run(
            ['git','log','--format=%H|%h|%ad|%s','--date=short'],cwd=d,capture_output=True,text=True).stdout.splitlines()):
        patch=subprocess.run(['git','show','--format=','--unified=0',full],cwd=d,capture_output=True,text=True).stdout
        cur=None
        for line in patch.splitlines():
            if line.startswith('+++ b/'): cur=line[6:]; continue
            if not line.startswith('+') or line.startswith('+++'): continue
            body=line[1:]
            seen=set()
            for s in sh(body):
                b=uniq.get(s)
                if b and b not in seen:
                    seen.add(b); Q[b].append((r,short,date,subj[:70],cur,body.strip()[:300],s))
json.dump(Q,open(S+'/qhits.json','w'))
print("raw Q candidate lines:",sum(len(v) for v in Q.values()),"across",len(Q),"files",file=sys.stderr)
