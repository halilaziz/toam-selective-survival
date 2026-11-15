#!/usr/bin/env python3
"""Runner for the preregistered TOAM analyses. Steps (README.md):

  h1        exclusions, classes, m, H1 tests and robustness checks
  glm-spec  first-level specification (JSON) per participant, for matlab/first_level.sh
  roi       ROI values from the first-level contrast images
  group     H2 (decision rules, composition share) and H3 (estimation) group results
  synthetic write a synthetic dataset in the released format (for trying the steps)

Real TOAM data are refused unless --registered gives the OSF registration (the preregistration must be public or
time-stamped before any outcome is computed). Synthetic roots carry SYNTHETIC_DATA.txt and need no flag.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import platform
import re
import subprocess
import sys

import nibabel as nib
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from toam_analysis import events, exclusions, glm_spec, h1, h2h3, roi, synthetic  # noqa: E402

OSF_RE = re.compile(r"(osf\.io/[a-z0-9]{5}|10\.17605/OSF\.IO/[A-Z0-9]{5})", re.I)


def guard(roots: list[str], registered: str | None) -> str:
    synth = [os.path.exists(os.path.join(r, "SYNTHETIC_DATA.txt")) for r in roots]
    if all(synth):
        return "synthetic"
    if any(synth):
        sys.exit("refusing to mix synthetic and real inputs")
    if not registered or not OSF_RE.search(registered):
        sys.exit("real TOAM data: give --registered with the OSF registration (URL or DOI) first")
    return f"real (registered: {registered})"


def provenance(args, mode: str) -> dict:
    import scipy
    try:
        commit = subprocess.run(["git", "-C", HERE, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", HERE, "status", "--porcelain", "."], capture_output=True,
                                    text=True).stdout.strip())
    except OSError:
        commit, dirty = "", None
    return {"time": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "mode": mode,
            "argv": sys.argv, "git_commit": commit, "git_dirty": dirty, "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__,
            "nibabel": nib.__version__}


def load_items(a, recog_rt_rule=False):
    roots = {"ds006265": a.bids_hipp, "ds006266": a.bids_wb}
    wide = events.to_wide(events.load_long(roots))
    logs = pd.concat([exclusions.read_logs(a.logs, s) for s in wide["sub"].unique()], ignore_index=True)
    return roots, exclusions.item_exclusions(wide, logs, recog_rt_rule=recog_rt_rule)


def cmd_h1(a):
    mode = guard([a.bids_hipp, a.bids_wb], a.registered)
    os.makedirs(a.out, exist_ok=True)
    _, w = load_items(a, a.recog_rt_rule)
    res, d, prep = h1.run_h1(w)
    res.to_csv(os.path.join(a.out, "h1_results.csv"), index=False)
    d.to_csv(os.path.join(a.out, "h1_participants.csv"), index=False)
    prep.to_csv(os.path.join(a.out, "items.csv"), index=False)
    rules = [c for c in ("immediate_recall", "false_memory", "invalid_answer", "recog_rt") if c in prep]
    prep.groupby(["sub", "arm"])[rules + ["excluded"]].sum().to_csv(os.path.join(a.out, "exclusions_by_participant.csv"))
    json.dump(provenance(a, mode), open(os.path.join(a.out, "provenance_h1.json"), "w"), indent=1)
    print(res.to_string())


def cmd_glm_spec(a):
    mode = guard([a.bids_hipp, a.bids_wb], a.registered)
    os.makedirs(a.out, exist_ok=True)
    roots, w = load_items(a, a.recog_rt_rule)
    prep = h1.prepare(w)
    summary = []
    for sub, g in prep.groupby("sub"):
        ds, arm = g["ds"].iloc[0], g["arm"].iloc[0]
        spec = glm_spec.build_spec(sub, arm, roots[ds], dict(zip(g["item"], g["cls"])), a.deriv,
                                   glm_spec.first_bold_json(roots[ds], sub))
        glm_spec.write_spec(spec, os.path.join(a.out, f"spec_{sub}.json"))
        summary += [{"sub": sub, "arm": arm, "contrast": c["name"], "eligible": c["eligible"], "reason": c["reason"]}
                    for c in spec["contrasts"]]
    pd.DataFrame(summary).to_csv(os.path.join(a.out, "contrast_eligibility.csv"), index=False)
    json.dump(provenance(a, mode), open(os.path.join(a.out, "provenance_glm_spec.json"), "w"), indent=1)


def cmd_roi(a):
    rows = []
    for f in sorted(glob.glob(os.path.join(a.specs, "spec_sub-*.json"))):
        spec = json.load(open(f))
        tsv = os.path.join(spec["outdir"], "contrasts.tsv")
        peaks = roi.RQ2_PEAKS if spec["arm"] == "hipp" else roi.RQ3_PEAKS
        row = {"sub": spec["sub"], "arm": spec["arm"]}
        cons = dict(pd.read_csv(tsv, sep="\t").itertuples(index=False)) if os.path.exists(tsv) else {}
        for c in spec["contrasts"]:
            if c["name"] in cons:
                val, sv = roi.roi_mean(nib.load(os.path.join(spec["outdir"], cons[c["name"]])), peaks)
                row[c["name"]] = val
                row[c["name"] + "_min_coverage"] = min(s["coverage"] for s in sv)
            else:
                row[c["name"]] = np.nan
        rows.append(row)
    pd.DataFrame(rows).to_csv(a.out, index=False)


def cmd_group(a):
    t = pd.read_csv(a.roi_table)
    out = {}
    hipp, wb = t[t["arm"] == "hipp"], t[t["arm"] == "wb"]
    if len(hipp):
        out["RQ2"] = h2h3.group_h2(hipp)
    if len(wb):
        out["RQ3"] = h2h3.group_h3(wb)
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


def cmd_synthetic(a):
    gt = synthetic.simulate_behaviour(seed=a.seed)
    roots = synthetic.write_dataset(gt, a.out)
    gt.to_csv(os.path.join(a.out, "ground_truth.csv"), index=False)
    print(json.dumps({k: v for k, v in roots.items() if k != "crashed"}, indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name in ("h1", "glm-spec"):
        p = sp.add_parser(name)
        p.add_argument("--bids-hipp", required=True, help="BIDS root of ds006265")
        p.add_argument("--bids-wb", required=True, help="BIDS root of ds006266")
        p.add_argument("--logs", required=True, help="authors' data/behavioral_data folder")
        p.add_argument("--out", required=True)
        p.add_argument("--registered", help="OSF registration URL or DOI (required for real data)")
        p.add_argument("--recog-rt-rule", action="store_true", help="also apply r_utils.R:185 (README Q1)")
        if name == "glm-spec":
            p.add_argument("--deriv", required=True, help="derivatives/spmMB as MATLAB will see it")
    p = sp.add_parser("roi")
    p.add_argument("--specs", required=True)
    p.add_argument("--out", required=True)
    p = sp.add_parser("group")
    p.add_argument("--roi-table", required=True)
    p.add_argument("--out", required=True)
    p = sp.add_parser("synthetic")
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=3)
    a = ap.parse_args(argv)
    {"h1": cmd_h1, "glm-spec": cmd_glm_spec, "roi": cmd_roi, "group": cmd_group, "synthetic": cmd_synthetic}[a.cmd](a)


if __name__ == "__main__":
    main()
