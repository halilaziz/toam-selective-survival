"""Statistics against scipy, pingouin, a published value and hand computation."""
import math

import numpy as np
import pingouin as pg
import pytest
from scipy import stats as ss

from toam_analysis import stats

SLEEP_DIFF = np.array([-1.2, -2.4, -1.3, -1.3, 0.0, -1.0, -1.8, -0.8, -4.6, -1.4])  # R 'sleep', group 1 - group 2


def test_t_test_matches_scipy():
    rng = np.random.default_rng(0)
    for _ in range(20):
        x = rng.normal(0.3, 1, int(rng.integers(5, 60)))
        r = stats.one_sample_greater(x)
        ref = ss.ttest_1samp(x, 0, alternative="greater")
        assert r.t == pytest.approx(ref.statistic, rel=1e-12)
        assert r.p_one_sided == pytest.approx(ref.pvalue, rel=1e-10)
        assert r.df == x.size - 1


def test_bf10_published_value():
    # BayesFactor::ttestBF on the paired 'sleep' data, r = sqrt(2)/2: BF10 = 17.25888 (package documentation)
    t = ss.ttest_1samp(SLEEP_DIFF, 0).statistic
    assert t == pytest.approx(-4.062128, abs=1e-6)
    assert stats.jzs_bf10(t, 10) == pytest.approx(17.25888, rel=1e-5)


@pytest.mark.parametrize("t,n", [(0.0, 20), (1.5, 20), (-2.2, 17), (3.1, 40), (5.0, 12), (0.4, 39)])
def test_bf10_two_independent_formulas_and_pingouin(t, n):
    a = stats.jzs_bf10(t, n)
    b = stats.jzs_bf10_nct(t, n)
    assert a == pytest.approx(b, rel=1e-6)
    assert a == pytest.approx(float(pg.bayesfactor_ttest(t, n, r=math.sqrt(2) / 2)), rel=1e-3)


@pytest.mark.parametrize("t,n", [(0.0, 20), (1.5, 20), (-2.2, 17), (3.1, 40)])
def test_one_sided_bf_identity(t, n):
    # the two-sided Cauchy prior is the 50/50 mixture of the two half-Cauchy priors: BF10 = (BF+0 + BF-0) / 2
    bf_plus = stats.jzs_bf_plus0(t, n)
    bf_minus = stats.jzs_bf_plus0(-t, n)  # symmetry: BF-0(t) = BF+0(-t)
    assert (bf_plus + bf_minus) / 2 == pytest.approx(stats.jzs_bf10(t, n), rel=1e-6)
    if t > 0:
        assert bf_plus > stats.jzs_bf10(t, n)


def test_dz_ci_defining_property():
    for t, n in [(2.5, 20), (-1.0, 40), (6.0, 17), (0.2, 10)]:
        lo, hi = stats.dz_ci(t, n)
        assert lo < t / math.sqrt(n) < hi
        assert ss.nct.cdf(t, n - 1, lo * math.sqrt(n)) == pytest.approx(0.975, abs=1e-8)
        assert ss.nct.cdf(t, n - 1, hi * math.sqrt(n)) == pytest.approx(0.025, abs=1e-8)


def test_holm_by_hand_and_pingouin():
    p = np.array([0.01, 0.04, 0.03])
    assert np.allclose(stats.holm(p), [0.03, 0.06, 0.06])
    _, ref = pg.multicomp(p, method="holm")
    assert np.allclose(stats.holm(p), ref)
    q = stats.holm([0.2, np.nan, 0.01])
    assert np.isnan(q[1]) and np.allclose(q[[0, 2]], [0.2, 0.02])


def test_trimmed_mean_by_hand():
    x = np.array([2.1, -0.3, 0.8, 1.5, 9.0, 0.2, 1.1, -1.4, 0.9, 1.3])
    r = stats.trimmed_mean_greater(x, 0.2)
    xs = np.sort(x)
    g = 2  # floor(0.2 * 10)
    assert r.trimmed_mean == pytest.approx(ss.trim_mean(x, 0.2))
    w = np.concatenate([[xs[g]] * g, xs[g:-g], [xs[-g - 1]] * g])
    se = np.std(w, ddof=1) / (0.6 * math.sqrt(10))
    assert r.se == pytest.approx(se)
    assert r.t == pytest.approx(ss.trim_mean(x, 0.2) / se)
    assert r.df == 10 - 2 * g - 1
    assert r.p_one_sided == pytest.approx(ss.t.sf(r.t, r.df))


def test_percentile_bootstrap_reproducible():
    data = np.arange(30, dtype=float)[:, None]
    f = lambda rows: rows[:, 0].mean()
    a = stats.percentile_bootstrap(f, data, 2000, seed=5)
    b = stats.percentile_bootstrap(f, data, 2000, seed=5)
    assert a[:2] == b[:2] and a[0] < 14.5 < a[1]
