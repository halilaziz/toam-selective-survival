# Sensitivity analysis: repaired coregistration for the four excluded small-FOV participants (not preregistered)

- **Specified** 2026-11-21 16:08 EST, before any H2 or H3 value was read. No ROI or group command has been run on real data. The only first-level output read so far is the control contrast of the sub-60100 pilot.
- **Requested by** Halil ("hepsini yap", 2026-11-21), after reading the QC record (`QC_DECISIONS.md`).

## Question
The primary RQ2 analysis excludes four of the 20 small-FOV participants: sub-60601, sub-62162, sub-67823 and sub-67903. The authors' SPM coregistration misplaced their EPI relative to their T1 (`QC_DECISIONS.md`). This analysis asks whether the RQ2 results depend on that exclusion.

## Repair
For all three modelled runs of these four participants (learning, 30-minute test, 24-hour test), the SPM coregistration estimate is replaced by the scanner coordinates. The EPI is taken as aligned to the same-session T1 through the shared scanner frame:
- The pipeline leaves the T1 headers unchanged.
- Realignment does not move the first volume; the first row of the motion parameters is zero.
- The header of each run's mean image, and of every realigned frame, is set to the voxel-to-world matrix of the run's unprocessed first volume. This undoes exactly what the coregistration estimate wrote.

Reasons:
1. In the whole-brain arm, where coregistration is reliable, SPM's correction to the scanner coordinates is at most 2.9 mm and 3.7°.
2. For these four participants, the EPI–CSF agreement in the medial-temporal box is higher in scanner coordinates (ρ 0.21–0.39) than under SPM (−0.01 to 0.28).
3. One rule per participant, applied to all of the participant's runs, avoids mixing two alignments within a participant.

## Everything else as in the primary analysis
- **Preprocessing.** The rest of the authors' step 2 is unchanged: reslicing of the T1 masks to the mean image, normalisation with the participant's existing deformation field (0.8-mm voxels, the authors' bounding box, 4th-degree B-spline), binarised masks, the cross-session mask, and 6-mm smoothing.
  - Not written: the odd-even run (not modelled, implementation note 1), the native 1-mm smoothing and the MNI 3-mm smoothing. The first level uses none of them.
- **First-level model.** The specification is identical; only the derivative paths change, and `make_sens_specs.py` asserts this.
- **ROI and group analysis.** Same code, same four-trial rule.

## Code and outputs
- **Code:** `code/spm_prepro/sensitivity/`.
  - `smallFOV_preprocessing_2_scannercoords.m`: a copy of the step-2 script with four changes, marked [SENS].
  - `run_sens_subject.m` and `run_sens_prepro.sge`: run it.
  - `prepare_tree.sh`: copies the step-2 inputs; `derivatives/spmMB` is only read.
  - `make_sens_specs.py`: writes the first-level specifications.
- **Outputs:** `derivatives/spmMB_coregfix/`, `results/glm_specs_coregfix/`, `results/qc_overlays_coregfix/` and `results/sensitivity_coregfix/`.

## Quality control
- The repaired runs get the same overlays as the primary analysis: the MNI overlay of the normalised mean EPI with the TPM and the participant's grey matter, plus the native-space check.
- A participant whose hippocampal region is still visibly misaligned after the repair stays excluded from this analysis, and this is reported.
- These QC decisions are recorded before any contrast value of the repaired participants is read.

## Analysis and reporting
- **Analysis.** The RQ2 group tests: H2r, H2a and H2b, the Table 3 decision rules and the composition share. They use the 16 primary participants plus the repaired participants that pass QC, at most 20. RQ3 and RQ1 are not affected.
- **Reporting.**
  - The primary analysis is the registered one (N = 16), and its Table 3 decision is the answer to RQ2.
  - The sensitivity result is reported beside it, labelled unregistered and exploratory, with N, estimates and decisions. Any difference in the Table 3 decision is stated, not resolved in favour of either analysis.
  - No other variant (another repair method or another participant set) is run unless it is specified in this file first.
