"""First-level specification: the authors' conditions, the preregistered split, onsets, renaming, contrasts and the
>= 4 trials rule."""
import json

import numpy as np
import pandas as pd
import pytest

from toam_analysis import events, glm_spec, h1

CG, CS = glm_spec.CG, glm_spec.CS


def test_authors_condition_lists():
    assert len(glm_spec.authors_names("learning")) == 4 * 5      # contrasts_enc_subsequent.m
    assert glm_spec.authors_names("consolidation") == ["number"]  # contrasts_consolidation.m
    assert len(glm_spec.authors_names("30min")) == 5 * 5          # contrasts_ret_twoEvents.m
    assert len(glm_spec.authors_names("24h")) == 9 * 5            # contrasts_delret.m
    n24 = glm_spec.authors_names("24h")
    assert n24[:5] == ["faceRecog_correct_consc", "faceRecog_correct_unconsc", "faceRecog_correct_between",
                       "faceRecog_incorrect_unconsc", "faceRecog_incorrect_between"]
    assert "faceRecog_incorrect_consc" not in n24 and "recogRatingFeedback_incorrect_between" in n24
    assert "Face_incorrect_subseqconsc" not in glm_spec.authors_names("learning")


def test_split_replaces_in_place():
    hipp = glm_spec._split_names(glm_spec.authors_names("30min"), split_sure=False)
    assert hipp[:6] == [CS, f"{CG}_SG", f"{CG}_FO", f"{CG}_other", f"{CG}_excl", "faceRecog_correct_between"]
    wb = glm_spec._split_names(glm_spec.authors_names("30min"), split_sure=True)
    assert wb[:4] == [f"{CS}_SS", f"{CS}_other", f"{CS}_excl", f"{CG}_SG"]
    assert len(wb) == 25 - 2 + 3 + 4


@pytest.fixture(scope="module")
def prepared(syn):
    return h1.prepare(syn["excl"])


def _spec(syn, prepared, ds, k=0, **kw):
    sub = sorted(prepared.loc[prepared["ds"] == ds, "sub"].unique())[k]
    root = syn["roots"][ds]
    cls = dict(zip(prepared.loc[prepared["sub"] == sub, "item"], prepared.loc[prepared["sub"] == sub, "cls"]))
    arm = "hipp" if ds == "ds006265" else "wb"
    return sub, glm_spec.build_spec(sub, arm, root, cls, "/deriv", glm_spec.first_bold_json(root, sub), **kw)


def test_onsets_match_events_and_classes(syn, prepared):
    for ds in ("ds006265", "ds006266"):
        sub, spec = _spec(syn, prepared, ds)
        ev = events.load_participant(syn["roots"][ds], sub)
        w = prepared[prepared["sub"] == sub].set_index("item")
        for s in spec["sessions"]:
            if s["kind"] == "learning":
                continue
            test = s["kind"]
            c, a = ("conf30", "acc30") if test == "30min" else ("conf24", "acc24")
            face = ev[test][ev[test]["event"] == "faceRecog"].set_index("item")["onset"]
            for cond in s["conditions"]:
                if not cond["base"].startswith(CG):
                    continue
                part = cond["base"].split("_")[-1]
                items = cond["items"]
                assert (w.loc[items, c] == "guess").all() and (w.loc[items, a] == "correct").all()
                if part in ("SG", "FO", "excl"):
                    assert (w.loc[items, "cls"] == part).all()
                else:
                    assert (~w.loc[items, "cls"].isin(["SG", "FO", "excl"])).all()
                assert np.allclose(cond["onsets"], np.sort(face.loc[items].to_numpy()))
            # every correct-guess faceRecog trial is in exactly one split part
            cg_items = w.index[(w[c] == "guess") & (w[a] == "correct") & w.index.isin(face.index)]
            got = [i for cond in s["conditions"] if cond["base"].startswith(CG) for i in cond["items"]]
            assert sorted(got) == sorted(cg_items)
            if test == "30min":
                assert not any(cond["base"] == f"{CG}_FO" for cond in s["conditions"])


def test_recognition_events_take_the_retrieval_status(syn, prepared):
    sub, spec = _spec(syn, prepared, "ds006266")
    s24 = next(s for s in spec["sessions"] if s["kind"] == "24h")
    w = prepared[prepared["sub"] == sub].set_index("item")
    cond = next(c for c in s24["conditions"] if c["base"] == "recog_correct_unconsc")
    assert (w.loc[cond["items"], "conf24"] == "guess").all() and (w.loc[cond["items"], "acc24"] == "correct").all()
    mixed = w.loc[cond["items"], "recog_conf"].dropna().unique()
    assert len(mixed) > 1  # recognition ratings differ, the condition follows the retrieval status


