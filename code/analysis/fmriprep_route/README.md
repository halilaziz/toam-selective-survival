# fMRIPrep route for RQ3 (written 2026-11-21, after the registration)

This route implements the registered robustness analysis for RQ3 (Reliability and robustness testing): "The MNI-space outputs are smoothed with a 6-mm kernel in SPM12, and the same first-level models are fitted with fMRIPrep's six motion parameters. H3r and H3a are re-estimated with this pipeline. ... The RQ3 result is called robust if both pipelines give the same sign and each estimate lies inside the other's 95% CI."

## Steps, one whole-brain participant at a time
1. `prep_inputs.py` (inside `prep_smooth.sge`):
   - uncompresses the MNI152NLin2009cAsym preprocessed BOLD of the three modelled runs (SPM12 reads only uncompressed NIfTI);
   - writes `rp_fmriprep_*.txt` with fMRIPrep's six motion parameters (mm, radians; the layout of SPM's `rp_*.txt`);
   - makes the explicit first-level mask.
2. `smooth_s6.m` (inside `prep_smooth.sge`): 6-mm smoothing in SPM12 r7771 (prefix `s6`). The unsmoothed uncompressed copies are then deleted.
3. `make_specs.py`: first-level specifications. Each is the SPM-route specification with only the inputs replaced; the conditions, onsets, contrasts and eligibility are unchanged, and the script asserts this.
4. The first level is `matlab/first_level.sge`, unchanged. The ROI and group steps are `run_toam.py roi` and `run_toam.py group`, unchanged.
5. `agree.py` applies the registered agreement criterion to d_z and its 95% CI (decision D6).

## Implementation choice not fixed by the registration
**The explicit mask.** It is grey plus white matter probability > 0.2, taken from fMRIPrep's MNI-space tissue maps of the same participant and resampled to the BOLD grid. This mirrors the authors' grey-plus-white-matter mask (> 0.2) used in the SPM route.

## Outputs
Everything goes to `$TOAM/derivatives/fmriprep_spm/<sub>/`. The fMRIPrep derivatives are only read.
