T=${TOAM:?source code/env.sh first}
mkdir -p $T/results/qc_overlays_v2
$T/code/analysis/.venv/bin/python - <<'PY'
import glob, os, numpy as np, nibabel as nib
T=os.environ["TOAM"]
RUNS=[("ses-1","forgetexp","learning"),("ses-1","retrieval","30min"),("ses-1","consolidation","oddeven"),("ses-2","forgetexp","24h")]
def rot_deg(R):
    R=R/np.cbrt(np.linalg.det(R))
    return float(np.degrees(np.arccos(np.clip((np.trace(R)-1)/2,-1,1))))
rows=[]
for ds,arm in (("ds006265","hipp"),("ds006266","wb")):
    for sd in sorted(glob.glob(f"{T}/raw/{ds}/sub-*")):
        s=os.path.basename(sd); M={}; C={}
        for ses,task,lab in RUNS:
            raw=glob.glob(f"{sd}/{ses}/func/{s}_{ses}_task-{task}_*bold.nii*")
            ra=glob.glob(f"{T}/derivatives/spmMB/{s}/preproc/{ses}/func/rasub-*task-{task}_*bold.nii")
            if not raw or not ra: continue
            i0=nib.load(raw[0]); i1=nib.load(ra[0])
            m=i1.affine@np.linalg.inv(i0.affine); c=i0.affine@np.r_[(np.array(i0.shape[:3])-1)/2,1]
            M[lab]=m; C[lab]=c
            d=(m@c-c)[:3]
            row=dict(sub=s,arm=arm,run=lab,shift_mm=float(np.linalg.norm(d)),dx=d[0],dy=d[1],dz=d[2],rot_deg=rot_deg(m[:3,:3]))
            if lab in ("30min","oddeven") and "learning" in M:
                D=m@np.linalg.inv(M["learning"]); dd=(D@c-c)[:3]
                row.update(vs_learning_mm=float(np.linalg.norm(dd)),vs_learning_deg=rot_deg(D[:3,:3]))
            rows.append(row)
cols=["sub","arm","run","shift_mm","dx","dy","dz","rot_deg","vs_learning_mm","vs_learning_deg"]
out=f"{T}/results/qc_overlays_v2/coreg_check.tsv"
with open(out,"w") as fh:
    fh.write("\t".join(cols)+"\n")
    for r in rows:
        fh.write("\t".join((f"{r[c]:.2f}" if isinstance(r.get(c),float) else str(r.get(c,""))) for c in cols)+"\n")
print("wrote",out,len(rows))
PY
column -t $T/results/qc_overlays_v2/coreg_check.tsv | awk 'NR==1 || $3!="oddeven"' | sort -k1,1 -k3,3 | awk 'NR==1{print;next} ($4>8 || $8>5 || ($9!="" && ($9>5 || $10>3)))' 
echo "== all rows count"; wc -l $T/results/qc_overlays_v2/coreg_check.tsv
