#!/usr/bin/env python3
"""Final audit: every annexed file present with the size and SHA-256 named by its git-annex key."""
import os, csv, hashlib, sys
T=os.environ['TOAM']; R=list(csv.DictReader(open(f'{T}/manifests/toam_annex_manifest.tsv'),delimiter='\t'))
bad=[]; ok=0
for r in R:
    o=r['obj']
    if not os.path.exists(o) or os.path.getsize(o)!=int(r['size']): bad.append((r['ds'],r['path'],'missing/size')); continue
    h=hashlib.sha256()
    with open(o,'rb') as fh:
        for b in iter(lambda: fh.read(1<<24), b''): h.update(b)
    if h.hexdigest()!=r['sha256']: bad.append((r['ds'],r['path'],'sha256')); continue
    ok+=1
with open(f'{T}/manifests/verify_report.tsv','w') as fh:
    fh.write('ds\tpath\tproblem\n'); [fh.write('\t'.join(b)+'\n') for b in bad]
print(f'verified {ok}/{len(R)} files; problems {len(bad)} (manifests/verify_report.tsv)')
