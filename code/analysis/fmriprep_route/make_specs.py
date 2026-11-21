"""fMRIPrep route for RQ3: first-level specs for whole-brain participants. Each spec is the primary (SPM route) spec
with the inputs moved to $TOAM/derivatives/fmriprep_spm/<sub>: smoothed MNI152NLin2009cAsym BOLD (s6), fMRIPrep's six
motion parameters and the fMRIPrep-based mask; conditions, onsets, contrasts and eligibility are untouched.
usage: python make_specs.py <TOAM> <primary glm_specs dir> <out dir> sub-... sub-..."""
import json
import os
import sys

T, src, out, subs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
os.makedirs(out, exist_ok=True)
for s in subs:
    spec = json.load(open(os.path.join(src, f"spec_{s}.json")))
    assert spec["arm"] == "wb", f"{s}: the fMRIPrep route is for the whole-brain arm only"
    keep = {k: v for k, v in spec.items() if k not in ("preproc_dir", "outdir", "sessions")}
    root = f"{T}/derivatives/fmriprep_spm/{s}"
    spec["preproc_dir"] = root
    spec["outdir"] = f"{root}/l1_toam_prereg_fmriprep_s6"
    for ses in spec["sessions"]:
        task = ses["task"]
        ses["func_dir"] = f"{root}/{ses['ses']}/func"
        ses["scan_regex"] = f"^s6{s}_{ses['ses']}_task-{task}_.*space-MNI152NLin2009cAsym_desc-preproc_bold\\.nii$"
        ses["rp_regex"] = f"^rp_fmriprep_{s}_{ses['ses']}_task-{task}_.*\\.txt$"
    assert keep == {k: v for k, v in spec.items() if k not in ("preproc_dir", "outdir", "sessions")}
    json.dump(spec, open(os.path.join(out, f"spec_{s}.json"), "w"), indent=1)
    print("wrote", s)
