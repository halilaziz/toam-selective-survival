"""Synthetic TOAM-like data with known ground truth, written in the exact format of the released events and of the
authors' public logfiles. Used only by the tests; never mixed with real data (each root holds SYNTHETIC_DATA.txt).

Behaviour: items differ in memorability (a_i, shared by all participants), participants in ability (b_p). The
30-minute strength s30 = lam * a_i + b_p + noise sets the rating (sure > 0.6 >= unsure > -0.3 >= guess); overnight
s24 = s30 - forget + noise(forget_sd). Correctness depends on the rating. With lam > 0, items that survive are more
memorable (H1 true); with lam = 0 they are not (H1 null).
Neural worlds for the beta-level simulation (simulate_betas): 'selective' (faceRecog response grows with item
strength a_i, no test effect) and 'trace' (24-h responses are higher by tau for every item, no item effect).
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

from . import ARMS

CONF_CODE = {"sure": 4, "unsure": 3, "guess": 2}
N_ITEMS = 96


def item_names(n: int = N_ITEMS) -> list[str]:
    letters = "abcdefghijklmnopqrstuvwx"
    return [f"{'f' if i % 2 else 'm'}{'ao'[i % 4 // 2]}{letters[i % 24]}_{10000 + 37 * i:05d}.png" for i in range(n)]


def _rate(s):
    return np.where(s > 0.6, "sure", np.where(s > -0.3, "unsure", "guess"))


def simulate_behaviour(n_per_arm: int = 20, lam: float = 1.0, seed: int = 1, forget: float = 0.5,
                       forget_sd: float = 0.8) -> pd.DataFrame:
    """Ground truth, one row per participant x item."""
    rng = np.random.default_rng(seed)
    items = item_names()
    a = rng.normal(0, 1, N_ITEMS)
    rows = []
    subs = [("ds006265", f"sub-{60000 + 11 * k}") for k in range(n_per_arm)] + \
           [("ds006266", f"sub-{70000 + 13 * k}") for k in range(n_per_arm)]
    for p, (ds, sub) in enumerate(subs):
        b = rng.normal(0, 0.5)
        keep = rng.permutation(N_ITEMS)[: N_ITEMS - int(rng.integers(0, 9))]  # aborted acquisitions: 88-96 items
        s30 = lam * a + b + rng.normal(0, 1, N_ITEMS)
        s24 = s30 - forget + rng.normal(0, forget_sd, N_ITEMS)
        conf30, conf24 = _rate(s30), _rate(s24)
        pc = {"sure": 0.97, "unsure": 0.6, "guess": 0.5}
        acc30 = np.where(rng.random(N_ITEMS) < np.vectorize(pc.get)(conf30), "correct", "incorrect")
        acc24 = np.where(rng.random(N_ITEMS) < np.vectorize(pc.get)(conf24), "correct", "incorrect")
        rconf = _rate(s24 + 0.8 + rng.normal(0, 0.5, N_ITEMS))
        prc = {"sure": 0.95, "unsure": 0.75, "guess": 0.55}
        racc = np.where(rng.random(N_ITEMS) < np.vectorize(prc.get)(rconf), "correct", "incorrect")
        for i in sorted(keep):
            rows.append({"ds": ds, "arm": ARMS[ds], "sub": sub, "item": items[i], "a": a[i], "s30": s30[i],
                         "s24": s24[i], "conf30": conf30[i], "acc30": acc30[i], "conf24": conf24[i],
                         "acc24": acc24[i], "recog_conf": rconf[i], "recog_acc": racc[i]})
    gt = pd.DataFrame(rows)
    n = len(gt)
    # immediate recall (logfile only): 2% wrong, 0.5% misses
    u = rng.random(n)
    gt["acc1"] = np.where(u < 0.02, "incorrect", np.where(u < 0.025, "miss", "correct"))
    gt["button1"] = np.where(gt["acc1"] == "miss", 0, rng.choice([2, 3], n))
    # buttons and ratings behind the 30-min, 24-h and recognition responses
    for k, (cc, ac) in {"2": ("conf30", "acc30"), "3": ("conf24", "acc24"), "4": ("recog_conf", "recog_acc")}.items():
        gt[f"button{k}"] = rng.choice([2, 3], n)
        gt[f"rating{k}"] = gt[cc].map(CONF_CODE)
        miss = rng.random(n) < 0.01            # missed, not recovered: no status in the events
        late = (~miss) & (rng.random(n) < 0.01)  # missed in the logfile, recovered by the authors (status present)
        wrong = (~miss) & (~late) & (rng.random(n) < 0.005)  # button 1 (out of bounds), status still present
        gt.loc[miss, [cc, ac]] = None
        gt.loc[miss | late, f"button{k}"] = 0
        gt.loc[miss, f"rating{k}"] = 0
        gt.loc[wrong, f"button{k}"] = 1
    gt["rt4"] = np.where(rng.random(n) < 0.01, 80.0, rng.uniform(400, 2500, n)).round(1)
    return gt


def _status(conf, acc):
    return f"_{conf}_{acc}" if isinstance(conf, str) and isinstance(acc, str) else "NA"


def write_dataset(gt: pd.DataFrame, out_dir: str, seed: int = 2, crash_sub: str | None = None,
                  crash_items: int = 5) -> dict[str, str]:
    """Write events (exact released format), participants.tsv, a bold JSON per participant and the authors'
    logfiles. crash_sub: participant whose last crash_items trials are missing at the 30-min test (like sub-65399).
    Returns {'ds006265': root, 'ds006266': root, 'logs': dir}."""
    rng = np.random.default_rng(seed)
    roots = {}
    logs = os.path.join(out_dir, "authors_behavioral_data")
    os.makedirs(logs, exist_ok=True)
    for ds, gd in gt.groupby("ds"):
        root = os.path.join(out_dir, ds)
        roots[ds] = root
        os.makedirs(root, exist_ok=True)
        with open(os.path.join(root, "SYNTHETIC_DATA.txt"), "w") as f:
            f.write("Synthetic data generated by toam_analysis.synthetic; not TOAM.\n")
        subs = sorted(gd["sub"].unique())
        pd.DataFrame({"participant_id": subs}).to_csv(os.path.join(root, "participants.tsv"), sep="\t", index=False)
        tr, nsl = (2.12, 28) if ARMS[ds] == "hipp" else (2.7, 96)
        for sub in subs:
            g = gd[gd["sub"] == sub].sample(frac=1, random_state=int(rng.integers(1e9))).reset_index(drop=True)
            f1 = os.path.join(root, sub, "ses-1", "func")
            f2 = os.path.join(root, sub, "ses-2", "func")
            os.makedirs(f1, exist_ok=True)
            os.makedirs(f2, exist_ok=True)
            with open(os.path.join(f1, f"{sub}_ses-1_task-retrieval_bold.json"), "w") as f:
                json.dump({"RepetitionTime": tr, "SliceTiming": list(np.linspace(0, tr, nsl, endpoint=False))}, f)
            crashed = set(g["item"].iloc[-crash_items:]) if sub == crash_sub else set()
            if crashed:
                roots.setdefault("crashed", {})[sub] = sorted(crashed)
            # learning run: Face, Enc, Recall, Feedback, labelled with the 30-min status
            t, rows = 10.0, []
            for _, r in g.iterrows():
                st = _status(r["conf30"], r["acc30"]) if r["item"] not in crashed else "NA"
                for ev, dt in (("Face", 0), ("Enc", 1.0), ("Recall", 3.5), ("Feedback", 6.25)):
                    rows.append((round(t + dt, 2), 0, "NA" if st == "NA" else ev + st, r["item"]))
                t += 6.25 + rng.uniform(4.5, 6.5)
            _write_events(os.path.join(f1, f"{sub}_ses-1_task-forgetexp_events.tsv"), rows)
            # 30-min test (order shuffled again, as the authors' windowed shuffle)
            g30 = g.sample(frac=1, random_state=int(rng.integers(1e9)))
            t, rows = 8.48, []
            for _, r in g30.iterrows():
                if r["item"] in crashed:
                    continue
                st = _status(r["conf30"], r["acc30"])
                for ev, dt in (("faceRecog", 0), ("ret", 1.0), ("retFeedback", 3.75), ("retRating", 3.8),
                               ("retRatingFeedback", 6.3)):
                    rows.append((round(t + dt, 2), 0, ev + st, r["item"]))
                t += 6.3 + rng.uniform(4.5, 6.5)
            _write_events(os.path.join(f1, f"{sub}_ses-1_task-retrieval_events.tsv"), rows)
            # 24-h test with recognition
            g24 = g.sample(frac=1, random_state=int(rng.integers(1e9)))
            t, rows = 5.4, []
            for _, r in g24.iterrows():
                st, rs = _status(r["conf24"], r["acc24"]), _status(r["recog_conf"], r["recog_acc"])
                for ev, dt, s in (("faceRecog", 0, st), ("ret", 1.0, st), ("retFeedback", 3.75, st),
                                  ("retRating", 3.8, st), ("retRatingFeedback", 6.3, st), ("recog", 6.6, rs),
                                  ("recogFeedback", 9.6, rs), ("recogRating", 9.65, rs),
                                  ("recogRatingFeedback", 12.15, rs)):
                    rows.append((round(t + dt, 2), 0, ev + s, r["item"]))
                t += 12.15 + rng.uniform(4.5, 6.5)
            _write_events(os.path.join(f2, f"{sub}_ses-2_task-forgetexp_events.tsv"), rows)
            _write_logs(logs, sub, g)
    roots["logs"] = logs
    return roots


def _write_events(path, rows):
    pd.DataFrame(rows, columns=["onset", "duration", "trial_type", "item"]).to_csv(path, sep="\t", index=False)


def _write_logs(log_dir, sub, g):
    pid = sub.replace("sub-", "")
    base = {"ID": pid, "Presented_Person": g["item"]}
    enc = pd.DataFrame({**base, "Immediate_Recall_Pressed_Button": g["button1"],
                        "Immediate_Recall_RT": 900, "Immediate_Recall_Accuracy": g["acc1"]})
    ret = pd.DataFrame({**base, "Assoc_Retrieval_Pressed_Button": g["button2"],
                        "Assoc_Retrieval_Accuracy": g["acc30"].fillna("miss"),
                        "Retrieval_consc_Rating_Pressed_Button": g["rating2"]})
    dret = pd.DataFrame({**base, "Assoc_Retrieval_Pressed_Button": g["button3"],
                         "Retrieval_consc_Rating_Pressed_Button": g["rating3"],
                         "ForcedChoice_Pressed_Button": g["button4"], "ForcedChoice_RT": g["rt4"],
                         "Recognition_consc_Rating_Pressed_Button": g["rating4"]})
    for kind, df in (("encoding", enc), ("retrieval", ret), ("delayed_retrieval", dret)):
        df.to_csv(os.path.join(log_dir, f"{pid}-{kind}_run1_logfile.txt"), sep="\t", index=False)


def simulate_betas(spec: dict, gt_sub: pd.DataFrame, world: str, rng: np.random.Generator,
                   kappa: float = 0.8, tau: float = 0.8, noise_trial: float = 1.0, noise_beta: float = 0.3) -> dict:
    """Beta of every faceRecog condition of one participant: mean of simulated trial responses over the
    condition's trials plus estimation noise. Returns {(session index, condition name): beta}."""
    a = gt_sub.set_index("item")["a"]
    out = {}
    for si, s in enumerate(spec["sessions"], start=1):
        if s["kind"] not in ("30min", "24h"):
            continue
        is24 = s["kind"] == "24h"
        for c in s["conditions"]:
            if not c["base"].startswith("faceRecog_correct"):
                continue
            items = c["items"]
            base = 1.0 + (0.5 if "_consc" in c["base"] else 0.0)
            if world == "selective":
                y = base + kappa * a.reindex(items).to_numpy() + rng.normal(0, noise_trial, len(items))
            elif world == "trace":
                y = base + tau * is24 + rng.normal(0, noise_trial, len(items))
            else:
                raise ValueError(world)
            out[(si, c["name"])] = float(np.mean(y)) + rng.normal(0, noise_beta)
    return out


def contrast_value(contrast: dict, betas: dict) -> float:
    if not contrast["eligible"]:
        return float("nan")
    return float(sum(w["weight"] * betas[(w["session"], w["condition"])] for w in contrast["weights"]))
