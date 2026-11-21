#!/usr/bin/env python3
"""Quality-control overlays required by the preregistration before any first-level GLM (Part 5: "each participant's
normalised mean EPI is overlaid on the MNI template and on the participant's normalised T1 image; participants whose
hippocampal region is visibly misaligned are excluded, and the images and decisions are archived").

For every participant and both retrieval runs (30-min test: ses-1 task-retrieval; 24-h test: ses-2 task-forgetexp),
the normalised mean EPI (mean of the first 20 volumes of wra*) is the background, the SPM TPM grey-matter contour
(p = 0.5) shows the MNI template, and the edges of the participant's normalised T1 (wskullStripped, same session) show
the anatomy. Cuts go through both published hippocampal peaks. In the small-field-of-view arm the normalised T1 covers
only the slab (SPM12 Normalise: Write masking). One PNG per participant, plus a numeric summary (share of EPI coverage
inside the TPM brain). Reads no events or responses.

usage (fMRIPrep container python): python qc_overlays.py <TOAM> <out_dir> [sub ...]
"""
import glob
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import nibabel as nib  # noqa: E402
from nilearn import image, plotting  # noqa: E402

T, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
D = f"{T}/derivatives/spmMB"
PEAKS = {"L (-27,-16,-14)": (-27, -16, -14), "R (39,-22,-12)": (39, -22, -12)}
RUNS = {"30 min (ses-1 retrieval)": ("ses-1", "task-retrieval"), "24 h (ses-2 forgetexp)": ("ses-2", "task-forgetexp")}
tpm = image.index_img(f"{T}/tools/spm12/tpm/TPM.nii", 0)
subs = sys.argv[3:] or sorted(os.path.basename(p) for p in glob.glob(f"{D}/sub-*"))
rows = []
for s in subs:
    fig, axes = plt.subplots(2, 2, figsize=(16, 7.5))
    for i, (rname, (ses, task)) in enumerate(RUNS.items()):
        f = sorted(glob.glob(f"{D}/{s}/preproc/{ses}/func/wra*{task}*.nii"))
        t1 = sorted(glob.glob(f"{D}/{s}/preproc/{ses}/anat/wskullStripped*.nii"))
        if not f:
            for j in range(2):
                axes[i, j].set_axis_off(); axes[i, j].set_title(f"{s} {rname}: no wra file", fontsize=9)
            rows.append((s, rname, "missing", np.nan)); continue
        img = nib.load(f[0])
        mean = image.mean_img(image.index_img(img, slice(0, min(20, img.shape[3]))), copy_header=True)
        m = np.asarray(mean.dataobj); cov = m > 0.05 * np.nanmax(m)
        brain = np.asarray(image.resample_to_img(tpm, mean, interpolation="nearest", copy_header=True,
                                                 force_resample=True).dataobj) > 0.5
        inside = float((cov & brain).sum() / max(cov.sum(), 1))
        rows.append((s, rname, os.path.basename(f[0]), inside))
        for j, (pname, xyz) in enumerate(PEAKS.items()):
            d = plotting.plot_anat(mean, cut_coords=xyz, display_mode="ortho", axes=axes[i, j], dim=-0.3,
                                   draw_cross=True, annotate=False,
                                   title=f"{s} | {rname} | peak {pname} | inside-brain {inside:.2f}")
            d.add_contours(tpm, levels=[0.5], colors="r", linewidths=0.6)
            if t1:
                d.add_edges(t1[0], color="c")
    fig.savefig(f"{OUT}/{s}_qc.png", dpi=70, bbox_inches="tight"); plt.close(fig)
    print("ok", s, flush=True)
with open(f"{OUT}/qc_summary.tsv", "w") as fh:
    fh.write("sub\trun\tfile\tepi_coverage_inside_tpm_brain\n")
    for r in rows:
        fh.write("\t".join(str(x) for x in r) + "\n")
