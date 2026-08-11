import subprocess,json,re,collections,os,sys
S='/tmp/claude-1000/-home-it-sandbox-elixirws-aetheris-agents/90489c34-9e84-449e-b474-4ca763cbabb4/scratchpad'
REPOS={'agents':'/home/it/sandbox/elixirws/aetheris-agents','harness':'/home/it/sandbox/elixirws/aetheris'}
pop=json.load(open(S+'/pop.json')); by={p['base']:p for p in pop}
popaths={(p['repo'],p['path']) for p in pop}
W=re.compile(r"[a-z0-9]+")
def shingles(text,n=8):
    w=W.findall(text.lower())
    for i in range(len(w)-n+1): yield ' '.join(w[i:i+n])
# 1. shingles per notes file (content AT ITS CREATING COMMIT, so later edits don't leak)
owner=collections.defaultdict(set)
for p in pop:
    blob=subprocess.run(['git','show',f"{p['created']}:{p['path']}"],cwd=REPOS[p['repo']],capture_output=True,text=True).stdout
    for s in set(shingles(blob)): owner[s].add(p['base'])
uniq={s:list(v)[0] for s,v in owner.items() if len(v)==1}
print("shingles total:",len(owner)," unique-to-one-notes-file:",len(uniq),file=sys.stderr)
# 2. subtract shingles that also occur in NON-population tracked .md at HEAD (so a shared quote of a third doc doesn't count)
other=set()
for r,d in REPOS.items():
    for f in subprocess.run(['git','ls-files','*.md'],cwd=d,capture_output=True,text=True).stdout.splitlines():
        if (r,f) in popaths: continue
        try: t=open(os.path.join(d,f),errors='replace').read()
        except: continue
        other.update(shingles(t))
uniq={s:b for s,b in uniq.items() if s not in other}
print("after subtracting non-population .md at HEAD:",len(uniq),file=sys.stderr)
json.dump(uniq,open(S+'/uniq.json','w'))
