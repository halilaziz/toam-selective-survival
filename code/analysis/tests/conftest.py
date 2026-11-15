"""Shared synthetic data (written once per test session, in the exact released format)."""
import pandas as pd
import pytest

from toam_analysis import events, exclusions, synthetic


@pytest.fixture(scope="session")
def syn(tmp_path_factory):
    gt = synthetic.simulate_behaviour(seed=3)
    crash = gt.loc[gt["ds"] == "ds006265", "sub"].iloc[0]
    out = tmp_path_factory.mktemp("synthetic")
    roots = synthetic.write_dataset(gt, str(out), crash_sub=crash)
    long = events.load_long({k: v for k, v in roots.items() if k.startswith("ds")})
    wide = events.to_wide(long)
    logs = pd.concat([exclusions.read_logs(roots["logs"], s) for s in wide["sub"].unique()], ignore_index=True)
    excl = exclusions.item_exclusions(wide, logs)
    return {"gt": gt, "roots": roots, "long": long, "wide": wide, "logs": logs, "excl": excl, "crash": crash}
