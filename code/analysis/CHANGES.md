# First-level model: differences from the authors' code

Source: github.com/TomW92/TOAM-fMRI, commit `e257c25` (CC BY 4.0): `fmri/1st_level/multi_session_first_level.m` and `fmri/1st_level/contrasts/` (`contrast_multi_session.m`, `contrasts_enc_subsequent.m`, `contrasts_consolidation.m`, `archive/contrasts_ret_twoEvents.m`, `contrasts_delret.m`).
`matlab/toam_first_level.m` is adapted from `multi_session_first_level.m` and stays under CC BY 4.0 (`matlab/LICENSE_authors_CC-BY-4.0.txt`). Its comments give the line of the authors' file for every setting.

## Unchanged
These settings are the authors':
- **Timing:** units in seconds; TR and microtime `fmri_t = nslices`, `fmri_t0 = nslices/2` (l.73–76).
- **Basis and scaling:** canonical HRF without derivatives (l.79); `volt 1`, `global None` (l.80–81).
- **Masking:** `mthresh -Inf` (l.77) and the explicit mask `crossSessionWhiteandGreyMatterMask*` (l.83–84; `setup_config.m:159`).
- **Model:** AR(1) (l.85) and classical estimation (l.92).
- **Events and nuisance:** event duration 0 (l.61); one rp_ motion file per session (l.68); 128 s high-pass filter (l.69).
- **Scans:** `^s6wra.*<task>.*\.nii$` (`contrast_multi_session.m:39, 100`).
- **Session order:** forgetexp, consolidation, retrieval, forgetexp (`contrast_multi_session.m:30–33`).
- **Condition naming:** a name already used in an earlier session gets ' <session sign>' (`contrast_multi_session.m:67–77`).
- **Conditions:** event × {correct, incorrect} × {consc, unconsc, between}, without incorrect + consc (`contrasts_*.m`, lines 29–31 and 46–48).
- **Status rule:** in the 24-h run, every event of a trial takes the trial's retrieval status, including the recognition events (`contrasts_delret.m:121–122`).

## Changes
1. **Onsets come from the released events.** The authors read onset tables from `utilities/eventFiles/*.csv` (`setup_config.m:170–176`), which are not public. Those tables come from the same 'maxTrials' rows as the released events (`04_fmri_onsets.R:379–381, 688–690, 797–799`), and the released onsets are rounded to 0.01 s. `toam_analysis/glm_spec.py` rebuilds every condition from the events and writes a JSON spec that MATLAB reads.
2. **Preregistered split.** At each test, `faceRecog_correct_unconsc` becomes `_SG`, `_FO`, `_other` and `_excl`. In the whole-brain arm, `faceRecog_correct_consc` also becomes `_SS`, `_other` and `_excl`. The `_excl` part holds items excluded by the item rules (README, Q2), so they enter no preregistered contrast; every other regressor still holds them, as in the authors' model.
3. **Empty conditions are left out.** The authors kept them and only warned. An all-zero column changes no other estimate and no degree of freedom.
4. **Consolidation run.** Its onsets (the authors' `consolidation` table) are not public, and the released dataset has no events file for that run. The run is left out of the model unless the onsets are supplied (README, Q3).
5. **Contrasts.** Only the preregistered contrasts (H2r, H2a, H2b; H3r, H3a) are computed, by regressor name, after estimation. SPM12 r7771 calls the T-contrast field `weights`; the authors' code used `convec`.
6. **Paths and parameters.** These come from the JSON spec. TR and slice count are read from the participant's first ses-1 BOLD JSON, as `setup_config.m:141–142, 198–207` does. The output folder is `derivatives/spmMB/<sub>/l1_toam_prereg_s6wr`, following the authors' `l1_<name>_s6wr` (l.43).
7. **Software.** MATLAB R2026a runs in the `mathworks/matlab-deps:r2026a` container (`code/spm_prepro/env_spm.sh`) with SPM12 r7771. The authors ran MATLAB 2021b on their cluster.
