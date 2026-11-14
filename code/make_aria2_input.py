#!/usr/bin/env python3
"""TOAM download manifest. Every annexed file in the git clones (tag 1.0.2) is a symlink whose target names its
git-annex key, SHA256E-s<size>--<sha256><ext>. Content is fetched from OpenNeuro's S3 bucket straight into the
annex object path, so the symlinks resolve; aria2c checks each file's SHA-256 against the key."""
import os, re, csv
T=os.environ['TOAM']; RAW=f'{T}/raw'; rows=[]
for ds in ('ds006266','ds006265'):
    root=f'{RAW}/{ds}'
    for dp,dn,fn in os.walk(root):
        dn[:]=[d for d in dn if d!='.git']
        for f in fn:
            p=os.path.join(dp,f)
            if not os.path.islink(p): continue
            tgt=os.readlink(p); key=os.path.basename(tgt)
            m=re.match(r'SHA256E-s(\d+)--([0-9a-f]{64})',key)
            if not m: print('UNPARSED KEY',p,key); continue
            rel=os.path.relpath(p,root)
            rows.append(dict(ds=ds,path=rel,size=int(m.group(1)),sha256=m.group(2),key=key,
                             obj=os.path.normpath(os.path.join(dp,tgt)),url=f'https://s3.amazonaws.com/openneuro.org/{ds}/{rel}'))
def prio(r):  # anatomy first, then whole-brain BOLD (ds006266), then small-FOV BOLD, then the rest
    p=r['path']; k=0 if ('/anat/' in p or '/fmap/' in p) else 1 if (r['ds']=='ds006266' and '/func/' in p) else 2 if '/func/' in p else 3
    return (k,r['ds'],p)
rows.sort(key=prio)
with open(f'{T}/manifests/toam_annex_manifest.tsv','w') as fh:
    w=csv.DictWriter(fh,fieldnames=list(rows[0]),delimiter='\t'); w.writeheader(); w.writerows(rows)
todo=empty=done=0
with open(f'{T}/manifests/aria2_input.txt','w') as fh:
    for r in rows:
        os.makedirs(os.path.dirname(r['obj']),exist_ok=True)
        if r['size']==0:
            if not os.path.exists(r['obj']): open(r['obj'],'w').close()
            empty+=1; continue
        if os.path.exists(r['obj']) and os.path.getsize(r['obj'])==r['size'] and not os.path.exists(r['obj']+'.aria2'):
            done+=1; continue
        fh.write(f"{r['url']}\n  dir={os.path.dirname(r['obj'])}\n  out={os.path.basename(r['obj'])}\n  checksum=sha-256={r['sha256']}\n")
        todo+=1
print(f"annexed files {len(rows)} ({sum(r['size'] for r in rows)/1e9:.1f} GB) | to download {todo} | already present {done} | empty {empty}")
