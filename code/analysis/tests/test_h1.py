"""H1 per-participant differences and the end-to-end analysis in a true and a null world."""
import numpy as np
import pandas as pd

from toam_analysis import classes, h1, synthetic


def test_differences_by_hand():
    rows = [  # one participant; item sets: G24 = {a, b}, G30 = {b, c}, S24 = {c}, S30 = {a}; FO = {a}, SG = {b}
        ("a", "sure", "correct", "guess", "correct", 1.0),
        ("b", "guess", "correct", "guess", "correct", -1.0),
        ("c", "guess", "incorrect", "sure", "correct", 0.5),
    ]
    w = pd.DataFrame(rows, columns=["item", "conf30", "acc30", "conf24", "acc24", "m_30min"])
    w["sub"], w["arm"], w["excluded"] = "p", "hipp", False
    w["cls"] = classes.assign_classes(w)
    d = h1.participant_differences(w).iloc[0]
    assert d["H1a"] == (1.0 + -1.0) / 2 - (-1.0 + 0.5) / 2
    assert d["H1b"] == 0.5 - 1.0
    assert d["H1c"] == 1.0 - (-1.0)
    dc = h1.participant_differences(w, correct_only=True).iloc[0]
    assert dc["H1a"] == 0.0 - (-1.0)  # c is incorrect at 30 min, so G30 = {b}


def _in_memory(lam, seed):
    gt = synthetic.simulate_behaviour(lam=lam, seed=seed)
    gt = gt[gt[["conf30", "conf24", "recog_conf"]].notna().all(axis=1)].copy()
    fm = lambda c, a: (gt[c] == "sure") & (gt[a] == "incorrect")
    gt["excluded"] = fm("conf30", "acc30") | fm("conf24", "acc24") | fm("recog_conf", "recog_acc")
    return gt


def test_true_world_detects_selective_survival():
    res, d, _ = h1.run_h1(_in_memory(1.0, 11))
    p = res[res["analysis"] == "primary"].set_index("hypothesis")
    assert p.loc["H1a", "p_holm"] < 0.05 and p.loc["H1a", "dz"] > 0
    assert p.loc["H1c", "p_holm"] < 0.05 and p.loc["H1c", "dz"] > 0
    assert p.loc["H1c", "n"] >= 35
    assert (res["bf10"] > 0).all()


def test_null_world_false_positive_rate():
    hits = np.zeros(3)
    n_sim = 30
    for s in range(n_sim):
        res, _, _ = h1.run_h1(_in_memory(0.0, 100 + s))
        p = res[res["analysis"] == "primary"].set_index("hypothesis")["p_one_sided"]
        hits += (p.loc[["H1a", "H1b", "H1c"]].to_numpy() < 0.05)
    assert (hits / n_sim <= 0.2).all(), hits / n_sim  # nominal 0.05; 30 simulations
