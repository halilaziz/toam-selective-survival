#!/bin/bash
# Download progress: bytes present vs manifest, files complete, process state, recent errors.
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
python3 - <<'PY'
import os,csv
T=os.environ['TOAM']; R=list(csv.DictReader(open(f'{T}/manifests/toam_annex_manifest.tsv'),delimiter='\t'))
tot=sum(int(r['size']) for r in R); have=0; full=0
for r in R:
    o=r['obj']
    if os.path.exists(o):
        s=os.path.getsize(o); have+=min(s,int(r['size']))
        full+= (s==int(r['size']) and not os.path.exists(o+'.aria2'))
print(f"complete files {full}/{len(R)} | {have/1e9:.1f} of {tot/1e9:.1f} GB ({100*have/tot:.1f}%)")
PY
pid=$(cat $TOAM/logs/aria2.pid 2>/dev/null); if [ -n "$pid" ] && kill -0 $pid 2>/dev/null; then echo "aria2c running (pid $pid)"; else echo "aria2c not running"; fi
L=$(ls -t $TOAM/logs/aria2_2*.log 2>/dev/null | head -1); [ -n "$L" ] && { echo "errors in log: $(grep -c -E '\[ERROR\]' $L)"; grep -E '\[ERROR\]' $L | tail -3; }
