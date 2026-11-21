"""Sensitivity analysis: first-level specs for the repaired participants. Each spec is the primary spec with the
derivative paths moved from derivatives/spmMB to derivatives/spmMB_coregfix; conditions, onsets, contrasts and
eligibility are untouched (they come from the events, not from preprocessing). usage:
python make_sens_specs.py <primary glm_specs dir> <out dir> sub-60601 sub-62162 ..."""
import json
import os
import sys

src, out, subs = sys.argv[1], sys.argv[2], sys.argv[3:]
os.makedirs(out, exist_ok=True)
OLD, NEW = "/derivatives/spmMB/", "/derivatives/spmMB_coregfix/"
for s in subs:
    spec = json.load(open(os.path.join(src, f"spec_{s}.json")))
    before = json.dumps(spec, sort_keys=True)
    spec["preproc_dir"] = spec["preproc_dir"].replace(OLD, NEW)
    spec["outdir"] = spec["outdir"].replace(OLD, NEW)
    for ses in spec["sessions"]:
        ses["func_dir"] = ses["func_dir"].replace(OLD, NEW)
    after = json.dumps(spec, sort_keys=True)
    assert NEW in spec["preproc_dir"] and NEW in spec["outdir"] and all(NEW in x["func_dir"] for x in spec["sessions"])
    assert before.replace(OLD, NEW) == after, "only the derivative paths may change"
    json.dump(spec, open(os.path.join(out, f"spec_{s}.json"), "w"), indent=1)
    print("wrote", s, spec["outdir"])
