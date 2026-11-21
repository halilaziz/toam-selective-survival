T=${TOAM:?source code/env.sh first}
$T/code/analysis/.venv/bin/python - <<'PY'
import glob, os, numpy as np, nibabel as nib
from scipy.ndimage import map_coordinates
from scipy.stats import spearmanr
T=os.environ["TOAM"]
RUNS=[("ses-1","forgetexp","learning"),("ses-1","retrieval","30min"),("ses-2","forgetexp","24h")]
def sample(img, data_shape, affine):
    """values of img (3D) at the voxel centres of a grid with data_shape and affine"""
    ijk=np.indices(data_shape).reshape(3,-1)
    xyz=affine@np.vstack([ijk,np.ones(ijk.shape[1])])
    vox=np.linalg.inv(img.affine)@xyz
    return map_coordinates(np.asarray(img.dataobj,dtype=float),vox[:3],order=1,cval=0.0).reshape(data_shape)
out=[]
for ds,arm in (("ds006265","hipp"),):
    for sd in sorted(glob.glob(f"{T}/raw/{ds}/sub-*")):
        s=os.path.basename(sd)
        for ses,task,lab in RUNS:
            D=f"{T}/derivatives/spmMB/{s}/preproc/{ses}"
            mean=glob.glob(f"{D}/func/meanasub-*task-{task}_*bold.nii"); raw=glob.glob(f"{sd}/{ses}/func/{s}_{ses}_task-{task}_*bold.nii.gz")
            c3=glob.glob(f"{D}/anat/c3sub-*T1w.nii"); c1=glob.glob(f"{D}/anat/c1sub-*T1w.nii")
            if not (mean and raw and c3): continue
            mi=nib.load(mean[0]); m=np.asarray(mi.dataobj,dtype=float)
            A_coreg=mi.affine; A_raw=nib.load(raw[0]).affine
            msk=m>0.1*m.max()
            r={}
            for name,A in (("coreg",A_coreg),("raw",A_raw)):
                cs=sample(nib.load(c3[0]),m.shape,A); gm=sample(nib.load(c1[0]),m.shape,A)
                inbrain=float(((cs+gm)>0.05)[msk].mean())
                r[name]=(spearmanr(m[msk],cs[msk])[0], inbrain)
            out.append((s,lab,r["coreg"][0],r["raw"][0],r["coreg"][1],r["raw"][1]))
print(f"{'sub':10s} {'run':9s} {'rho_coreg':>9s} {'rho_raw':>8s} {'inbrain_coreg':>13s} {'inbrain_raw':>11s}")
for o in out:
    flag=" <==" if o[3]>o[2]+0.02 else ""
    print(f"{o[0]:10s} {o[1]:9s} {o[2]:9.3f} {o[3]:8.3f} {o[4]:13.2f} {o[5]:11.2f}{flag}")
PY
