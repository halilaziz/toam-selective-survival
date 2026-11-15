"""RQ1 / H1 (preregistration Part 5): per-participant differences in mean m between item sets, one-sided one-sample
t tests across participants, Holm across H1a-H1c, d_z with 95% CI, JZS Bayes factors, robustness checks."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import stats
from .classes import assign_classes, memorability

HYPOTHESES = {
    "H1a": "guessed at 24 h minus guessed at 30 min",
    "H1b": "sure at 24 h minus sure at 30 min",
    "H1c": "FO minus SG",
}


def prepare(w: pd.DataFrame) -> pd.DataFrame:
    """Add class and every version of m to the wide table (after exclusions)."""
    w = w.copy()
    w["cls"] = assign_classes(w)
    for v in ("30min", "24h", "mean"):
        w[f"m_{v}"] = memorability(w, v)
    return w


def _sets(g: pd.DataFrame, correct_only: bool):
    inc = ~g["excluded"].astype(bool)
    c30, c24, a30, a24 = g["conf30"], g["conf24"], g["acc30"], g["acc24"]
    ok30 = (a30 == "correct") if correct_only else True
    ok24 = (a24 == "correct") if correct_only else True
    return {
        "G24": inc & (c24 == "guess") & ok24,
        "G30": inc & (c30 == "guess") & ok30,
        "S24": inc & (c24 == "sure") & ok24,
        "S30": inc & (c30 == "sure") & ok30,
        "FO": inc & (g["cls"] == "FO") & ok30 & ok24,
        "SG": inc & (g["cls"] == "SG") & ok30 & ok24,
    }


def participant_differences(w: pd.DataFrame, m_col: str = "m_30min", correct_only: bool = False) -> pd.DataFrame:
    """One row per participant: dA, dB, dC (NaN when either item set is empty) and the set sizes."""
    rows = []
    for sub, g in w.groupby("sub", sort=True):
        s = _sets(g, correct_only)
        mean = lambda k: g.loc[s[k], m_col].mean() if s[k].any() else np.nan
        row = {"sub": sub, "arm": g["arm"].iloc[0],
               "H1a": mean("G24") - mean("G30"), "H1b": mean("S24") - mean("S30"), "H1c": mean("FO") - mean("SG")}
        row.update({f"n_{k}": int(v.sum()) for k, v in s.items()})
        rows.append(row)
    return pd.DataFrame(rows)


def group_tests(d: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    for h in HYPOTHESES:
        r = stats.one_sample_greater(d[h]).as_dict()
        tm = stats.trimmed_mean_greater(d[h])
        r.update({"hypothesis": h, "analysis": label, "tm": tm.trimmed_mean, "tm_t": tm.t, "tm_df": tm.df,
                  "tm_p_one_sided": tm.p_one_sided})
        rows.append(r)
    out = pd.DataFrame(rows)
    out["p_holm"] = stats.holm(out["p_one_sided"])
    out["tm_p_holm"] = stats.holm(out["tm_p_one_sided"])
    cols = ["analysis", "hypothesis", "n", "mean", "sd", "t", "df", "p_one_sided", "p_holm", "dz", "dz_ci_low",
            "dz_ci_high", "bf10", "bf_plus0", "tm", "tm_t", "tm_df", "tm_p_one_sided", "tm_p_holm"]
    return out[cols]


def run_h1(w_excl: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Primary analysis plus the preregistered robustness checks (correct trials only; m from the 24-h test; m as the
    mean of the two tests). 20% trimmed means are reported for every analysis. Returns (results, primary
    per-participant differences, prepared item table)."""
    w = prepare(w_excl)
    primary = participant_differences(w, "m_30min")
    res = [group_tests(primary, "primary"),
           group_tests(participant_differences(w, "m_30min", correct_only=True), "robust: correct trials only"),
           group_tests(participant_differences(w, "m_24h"), "robust: m from the 24-h test"),
           group_tests(participant_differences(w, "m_mean"), "robust: m from the mean of both tests")]
    return pd.concat(res, ignore_index=True), primary, w
