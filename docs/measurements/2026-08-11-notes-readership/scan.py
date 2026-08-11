import subprocess, os, json, collections, sys
S='/tmp/claude-1000/-home-it-sandbox-elixirws-aetheris-agents/90489c34-9e84-449e-b474-4ca763cbabb4/scratchpad'
REPOS = {'agents': '/home/it/sandbox/elixirws/aetheris-agents',
         'harness': '/home/it/sandbox/elixirws/aetheris'}
pop = json.load(open(S+'/pop.json'))
bases = {p['base']: p for p in pop}
# commit inventory per repo
commits = {}
for r,d in REPOS.items():
    out = subprocess.run(['git','log','--format=%H|%h|%ad|%s','--date=short'],
                         cwd=d, capture_output=True, text=True).stdout.splitlines()
    commits[r] = [l.split('|',3) for l in out]
    print(f"{r}: {len(commits[r])} commits", file=sys.stderr)
# scan each commit's added lines for any notes basename
hits = collections.defaultdict(list)   # base -> [(repo, short, date, subj, file_in_diff, line)]
for r,d in REPOS.items():
    for full, short, date, subj in commits[r]:
        p = subprocess.run(['git','show','--format=','--unified=0',full],
                           cwd=d, capture_output=True, text=True).stdout
        cur=None
        for line in p.splitlines():
            if line.startswith('+++ b/'): cur=line[6:]; continue
            if not line.startswith('+') or line.startswith('+++'): continue
            body=line[1:]
            for b in bases:
                if b in body:
                    hits[b].append((r, short, date, subj[:60], cur, body.strip()[:400]))
json.dump({k:v for k,v in hits.items()}, open(S+'/hits.json','w'))
print("files with >=1 raw basename hit:", len(hits), file=sys.stderr)
print("total raw hit lines:", sum(len(v) for v in hits.values()), file=sys.stderr)
