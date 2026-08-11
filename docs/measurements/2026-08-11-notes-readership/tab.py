import json,re,collections,datetime
S='/tmp/claude-1000/-home-it-sandbox-elixirws-aetheris-agents/90489c34-9e84-449e-b474-4ca763cbabb4/scratchpad'
ME='90489c34-9e84-449e-b474-4ca763cbabb4'
pop=json.load(open(S+'/pop2.json')); byk={f"{p['repo']}|{p['path']}":p for p in pop}
F=json.load(open(S+'/final.json')); O=json.load(open(S+'/opens2.json'))
# --- R criterion: the hit line attributes CONTENT (a section, a figure, or quoted text) to the file.
#     P otherwise: the path named in a structural field, a list, or a shell command.
SECT=re.compile(r'§|:\d+\b|—\s*\*\*\d|\*\*\d+ items\*\*')
QUOTE=re.compile(r'[«"“”]|\*"')
def classify(body, path, base):
    tail=body.split(base,1)[1] if base in body else ''
    if SECT.search(tail[:80]) or QUOTE.search(tail[:80]): return 'R'
    if SECT.search(body) and QUOTE.search(body): return 'R'
    return 'P'
rows=[]
for p in pop:
    k=f"{p['repo']}|{p['path']}"
    pr=collections.Counter(); rcom=[]
    for r,short,date,subj,cur,body,how in F['P'].get(k,[]):
        c=classify(body,p['path'],p['base']); pr[c]+=1
        if c=='R': rcom.append((short,date,cur))
    q=F['Q'].get(k,[]); qcom=sorted({(x[1],x[2],x[4]) for x in q})
    sess=[s for s,d in O['strong'].get(k,{}).items() if any(x>p['date'] for x in d)]
    wsess=[s for s,d in O['weak'].get(k,{}).items() if any(x>p['date'] for x in d)]
    days=(datetime.date(2026,8,11)-datetime.date.fromisoformat(p['date'])).days
    rows.append(dict(path=p['path'],lines=p['lines'],date=p['date'],days=days,
                     P=pr['P'],R=pr['R'],Q=len(q),Qc=qcom,Rc=rcom,S=len(sess),W=len(wsess)))
rows.sort(key=lambda r:-r['lines'])
json.dump(rows,open(S+'/rows.json','w'))
T=len(rows); TL=sum(r['lines'] for r in rows)
dead=[r for r in rows if r['Q']==0 and r['R']==0 and r['S']==0]
print(f"POPULATION {T} files / {TL} lines")
print(f"P>0: {sum(1 for r in rows if r['P'])} files | R>0: {sum(1 for r in rows if r['R'])} | Q>0: {sum(1 for r in rows if r['Q'])} | later-session-open>0: {sum(1 for r in rows if r['S'])}")
print(f"TOTAL P hits {sum(r['P'] for r in rows)} | R hits {sum(r['R'] for r in rows)} | Q hits {sum(r['Q'] for r in rows)}")
print()
print(f"ZERO Q + ZERO R + ZERO later opens: {len(dead)}/{T} files = {len(dead)/T:.1%}")
print(f"   lines in those files: {sum(r['lines'] for r in dead)}/{TL} = {sum(r['lines'] for r in dead)/TL:.1%}")
print()
print("=== TOP 22 BY LINES ===")
print(f"{'lines':>6} {'days':>5} {'P':>3} {'R':>3} {'Q':>3} {'sess':>4}  path")
for r in rows[:22]:
    print(f"{r['lines']:6d} {r['days']:5d} {r['P']:3d} {r['R']:3d} {r['Q']:3d} {r['S']:4d}  {r['path']}")
print()
big=[r for r in rows if r['lines']>=400]; sml=[r for r in rows if r['lines']<400]
def frac(g,f): return f"{sum(1 for r in g if f(r))}/{len(g)} = {sum(1 for r in g if f(r))/len(g):.0%}"
read=lambda r: r['Q'] or r['R'] or r['S']
print("LENGTH vs READ:  >=400 lines:",frac(big,read),"   <400 lines:",frac(sml,read))
