T=${TOAM:?source code/env.sh first}
OUT=$T/results/qc_overlays_v2/coreg_native; mkdir -p $OUT
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 $T/code/analysis/.venv/bin/python - <<'PY'
import glob, os, numpy as np, nibabel as nib
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.ndimage import map_coordinates
from scipy.stats import spearmanr
T=os.environ["TOAM"]; OUT=f"{T}/results/qc_overlays_v2/coreg_native"
RUN={"learning":("ses-1","forgetexp"),"30min":("ses-1","retrieval"),"24h":("ses-2","forgetexp")}
BOX=dict(ax=(15,45),y=(-45,-5),z=(-32,0))   # MNI box around both hippocampi and temporal horns (|x| 15-45 mm)
FIG={("sub-62954","learning"),("sub-62954","30min"),("sub-69606","30min"),("sub-63071","24h")}
def sample(data, aff, shape, A, order=1):
    ijk=np.indices(shape).reshape(3,-1); xyz=A@np.vstack([ijk,np.ones(ijk.shape[1])])
    v=np.linalg.inv(aff)@xyz
    return map_coordinates(data,v[:3],order=order,cval=0.0).reshape(shape)
rows=[]
for sd in [f"{T}/raw/ds006265/{x}" for x in ("sub-62954","sub-69606","sub-63071")]:
    s=os.path.basename(sd); cache={}
    for lab,(ses,task) in RUN.items():
        D=f"{T}/derivatives/spmMB/{s}/preproc/{ses}"
        if ses not in cache:
            iy=nib.load(glob.glob(f"{D}/anat/iy_sub-*T1w.nii")[0]); f=np.asarray(iy.dataobj,dtype=np.float32)
            f=f.reshape(f.shape[:3]+(3,))
            box=((np.abs(f[...,0])>=BOX["ax"][0])&(np.abs(f[...,0])<=BOX["ax"][1])&(f[...,1]>=BOX["y"][0])&(f[...,1]<=BOX["y"][1])
                 &(f[...,2]>=BOX["z"][0])&(f[...,2]<=BOX["z"][1])).astype(np.float32)
            c3i=nib.load(glob.glob(f"{D}/anat/c3sub-*T1w.nii")[0]); c1i=nib.load(glob.glob(f"{D}/anat/c1sub-*T1w.nii")[0])
            assert np.allclose(c3i.affine, iy.affine, atol=1e-3)
            cache[ses]=(box,np.asarray(c3i.dataobj,dtype=np.float32),np.asarray(c1i.dataobj,dtype=np.float32),c3i.affine,
                        (float(np.nanmin(f[...,0])),float(np.nanmax(f[...,0]))))
            del f
        box,c3,c1,aff,rng=cache[ses]
        mi=nib.load(glob.glob(f"{D}/func/meanasub-*task-{task}_*bold.nii")[0]); m=np.asarray(mi.dataobj,dtype=float)
        A_raw=nib.load(glob.glob(f"{sd}/{ses}/func/{s}_{ses}_task-{task}_*bold.nii.gz")[0]).affine
        res={}; maps={}
        for name,A in (("coreg",mi.affine),("scanner",A_raw)):
            b=sample(box,aff,m.shape,A)>0.5; c=sample(c3,aff,m.shape,A); g=sample(c1,aff,m.shape,A)
            sel=b&(m>0.1*m.max())
            res[name]=(spearmanr(m[sel],c[sel])[0] if sel.sum()>200 else np.nan, int(sel.sum()))
            maps[name]=(b,c,g)
        rows.append((s,lab,res["coreg"][0],res["scanner"][0],res["coreg"][1],res["scanner"][1]))
        if (s,lab) in FIG:
            b=maps["scanner"][0]; zc=int(np.argmax(b.sum((0,1)))); zs=[max(zc-4,0),zc,min(zc+4,m.shape[2]-1)]
            ii,jj=np.where(b[:,:,zc]); i0,i1=max(ii.min()-15,0),min(ii.max()+15,m.shape[0]); j0,j1=max(jj.min()-15,0),min(jj.max()+15,m.shape[1])
            lo,hi=np.percentile(m[m>0.1*m.max()],[2,98])
            fig,ax=plt.subplots(2,3,figsize=(15,9))
            for r,name in enumerate(("coreg","scanner")):
                _,c,g=maps[name]
                for j,z in enumerate(zs):
                    a=ax[r,j]; a.imshow(np.rot90(m[i0:i1,j0:j1,z]),cmap="gray",vmin=lo,vmax=hi,interpolation="nearest")
                    a.contour(np.rot90(c[i0:i1,j0:j1,z]),levels=[0.5],colors="c",linewidths=1.0)
                    a.contour(np.rot90(g[i0:i1,j0:j1,z]),levels=[0.5],colors="r",linewidths=0.7)
                    a.set_axis_off(); a.set_title(("SPM coregistration (used)" if name=="coreg" else "scanner coordinates")+f" | slice {z+1}",fontsize=10)
            fig.suptitle(f"{s} {lab}: medial temporal crop (both hippocampi); T1 CSF cyan, GM red (p = 0.5); "
                         f"rho(EPI, CSF) in MTL box: SPM {res['coreg'][0]:.2f}, scanner {res['scanner'][0]:.2f}",fontsize=11)
            fig.tight_layout(); fig.savefig(f"{OUT}/{s}_{lab}_MTLcrop.png",dpi=70); plt.close(fig)
    print("done",s,"iy x-range",tuple(round(v) for v in cache["ses-1"][4]),flush=True)
with open(f"{T}/results/qc_overlays_v2/coreg_mtl_rho_extra_crops.tsv","w") as fh:
    fh.write("sub\trun\trho_csf_mtl_spm\trho_csf_mtl_scanner\tn_vox_spm\tn_vox_scanner\n")
    for r in rows: fh.write(f"{r[0]}\t{r[1]}\t{r[2]:.3f}\t{r[3]:.3f}\t{r[4]}\t{r[5]}\n")
PY
cat $T/results/qc_overlays_v2/coreg_mtl_rho_extra_crops.tsv
