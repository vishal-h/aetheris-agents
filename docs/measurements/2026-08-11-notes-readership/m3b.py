import json,glob,os,collections,re,sys
S='/tmp/claude-1000/-home-it-sandbox-elixirws-aetheris-agents/90489c34-9e84-449e-b474-4ca763cbabb4/scratchpad'
ME='90489c34-9e84-449e-b474-4ca763cbabb4'
pop=json.load(open(S+'/pop2.json'))
pats=[]
for p in pop:
    rx=[re.escape(p['path'])]
    if p['base_unique']: rx.append(r'(?<![A-Za-z0-9_/-])'+re.escape(p['base']))
    pats.append((f"{p['repo']}|{p['path']}", re.compile('|'.join(rx)), re.compile(re.escape(p['path'])+r'$|'+re.escape('/'+p['path'])+r'$')))
READCLASS={'Read','Edit','Write','NotebookEdit'}
strong=collections.defaultdict(lambda: collections.defaultdict(set))
weak  =collections.defaultdict(lambda: collections.defaultdict(set))
for path in glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl'))+glob.glob(os.path.expanduser('~/.claude/projects/*/*/subagents/*.jsonl')):
    parts=path.split('/')
    sess = parts[-3] if 'subagents' in parts else os.path.basename(path)[:-6]
    for line in open(path,errors='replace'):
        try: o=json.loads(line)
        except: continue
        ts=(o.get('timestamp') or '')[:10]; m=o.get('message')
        if not isinstance(m,dict) or not isinstance(m.get('content'),list): continue
        for b in m['content']:
            if not (isinstance(b,dict) and b.get('type')=='tool_use'): continue
            nm=b.get('name'); inp=b.get('input') or {}
            fp=str(inp.get('file_path','')); cmd=' '.join(str(inp.get(k,'')) for k in ('command','pattern','path','query'))
            for k,rx,fprx in pats:
                if nm in READCLASS and fp and fprx.search(fp): strong[k][sess].add(ts)
                elif cmd and rx.search(cmd):                   weak[k][sess].add(ts)
json.dump({'strong':{k:{s:sorted(v) for s,v in d.items()} for k,d in strong.items()},
           'weak':  {k:{s:sorted(v) for s,v in d.items()} for k,d in weak.items()}}, open(S+'/opens2.json','w'))
byk={f"{p['repo']}|{p['path']}":p for p in pop}
def later(d,k,excl_me):
    p=byk[k]; out=[]
    for s,dates in d.get(k,{}).items():
        if excl_me and s==ME: continue
        if any(x>p['date'] for x in dates): out.append(s)
    return out
tot=len(pop)
for label,excl in (('EXCLUDING this measurement session',True),('including it',False)):
    ns=sum(1 for p in pop if later(strong,f"{p['repo']}|{p['path']}",excl))
    nw=sum(1 for p in pop if later(weak,f"{p['repo']}|{p['path']}",excl))
    print(f"{label}: files opened later by a Read/Edit/Write = {ns}/{tot} | by any command text = {nw}/{tot}")
print()
print("=== files with a STRONG later open (excluding this session) ===")
for p in sorted(pop,key=lambda x:-x['lines']):
    k=f"{p['repo']}|{p['path']}"; L=later(strong,k,True)
    if L: print(f"  {p['lines']:5d}L {p['date']} {p['path']}  → {len(L)} session(s)")
