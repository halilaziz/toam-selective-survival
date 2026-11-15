"""Item exclusions reproduce the authors' cleanUpBehavData rules (behavior/r_utils.R:182-214)."""
import numpy as np
import pandas as pd

from toam_analysis import exclusions


def _case(**kw):
    base = dict(sub="sub-1", item="x", conf30="sure", acc30="correct", conf24="guess", acc24="correct",
                recog_conf="unsure", recog_acc="correct")
    base.update(kw)
    return base


def _log(**kw):
    base = dict(sub="sub-1", item="x", button1=2, acc1="correct", button2=3, rating2=4, button3=2, rating3=2,
                button4=3, rt4=900.0, rating4=3)
    base.update(kw)
    return base


CASES = [  # (name, wide overrides, log overrides, excluded by default, failing rule)
    ("valid", {}, {}, False, None),
    ("immediate recall wrong", {}, {"acc1": "incorrect"}, True, "immediate_recall"),
    ("immediate recall missed", {}, {"acc1": "miss", "button1": 0}, True, "immediate_recall"),
    ("immediate recall button 1", {}, {"button1": 1}, True, "invalid_answer"),
    ("false memory at 30 min", {"acc30": "incorrect"}, {}, True, "false_memory"),
    ("false memory at 24 h", {"conf24": "sure", "acc24": "incorrect"}, {}, True, "false_memory"),
    ("false memory at recognition", {"recog_conf": "sure", "recog_acc": "incorrect"}, {}, True, "false_memory"),
    ("unsure + incorrect is kept", {"conf30": "unsure", "acc30": "incorrect"}, {}, False, None),
    ("NA at 24 h", {"conf24": None, "acc24": None}, {}, True, "invalid_answer"),
    ("NA at recognition", {"recog_conf": None, "recog_acc": None}, {}, True, "invalid_answer"),
    ("button 1 at 30 min", {}, {"button2": 1}, True, "invalid_answer"),
    ("rating 1 at recognition", {}, {"rating4": 1}, True, "invalid_answer"),
    ("late response recovered by the authors", {}, {"button3": 0, "rating3": 0}, False, None),
    ("fast recognition (R4 off by default)", {}, {"rt4": 80.0}, False, None),
]


def test_each_rule():
    wide = pd.DataFrame([_case(item=n, **w) for n, w, _, _, _ in CASES])
    logs = pd.DataFrame([_log(item=n, **l) for n, _, l, _, _ in CASES])
    out = exclusions.item_exclusions(wide, logs).set_index("item")
    for name, _, _, excluded, rule in CASES:
        assert bool(out.loc[name, "excluded"]) == excluded, name
        if rule:
            assert bool(out.loc[name, rule]), name
    out4 = exclusions.item_exclusions(wide, logs, recog_rt_rule=True).set_index("item")
    assert out4.loc["fast recognition (R4 off by default)", "excluded"]
    assert not out4.loc["valid", "excluded"]


def test_without_logs():
    wide = pd.DataFrame([_case(item="a"), _case(item="b", acc30="incorrect")])
    out = exclusions.item_exclusions(wide, None).set_index("item")
    assert not out.loc["a", "excluded"] and out.loc["b", "excluded"]
    assert not out["logs_available"].any()


def test_synthetic_matches_independent_rules(syn):
    """Expected exclusions computed directly from the ground truth, independently of exclusions.py."""
    gt = syn["gt"].copy()
    crashed = set(syn["roots"]["crashed"][syn["crash"]])
    miss30 = (gt["sub"] == syn["crash"]) & gt["item"].isin(crashed)
    gt.loc[miss30, ["conf30", "acc30"]] = None
    fm = lambda c, a: (gt[c] == "sure") & (gt[a] == "incorrect")
    expected = (
        (gt["acc1"] != "correct")
        | ~gt["button1"].isin([2, 3])
        | fm("conf30", "acc30") | fm("conf24", "acc24") | fm("recog_conf", "recog_acc")
        | gt[["conf30", "conf24", "recog_conf"]].isna().any(axis=1)
        | (gt[["button2", "button3", "button4"]] == 1).any(axis=1)
    )
    got = syn["excl"].set_index(["sub", "item"])["excluded"]
    exp = pd.Series(expected.values, index=pd.MultiIndex.from_frame(gt[["sub", "item"]]))
    assert (got.loc[exp.index] == exp).all()
    assert 0.03 < exp.mean() < 0.2  # the synthetic data exercise the rules
