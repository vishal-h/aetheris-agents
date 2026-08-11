import subprocess,json,re,collections,os,sys
S='/tmp/claude-1000/-home-it-sandbox-elixirws-aetheris-agents/90489c34-9e84-449e-b474-4ca763cbabb4/scratchpad'
REPOS={'agents':'/home/it/sandbox/elixirws/aetheris-agents','harness':'/home/it/sandbox/elixirws/aetheris'}
pop=json.load(open(S+'/pop2.json'))
W=re.compile(r"[a-z0-9]+")
def shg(t,n=8):
    w=W.findall(t.lower())
    for i in range(len(w)-n+1): yield ' '.join(w[i:i+n])
# distinctive shingles per PATH, from content at creating commit
owner=collections.defaultdict(set)
for p in pop:
    blob=subprocess.run(['git','show',f"{p['created']}:{p['path']}"],cwd=REPOS[p['repo']],capture_output=True,text=True).stdout
    for s in set(shg(blob)): owner[s].add((p['repo'],p['path']))
uniq={s:list(v)[0] for s,v in owner.items() if len(v)==1}
popaths={(p['repo'],p['path']) for p in pop}
other=set()
for r,d in REPOS.items():
    for f in subprocess.run(['git','ls-files','*.md'],cwd=d,capture_output=True,text=True).stdout.splitlines():
        if (r,f) in popaths: continue
        try: other.update(shg(open(os.path.join(d,f),errors='replace').read()))
        except: pass
uniq={s:v for s,v in uniq.items() if s not in other}
print("distinctive shingles:",len(uniq),file=sys.stderr)
# path + basename patterns
pat_path={(p['repo'],p['path']): re.compile(re.escape(p['path'])) for p in pop}
pat_base={(p['repo'],p['path']): re.compile(r'(?<![A-Za-z0-9_/-])'+re.escape(p['base'])) for p in pop if p['base_unique']}
byk={(p['repo'],p['path']):p for p in pop}
P=collections.defaultdict(list); Q=collections.defaultdict(list); amb=0
for r,d in REPOS.items():
    log=subprocess.run(['git','log','--format=%H|%h|%ad|%at|%s','--date=short'],cwd=d,capture_output=True,text=True).stdout.splitlines()
    for full,short,date,at,subj in (l.split('|',4) for l in log):
        at=int(at)
        patch=subprocess.run(['git','show','--format=','--unified=0',full],cwd=d,capture_output=True,text=True).stdout
        cur=None
        for line in patch.splitlines():
            if line.startswith('+++ b/'): cur=line[6:]; continue
            if not line.startswith('+') or line.startswith('+++'): continue
            body=line[1:]
            # --- P: path or unique basename mentioned
            for k,rx in pat_path.items():
                p=byk[k]
                if at<=p['at'] or short==p['created'] or date==p['date']: continue
                if cur==p['path'] and r==p['repo']: continue
                if rx.search(body): P[k].append((r,short,date,subj[:70],cur,body.strip()[:300],'path'))
            for k,rx in pat_base.items():
                p=byk[k]
                if at<=p['at'] or short==p['created'] or date==p['date']: continue
                if cur==p['path'] and r==p['repo']: continue
                if p['path'] in body: continue
                if rx.search(body): P[k].append((r,short,date,subj[:70],cur,body.strip()[:300],'base'))
            # --- Q: distinctive shingle
            seen=set()
            for s in shg(body):
                k=uniq.get(s)
                if not k or k in seen: continue
                p=byk[k]
                if at<=p['at'] or short==p['created'] or date==p['date']: continue
                if cur==p['path'] and r==p['repo']: continue
                seen.add(k); Q[k].append((r,short,date,subj[:70],cur,body.strip()[:300],s))
json.dump({'P':{f"{k[0]}|{k[1]}":v for k,v in P.items()},'Q':{f"{k[0]}|{k[1]}":v for k,v in Q.items()}},open(S+'/final.json','w'))
print("P hit lines:",sum(len(v) for v in P.values()),"across",len(P),"files")
print("Q hit lines:",sum(len(v) for v in Q.values()),"across",len(Q),"files")
