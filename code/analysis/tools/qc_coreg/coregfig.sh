T=${TOAM:?source code/env.sh first}
OUT=$T/results/qc_overlays_v2/coreg_native; mkdir -p $OUT
$T/code/analysis/.venv/bin/python - <<'PY'
import glob, os, numpy as np, nibabel as nib
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.ndimage import map_coordinates
T=os.environ["TOAM"]; OUT=f"{T}/results/qc_overlays_v2/coreg_native"
RUN={"learning":("ses-1","forgetexp"),"30min":("ses-1","retrieval"),"24h":("ses-2","forgetexp")}
CASES=[("sub-60601","30min"),("sub-67823","30min"),("sub-67823","24h"),("sub-67903","learning"),("sub-67903","30min"),
       ("sub-67903","24h"),("sub-62162","learning"),("sub-62162","30min"),("sub-65837","30min"),("sub-69606","30min"),
       ("sub-68766","30min"),("sub-63158","30min")]
def sample(img, shape, A):
    ijk=np.indices(shape).reshape(3,-1); xyz=A@np.vstack([ijk,np.ones(ijk.shape[1])])
    v=np.linalg.inv(img.affine)@xyz
    return map_coordinates(np.asarray(img.dataobj,dtype=float),v[:3],order=1,cval=0.0).reshape(shape)
for s,lab in CASES:
    ses,task=RUN[lab]; D=f"{T}/derivatives/spmMB/{s}/preproc/{ses}"
    mi=nib.load(glob.glob(f"{D}/func/meanasub-*task-{task}_*bold.nii")[0]); m=np.asarray(mi.dataobj,dtype=float)
    A_raw=nib.load(glob.glob(f"{T}/raw/ds006265/{s}/{ses}/func/{s}_{ses}_task-{task}_*bold.nii.gz")[0]).affine
    c3=nib.load(glob.glob(f"{D}/anat/c3sub-*T1w.nii")[0]); c1=nib.load(glob.glob(f"{D}/anat/c1sub-*T1w.nii")[0])
    lo,hi=np.percentile(m[m>0.1*m.max()],[2,98]); nz=m.shape[2]; zs=[nz//4, nz//2, 3*nz//4]
    fig,ax=plt.subplots(2,3,figsize=(13,8.6))
    for r,(name,A) in enumerate((("SPM coregistration (used)",mi.affine),("scanner coordinates (no coregistration)",A_raw))):
        g=sample(c1,m.shape,A); c=sample(c3,m.shape,A)
        for j,z in enumerate(zs):
            a=ax[r,j]; a.imshow(np.rot90(m[:,:,z]),cmap="gray",vmin=lo,vmax=hi)
            a.contour(np.rot90(c[:,:,z]),levels=[0.5],colors="c",linewidths=0.8)
            a.contour(np.rot90(g[:,:,z]),levels=[0.5],colors="r",linewidths=0.6)
            a.set_axis_off(); a.set_title(f"{name}\nslice {z+1}/{nz}",fontsize=9)
    fig.suptitle(f"{s} {lab}: mean EPI (native slab) with the same-session T1 CSF (cyan) and grey matter (red), p = 0.5",fontsize=11)
    fig.tight_layout(); fig.savefig(f"{OUT}/{s}_{lab}_coreg_vs_scanner.png",dpi=60); plt.close(fig); print("ok",s,lab,flush=True)
PY
ls $OUT | wc -l
