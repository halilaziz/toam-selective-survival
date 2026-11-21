"""RQ3 robustness (preregistration, Reliability and robustness testing): the SPM12 and fMRIPrep routes agree if both
give the same sign and each d_z lies inside the other's 95% CI (toam_analysis.h2h3.pipelines_agree, decision D6).
usage: python agree.py <group json, SPM route> <group json, fMRIPrep route> <out json>"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from toam_analysis import h2h3  # noqa: E402

spm, fpr = (json.load(open(p))["RQ3"] for p in sys.argv[1:3])
out = {"spm": {h: spm[h] for h in ("H3r", "H3a")}, "fmriprep": {h: fpr[h] for h in ("H3r", "H3a")},
       "agreement": h2h3.pipelines_agree(spm, fpr)}
json.dump(out, open(sys.argv[3], "w"), indent=1, default=float)
print(json.dumps(out["agreement"], indent=1))
