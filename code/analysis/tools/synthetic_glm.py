#!/usr/bin/env python3
"""End-to-end check of the MATLAB first level on synthetic NIfTI (no TOAM data).

make:  writes, for one synthetic small-FOV participant, 4-D images named like the authors' s6wra* files, rp_* motion
       files and the cross-session mask, with a known signal: every faceRecog correct-guess regressor has amplitude 1
       except the 24-h FO part (amplitude 3); everything else has amplitude 1. Writes the JSON spec with paths rooted
       at --deriv-root (the folder as the MATLAB step will see it).
check: reads the contrast images SPM wrote and checks, up to SPM's unknown common scale k:
       H2a ~ 0, H2b = 2k > 0, H2r / H2b = n_FO / N_24 (the count weights), and the regressor names.

  python tools/synthetic_glm.py make  --out DIR --deriv-root /analysis/.../tmp/synthetic_glm/derivatives/spmMB
  python tools/synthetic_glm.py check --glm DIR/derivatives/spmMB/<sub>/l1_toam_prereg_s6wr --spec DIR/spec.json
"""
import argparse
import json
import os
import sys

import numpy as np
import nibabel as nib
from scipy import stats

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from toam_analysis import events, exclusions, glm_spec, h1, roi, synthetic  # noqa: E402


def hrf(dt):
    t = np.arange(0, 32, dt)
    h = stats.gamma.pdf(t, 6) - stats.gamma.pdf(t, 16) / 6
    return h / h.sum()


def amplitude(cond_base, kind):
    return 3.0 if (kind == "24h" and cond_base == f"{glm_spec.CG}_FO") else 1.0


def make(out, deriv_root):
    gt = synthetic.simulate_behaviour(seed=21, forget=0.9)
    roots = synthetic.write_dataset(gt, os.path.join(out, "bids"))
    long = events.load_long({k: v for k, v in roots.items() if k.startswith("ds")})
    wide = events.to_wide(long)
    import pandas as pd
    logs = pd.concat([exclusions.read_logs(roots["logs"], s) for s in wide["sub"].unique()], ignore_index=True)
    prep = h1.prepare(exclusions.item_exclusions(wide, logs))
    # a small-FOV participant with enough FO trials
    for sub in sorted(prep.loc[prep["ds"] == "ds006265", "sub"].unique()):
        g = prep[prep["sub"] == sub]
        spec = glm_spec.build_spec(sub, "hipp", roots["ds006265"], dict(zip(g["item"], g["cls"])), deriv_root,
                                   glm_spec.first_bold_json(roots["ds006265"], sub))
        if all(c["eligible"] for c in spec["contrasts"]):
            break
    rng = np.random.default_rng(0)
    tr, nsl = spec["TR"], spec["nslices"]
    dt = tr / nsl
    h = hrf(dt)
    # 8 x 8 x 8 grid, 4 mm, voxel (4, 4, 4) at the left hippocampal peak
    aff = np.diag([4.0, 4.0, 4.0, 1.0])
    aff[:3, 3] = np.array(roi.RQ2_PEAKS[0]) - 4 * 4.0
    local = os.path.join(out, "derivatives", "spmMB", sub, "preproc")
    for s in spec["sessions"]:
        last = max(max(c["onsets"]) for c in s["conditions"])
        nvol = int(np.ceil((last + 40) / tr))
        micro = np.zeros(nvol * nsl)
        for c in s["conditions"]:
            idx = np.round(np.asarray(c["onsets"]) / dt).astype(int)
            np.add.at(micro, idx, amplitude(c["base"], s["kind"]))
        sig = np.convolve(micro, h)[: nvol * nsl][nsl // 2::nsl] * 200  # sampled at fmri_t0 = nslices/2
        y = 100 + sig[None, None, None, :] + rng.normal(0, 0.2, (8, 8, 8, nvol))
        fdir = os.path.join(local, s["ses"], "func")
        os.makedirs(fdir, exist_ok=True)
        stem = f"{sub}_{s['ses']}_task-{s['task']}_bold"
        nib.save(nib.Nifti1Image(y.astype(np.float32), aff), os.path.join(fdir, f"s6wra{stem}.nii"))
        np.savetxt(os.path.join(fdir, f"rp_a{stem}.txt"), rng.normal(0, 0.01, (nvol, 6)), fmt="%.6f")
    nib.save(nib.Nifti1Image(np.ones((8, 8, 8), np.uint8), aff),
             os.path.join(local, "crossSessionWhiteandGreyMatterMaskMNI.nii"))
    glm_spec.write_spec(spec, os.path.join(out, "spec.json"))
    print("made", sub, "->", os.path.join(out, "spec.json"))


def check(glm, spec_path):
    spec = json.load(open(spec_path))
    rows = [l.rstrip("\n").split("\t") for l in open(os.path.join(glm, "contrasts.tsv"))][1:]
    files = {name: os.path.join(glm, f) for name, f in rows}
    assert set(files) == {"H2r", "H2a", "H2b"}, files
    val = {k: roi.roi_mean(nib.load(f), roi.RQ2_PEAKS[:1], radius_mm=6)[0] for k, f in files.items()}
    con = {c["name"]: c for c in spec["contrasts"]}
    n = con["H2r"]["trial_counts"]
    s24 = next(s for s in spec["sessions"] if s["kind"] == "24h")
    cnt = {c["base"]: c["n"] for c in s24["conditions"]}
    share_fo = cnt[f"{glm_spec.CG}_FO"] / n["cg24_all"]
    print("ROI values:", {k: round(v, 4) for k, v in val.items()}, "| expected H2r/H2b =", round(share_fo, 4))
    assert val["H2b"] > 0
    assert abs(val["H2a"]) < 0.1 * val["H2b"], val
    assert abs(val["H2r"] / val["H2b"] - share_fo) < 0.1 * share_fo + 0.02, (val, share_fo)
    print("synthetic first level OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    m = sp.add_parser("make")
    m.add_argument("--out", required=True)
    m.add_argument("--deriv-root", required=True)
    c = sp.add_parser("check")
    c.add_argument("--glm", required=True)
    c.add_argument("--spec", required=True)
    a = ap.parse_args()
    make(a.out, a.deriv_root) if a.cmd == "make" else check(a.glm, a.spec)
