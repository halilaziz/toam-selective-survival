"""Read the released BIDS events of TOAM (OpenNeuro ds006265 and ds006266, snapshot 1.0.2).

Layout, checked on the real files with every status token masked (2026-11-15; structure only):
  ses-1 task-forgetexp  learning run. Four events per item (Face, Enc, Recall, Feedback), each with the suffix
                        '_<conf>_<acc>' of the item's 30-minute test, or the whole trial_type 'NA' when the 30-minute
                        response is missing (authors' behavior/04_fmri_onsets.R:782-799).
  ses-1 task-retrieval  30-minute test. Five events per item (faceRecog, ret, retFeedback, retRating,
                        retRatingFeedback), suffix '_<conf>_<acc>', or 'NA' appended (04_fmri_onsets.R:352-381).
  ses-2 task-forgetexp  24-hour test. Nine events per item. The five retrieval events carry the 24-hour retrieval
                        status and the four recog* events the recognition status (04_fmri_onsets.R:639-690).
Columns are onset, duration (always 0), trial_type, item. <conf> is sure, unsure or guess (rating 4, 3, 2);
<acc> is correct or incorrect. The files are the authors' 'maxTrials' version: late responses recovered, no item
cleaning, trials of aborted acquisitions already removed (04_fmri_onsets.R:45-54, 379-381, 688-690).
"""
from __future__ import annotations

import glob
import os
import re

import numpy as np
import pandas as pd

from . import ARMS

_PAT = re.compile(r"^(?P<event>[A-Za-z]+?)(?:_(?P<conf>sure|unsure|guess)_(?P<acc>correct|incorrect)|(?P<na>NA))$")

RETRIEVAL_EVENTS = ("faceRecog", "ret", "retFeedback", "retRating", "retRatingFeedback")
RECOG_EVENTS = ("recog", "recogFeedback", "recogRating", "recogRatingFeedback")
LEARNING_EVENTS = ("Face", "Enc", "Recall", "Feedback")

FILES = {  # key: (session, task)
    "learning": ("ses-1", "forgetexp"),
    "30min": ("ses-1", "retrieval"),
    "24h": ("ses-2", "forgetexp"),
}


def parse_trial_type(tt: str):
    """'faceRecog_guess_correct' -> ('faceRecog', 'guess', 'correct'); 'retNA' -> ('ret', None, None);
    'NA' (learning event without a 30-minute status) -> (None, None, None)."""
    if tt == "NA":
        return None, None, None
    m = _PAT.match(tt)
    if not m:
        raise ValueError(f"unexpected trial_type {tt!r}")
    if m.group("na"):
        return m.group("event"), None, None
    return m.group("event"), m.group("conf"), m.group("acc")


def read_events(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, na_values=[])
    expected = ["onset", "duration", "trial_type", "item"]
    if list(df.columns) != expected:
        raise ValueError(f"{path}: columns {list(df.columns)} != {expected}")
    parsed = [parse_trial_type(t) for t in df["trial_type"]]
    df["event"] = [p[0] for p in parsed]
    df["conf"] = [p[1] for p in parsed]
    df["acc"] = [p[2] for p in parsed]
    df["onset"] = pd.to_numeric(df["onset"].replace({"NA": np.nan, "n/a": np.nan}), errors="raise")
    df["duration"] = pd.to_numeric(df["duration"].replace({"NA": np.nan, "n/a": np.nan}), errors="raise")
    return df


def find_events(root: str, sub: str, key: str) -> str | None:
    ses, task = FILES[key]
    hits = sorted(glob.glob(os.path.join(root, sub, ses, "func", f"{sub}_{ses}_task-{task}*_events.tsv")))
    if len(hits) > 1:
        raise ValueError(f"several event files for {sub} {key}: {hits}")
    return hits[0] if hits else None


def participants(root: str) -> list[str]:
    tsv = os.path.join(root, "participants.tsv")
    return pd.read_csv(tsv, sep="\t", dtype=str)["participant_id"].tolist()


def load_participant(root: str, sub: str) -> dict[str, pd.DataFrame]:
    out = {}
    for key in FILES:
        f = find_events(root, sub, key)
        if f is None:
            raise FileNotFoundError(f"{sub}: no {key} events in {root}")
        out[key] = read_events(f)
    return out


def _item_status(df: pd.DataFrame, events: tuple, label: str, sub: str) -> pd.DataFrame:
    """One row per item: status of the 'ret' (or 'recog') event and the faceRecog onset. Checks that every event of
    an item carries the same status, as the authors' files do (one suffix repeated over the trial's events)."""
    rows = []
    sel = df[df["event"].isin(events)]
    for item, g in sel.groupby("item", sort=False):
        st = {(c, a) for c, a in zip(g["conf"], g["acc"])}
        if len(st) != 1:
            raise ValueError(f"{sub} {label} item {item}: events disagree on status")
        conf, acc = st.pop()
        face = g.loc[g["event"] == "faceRecog", "onset"] if "faceRecog" in events else pd.Series(dtype=float)
        rows.append({"item": item, "conf": conf, "acc": acc,
                     "onset_faceRecog": float(face.iloc[0]) if len(face) == 1 else np.nan,
                     "n_events": len(g)})
    return pd.DataFrame(rows, columns=["item", "conf", "acc", "onset_faceRecog", "n_events"])


def participant_long(root: str, sub: str, ds: str) -> pd.DataFrame:
    """One row per participant x item x test (30min, 24h), with confidence, correctness, faceRecog onset, session
    and task; the 24-hour rows also carry the recognition status."""
    ev = load_participant(root, sub)
    out = []
    for test in ("30min", "24h"):
        ses, task = FILES[test]
        st = _item_status(ev[test], RETRIEVAL_EVENTS, test, sub)
        st.insert(0, "test", test)
        st["session"], st["task"] = ses, task
        if test == "24h":
            rec = _item_status(ev[test], RECOG_EVENTS, "recognition", sub)[["item", "conf", "acc"]]
            rec = rec.rename(columns={"conf": "recog_conf", "acc": "recog_acc"})
            st = st.merge(rec, on="item", how="left")
        else:
            st["recog_conf"], st["recog_acc"] = None, None
        out.append(st)
    long = pd.concat(out, ignore_index=True)
    long.insert(0, "sub", sub)
    long.insert(1, "ds", ds)
    long.insert(2, "arm", ARMS[ds])
    return long


def load_long(roots: dict[str, str]) -> pd.DataFrame:
    """roots: {'ds006265': path, 'ds006266': path}. Returns the long item table for every participant."""
    parts = []
    for ds, root in roots.items():
        for sub in participants(root):
            parts.append(participant_long(root, sub, ds))
    return pd.concat(parts, ignore_index=True)


def to_wide(long: pd.DataFrame) -> pd.DataFrame:
    """One row per participant x item with *_30 and *_24 columns (an item missing at a test has NaN there)."""
    keys = ["sub", "ds", "arm", "item"]
    a = long[long["test"] == "30min"].set_index(keys)[["conf", "acc", "onset_faceRecog"]]
    b = long[long["test"] == "24h"].set_index(keys)[["conf", "acc", "onset_faceRecog", "recog_conf", "recog_acc"]]
    w = a.add_suffix("30").join(b.add_suffix("24").rename(columns={"recog_conf24": "recog_conf",
                                                                    "recog_acc24": "recog_acc"}), how="outer")
    w["present30"] = w.index.isin(a.index)
    w["present24"] = w.index.isin(b.index)
    return w.reset_index()
