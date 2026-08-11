import subprocess,json,re,collections
S='/tmp/claude-1000/-home-it-sandbox-elixirws-aetheris-agents/90489c34-9e84-449e-b474-4ca763cbabb4/scratchpad'
REPOS={'agents':'/home/it/sandbox/elixirws/aetheris-agents','harness':'/home/it/sandbox/elixirws/aetheris'}
pop=json.load(open(S+'/pop2.json'))
pat={(p['repo'],p['path']):re.compile(re.escape(p['path'])) for p in pop}
byk={(p['repo'],p['path']):p for p in pop}
ex=collections.Counter(); kept=0
for r,d in REPOS.items():
    for full,short,date,at,subj in (l.split('|',4) for l in subprocess.run(
        ['git','log','--format=%H|%h|%ad|%at|%s','--date=short'],cwd=d,capture_output=True,text=True).stdout.splitlines()):
        at=int(at); patch=subprocess.run(['git','show','--format=','--unified=0',full],cwd=d,capture_output=True,text=True).stdout
        cur=None
        for line in patch.splitlines():
            if line.startswith('+++ b/'): cur=line[6:]; continue
            if not line.startswith('+') or line.startswith('+++'): continue
            for k,rx in pat.items():
                if not rx.search(line[1:]): continue
                p=byk[k]
                if short==p['created']: ex['own creating commit']+=1
                elif cur==p['path'] and r==p['repo']: ex['inside the file itself']+=1
                elif date==p['date']: ex['same day as creation']+=1
                elif at<=p['at']: ex['commit predates creation']+=1
                else: kept+=1
print("FINAL-SCAN EXCLUSIONS (full-path matches):",dict(ex)," TOTAL EXCLUDED:",sum(ex.values()))
print("KEPT:",kept)
