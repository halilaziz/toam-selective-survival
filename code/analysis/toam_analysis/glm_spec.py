"""First-level model specification for H2 and H3 (preregistration Part 3, "Preprocessing and first-level models").

The model is the authors' multi-session SPM12 model (TomW92/TOAM-fMRI e257c25):
  fmri/1st_level/multi_session_first_level.m      batch: duration 0 (l.61), motion regressors rp_* (l.68), HPF 128 s
                                                   (l.69), units secs, RT, microtime fmri_t = nslices and
                                                   fmri_t0 = nslices/2 (l.73-76), mthresh -Inf (l.77), no
                                                   derivatives (l.79), volt 1, global None, explicit mask (l.84),
                                                   AR(1) (l.85), classical estimation (l.92)
  fmri/1st_level/contrasts/contrast_multi_session.m session order {forgetexp, consolidation, retrieval, forgetexp}
                                                   (l.30-33), scans '^s6wra.*<task>.*\\.nii$' (l.39, 100), names
                                                   repeated from an earlier session get ' <session sign>' (l.67-77)
  conditions per session: contrasts/contrasts_enc_subsequent.m (learning run, labelled by the 30-min status),
  contrasts/contrasts_consolidation.m (odd-even run: one condition 'number'), contrasts/archive/
  contrasts_ret_twoEvents.m (30-min test, 5 event types) and contrasts/contrasts_delret.m (24-h test, 9 event types;
  every event of a trial, the recognition events included, takes the trial's RETRIEVAL status, l.121-122).
  In each: event x {correct, incorrect} x {consc (rating 4, sure), unconsc (2, guess), between (3, unsure)}, without
  the incorrect + consc cell; trials without a status have no regressor.

The only change (preregistered): at each test, the correct-guess faceRecog regressor ('faceRecog_correct_unconsc')
is split by trajectory class (SG, FO, other) and, for RQ3 (whole-brain arm), the correct-sure faceRecog regressor
('faceRecog_correct_consc') is split into SS and other. Excluded items (exclusions.py) get their own part, 'excl',
so that they enter no preregistered contrast (README, question Q2).
Conditions without trials are left out: an all-zero column changes no other estimate.
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np
import pandas as pd

from .events import LEARNING_EVENTS, RECOG_EVENTS, RETRIEVAL_EVENTS, load_participant

KIND_TASK = {"learning": ("ses-1", "forgetexp", 1), "consolidation": ("ses-1", "consolidation", 1),
             "30min": ("ses-1", "retrieval", 1), "24h": ("ses-2", "forgetexp", 2)}  # sign: setup_config.m:215-216
EVENTS = {"learning": LEARNING_EVENTS, "30min": RETRIEVAL_EVENTS, "24h": RETRIEVAL_EVENTS + RECOG_EVENTS}
CONSC = {"learning": {"sure": "subseqconsc", "guess": "subsequnconsc", "unsure": "subseqbetween"},
         "30min": {"sure": "consc", "guess": "unconsc", "unsure": "between"},
         "24h": {"sure": "consc", "guess": "unconsc", "unsure": "between"}}
CG, CS = "faceRecog_correct_unconsc", "faceRecog_correct_consc"
GUESS_PARTS = ("SG", "FO", "other", "excl")
SURE_PARTS = ("SS", "other", "excl")
INCLUDED = {"guess": ("SG", "FO", "other"), "sure": ("SS", "other")}
MIN_TRIALS = 4


def authors_names(kind: str) -> list[str]:
    """Condition names in the authors' order (levels loop, then the incorrect+consc cells removed)."""
    if kind == "consolidation":
        return ["number"]  # contrasts_consolidation.m:13
    order = ["subseqconsc", "subsequnconsc", "subseqbetween"] if kind == "learning" else ["consc", "unconsc", "between"]
    drop = "incorrect_subseqconsc" if kind == "learning" else "incorrect_consc"
    names = [f"{e}_{a}_{c}" for e in EVENTS[kind] for a in ("correct", "incorrect") for c in order]
    return [n for n in names if drop not in n]


def _split_names(names: list[str], split_sure: bool) -> list[str]:
    out = []
    for n in names:
        if n == CG:
            out += [f"{CG}_{p}" for p in GUESS_PARTS]
        elif n == CS and split_sure:
            out += [f"{CS}_{p}" for p in SURE_PARTS]
        else:
            out.append(n)
    return out


