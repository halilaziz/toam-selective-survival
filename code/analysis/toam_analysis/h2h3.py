"""RQ2 (H2r, H2a, H2b) and RQ3 (H3r, H3a) group analyses (preregistration Part 5, Table 3)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import stats

ALPHA = 0.05


def group_h2(table: pd.DataFrame, n_boot: int = 10_000, seed: int = 20261112) -> dict:
    """table: one row per small-FOV participant with columns H2r, H2a, H2b (ROI contrast estimates; NaN when the
    participant is not eligible for that contrast). One-sided tests; Holm across H2a and H2b only."""
    res = {h: stats.one_sample_greater(table[h]).as_dict() for h in ("H2r", "H2a", "H2b")}
    ph = stats.holm([res["H2a"]["p_one_sided"], res["H2b"]["p_one_sided"]])
    res["H2a"]["p_holm"], res["H2b"]["p_holm"] = float(ph[0]), float(ph[1])
    res["H2r"]["p_holm"] = res["H2r"]["p_one_sided"]  # not in the Holm family
    for h in ("H2r", "H2a", "H2b"):
        tm = stats.trimmed_mean_greater(table[h])
        res[h].update({"tm": tm.trimmed_mean, "tm_t": tm.t, "tm_df": tm.df, "tm_p_one_sided": tm.p_one_sided})
    share, lo, hi = composition_share(table["H2a"].to_numpy(float), table["H2r"].to_numpy(float), n_boot, seed)
    res["composition_share"] = {"estimate": share, "ci_low": lo, "ci_high": hi, "n_boot": n_boot}
    res["decision"] = decide_rq2(res)
    return res


def composition_share(a: np.ndarray, r: np.ndarray, n_boot: int = 10_000, seed: int = 20261112):
    """1 - (mean H2a / mean H2r) with a percentile bootstrap over participants (Part 5, RQ2). Each mean is taken
    over the participants eligible for that contrast, in the full sample and in every resample."""
    def share(rows):
        ma, mr = np.nanmean(rows[:, 0]), np.nanmean(rows[:, 1])
        return 1 - ma / mr if np.isfinite(ma) and np.isfinite(mr) and mr != 0 else np.nan

    data = np.column_stack([a, r])
    data = data[np.isfinite(data).any(axis=1)]
    est = share(data)
    lo, hi, _ = stats.percentile_bootstrap(share, data, n_boot, seed)
    return float(est), lo, hi


def decide_rq2(res: dict) -> str:
    """Table 3 decision rules for the primary ROI."""
    sig = lambda h: bool(np.isfinite(res[h]["p_holm"]) and res[h]["p_holm"] < ALPHA)
    r, a, b = sig("H2r"), sig("H2a"), sig("H2b")
    if not r:
        return "Reproduction failed"
    if a and not b:
        return "Trace change supported"
    if b and not a and res["H2a"]["mean"] < 0.5 * res["H2r"]["mean"]:
        return "Selective survival supported"
    if a and b:
        return "Mixed account"
    return "Inconclusive"


def group_h3(table: pd.DataFrame, n_boot: int = 10_000, seed: int = 20261112) -> dict:
    """RQ3: estimation only (d_z, 95% CIs, composition share), no decision rule."""
    res = {h: stats.one_sample_greater(table[h]).as_dict() for h in ("H3r", "H3a")}
    share, lo, hi = composition_share(table["H3a"].to_numpy(float), table["H3r"].to_numpy(float), n_boot, seed)
    res["composition_share"] = {"estimate": share, "ci_low": lo, "ci_high": hi, "n_boot": n_boot}
    return res


def pipelines_agree(spm: dict, fmriprep: dict) -> dict:
    """RQ3 robustness (Part 5): robust if both pipelines give the same sign and each estimate lies inside the other's
    95% CI. Applied to d_z and its CI, per hypothesis (README, question Q6)."""
    out = {}
    for h in ("H3r", "H3a"):
        a, b = spm[h], fmriprep[h]
        same = np.sign(a["dz"]) == np.sign(b["dz"])
        inside = (b["dz_ci_low"] <= a["dz"] <= b["dz_ci_high"]) and (a["dz_ci_low"] <= b["dz"] <= a["dz_ci_high"])
        out[h] = {"same_sign": bool(same), "each_inside_other_ci": bool(inside), "robust": bool(same and inside)}
    return out
