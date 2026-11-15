"""Trajectory classes (preregistration Table 2) and the memorability index m (Part 3)."""
from __future__ import annotations

import numpy as np
import pandas as pd

CLASSES = ("SG", "FO", "SS", "other", "excl")


def assign_classes(w: pd.DataFrame) -> pd.Series:
    """SG: guess at both tests. FO: sure or unsure at 30 min, guess at 24 h. SS: sure at both tests.
    Excluded items (exclusions.item_exclusions) are 'excl'; every other included item is 'other'.
    Classes depend on the confidence ratings only, as in Table 2."""
    c30, c24 = w["conf30"], w["conf24"]
    cls = np.select(
        [w["excluded"].astype(bool),
         (c30 == "guess") & (c24 == "guess"),
         c30.isin(["sure", "unsure"]) & (c24 == "guess"),
         (c30 == "sure") & (c24 == "sure")],
        ["excl", "SG", "FO", "SS"], default="other")
    return pd.Series(cls, index=w.index, name="cls")


def _loso_proportion(w: pd.DataFrame, test: str) -> pd.Series:
    """For each row (participant p, item i): share of the OTHER participants with a valid trial for i at `test`
    who gave a correct 'sure' response. Valid = item not excluded for that participant and a status at that test.
    The target participant's own trial is removed from numerator and denominator (leave-one-subject-out)."""
    s = "30" if test == "30min" else "24"
    valid = (~w["excluded"].astype(bool)) & w[f"conf{s}"].notna() & w[f"acc{s}"].notna()
    hit = valid & (w[f"conf{s}"] == "sure") & (w[f"acc{s}"] == "correct")
    tot = pd.DataFrame({"item": w["item"], "v": valid.astype(int), "h": hit.astype(int)}).groupby("item").sum()
    num = w["item"].map(tot["h"]) - hit.astype(int)
    den = w["item"].map(tot["v"]) - valid.astype(int)
    return (num / den.where(den > 0)).astype(float)


def memorability(w: pd.DataFrame, version: str = "30min") -> pd.Series:
    """m: leave-one-subject-out proportion of correct-sure responses (both arms, up to 39 other participants),
    z-scored across the target participant's included items (population SD, ddof = 0).
    version: '30min' (primary), '24h' or 'mean' (mean of the two proportions) as the secondary versions."""
    if version == "mean":
        raw = (_loso_proportion(w, "30min") + _loso_proportion(w, "24h")) / 2
    else:
        raw = _loso_proportion(w, version)
    raw = raw.where(~w["excluded"].astype(bool))
    g = raw.groupby(w["sub"])
    z = (raw - g.transform("mean")) / g.transform(lambda x: x.std(ddof=0))
    return z.rename(f"m_{version}")
