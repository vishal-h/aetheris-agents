import subprocess,json,os,collections,sys
S='/tmp/claude-1000/-home-it-sandbox-elixirws-aetheris-agents/90489c34-9e84-449e-b474-4ca763cbabb4/scratchpad'
REPOS={'agents':'/home/it/sandbox/elixirws/aetheris-agents','harness':'/home/it/sandbox/elixirws/aetheris'}
EXCL={'agents/notes.md','docs/aetheris/claude-notes.md','docs/aetheris/notes.md'}
pop=[]
for r,d in REPOS.items():
    for f in subprocess.run(['git','ls-files'],cwd=d,capture_output=True,text=True).stdout.splitlines():
        if not os.path.basename(f).endswith('notes.md') or f in EXCL: continue
        lines=sum(1 for _ in open(os.path.join(d,f),errors='replace'))
        log=subprocess.run(['git','log','--diff-filter=A','--format=%h|%ad|%at','--date=short','--',f],
                           cwd=d,capture_output=True,text=True).stdout.splitlines()
        if not log:
            log=subprocess.run(['git','log','--format=%h|%ad|%at','--date=short','--',f],cwd=d,capture_output=True,text=True).stdout.splitlines()
        c,dt,at=log[-1].split('|')
        pop.append(dict(repo=r,path=f,base=os.path.basename(f),lines=lines,created=c,date=dt,at=int(at)))
bn=collections.Counter(p['base'] for p in pop)
for p in pop: p['base_unique']= bn[p['base']]==1
json.dump(pop,open(S+'/pop2.json','w'))
print("POPULATION:",len(pop),"files |",sum(p['lines'] for p in pop),"lines")
print("basenames that COLLIDE (>1 file):",sum(1 for p in pop if not p['base_unique']),"files across",
      len([b for b,n in bn.items() if n>1]),"colliding basenames")
for b,n in sorted(bn.items(),key=lambda x:-x[1])[:8]:
    if n>1: print(f"   {n}x  {b}")
ds=sorted(p['date'] for p in pop); print("DATE SPAN:",ds[0],"..",ds[-1])
