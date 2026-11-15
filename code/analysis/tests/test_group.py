"""RQ2 decision rules (Table 3), composition share, RQ3 estimation and pipeline agreement; end to end on beta-level
simulations of a selective-survival world and a trace-change world."""
import numpy as np
import pandas as pd
import pytest

from toam_analysis import glm_spec, h1, h2h3, synthetic


def _res(p_r, p_a, p_b, m_r=1.0, m_a=0.1):
    return {"H2r": {"p_holm": p_r, "mean": m_r}, "H2a": {"p_holm": p_a, "mean": m_a}, "H2b": {"p_holm": p_b}}


@pytest.mark.parametrize("res,expected", [
    (_res(0.2, 0.01, 0.01), "Reproduction failed"),
    (_res(0.01, 0.01, 0.3), "Trace change supported"),
    (_res(0.01, 0.3, 0.01, m_a=0.4), "Selective survival supported"),
    (_res(0.01, 0.3, 0.01, m_a=0.6), "Inconclusive"),  # H2a estimate not below half of H2r
    (_res(0.01, 0.01, 0.01), "Mixed account"),
    (_res(0.01, 0.3, 0.3), "Inconclusive"),
])
def test_table3(res, expected):
    assert h2h3.decide_rq2(res) == expected


def test_composition_share():
    rng = np.random.default_rng(1)
    r = rng.normal(1.0, 0.2, 20)
    a = 0.5 * r
    est, lo, hi = h2h3.composition_share(a, r, 2000)
    assert est == pytest.approx(0.5) and lo <= 0.5 <= hi
    a2 = a.copy()
    a2[:3] = np.nan  # ineligible for H2a
    est2, _, _ = h2h3.composition_share(a2, r, 500)
    assert est2 == pytest.approx(1 - np.nanmean(a2) / np.mean(r))


def test_pipelines_agree():
    mk = lambda d, lo, hi: {"dz": d, "dz_ci_low": lo, "dz_ci_high": hi}
    spm = {"H3r": mk(0.5, 0.1, 0.9), "H3a": mk(0.2, -0.2, 0.6)}
    fp = {"H3r": mk(0.6, 0.2, 1.0), "H3a": mk(-0.1, -0.5, 0.3)}
    out = h2h3.pipelines_agree(spm, fp)
    assert out["H3r"]["robust"] and not out["H3a"]["robust"] and not out["H3a"]["same_sign"]


@pytest.fixture(scope="module")
def specs(tmp_path_factory):
    gt = synthetic.simulate_behaviour(seed=21, forget=0.9)
    roots = synthetic.write_dataset(gt, str(tmp_path_factory.mktemp("worlds")))
    from toam_analysis import events, exclusions
    long = events.load_long({k: v for k, v in roots.items() if k.startswith("ds")})
    wide = events.to_wide(long)
    logs = pd.concat([exclusions.read_logs(roots["logs"], s) for s in wide["sub"].unique()], ignore_index=True)
    prepared = h1.prepare(exclusions.item_exclusions(wide, logs))
    out = {}
    for sub, g in prepared.groupby("sub"):
        ds = g["ds"].iloc[0]
        root = roots[ds]
        arm = "hipp" if ds == "ds006265" else "wb"
        out[sub] = glm_spec.build_spec(sub, arm, root, dict(zip(g["item"], g["cls"])), "/deriv",
                                       glm_spec.first_bold_json(root, sub))
    return gt, out


def _table(gt, specs, world, arm, seed):
    """Strong, low-noise worlds: these tests check the weights and the decision logic, not power."""
    rng = np.random.default_rng(seed)
    rows = []
    for sub, spec in specs.items():
        if spec["arm"] != arm:
            continue
        betas = synthetic.simulate_betas(spec, gt[gt["sub"] == sub], world, rng, kappa=2.0, tau=1.0,
                                         noise_trial=0.5, noise_beta=0.1)
        rows.append({"sub": sub, **{c["name"]: synthetic.contrast_value(c, betas) for c in spec["contrasts"]}})
    return pd.DataFrame(rows)


def test_selective_world_gives_selective_survival(specs):
    gt, sp = specs
    t = _table(gt, sp, "selective", "hipp", 3)
    assert t["H2b"].notna().sum() >= 15
    res = h2h3.group_h2(t, n_boot=2000)
    assert res["decision"] == "Selective survival supported", res
    assert res["composition_share"]["estimate"] > 0.5


def test_trace_world_gives_trace_change(specs):
    gt, sp = specs
    t = _table(gt, sp, "trace", "hipp", 4)
    res = h2h3.group_h2(t, n_boot=2000)
    assert res["decision"] == "Trace change supported", res
    assert abs(res["composition_share"]["estimate"]) < 0.5


def test_rq3_estimation(specs):
    gt, sp = specs
    t = _table(gt, sp, "trace", "wb", 5)
    res = h2h3.group_h3(t, n_boot=1000)
    assert set(res) == {"H3r", "H3a", "composition_share"}
    # trace world: 24-h responses higher for every item, equally for sure and guess -> interaction near 0
    assert abs(res["H3a"]["mean"]) < 0.5 and abs(res["H3r"]["mean"]) < 0.5
