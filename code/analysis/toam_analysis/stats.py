"""Statistics named in the preregistration (Part 5): one-sided one-sample t tests, Holm correction, d_z with a
95% CI, JZS Bayes factors (r = sqrt(2)/2), 20% trimmed-mean tests and percentile bootstrap CIs."""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict

import numpy as np
from scipy import integrate, optimize, stats

R_DEFAULT = math.sqrt(2) / 2


@dataclass
class OneSample:
    n: int
    mean: float
    sd: float
    t: float
    df: int
    p_one_sided: float          # H1: mean > 0
    dz: float
    dz_ci_low: float
    dz_ci_high: float
    bf10: float                 # two-sided JZS Bayes factor
    bf_plus0: float             # one-sided (delta > 0) JZS Bayes factor

    def as_dict(self):
        return asdict(self)


def _clean(x) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return x[np.isfinite(x)]


def one_sample_greater(x, r: float = R_DEFAULT) -> OneSample:
    """One-sided one-sample t test of mean(x) > 0, with d_z, its 95% CI and JZS Bayes factors."""
    x = _clean(x)
    n = x.size
    if n < 2:
        nan = float("nan")
        return OneSample(n, float(np.mean(x)) if n else nan, nan, nan, max(n - 1, 0), nan, nan, nan, nan, nan, nan)
    mean, sd = float(np.mean(x)), float(np.std(x, ddof=1))
    t = mean / (sd / math.sqrt(n))
    df = n - 1
    p = float(stats.t.sf(t, df))
    dz = mean / sd
    lo, hi = dz_ci(t, n)
    return OneSample(n, mean, sd, float(t), df, p, dz, lo, hi, jzs_bf10(t, n, r), jzs_bf_plus0(t, n, r))


def dz_ci(t: float, n: int, conf: float = 0.95) -> tuple[float, float]:
    """CI for d_z by inverting the noncentral t distribution (delta = d_z * sqrt(n))."""
    df = n - 1
    a = (1 - conf) / 2
    sq = math.sqrt(n)

    d0 = t / sq
    step = math.sqrt(1 / n + d0 ** 2 / (2 * df))  # approximate SE of d_z

    def bound(target):
        # f decreases in d; walk out from the estimate in SE steps (far brackets make nct.cdf return NaN)
        f = lambda d: stats.nct.cdf(t, df, d * sq) - target
        lo, hi = d0, d0
        while f(lo) <= 0:
            lo -= step
        while f(hi) >= 0:
            hi += step
        return optimize.brentq(f, lo, hi, xtol=1e-12)

    return bound(1 - a), bound(a)


def jzs_bf10(t: float, n: int, r: float = R_DEFAULT) -> float:
    """Two-sided JZS Bayes factor for a one-sample t test (Rouder et al., 2009, eq. 1, Cauchy scale r)."""
    nu = n - 1

    def integrand(g):
        if g <= 0:
            return 0.0
        a = (1 + n * g * r ** 2) ** -0.5
        b = (1 + t ** 2 / ((1 + n * g * r ** 2) * nu)) ** (-(nu + 1) / 2)
        prior = (2 * math.pi) ** -0.5 * g ** -1.5 * math.exp(-1 / (2 * g))
        return a * b * prior

    num, _ = integrate.quad(integrand, 0, np.inf, limit=500)
    den = (1 + t ** 2 / nu) ** (-(nu + 1) / 2)
    return float(num / den)


def _bf_nct(t: float, n: int, r: float, lower: float) -> float:
    """BF against delta = 0 from the noncentral-t likelihood and a Cauchy(0, r) prior on delta,
    truncated to (lower, inf) and renormalised. lower = -inf gives the two-sided BF, 0 the one-sided BF+0."""
    df, sq = n - 1, math.sqrt(n)
    like0 = stats.t.pdf(t, df)
    mass = 1.0 if lower == -np.inf else 0.5
    f = lambda d: stats.nct.pdf(t, df, d * sq) * stats.cauchy.pdf(d, 0, r) / mass
    # integrate where the likelihood lives, then the tails
    centre = t / sq
    pts = sorted({max(lower, centre - 3), centre, centre + 3} - {-np.inf})
    total = 0.0
    edges = [lower] + [p for p in pts if p > lower] + [np.inf]
    for a, b in zip(edges[:-1], edges[1:]):
        if b > a:
            v, _ = integrate.quad(f, a, b, limit=500)
            total += v
    return float(total / like0)


def jzs_bf_plus0(t: float, n: int, r: float = R_DEFAULT) -> float:
    """One-sided JZS Bayes factor, H+: delta > 0 (half-Cauchy prior), versus delta = 0."""
    return _bf_nct(t, n, r, 0.0)


def jzs_bf10_nct(t: float, n: int, r: float = R_DEFAULT) -> float:
    """Two-sided JZS BF computed a second, independent way (noncentral-t likelihood); used in the tests."""
    return _bf_nct(t, n, r, -np.inf)


def holm(pvals) -> np.ndarray:
    """Holm step-down adjusted p values (NaN entries are left out of the family and stay NaN)."""
    p = np.asarray(pvals, dtype=float)
    out = np.full(p.shape, np.nan)
    idx = np.where(np.isfinite(p))[0]
    m = idx.size
    if m == 0:
        return out
    order = idx[np.argsort(p[idx])]
    running = 0.0
    for k, i in enumerate(order):
        running = max(running, min(1.0, (m - k) * p[i]))
        out[i] = running
    return out


@dataclass
class TrimmedTest:
    n: int
    trim: float
    trimmed_mean: float
    se: float
    t: float
    df: int
    p_one_sided: float

    def as_dict(self):
        return asdict(self)


def trimmed_mean_greater(x, trim: float = 0.2) -> TrimmedTest:
    """Tukey-McLaughlin one-sample test on the 20% trimmed mean (Wilcox, 2012, sec. 4.4), H1: mean > 0."""
    x = np.sort(_clean(x))
    n = x.size
    g = int(math.floor(trim * n))
    h = n - 2 * g
    if h < 2:
        nan = float("nan")
        return TrimmedTest(n, trim, nan, nan, nan, max(h - 1, 0), nan)
    tm = float(np.mean(x[g:n - g]))
    w = x.copy()
    if g > 0:
        w[:g] = x[g]
        w[n - g:] = x[n - g - 1]
    sw = float(np.std(w, ddof=1))
    se = sw / ((1 - 2 * trim) * math.sqrt(n))
    t = tm / se
    df = h - 1
    return TrimmedTest(n, trim, tm, se, float(t), df, float(stats.t.sf(t, df)))


def percentile_bootstrap(statistic, data: np.ndarray, n_boot: int = 10_000, seed: int = 20261112,
                         conf: float = 0.95) -> tuple[float, float, np.ndarray]:
    """Percentile bootstrap over rows of `data` (participants). `statistic(rows)` returns a float."""
    data = np.asarray(data, dtype=float)
    rng = np.random.default_rng(seed)
    n = data.shape[0]
    reps = np.empty(n_boot)
    for b in range(n_boot):
        reps[b] = statistic(data[rng.integers(0, n, n)])
    a = (1 - conf) / 2
    lo, hi = np.nanquantile(reps, [a, 1 - a])
    return float(lo), float(hi), reps
