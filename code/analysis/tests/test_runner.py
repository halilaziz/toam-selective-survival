"""The runner refuses real data without an OSF registration and runs end to end on synthetic data."""
import json
import os

import pandas as pd
import pytest

import run_toam


def test_guard(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    with pytest.raises(SystemExit):
        run_toam.guard([str(real)], None)
    with pytest.raises(SystemExit):
        run_toam.guard([str(real)], "registered somewhere")
    assert run_toam.guard([str(real)], "https://osf.io/abc12").startswith("real")
    syn = tmp_path / "syn"
    syn.mkdir()
    (syn / "SYNTHETIC_DATA.txt").write_text("x")
    assert run_toam.guard([str(syn)], None) == "synthetic"
    with pytest.raises(SystemExit):
        run_toam.guard([str(syn), str(real)], "https://osf.io/abc12")


def test_cli_end_to_end_on_synthetic(tmp_path):
    out = tmp_path / "syn"
    run_toam.main(["synthetic", "--out", str(out)])
    args = ["--bids-hipp", str(out / "ds006265"), "--bids-wb", str(out / "ds006266"),
            "--logs", str(out / "authors_behavioral_data")]
    run_toam.main(["h1", *args, "--out", str(tmp_path / "h1")])
    res = pd.read_csv(tmp_path / "h1" / "h1_results.csv")
    assert set(res["hypothesis"]) == {"H1a", "H1b", "H1c"} and len(res) == 12
    prov = json.load(open(tmp_path / "h1" / "provenance_h1.json"))
    assert prov["mode"] == "synthetic"
    run_toam.main(["glm-spec", *args, "--deriv", "/deriv", "--out", str(tmp_path / "specs")])
    specs = sorted(os.listdir(tmp_path / "specs"))
    assert sum(f.startswith("spec_sub-") for f in specs) == 40
    el = pd.read_csv(tmp_path / "specs" / "contrast_eligibility.csv")
    assert set(el["contrast"]) == {"H2r", "H2a", "H2b", "H3r", "H3a"}