def test_false_memories_and_na_are_unmodelled(syn, prepared):
    sub, spec = _spec(syn, prepared, "ds006265")
    s30 = next(s for s in spec["sessions"] if s["kind"] == "30min")
    modelled = {i for c in s30["conditions"] for i in c["items"]}
    w = prepared[prepared["sub"] == sub].set_index("item")
    fm = w.index[(w["conf30"] == "sure") & (w["acc30"] == "incorrect")]
    na = w.index[w["conf30"].isna()]
    assert not (set(fm) | set(na)) & modelled
    assert all(c["n"] == len(c["onsets"]) > 0 for c in s30["conditions"])


def test_renaming_rule(syn, prepared):
    _, spec = _spec(syn, prepared, "ds006265")
    names24 = [c["name"] for c in spec["sessions"][2]["conditions"]]
    assert f"{CG}_SG 2" in names24 and "faceRecog_correct_between 2" in names24
    assert any(n == "recog_correct_unconsc" for n in names24)  # not in an earlier session: no suffix
    names30 = [c["name"] for c in spec["sessions"][1]["conditions"]]
    assert not any(n.endswith(" 2") for n in names30)


def test_contrast_weights(syn, prepared):
    _, spec = _spec(syn, prepared, "ds006265")
    con = {c["name"]: c for c in spec["contrasts"]}
    assert set(con) == {"H2r", "H2a", "H2b"}
    for c in con.values():
        if c["eligible"]:
            assert sum(w["weight"] for w in c["weights"]) == pytest.approx(0)
    r = con["H2r"]
    if r["eligible"]:
        s30 = glm_spec._sess_index(spec, "30min")
        assert sum(w["weight"] for w in r["weights"] if w["session"] == s30) == pytest.approx(-1)
        assert all(not w["condition"].startswith(f"{CG}_excl") for w in r["weights"])
    a = con["H2a"]
    assert {(w["condition"], w["weight"]) for w in a["weights"]} == {(f"{CG}_SG 2", 1.0), (f"{CG}_SG", -1.0)}
    _, wb = _spec(syn, prepared, "ds006266")
    con = {c["name"]: c for c in wb["contrasts"]}
    assert set(con) == {"H3r", "H3a"}
    h3a = {(w["condition"], w["weight"]) for w in con["H3a"]["weights"]}
    assert h3a == {(f"{CS}_SS 2", 1.0), (f"{CG}_SG 2", -1.0), (f"{CS}_SS", -1.0), (f"{CG}_SG", 1.0)}


def test_min_trials_rule(syn, prepared):
    sub, spec = _spec(syn, prepared, "ds006265")
    s24 = next(s for s in spec["sessions"] if s["kind"] == "24h")
    fo = next((c for c in s24["conditions"] if c["base"] == f"{CG}_FO"), None)
    n_fo = fo["n"] if fo else 0
    h2b = next(c for c in spec["contrasts"] if c["name"] == "H2b")
    assert h2b["eligible"] == (n_fo >= 4 and h2b["trial_counts"]["cg24_SG"] >= 4)
    # force too few FO trials: relabel all but 3 FO items as 'other'
    w = prepared[prepared["sub"] == sub]
    cls = dict(zip(w["item"], w["cls"]))
    fo_items = [i for i, c in cls.items() if c == "FO"]
    for i in fo_items[3:]:
        cls[i] = "other"
    root = syn["roots"]["ds006265"]
    spec2 = glm_spec.build_spec(sub, "hipp", root, cls, "/deriv", glm_spec.first_bold_json(root, sub))
    h2b2 = next(c for c in spec2["contrasts"] if c["name"] == "H2b")
    assert not h2b2["eligible"] and h2b2["weights"] == [] and "cg24_FO" in h2b2["reason"]


def test_consolidation_session_and_json(syn, prepared, tmp_path):
    sub, spec = _spec(syn, prepared, "ds006265", consolidation_onsets=[10.0, 20.0, 30.5])
    assert [s["kind"] for s in spec["sessions"]] == ["learning", "consolidation", "30min", "24h"]
    assert spec["sessions"][1]["conditions"][0]["name"] == "number"
    a = next(c for c in spec["contrasts"] if c["name"] == "H2a")
    assert {w["session"] for w in a["weights"]} == {3, 4}
    p = tmp_path / "spec.json"
    glm_spec.write_spec(spec, str(p))
    back = json.loads(p.read_text())
    assert back["contrasts"] == spec["contrasts"] and back["TR"] == pytest.approx(2.12)
    assert back["nslices"] == 28 and back["sessions"][2]["scan_regex"] == "^s6wra.*retrieval.*\\.nii$"
