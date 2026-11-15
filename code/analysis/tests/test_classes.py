"""Trajectory classes (Table 2) and the leave-one-subject-out memorability index m."""
import numpy as np
import pandas as pd
import pytest

from toam_analysis import classes


def test_classes_table2():
    rows = [("guess", "guess", False, "SG"), ("sure", "guess", False, "FO"), ("unsure", "guess", False, "FO"),
            ("sure", "sure", False, "SS"), ("unsure", "unsure", False, "other"), ("guess", "sure", False, "other"),
            ("sure", "unsure", False, "other"), ("guess", "guess", True, "excl"), ("sure", "sure", True, "excl")]
    w = pd.DataFrame(rows, columns=["conf30", "conf24", "excluded", "expected"])
    assert (classes.assign_classes(w) == w["expected"]).all()


def _tiny():
    # 4 participants x 3 items; hit = sure + correct at 30 min
    rec = []
    hits = {"p1": [1, 0, 1], "p2": [1, 1, 0], "p3": [0, 0, 1], "p4": [1, 0, 0]}
    for p, hs in hits.items():
        for i, h in enumerate(hs):
            rec.append({"sub": p, "item": f"i{i}", "conf30": "sure" if h else "guess", "acc30": "correct",
                        "conf24": "guess", "acc24": "correct", "excluded": False})
    return pd.DataFrame(rec)


def test_loso_by_hand():
    w = _tiny()
    raw = classes._loso_proportion(w, "30min")
    # item i0 hits: p1 p2 p4 -> for p1 the others are p2 p3 p4 -> 2/3; for p3 -> 3/3
    get = lambda p, i: raw[(w["sub"] == p) & (w["item"] == i)].item()
    assert get("p1", "i0") == pytest.approx(2 / 3)
    assert get("p3", "i0") == pytest.approx(1.0)
    assert get("p2", "i1") == pytest.approx(0.0)
    assert get("p1", "i2") == pytest.approx(1 / 3)


def test_no_self_leakage():
    w = _tiny()
    m0 = classes.memorability(w)
    w2 = w.copy()
    sel = w2["sub"] == "p1"
    w2.loc[sel, "conf30"] = np.where(w2.loc[sel, "conf30"] == "sure", "guess", "sure")  # flip p1's own answers
    m1 = classes.memorability(w2)
    assert np.allclose(m0[sel], m1[sel])          # p1's m does not use p1's responses
    assert not np.allclose(m0[~sel], m1[~sel])    # but the others' m does


def test_excluded_trials_leave_the_denominator():
    w = _tiny()
    w.loc[(w["sub"] == "p2") & (w["item"] == "i0"), "excluded"] = True
    raw = classes._loso_proportion(w, "30min")
    # p1, item i0: valid others are p3, p4 -> hits 1 of 2
    assert raw[(w["sub"] == "p1") & (w["item"] == "i0")].item() == pytest.approx(0.5)
    m = classes.memorability(w)
    assert np.isnan(m[(w["sub"] == "p2") & (w["item"] == "i0")].item())


def test_zscore_within_participant(syn):
    w = syn["excl"]
    m = classes.memorability(w)
    g = m.groupby(w["sub"])
    assert np.allclose(g.mean().dropna(), 0, atol=1e-12)
    assert np.allclose(g.apply(lambda x: x.dropna().std(ddof=0)), 1)


def test_secondary_versions(syn):
    w = syn["excl"]
    raw_mean = (classes._loso_proportion(w, "30min") + classes._loso_proportion(w, "24h")) / 2
    raw_mean = raw_mean.where(~w["excluded"])
    g = raw_mean.groupby(w["sub"])
    expected = (raw_mean - g.transform("mean")) / g.transform(lambda x: x.std(ddof=0))
    assert np.allclose(classes.memorability(w, "mean"), expected, equal_nan=True)
    assert not np.allclose(classes.memorability(w, "24h"), classes.memorability(w, "30min"), equal_nan=True)


def test_m_tracks_true_memorability(syn):
    w = syn["excl"].merge(syn["gt"][["sub", "item", "a"]], on=["sub", "item"])
    m = classes.memorability(w)
    ok = m.notna()
    assert np.corrcoef(m[ok], w.loc[ok, "a"])[0, 1] > 0.6
