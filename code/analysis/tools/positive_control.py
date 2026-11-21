#!/usr/bin/env python3
"""Positive control for the events reader and the exclusions on the real TOAM data, run after the OSF registration
(https://osf.io/58q3c/) and BEFORE any H1 statistic is read. It compares descriptive behaviour with values that are
already known, so a parsing error shows up before the preregistered tests:
  - Willems et al. (2025, preprint v3, N = 40): sure 27.1% -> 21.6%, unsure 33.1% -> 27.6%, guess 39.8% -> 50.8%
    of category-retrieval responses at 30 min -> 24 h, and immediate category accuracy of about 98%;
  - our Stage A (ds006265): accuracy .623 (30 min) and .603 (24 h) over the 1,847 item-participant pairs with a
    status at both tests.
It computes no memorability index, no trajectory class and no H1 difference.

usage: python tools/positive_control.py --bids-hipp <ds006265> --bids-wb <ds006266> --logs <behavioral_data> --out <json>
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from toam_analysis import events, exclusions  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--bids-hipp", required=True)
ap.add_argument("--bids-wb", required=True)
ap.add_argument("--logs", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()

long = events.load_long({"ds006265": a.bids_hipp, "ds006266": a.bids_wb})
wide = events.to_wide(long)
subs = sorted(wide["sub"].unique())
logs = pd.concat([exclusions.read_logs(a.logs, s) for s in subs], ignore_index=True)
w = exclusions.item_exclusions(wide, logs)
n_logfiles = {s: len(glob.glob(os.path.join(a.logs, s.replace("sub-", "") + "-*_logfile.txt"))) for s in subs}


def conf_shares(df, test, mask=None):
    c = df[f"conf{test}"]
    if mask is not None:
        c = c[mask]
    d = df.loc[c.index].assign(c=c).dropna(subset=["c"])
    per = d.groupby("sub")["c"].value_counts(normalize=True).unstack(fill_value=0.0)
    return {k: [round(float(per[k].mean()) * 100, 1), round(float(per[k].std(ddof=1)) * 100, 1)]
            for k in ("sure", "unsure", "guess") if k in per}


res = {
    "n_participants": len(subs),
    "n_participants_by_arm": wide.groupby("ds")["sub"].nunique().to_dict(),
    "logfiles_per_participant": sorted(set(n_logfiles.values())),
    "items_per_participant_present30": [int(x) for x in wide.groupby("sub")["present30"].sum().agg(["min", "max"])],
    "items_per_participant_present24": [int(x) for x in wide.groupby("sub")["present24"].sum().agg(["min", "max"])],
    "confidence_shares_all_items_mean_sd_pct": {"30min": conf_shares(w, "30"), "24h": conf_shares(w, "24")},
    "confidence_shares_after_exclusions_mean_sd_pct": {"30min": conf_shares(w, "30", ~w["excluded"]),
                                                       "24h": conf_shares(w, "24", ~w["excluded"])},
    "immediate_recall_accuracy_mean_pct": round(float(w.groupby("sub")["acc1"].apply(
        lambda s: (s == "correct").mean()).mean()) * 100, 1),
    "exclusions": {r: int(w[r].sum()) for r in ("immediate_recall", "false_memory", "invalid_answer", "excluded")},
    "n_items_total": int(len(w)),
}
h = w[(w["ds"] == "ds006265") & w["acc30"].notna() & w["acc24"].notna()]
res["stageA_check_ds006265"] = {"pairs_with_status_at_both_tests": int(len(h)),
                                "accuracy30": round(float((h["acc30"] == "correct").mean()), 3),
                                "accuracy24": round(float((h["acc24"] == "correct").mean()), 3)}
res["published_reference"] = {"sure_pct": [27.1, 21.6], "unsure_pct": [33.1, 27.6], "guess_pct": [39.8, 50.8],
                              "immediate_accuracy_pct": 98, "stageA": {"pairs": 1847, "acc30": 0.623, "acc24": 0.603}}
os.makedirs(os.path.dirname(a.out), exist_ok=True)
json.dump(res, open(a.out, "w"), indent=1)
print(json.dumps(res, indent=1))
