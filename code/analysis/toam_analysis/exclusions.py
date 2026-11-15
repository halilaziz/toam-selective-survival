"""Item exclusions as in the authors' code (TomW92/TOAM-fMRI e257c25, behavior/r_utils.R, cleanUpBehavData,
lines 182-214), applied per participant x item to both tests:

  R1  r_utils.R:186      immediate recall (during learning) must be correct      -> 'immediate_recall'
  R2  r_utils.R:192-195  no 'sure' + incorrect at the 30-min test, the 24-h test or the recognition test -> 'false_memory'
  R3  r_utils.R:201-209  valid answers only: every button in {2, 3} and every rating in {2, 3, 4}       -> 'invalid_answer'
  R4  r_utils.R:185      recognition RT > 100 ms                                  -> 'recog_rt' (OFF by default:
                         not in the preregistered list; see README, question Q1)

Sources. The 30-min, 24-h and recognition statuses come from the released events (the authors' 'maxTrials' files,
which already contain the late responses the authors recovered from raw logs, r_utils.R:5-180). A missing status
('NA' in the events, or no events for the item at a test) is an invalid answer (R3).
Immediate recall, and the button codes behind R3, are not in the events. They come from the authors' public logfiles
(data/behavioral_data/<id>-{encoding,retrieval,delayed_retrieval}_run1_logfile.txt; columns as read by
behavior/01_fmri_create_dfs.R:54-80). A button code of 0 there is a miss; for the 30-min, 24-h and recognition
responses the events show whether the authors recovered it, so 0 counts as invalid only when the events say NA.
For immediate recall the raw logs needed for that recovery are not public, so a 0 stays a miss (R1 and R3).
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

LOG_COLUMNS = {
    "encoding": {"Presented_Person": "item", "Immediate_Recall_Pressed_Button": "button1",
                 "Immediate_Recall_Accuracy": "acc1"},
    "retrieval": {"Presented_Person": "item", "Assoc_Retrieval_Pressed_Button": "button2",
                  "Retrieval_consc_Rating_Pressed_Button": "rating2"},
    "delayed_retrieval": {"Presented_Person": "item", "Assoc_Retrieval_Pressed_Button": "button3",
                          "Retrieval_consc_Rating_Pressed_Button": "rating3",
                          "ForcedChoice_Pressed_Button": "button4", "ForcedChoice_RT": "rt4",
                          "Recognition_consc_Rating_Pressed_Button": "rating4"},
}


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.strip().replace({"": np.nan, "NA": np.nan, "nan": np.nan}),
                         errors="coerce")


def read_logs(log_dir: str, sub: str) -> pd.DataFrame:
    """Per-item button codes and immediate-recall accuracy for one participant ('sub-60601' -> 60601-*.txt)."""
    pid = sub.replace("sub-", "")
    merged = None
    for kind, cols in LOG_COLUMNS.items():
        path = os.path.join(log_dir, f"{pid}-{kind}_run1_logfile.txt")
        df = pd.read_csv(path, sep="\t", dtype=str, encoding="latin-1", keep_default_na=False)
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(f"{path}: missing columns {missing}")
        df = df[list(cols)].rename(columns=cols)
        if df["item"].duplicated().any():
            raise ValueError(f"{path}: an item appears twice")
        merged = df if merged is None else merged.merge(df, on="item", how="outer")
    for c in merged.columns:
        if c not in ("item", "acc1"):
            merged[c] = _num(merged[c])
    merged["acc1"] = merged["acc1"].astype(str).str.strip().str.lower()
    merged.insert(0, "sub", sub)
    return merged


def item_exclusions(wide: pd.DataFrame, logs: pd.DataFrame | None, recog_rt_rule: bool = False) -> pd.DataFrame:
    """Add rule columns and 'excluded' to the wide item table (one row per participant x item).
    `logs` is the concatenation of read_logs() over participants, or None (then R1 and the button part of R3
    cannot be applied and 'logs_available' is False)."""
    w = wide.copy()
    status_ok = lambda c, a: w[c].notna() & w[a].notna()
    # R3 (events part): a valid status at every test, including recognition
    w["invalid_answer"] = ~(status_ok("conf30", "acc30") & status_ok("conf24", "acc24")
                            & status_ok("recog_conf", "recog_acc"))
    # R2
    fm = lambda c, a: (w[c] == "sure") & (w[a] == "incorrect")
    w["false_memory"] = fm("conf30", "acc30") | fm("conf24", "acc24") | fm("recog_conf", "recog_acc")
    w["logs_available"] = logs is not None
    if logs is not None:
        w = w.merge(logs, on=["sub", "item"], how="left", validate="one_to_one")
        # R1: first.retrieval == "correct" (r_utils.R:186); NA or anything else fails
        w["immediate_recall"] = w["acc1"].ne("correct")
        # R3 (logfile part). 0 = miss: invalid for immediate recall (cannot be recovered from public files);
        # for the other responses only if the events have no status, which is already covered above.
        bad_button = lambda c: w[c].notna() & ~w[c].isin([0, 2, 3])
        bad_rating = lambda c: w[c].notna() & ~w[c].isin([0, 2, 3, 4])
        w["invalid_answer"] = (w["invalid_answer"] | ~w["button1"].isin([2, 3])
                               | bad_button("button2") | bad_button("button3") | bad_button("button4")
                               | bad_rating("rating2") | bad_rating("rating3") | bad_rating("rating4"))
        # R4 (optional): fourth.RT > 100; R's filter() also drops a missing RT
        w["recog_rt"] = ~(w["rt4"] > 100)
    else:
        w["immediate_recall"] = False
        w["recog_rt"] = False
    rules = ["immediate_recall", "false_memory", "invalid_answer"] + (["recog_rt"] if recog_rt_rule else [])
    w["excluded"] = w[rules].any(axis=1)
    w["exclusion_rules_applied"] = ",".join(rules)
    return w
