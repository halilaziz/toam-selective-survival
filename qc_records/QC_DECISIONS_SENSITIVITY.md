# QC decisions for the coregistration sensitivity analysis (not preregistered)

- **Plan:** `SENSITIVITY_COREG_PLAN.md` (commit 1476836).
- **Decided** 2026-11-22 13:04 EST from the overlays alone. Not yet read at that point: any contrast value of these four participants, and any H2 value of the primary analysis (the H3 SPM-route estimates of the whole-brain arm had been read).
- **Images:** `results/qc_overlays_coregfix/sub-*_qc.png`, the same overlay tool and views as the primary record, with `TOAM_QC_DERIV=derivatives/spmMB_coregfix`. Table: `qc_summary_coregfix.tsv`.
- **Native-space alignment:** the "scanner coordinates" rows of `results/qc_overlays_v2/coreg_native/*` are exactly the alignment used here.
- **Rule:** the registered one. A participant whose hippocampal region is visibly misaligned stays excluded.

| sub | decision | note |
|---|---|---|
| sub-60601 | include in the sensitivity analysis | The 30-min and 24-h slabs now agree with each other, and the ventricle in the 30-min slab sits where it does at 24 h. The slab covers both peaks, and the hippocampal contours follow each other. |
| sub-62162 | include in the sensitivity analysis | Both slabs cover both peaks along the hippocampus; contours follow each other. The low share of the slab inside the TPM brain (0.53–0.55) comes from a low slab position, not from misalignment. |
| sub-67823 | include in the sensitivity analysis | Both slabs cover both peaks; the temporal horn lies at the right peak in both sessions; contours follow each other. |
| sub-67903 | include in the sensitivity analysis | Both slabs cover both peaks; contours follow each other. Banding in the EPI is an image-quality problem, not a misalignment, and is reported. |

**Consequence:** the sensitivity analysis uses the 16 primary participants plus these 4 (N ≤ 20), with the four-trial rule as registered.
