import subprocess, os, json, re, collections
REPOS = {'agents': '/home/it/sandbox/elixirws/aetheris-agents',
         'harness': '/home/it/sandbox/elixirws/aetheris'}
EXCLUDE = {'agents/notes.md', 'docs/aetheris/claude-notes.md', 'docs/aetheris/notes.md'}
def sh(repo, *a):
    return subprocess.run(a, cwd=REPOS[repo], capture_output=True, text=True).stdout
pop=[]
for r in REPOS:
    for f in sh(r,'git','ls-files').splitlines():
        b=os.path.basename(f)
        if not b.endswith('notes.md'): continue
        if f in EXCLUDE: continue
        lines=sum(1 for _ in open(os.path.join(REPOS[r],f), errors='replace'))
        log=sh(r,'git','log','--diff-filter=A','--format=%h|%ad','--date=short','--','ature'.replace('ature',f)).splitlines()
        if not log:
            log=sh(r,'git','log','--format=%h|%ad','--date=short','--',f).splitlines()
        c,d=(log[-1].split('|') if log else ('?','?'))
        pop.append(dict(repo=r, path=f, base=b, lines=lines, created=c, date=d))
pop.sort(key=lambda x:-x['lines'])
json.dump(pop, open('/tmp/claude-1000/-home-it-sandbox-elixirws-aetheris-agents/90489c34-9e84-449e-b474-4ca763cbabb4/scratchpad/pop.json','w'), indent=0)
print("POPULATION:", len(pop), "files")
print("TOTAL LINES:", sum(p['lines'] for p in pop))
ds=sorted(p['date'] for p in pop if p['date']!='?')
print("DATE SPAN:", ds[0], "..", ds[-1])
print("BY REPO:", collections.Counter(p['repo'] for p in pop))
print()
print("TOP 15 BY LINES:")
for p in pop[:15]: print(f"  {p['lines']:5d}  {p['date']}  {p['created']}  {p['repo']:7s} {p['path']}")