def _part(kind_base: str, cls: str) -> str:
    if kind_base == "guess":
        return cls if cls in ("SG", "FO", "excl") else "other"
    return cls if cls in ("SS", "excl") else "other"


def session_trials(kind: str, ev: pd.DataFrame, item_cls: dict, split_sure: bool) -> pd.DataFrame:
    """Each modelled event of one session with its condition name (before renaming)."""
    if kind == "learning":
        df = ev[ev["event"].isin(LEARNING_EVENTS) & ev["conf"].notna()].copy()
        df["base"] = [f"{e}_{a}_{CONSC[kind][c]}" for e, a, c in zip(df["event"], df["acc"], df["conf"])]
    else:
        status = ev[ev["event"] == "ret"].set_index("item")[["conf", "acc"]]  # contrasts_delret.m:121-122
        df = ev[ev["event"].isin(EVENTS[kind])].copy()
        df["conf"] = df["item"].map(status["conf"])
        df["acc"] = df["item"].map(status["acc"])
        df = df[df["conf"].notna() & df["acc"].notna()]
        df["base"] = [f"{e}_{a}_{CONSC[kind][c]}" for e, a, c in zip(df["event"], df["acc"], df["conf"])]
        df = df[df["base"].isin(authors_names(kind))]  # drops incorrect + consc
        cls = df["item"].map(item_cls).fillna("excl")
        name = df["base"].copy()
        g = df["base"] == CG
        name[g] = [f"{CG}_{_part('guess', c)}" for c in cls[g]]
        if split_sure:
            s = df["base"] == CS
            name[s] = [f"{CS}_{_part('sure', c)}" for c in cls[s]]
        df["base"] = name
    df = df[df["base"].isin(_split_names(authors_names(kind), split_sure))]
    return df[["onset", "item", "base"]]


def build_spec(sub: str, arm: str, events_root: str, item_cls: dict, deriv_root: str, bold_json: str,
               consolidation_onsets: list | None = None, fl_name: str = "toam_prereg") -> dict:
    """Everything the MATLAB step needs for one participant. item_cls: item -> class (classes.assign_classes).
    consolidation_onsets: the authors' odd-even onsets, which are not public. Without them the consolidation run is
    left out of the model (README, question Q3)."""
    split_sure = arm == "wb"
    ev = load_participant(events_root, sub)
    with open(bold_json) as f:
        js = json.load(f)
    kinds = ["learning"] + (["consolidation"] if consolidation_onsets is not None else []) + ["30min", "24h"]
    sessions, seen = [], set()
    for kind in kinds:
        ses, task, sign = KIND_TASK[kind]
        full = _split_names(authors_names(kind), split_sure)
        if kind == "consolidation":
            trials = pd.DataFrame({"onset": consolidation_onsets, "item": None, "base": "number"})
        else:
            trials = session_trials(kind, ev[kind], item_cls, split_sure)
        rename = {n: (f"{n} {sign}" if n in seen else n) for n in full}  # contrast_multi_session.m:67-77
        seen.update(rename.values())
        conds = []
        for n in full:
            sel = trials[trials["base"] == n].sort_values("onset", kind="stable")
            if len(sel):
                conds.append({"name": rename[n], "base": n,
                              "onsets": [round(float(x), 4) for x in sel["onset"]], "n": int(len(sel)),
                              "items": [str(x) for x in sel["item"]] if kind != "consolidation" else []})
        func_dir = os.path.join(deriv_root, sub, "preproc", ses, "func")
        sessions.append({"kind": kind, "ses": ses, "task": task, "func_dir": func_dir,
                         "scan_regex": f"^s6wra.*{task}.*\\.nii$", "rp_regex": f"rp_.*{task}.*\\.txt",
                         "conditions": conds,
                         "dropped_empty": [rename[n] for n in full if n not in {c['base'] for c in conds}]})
    spec = {"sub": sub, "arm": arm, "TR": float(js["RepetitionTime"]), "nslices": len(js["SliceTiming"]),
            "preproc_dir": os.path.join(deriv_root, sub, "preproc"),
            "outdir": os.path.join(deriv_root, sub, f"l1_{fl_name}_s6wr"), "sessions": sessions,
            "consolidation_modelled": consolidation_onsets is not None}
    spec["contrasts"] = contrasts(spec)
    return spec


def _counts(spec: dict, kind: str) -> dict:
    s = next(x for x in spec["sessions"] if x["kind"] == kind)
    return {c["base"]: c["n"] for c in s["conditions"]}


