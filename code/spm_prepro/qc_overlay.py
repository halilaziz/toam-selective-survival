#!/usr/bin/env python3
"""QC images: normalised mean EPI (wra, first 20 volumes) and normalised T1, with SPM TPM grey-matter contours,
cut at the published left hippocampal peak. Writes PNGs to logs/qc_png only."""
import os, sys, glob, matplotlib; matplotlib.use('Agg')
from nilearn import plotting, image
T=os.environ['TOAM']; D=f'{T}/derivatives/spmMB'; out=f'{T}/logs/qc_png'; os.makedirs(out,exist_ok=True)
gm=image.index_img(f'{T}/tools/spm12/tpm/TPM.nii',0)
for s in sys.argv[1:]:
    f=sorted(glob.glob(f'{D}/{s}/preproc/ses-1/func/wra*task-retrieval*.nii'))[0]
    mean=image.mean_img(image.index_img(f,slice(0,20)),copy_header=True)
    for name,img in (('EPI_ses-1_retrieval',mean),('T1_ses-1',sorted(glob.glob(f'{D}/{s}/preproc/ses-1/anat/wskullStripped*.nii'))[0])):
        d=plotting.plot_anat(img,cut_coords=(-27,-16,-14),display_mode='ortho',title=f'{s} {name} + TPM GM 0.5',dim=-0.5,draw_cross=True)
        d.add_contours(gm,levels=[0.5],colors='r',linewidths=0.6)
        d.savefig(f'{out}/{s}_{name}.png',dpi=90); d.close()
    print('ok',s)
