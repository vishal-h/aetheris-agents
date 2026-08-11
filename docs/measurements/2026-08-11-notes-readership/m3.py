import json,glob,os,collections,re,sys
S='/tmp/claude-1000/-home-it-sandbox-elixirws-aetheris-agents/90489c34-9e84-449e-b474-4ca763cbabb4/scratchpad'
pop=json.load(open(S+'/pop2.json'))
# match on repo-relative path, or unique basename with left boundary
pats=[]
for p in pop:
    rx=[re.escape(p['path'])]
    if p['base_unique']: rx.append(r'(?<![A-Za-z0-9_/-])'+re.escape(p['base']))
    pats.append((f"{p['repo']}|{p['path']}", re.compile('|'.join(rx))))
opens=collections.defaultdict(lambda: collections.defaultdict(list))  # key -> session -> [(ts,tool)]
nfiles=0
for path in glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl'))+glob.glob(os.path.expanduser('~/.claude/projects/*/*/subagents/*.jsonl')):
    nfiles+=1
    parts=path.split('/')
    # attribute subagent transcripts to their PARENT session uuid
    sess = parts[-4] if 'subagents' in parts else os.path.basename(path)[:-6]
    for line in open(path,errors='replace'):
        try: o=json.loads(line)
        except: continue
        ts=o.get('timestamp'); m=o.get('message')
        if not isinstance(m,dict) or not isinstance(m.get('content'),list): continue
        for b in m['content']:
            if not (isinstance(b,dict) and b.get('type')=='tool_use'): continue
            inp=b.get('input') or {}
            blob=' '.join(str(inp.get(k,'')) for k in ('file_path','command','pattern','path','query','notebook_path'))
            if not blob.strip(): continue
            for k,rx in pats:
                if rx.search(blob): opens[k][sess].append((ts,b.get('name')))
json.dump({k:{s:v for s,v in d.items()} for k,d in opens.items()},open(S+'/opens.json','w'))
print("transcripts scanned:",nfiles,file=sys.stderr)
print("files with >=1 session touch:",len(opens),file=sys.stderr)