def _sess_index(spec: dict, kind: str) -> int:
    return 1 + [x["kind"] for x in spec["sessions"]].index(kind)


def _name(spec: dict, kind: str, base: str) -> str:
    s = next(x for x in spec["sessions"] if x["kind"] == kind)
    return next(c["name"] for c in s["conditions"] if c["base"] == base)


def _all_items(spec, kind, base, which):
    """Count-weighted combination of the split parts: estimates the response to all included items of the
    unsplit condition (README, question Q2). Returns ({(session, name): weight}, total trials)."""
    cnt = _counts(spec, kind)
    parts = [f"{base}_{p}" for p in INCLUDED[which] if cnt.get(f"{base}_{p}", 0) > 0]
    tot = sum(cnt[p] for p in parts)
    if tot == 0:
        return {}, 0
    s = _sess_index(spec, kind)
    return {(s, _name(spec, kind, p)): cnt[p] / tot for p in parts}, tot


def _single(spec, kind, name_base):
    cnt = _counts(spec, kind).get(name_base, 0)
    if cnt == 0:
        return {}, 0
    return {(_sess_index(spec, kind), _name(spec, kind, name_base)): 1.0}, cnt


def _combine(*terms):
    w = {}
    for sign, (d, _) in terms:
        for k, v in d.items():
            w[k] = w.get(k, 0.0) + sign * v
    return w


def contrasts(spec: dict) -> list[dict]:
    """H2r, H2a, H2b (small-FOV arm) and H3r, H3a (whole-brain arm), with the >= 4 trials rule (Part 5): every
    regressor in a contrast needs at least four trials. For the all-items terms of H2r and H3r the regressor is the
    unsplit condition (all included items of that test)."""
    out = []

    def add(name, terms, needed):
        counts = {k: n for k, (_, n) in needed.items()}
        ok = all(n >= MIN_TRIALS for n in counts.values())
        w = _combine(*terms) if ok else {}
        out.append({"name": name, "eligible": ok, "trial_counts": counts,
                    "reason": "" if ok else "fewer than 4 trials: " + ", ".join(k for k, n in counts.items()
                                                                                if n < MIN_TRIALS),
                    "weights": [{"session": s, "condition": c, "weight": round(v, 10)}
                                for (s, c), v in sorted(w.items()) if abs(v) > 0]})

    if spec["arm"] == "hipp":
        a24, a30 = _all_items(spec, "24h", CG, "guess"), _all_items(spec, "30min", CG, "guess")
        sg24, sg30 = _single(spec, "24h", f"{CG}_SG"), _single(spec, "30min", f"{CG}_SG")
        fo24 = _single(spec, "24h", f"{CG}_FO")
        add("H2r", [(+1, a24), (-1, a30)], {"cg24_all": a24, "cg30_all": a30})
        add("H2a", [(+1, sg24), (-1, sg30)], {"cg24_SG": sg24, "cg30_SG": sg30})
        add("H2b", [(+1, fo24), (-1, sg24)], {"cg24_FO": fo24, "cg24_SG": sg24})
    else:
        g24, g30 = _all_items(spec, "24h", CG, "guess"), _all_items(spec, "30min", CG, "guess")
        s24, s30 = _all_items(spec, "24h", CS, "sure"), _all_items(spec, "30min", CS, "sure")
        add("H3r", [(+1, s24), (-1, g24), (-1, s30), (+1, g30)],
            {"cs24_all": s24, "cg24_all": g24, "cs30_all": s30, "cg30_all": g30})
        ss24, ss30 = _single(spec, "24h", f"{CS}_SS"), _single(spec, "30min", f"{CS}_SS")
        sg24, sg30 = _single(spec, "24h", f"{CG}_SG"), _single(spec, "30min", f"{CG}_SG")
        add("H3a", [(+1, ss24), (-1, sg24), (-1, ss30), (+1, sg30)],
            {"cs24_SS": ss24, "cg24_SG": sg24, "cs30_SS": ss30, "cg30_SG": sg30})
    return out


def write_spec(spec: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(spec, f, indent=1, allow_nan=False)


def first_bold_json(bids_root: str, sub: str) -> str:
    """The JSON setup_config.m:141-142 reads: the first ses-1 functional file of the participant."""
    hits = sorted(glob.glob(os.path.join(bids_root, sub, "ses-1", "func", "s*_bold.json")))
    if not hits:
        raise FileNotFoundError(f"no ses-1 bold JSON for {sub}")
    return hits[0]
