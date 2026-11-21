#!/usr/bin/env python3
"""Quality-control overlays required by the preregistration before any first-level GLM (Part 5: "each participant's
normalised mean EPI is overlaid on the MNI template and on the participant's normalised T1 image; participants whose
hippocampal region is visibly misaligned are excluded, and the images and decisions are archived").

For every participant and both retrieval runs (30-min test: ses-1 task-retrieval; 24-h test: ses-2 task-forgetexp):
  - background: the normalised mean EPI (mean of the first 20 volumes of wra*), scaled to its 2nd-98th percentile
    inside the field of view;
  - red contour: SPM TPM grey matter (p = 0.5), i.e. the MNI template;
  - cyan contour: the participant's own grey matter from the T1 of the same session, carried through the same
    coregistration and normalisation as the EPI (wrfc1*, p = 0.5);
  - zoomed sagittal views through each published hippocampal peak (yellow markers) and a coronal view through both.
Numbers per run: share of EPI coverage inside the TPM brain, and Dice of participant vs TPM grey matter inside the
EPI coverage (normalisation check). One PNG per participant. Reads no events or responses.

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
D = os.environ.get("TOAM_QC_DERIV") or f"{T}/derivatives/spmMB"   # sensitivity analysis: derivatives/spmMB_coregfix
PEAKS = {"L": (-27, -16, -14), "R": (39, -22, -12)}
RUNS = {"30min": ("ses-1", "task-retrieval"), "24h": ("ses-2", "task-forgetexp")}
tpm = image.index_img(f"{T}/tools/spm12/tpm/TPM.nii", 0)
subs = sys.argv[3:] or sorted(os.path.basename(p) for p in glob.glob(f"{D}/sub-*"))


VIEWS = [("x", -27, "sagittal x=-27 (L peak)"), ("x", 39, "sagittal x=39 (R peak)"), ("y", -19, "coronal y=-19")]
LIMS = {"x": ((-62, 22), (-48, 22)), "y": ((-58, 58), (-48, 22))}


def zoom(display, mode):
    (x0, x1), (y0, y1) = LIMS[mode]
    for ax in display.axes.values():
        ax.ax.set_xlim(x0, x1)
        ax.ax.set_ylim(y0, y1)


rows = []
for s in subs:
    fig, axes = plt.subplots(2, 3, figsize=(18, 8))
    for i, (rname, (ses, task)) in enumerate(RUNS.items()):
        f = sorted(glob.glob(f"{D}/{s}/preproc/{ses}/func/wra*{task}*.nii"))
        gm = sorted(glob.glob(f"{D}/{s}/preproc/{ses}/anat/wrfc1*.nii"))
        if not f:
            for j in range(3):
                axes[i, j].set_axis_off()
                axes[i, j].set_title(f"{s} {rname}: no wra file", fontsize=10)
            rows.append((s, rname, "missing", np.nan, np.nan))
            continue
        img = nib.load(f[0])
        mean = image.mean_img(image.index_img(img, slice(0, min(20, img.shape[3]))), copy_header=True)
        m = np.asarray(mean.dataobj)
        cov = m > 0.05 * np.nanmax(m)
        lo, hi = np.percentile(m[cov], [2, 98])
        tb = np.asarray(image.resample_to_img(tpm, mean, interpolation="continuous", copy_header=True,
                                              force_resample=True).dataobj) > 0.5
        inside = float((cov & (np.asarray(image.resample_to_img(tpm, mean, interpolation="nearest", copy_header=True,
                                                                force_resample=True).dataobj) > 0.05)).sum()
                       / max(cov.sum(), 1))
        dice = np.nan
        if gm:
            g = np.asarray(image.resample_to_img(gm[0], mean, interpolation="continuous", copy_header=True,
                                                 force_resample=True).dataobj) > 0.5
            a, b = g & cov, tb & cov
            dice = float(2 * (a & b).sum() / max(a.sum() + b.sum(), 1))
        rows.append((s, rname, os.path.basename(f[0]), inside, dice))
        for j, (mode, cut, label) in enumerate(VIEWS):
            d = plotting.plot_img(mean, cut_coords=[cut], display_mode=mode, axes=axes[i, j], cmap="gray",
                                  vmin=lo, vmax=hi, black_bg=True, draw_cross=False, annotate=False, colorbar=False,
                                  title=f"{s} {rname} {label} | GM Dice {dice:.2f}")
            d.add_contours(tpm, levels=[0.5], colors="r", linewidths=1.0)
            if gm:
                d.add_contours(gm[0], levels=[0.5], colors="c", linewidths=1.0)
            d.add_markers([PEAKS["L"], PEAKS["R"]], marker_color="yellow", marker_size=40)
            zoom(d, mode)
    fig.savefig(f"{OUT}/{s}_qc.png", dpi=75, bbox_inches="tight")
    plt.close(fig)
    print("ok", s, flush=True)
with open(f"{OUT}/qc_summary.tsv", "w") as fh:
    fh.write("sub\trun\tfile\tepi_coverage_inside_tpm_brain\tgm_dice_participant_vs_tpm\n")
    for r in rows:
        fh.write("\t".join(str(x) for x in r) + "\n")
