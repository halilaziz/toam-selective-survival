#!/usr/bin/env python3
"""Independent QC of SPM12 preprocessing outputs (no outcome data): volumes vs raw, MNI bounding box, motion,
normalisation overlap with SPM's TPM, and slab coverage of the published hippocampal peaks. Read-only on derivatives."""
import os, glob, sys, numpy as np, nibabel as nib
from nibabel.processing import resample_from_to
T=os.environ['TOAM']; D=f'{T}/derivatives/spmMB'  # workspace root, exported by code/env.sh
tpm=nib.load(f'{T}/tools/spm12/tpm/TPM.nii'); tpmd=np.asarray(tpm.dataobj)
brain=nib.Nifti1Image((tpmd[...,0]+tpmd[...,1]+tpmd[...,2]>0.5).astype(np.uint8),tpm.affine)
PEAKS={'L hipp (-27,-16,-14)':(-27,-16,-14),'R hipp (39,-22,-12)':(39,-22,-12)}
subs=sys.argv[1:] or ['sub-60601','sub-60100']
for s in subs:
    ds='ds006265' if os.path.isdir(f'{T}/raw/ds006265/{s}') else 'ds006266'
    print(f'== {s} ({ds})')
    for f in sorted(glob.glob(f'{D}/{s}/preproc/ses-*/func/s6wra*.nii')):
        img=nib.load(f); sh=img.shape; vox=np.round(img.header.get_zooms()[:3],2)
        raw=glob.glob(f'{T}/raw/{ds}/{s}/'+f.split('/preproc/')[1].split('/')[0]+'/func/'+os.path.basename(f)[5:]+'*')
        nraw=nib.load(raw[0]).shape[3] if raw else -1
        corner=img.affine@np.array([0,0,0,1]); far=img.affine@np.array([sh[0]-1,sh[1]-1,sh[2]-1,1])
        mean=np.asarray(img.dataobj[...,:min(sh[3],20)],dtype=np.float32).mean(-1)
        cover=mean>0.05*np.nanmax(mean)
        rp=np.loadtxt(f.replace('/s6wra','/rp_a').replace('.nii','.txt'))
        fd=np.r_[0,np.abs(np.diff(rp[:,:3],axis=0)).sum(1)+50*np.abs(np.diff(rp[:,3:],axis=0)).sum(1)]
        # normalisation check: fraction of covered voxels inside the TPM brain, and Dice for whole-brain data
        cov=nib.Nifti1Image(cover.astype(np.uint8),img.affine)
        b=np.asarray(resample_from_to(brain,cov,order=0).dataobj)>0
        inside=(cover&b).sum()/max(cover.sum(),1); dice=2*(cover&b).sum()/max(cover.sum()+b.sum(),1)
        pk=[]
        for k,xyz in PEAKS.items():
            ijk=np.round(np.linalg.inv(img.affine)@np.array([*xyz,1]))[:3].astype(int)
            ok=all(0<=ijk[i]<sh[i] for i in range(3)) and bool(cover[tuple(ijk)])
            pk.append(f"{k.split(' (')[0]}:{'in' if ok else 'OUT'}")
        task=os.path.basename(f).split('task-')[1].split('_')[0]; ses=f.split('/preproc/')[1].split('/')[0]
        print(f"  {ses} {task:13s} vols {sh[3]} (raw {nraw}) vox {vox.tolist()} bbox x[{corner[0]:.0f},{far[0]:.0f}] y[{corner[1]:.0f},{far[1]:.0f}] z[{corner[2]:.0f},{far[2]:.0f}] | "
              f"maxtrans {np.abs(rp[:,:3]).max():.2f} mm maxrot {np.degrees(np.abs(rp[:,3:]).max()):.2f} deg meanFD {fd.mean():.3f} | in-brain {inside:.2f}"
              + (f" dice {dice:.2f}" if ds=='ds006266' else '') + f" | peaks {' '.join(pk)}")
    m=glob.glob(f'{D}/{s}/preproc/crossSessionWhiteandGreyMatterMaskMNI.nii')
    if m:
        mm=nib.load(m[0]); md=np.asarray(mm.dataobj)>0; b=np.asarray(resample_from_to(brain,mm,order=0).dataobj)>0
        print(f"  crossSession mask: {md.sum()} vox, dice with TPM brain {2*(md&b).sum()/(md.sum()+b.sum()):.2f}")
