# Coregistration check behind the QC decisions (2026-11-21)

These scripts were run on 2026-11-21 on the server copy of the workspace, after the registration and before any ROI or group value. They support the registered visual rule ("participants whose hippocampal region is visibly misaligned are excluded"). The decisions and their reasons are in `qc_records/QC_DECISIONS.md`.

The scripts are the ones that ran; only the hard-coded server path was replaced by `$TOAM`. Run each one with `bash <script>` after `source code/env.sh`. They read the SPM12 derivatives and the raw headers only, never events or responses.

Order:
1. `coregcheck.sh` → `coreg_check.tsv`. For every modelled run, the correction that SPM coregistration applied relative to the scanner coordinates: shift at the slab centre and rotation. For session-1 runs it also gives the disagreement with the learning run.
2. `csfcorr.sh` → `coreg_slab_rho.txt`. Spearman ρ between the mean EPI and the same-session T1 CSF probability over the whole slab, under the SPM coregistration and under the scanner coordinates. Small-FOV arm.
3. `coregfig.sh` → `coreg_native/*_coreg_vs_scanner.png`. Native-slab figures of flagged runs and control runs.
4. `mtlcheck.sh` → `coreg_mtl_rho.tsv` and `coreg_native/*_MTLcrop.png`. The same ρ inside a medial-temporal box (MNI |x| 15–45, y −45 to −5, z −32 to 0 mm, mapped through the inverse deformation `iy_`), plus zoomed crops.
   - The first run stopped on a NaN in a progress message; the fixed version is the one stored here.
5. `mtlcheck_extra.sh` → calibration crops for three included participants. It writes `coreg_mtl_rho_extra_crops.tsv`, whose values equal those in `coreg_mtl_rho.tsv`.
6. `write_qc_decisions.py` builds `QC_DECISIONS.md` from these tables and the decisions.
