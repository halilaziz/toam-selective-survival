"""fMRIPrep route for RQ3 (preregistration, Reliability and robustness testing): inputs for the SPM12 smoothing and
first level of one whole-brain participant. Reads only the fMRIPrep derivatives; writes only inside
$TOAM/derivatives/fmriprep_spm/<sub>.
  - the MNI152NLin2009cAsym preprocessed BOLD of the three modelled runs (learning = ses-1 forgetexp, 30-min test =
    ses-1 retrieval, 24-h test = ses-2 forgetexp), uncompressed for SPM12;
  - rp_fmriprep_<run>.txt: fMRIPrep's six motion parameters (trans_x, trans_y, trans_z in mm; rot_x, rot_y, rot_z in
    radians), the same layout as SPM's rp_*.txt;
  - crossSessionWhiteandGreyMatterMask_fmriprep.nii: explicit first-level mask on the BOLD grid, grey + white matter
    probability (fMRIPrep anat, MNI) > 0.2, mirroring the authors' grey + white matter mask (> 0.2) of the SPM route.
usage: python prep_inputs.py <TOAM> <sub>"""
import glob
import gzip
import os
import shutil
import sys

import nibabel as nib
import numpy as np
import pandas as pd
from scipy.ndimage import map_coordinates

T, S = sys.argv[1], sys.argv[2]
FP = f"{T}/derivatives/fmriprep-25.2.7/{S}"
OUT = f"{T}/derivatives/fmriprep_spm/{S}"
SPACE = "space-MNI152NLin2009cAsym"
RUNS = (("ses-1", "forgetexp"), ("ses-1", "retrieval"), ("ses-2", "forgetexp"))
assert os.path.realpath(OUT).startswith(os.path.realpath(T) + "/"), "write only inside TOAM"
grid = None
for ses, task in RUNS:
    bold = glob.glob(f"{FP}/{ses}/func/{S}_{ses}_task-{task}_*{SPACE}_desc-preproc_bold.nii.gz")
    conf = glob.glob(f"{FP}/{ses}/func/{S}_{ses}_task-{task}_*desc-confounds_timeseries.tsv")
    assert len(bold) == 1 and len(conf) == 1, (ses, task, bold, conf)
    d = f"{OUT}/{ses}/func"
    os.makedirs(d, exist_ok=True)
    dst = f"{d}/{os.path.basename(bold[0])[:-3]}"
    if not os.path.exists(dst):
        with gzip.open(bold[0], "rb") as fi, open(dst + ".part", "wb") as fo:
            shutil.copyfileobj(fi, fo, 64 << 20)
        os.replace(dst + ".part", dst)
    img = nib.load(dst)
    c = pd.read_csv(conf[0], sep="\t")[["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"]]
    assert len(c) == img.shape[3] and np.isfinite(c.to_numpy()).all(), (ses, task, len(c), img.shape)
    stem = os.path.basename(bold[0]).split(f"_{SPACE}")[0]
    np.savetxt(f"{d}/rp_fmriprep_{stem}.txt", c.to_numpy(), fmt="%.8e")
    if grid is None:
        grid = img
    else:
        assert np.allclose(grid.affine, img.affine, atol=1e-4) and grid.shape[:3] == img.shape[:3], "runs differ in grid"
    print(ses, task, img.shape, "rp", c.shape, flush=True)
# explicit mask on the BOLD grid
gm = glob.glob(f"{FP}/anat/{S}_*{SPACE}_label-GM_probseg.nii.gz")
wm = glob.glob(f"{FP}/anat/{S}_*{SPACE}_label-WM_probseg.nii.gz")
assert len(gm) == 1 and len(wm) == 1, (gm, wm)
g, w = nib.load(gm[0]), nib.load(wm[0])
assert np.allclose(g.affine, w.affine)
p = np.asarray(g.dataobj, float) + np.asarray(w.dataobj, float)
ijk = np.indices(grid.shape[:3]).reshape(3, -1)
xyz = grid.affine @ np.vstack([ijk, np.ones(ijk.shape[1])])
v = np.linalg.inv(g.affine) @ xyz
m = (map_coordinates(p, v[:3], order=1, cval=0.0).reshape(grid.shape[:3]) > 0.2).astype(np.uint8)
nib.save(nib.Nifti1Image(m, grid.affine), f"{OUT}/crossSessionWhiteandGreyMatterMask_fmriprep.nii")
print("mask voxels", int(m.sum()), flush=True)
