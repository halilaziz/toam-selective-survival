"""Build QC_DECISIONS.md from the QC tables (coregistration check, whole-slab and medial-temporal rho) and the
decisions given below. Reads only QC tables; no event, response or contrast file."""
import ast
import csv
import sys

QC = sys.argv[1]            # local qc/prereg_qc_v2 folder
OUT = sys.argv[2]
DEC = ast.literal_eval(open(sys.argv[3]).read())   # {sub: (decision, note, decided_EST)}
HEAD = open(sys.argv[4]).read()


def tsv(p):
    with open(p) as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


arm = {}
dice = {}
for a in ("hipp", "wb"):
    for r in tsv(f"{QC}/{a}/qc_summary.tsv"):
        arm[r["sub"]] = a
        dice.setdefault(r["sub"], {})[r["run"]] = float(r["gm_dice_participant_vs_tpm"])
coreg = {}
for r in tsv(f"{QC}/coreg_check.tsv"):
    coreg.setdefault(r["sub"], {})[r["run"]] = r
mtl = {}
for r in tsv(f"{QC}/coreg_mtl_rho.tsv"):
    mtl.setdefault(r["sub"], {})[r["run"]] = r


def run_txt(s, run):
    c = coreg[s].get(run)
    if c is None:
        return f"{run}: n/a"
    t = f"{run} {float(c['shift_mm']):.1f} mm/{float(c['rot_deg']):.1f}°"
    if c.get("vs_learning_mm"):
        t += f" (vs learning {float(c['vs_learning_mm']):.1f} mm/{float(c['vs_learning_deg']):.1f}°)"
    m = mtl.get(s, {}).get(run)
    if m:
        t += f", ρ MTL {float(m['rho_csf_mtl_spm']):.2f} vs {float(m['rho_csf_mtl_scanner']):.2f}"
    return t


lines = [HEAD.rstrip("\n"), "",
         "| sub | arm | decision | SPM coregistration vs scanner coordinates per run (shift at slab centre/rotation; "
         "ρ = EPI–CSF agreement in the medial-temporal box, SPM vs scanner) | note | decided (EST) |",
         "|---|---|---|---|---|---|"]
for s in sorted(arm, key=lambda x: (arm[x], x)):
    d, note, when = DEC[s]
    runs = ["learning", "30min", "24h"]
    cr = "; ".join(run_txt(s, r) for r in runs)
    lines.append(f"| {s} | {arm[s]} | **{d}** | {cr} | {note} | {when} |")
n = {}
for s in arm:
    n.setdefault((arm[s], DEC[s][0]), 0)
    n[(arm[s], DEC[s][0])] += 1
lines += ["", "Counts: " + "; ".join(f"{a} {d}: {k}" for (a, d), k in sorted(n.items()))]
open(OUT, "w").write("\n".join(lines) + "\n")
print("\n".join(lines[-3:]))
