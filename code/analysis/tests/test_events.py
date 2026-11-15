"""The events reader recovers the ground truth from files in the released format."""
import numpy as np
import pandas as pd
import pytest

from toam_analysis import events


@pytest.mark.parametrize("tt,expected", [
    ("faceRecog_guess_correct", ("faceRecog", "guess", "correct")),
    ("retRatingFeedback_unsure_incorrect", ("retRatingFeedback", "unsure", "incorrect")),
    ("Feedback_sure_correct", ("Feedback", "sure", "correct")),
    ("faceRecogNA", ("faceRecog", None, None)),
    ("recogRatingNA", ("recogRating", None, None)),
    ("NA", (None, None, None)),
])
def test_parse_trial_type(tt, expected):
    assert events.parse_trial_type(tt) == expected


@pytest.mark.parametrize("bad", ["faceRecog_maybe_correct", "faceRecog_sure", "ret_sure_correct_x", ""])
def test_parse_rejects_unknown(bad):
    with pytest.raises(ValueError):
        events.parse_trial_type(bad)


def test_na_strings_are_kept(syn):
    root = syn["roots"]["ds006265"]
    ev = events.load_participant(root, syn["crash"])
    assert (ev["learning"]["trial_type"] == "NA").any()  # 'NA' not turned into a missing value by pandas


def test_long_table_matches_ground_truth(syn):
    gt = syn["gt"].set_index(["sub", "item"])
    long = syn["long"]
    crashed = set(syn["roots"].get("crashed", {}).get(syn["crash"], []))
    assert crashed
    for test, (c, a) in {"30min": ("conf30", "acc30"), "24h": ("conf24", "acc24")}.items():
        L = long[long["test"] == test].set_index(["sub", "item"])
        expect_idx = gt.index if test == "24h" else gt.index.difference([(syn["crash"], i) for i in crashed])
        assert set(L.index) == set(expect_idx)
        g = gt.loc[L.index]
        assert (L["conf"].fillna("NA") == g[c].fillna("NA")).all()
        assert (L["acc"].fillna("NA") == g[a].fillna("NA")).all()
        assert L["onset_faceRecog"].notna().all()
        assert set(L["n_events"]) == {5}  # the five retrieval events of each trial
    raw = events.load_participant(syn["roots"]["ds006266"], sorted(gt.index.get_level_values(0))[-1])["24h"]
    assert set(raw.groupby("item").size()) == {9}  # 24-h file: retrieval + recognition events
    L24 = long[long["test"] == "24h"].set_index(["sub", "item"])
    assert (L24["recog_conf"].fillna("NA") == gt.loc[L24.index, "recog_conf"].fillna("NA")).all()


def test_wide_marks_missing_test(syn):
    w = syn["wide"]
    crashed = syn["roots"]["crashed"][syn["crash"]]
    sel = (w["sub"] == syn["crash"]) & w["item"].isin(crashed)
    assert sel.sum() == len(crashed)
    assert (~w.loc[sel, "present30"]).all() and w.loc[sel, "present24"].all()
    assert w.loc[sel, "conf30"].isna().all()


def test_onsets_of_faceRecog_are_the_files_values(syn):
    root = syn["roots"]["ds006266"]
    sub = sorted(syn["wide"].loc[syn["wide"]["ds"] == "ds006266", "sub"])[0]
    ev = events.load_participant(root, sub)["24h"]
    face = ev[ev["event"] == "faceRecog"].set_index("item")["onset"]
    L = syn["long"]
    L = L[(L["sub"] == sub) & (L["test"] == "24h")].set_index("item")["onset_faceRecog"]
    assert np.allclose(L.sort_index(), face.sort_index())
