#!/usr/bin/env python3
"""RQ2 primary ROI restricted to the field of view of both retrieval runs (qc_records/ROI_FOV_CORRECTION_PLAN.md).

Why: implementation note 8 counts a sphere voxel as covered when it lies inside the slab. roi.py took "finite in the
contrast image" as covered, assuming that SPM's analysis mask is the intersection of the sessions. In this pipeline
the explicit mask is the union of two session masks (crossSessionWhiteandGreyMatterMaskMNI, (i1 + i2) >= 1), the
normalised data are int16 with exact zeros outside the field of view, and mthresh is -Inf, so voxels outside the
30-minute or 24-hour slab enter the contrast with zero data. Here each sphere is restricted to voxels that are
non-zero in the first volume of BOTH retrieval runs' normalised images (wra*, the input of the 6-mm smoothing).
Everything else is roi.py: 6-mm spheres at the published peaks, mean over voxels, spheres averaged with equal
weight, NaN if a sphere keeps no voxel (note 8). Output has the columns of `run_toam.py roi`, so that
`run_toam.py group` runs unchanged.
usage: python roi_fov.py <specs dir> <out csv>"""
import glob
import json
import os
import sys

import nibabel as nib
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from toam_analysis import roi  # noqa: E402

specs, out = sys.argv[1], sys.argv[2]
rows, cov_rows = [], []
for f in sorted(glob.glob(os.path.join(specs, "spec_sub-*.json"))):
    sp = json.load(open(f))
    assert sp["arm"] == "hipp", "RQ2 only"
    fov, ref = {}, None
    for S in sp["sessions"]:
        if S["kind"] not in ("30min", "24h"):
            continue
        w = sorted(glob.glob(os.path.join(S["func_dir"], f"wra*task-{S['task']}_*bold.nii")))
        assert len(w) == 1, (sp["sub"], S["kind"], w)
        img = nib.load(w[0])
        v = np.asarray(img.dataobj[..., 0], dtype=float)
        fov[S["kind"]] = np.isfinite(v) & (v != 0)
        ref = img if ref is None else ref
        assert np.allclose(ref.affine, img.affine, atol=1e-4) and ref.shape[:3] == img.shape[:3]
    both = fov["30min"] & fov["24h"]
    tsv = os.path.join(sp["outdir"], "contrasts.tsv")
    cons = dict(pd.read_csv(tsv, sep="\t").itertuples(index=False)) if os.path.exists(tsv) else {}
    row = {"sub": sp["sub"], "arm": sp["arm"]}
    for c in sp["contrasts"]:
        name = c["name"]
        if name not in cons:
            row[name] = np.nan
            continue
        con = nib.load(os.path.join(sp["outdir"], cons[name]))
        assert np.allclose(con.affine, ref.affine, atol=1e-4) and con.shape[:3] == ref.shape[:3], "grid mismatch"
        data = np.asarray(con.dataobj, dtype=float)
        means, covs = [], []
        for centre in roi.RQ2_PEAKS:
            sm = roi.sphere_mask(con, centre)
            keep = sm & both & np.isfinite(data)
            covs.append(float(keep.sum() / sm.sum()))
            means.append(float(data[keep].mean()) if keep.any() else np.nan)
            cov_rows.append({"sub": sp["sub"], "contrast": name, "centre": str(centre), "n_sphere": int(sm.sum()),
                             "in_fov_30min": float(fov["30min"][sm].mean()), "in_fov_24h": float(fov["24h"][sm].mean()),
                             "kept": float(keep.sum() / sm.sum())})
        row[name] = float(np.mean(means)) if all(np.isfinite(means)) else np.nan
        row[name + "_min_coverage"] = min(covs)
    rows.append(row)
pd.DataFrame(rows).to_csv(out, index=False)
pd.DataFrame(cov_rows).to_csv(out.replace(".csv", "_coverage.csv"), index=False)
print("wrote", out, len(rows))
