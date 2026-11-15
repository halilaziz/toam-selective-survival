# Preregistered analyses (H1–H3)

This folder holds the code for RQ1–RQ3 of `TOAM_preregistration_HAV_v2.docx` (OSF "Secondary Data Preregistration"). It was written and tested on synthetic data only, before the registration. **No TOAM outcome has been computed with it.** `run_toam.py` refuses real data until `--registered <OSF URL or DOI>` is given.

## Layout
- **`toam_analysis/events.py`:** reads the released events. It returns one row per participant × item × test (30 min, 24 h), with confidence, correctness, the faceRecog onset, session and run; the 24-h rows also carry the recognition status.
- **`toam_analysis/exclusions.py`:** the authors' item rules (table below).
- **`toam_analysis/classes.py`:** trajectory classes SG, FO, SS, other and excl, and the memorability index *m* in its 30-min, 24-h and mean versions.
- **`toam_analysis/h1.py`:** H1a–H1c and the robustness checks.
- **`toam_analysis/stats.py`:** the statistics:
  - one-sided t tests;
  - Holm correction;
  - d_z with a 95% CI from noncentral-t inversion;
  - JZS Bayes factors, two-sided BF10 and one-sided BF+0, with r = √2/2;
  - Tukey–McLaughlin 20% trimmed-mean tests;
  - percentile bootstrap.
- **`toam_analysis/glm_spec.py`:** the first-level model as a JSON spec per participant:
  - the authors' conditions plus the preregistered split;
  - onsets;
  - H2/H3 contrasts and the ≥ 4 trials rule.
- **`matlab/`:** runs the spec in SPM12, adapted from the authors' `multi_session_first_level.m` (CC BY 4.0; see `CHANGES.md`).
  - `toam_first_level.m` is the model itself.
  - `run_first_level.m` initialises SPM12 r7771.
  - `first_level.sh` runs it in the MATLAB container with `ml_exec`.
- **`toam_analysis/roi.py`:** 6-mm sphere ROIs, plus the slab-coverage rule for the anatomical ROI.
- **`toam_analysis/h2h3.py`:** RQ2 group tests, Table 3 decisions, composition share (10,000-resample bootstrap), RQ3 estimation and the pipeline-agreement criterion.
- **`toam_analysis/synthetic.py`:** synthetic data in the exact released format, with ground truth.
- **`tools/synthetic_glm.py`:** an end-to-end check of the MATLAB step on synthetic NIfTI.
- **`tests/`:** the pytest suite, 70 tests.

## Environment
Python 3.13.15 in a project virtual environment. `requirements.txt` holds the direct pins and `requirements-lock.txt` the full freeze.

```bash
cd code/analysis && uv venv --python 3.13 .venv && VIRTUAL_ENV=.venv uv pip install -r requirements-lock.txt
.venv/bin/python -m pytest
```

## Order of steps on real data (only after the OSF registration)
`$REG` is the OSF registration URL or DOI. `$T` is the workspace root.

1. **H1.** Behaviour only; it can run as soon as the plan is registered.
   ```bash
   .venv/bin/python run_toam.py h1 --bids-hipp $T/raw/ds006265 --bids-wb $T/raw/ds006266 \
     --logs $T/code/authors/data/behavioral_data --out $T/results/h1 --registered $REG
   ```
2. **Quality-control overlays.** Before any GLM, overlay each participant's normalised mean EPI on the MNI template and on the normalised T1, then archive the decisions (prereg Part 5). In the small-FOV arm the authors' `wskullStripped` covers only the slab, because of SPM12's Normalise: Write masking (see `SPM_PILOT_REPORT.md`).
3. **First-level specs.**
   ```bash
   .venv/bin/python run_toam.py glm-spec <same inputs> --deriv $T/derivatives/spmMB --out $T/results/glm_specs --registered $REG
   ```
4. **First level per participant.** Run `bash code/analysis/matlab/first_level.sh $T/results/glm_specs/spec_sub-XXXXX.json`, at most 3 at once (MATLAB seats).
5. **ROI values.**
   ```bash
   .venv/bin/python run_toam.py roi --specs $T/results/glm_specs --out $T/results/roi_values.csv
   ```
6. **Group results.**
   ```bash
   .venv/bin/python run_toam.py group --roi-table $T/results/roi_values.csv --out $T/results/h2h3.json
   ```
7. **Still to write.** The secondary hippocampal-head ROI and the fMRIPrep route for RQ3 (see "Not yet implemented").

## Where each rule comes from (TomW92/TOAM-fMRI e257c25)

| Rule | Source |
|---|---|
| Item exclusion, immediate recall correct | `behavior/r_utils.R:186` (`first.retrieval == "correct"`) |
| No sure + incorrect at 30 min, 24 h or recognition | `behavior/r_utils.R:192–195` |
| Valid answers: buttons 2/3, ratings 2/3/4 | `behavior/r_utils.R:201–209` |
| Recognition RT > 100 ms (not applied by default, Q1) | `behavior/r_utils.R:185` |
| Logfile columns (immediate recall, buttons) | `behavior/01_fmri_create_dfs.R:54–55, 66–67, 76–80` |
| Released events = 'maxTrials' version; status suffix; 'NA' | `behavior/04_fmri_onsets.R:352–381, 639–690, 782–799` |
| Aborted-acquisition trials already removed | `behavior/04_fmri_onsets.R:45–54` |
| Rating 4/3/2 = sure (consc), unsure (between), guess (unconsc) | `04_fmri_onsets.R:328–331`; `contrasts_delret.m:113–119` |
| Learning-run conditions (subsequent memory) | `fmri/1st_level/contrasts/contrasts_enc_subsequent.m:29–31, 47, 113–125` |
| 30-min conditions, 5 event types | `fmri/1st_level/contrasts/archive/contrasts_ret_twoEvents.m:29–31, 46–48, 152–153` |
| 24-h conditions, 9 event types; recognition events take the retrieval status | `fmri/1st_level/contrasts/contrasts_delret.m:29–31, 46–48, 121–122` |
| Odd-even run: one condition 'number' | `fmri/1st_level/contrasts/contrasts_consolidation.m:13–17` |
| Sessions, onset version 'maxTrials', scans, renaming | `fmri/1st_level/contrasts/contrast_multi_session.m:30–39, 67–77, 100` |
| Model settings | `fmri/1st_level/multi_session_first_level.m:43–92` (see `CHANGES.md`) |
| TR, slices, mask, session signs | `fmri/functions/setup_config.m:141–142, 159, 198–207, 215–216` |

The released events lack the immediate-recall result and the button codes. They come from the authors' public logfiles (`data/behavioral_data`), the same files their `01_fmri_create_dfs.R` reads.

## What the tests show (70 passed, 2026-11-15)

**Statistics (`test_stats.py`)**
- t and p equal scipy's.
- BF10 reproduces the published BayesFactor value for the paired `sleep` data (17.25888).
- BF10 agrees between two independent formulas (Rouder integral and noncentral t) and with pingouin.
- BF+0 and BF−0 average to BF10.
- The d_z CI satisfies its defining equations.
- Holm matches a hand computation and pingouin.
- The trimmed-mean test matches a hand computation.

**Events (`test_events.py`)**
- Every trial_type form parses, including 'NA'.
- The reader returns the ground truth: status, onsets, recognition status and an item missing at one test (the crash case).

**Exclusions (`test_exclusions.py`)**
- Each rule on a constructed case, including a late response the authors recovered (kept) and the RT rule (off by default).
- On the synthetic set, exclusions equal an independent computation from the ground truth.

**Classes and m (`test_classes.py`)**
- Table 2 classes.
- *m* by hand.
- No self-leakage: changing a participant's own answers leaves their *m* unchanged.
- Excluded trials leave the denominator.
- z-scores within each participant.
- The secondary versions.
- *m* tracks the true memorability.

**H1 (`test_h1.py`)**
- Set differences by hand.
- H1a and H1c are detected in a world where memorability drives survival.
- In a null world the false-positive rate stays at or below 0.2 over 30 simulated datasets (nominal 0.05).

**First-level spec (`test_glm_spec.py`)**
- The authors' condition lists: 20, 1, 25 and 45 conditions, in order.
- The split, in place.
- Every correct-guess trial lands in exactly one part, with the right onsets.
- Recognition events follow the retrieval status.
- False memories and NA trials are not modelled.
- The renaming rule.
- Contrast weights.
- The ≥ 4 trials rule.
- The optional consolidation session and the JSON round trip.

**ROIs (`test_roi.py`)**
- Exact voxel count of a sphere.
- The mean of a linear field, with spheres weighted equally.
- NaN coverage handling.
- The 50% rule.

**Group results (`test_group.py`)**
- The Table 3 rules.
- The composition share.
- Pipeline agreement.
- End to end on beta-level simulations: the selective-survival world gives "Selective survival supported" and the trace-change world gives "Trace change supported".

**Runner (`test_runner.py`)**
- Real data are refused without an OSF registration.
- Synthetic and real inputs are never mixed.
- The full CLI runs on synthetic data.

**MATLAB step (`tools/synthetic_glm.py`, run on milner 2026-11-15 in `TOAM/tmp/synthetic_glm`)**
- SPM12 r7771 specified, estimated and wrote H2r, H2a and H2b for a synthetic participant with 3 sessions.
- The known signal had FO amplitude 3 and every other condition 1.
- In the ROI, H2a = 0.22 against H2b = 28.19, i.e. ≈ 0.
- H2r/H2b = 0.341 against the expected n_FO/N_24 = 0.333.

## Not yet implemented
- **Secondary RQ2 ROI.** `roi.anatomical_roi_mean` applies the coverage rule. The masks themselves are not made yet; that needs FreeSurfer 7 `segmentHA_T1` on each T1 and a warp with the participant's SPM12 deformation, as in the authors' `normalisation_spm.m`.
- **fMRIPrep route for RQ3.** Still needed: 6-mm smoothing of the MNI outputs, a spec variant pointing at the fMRIPrep files and its six motion parameters, and a brain mask. The agreement criterion is implemented (`h2h3.pipelines_agree`). The fMRIPrep run is still in progress.

## Questions for Halil (implementation choices that the plan does not settle)
- **Q1. Recognition RT rule.** `r_utils.R:185` drops items with a recognition RT ≤ 100 ms, but the preregistered list does not name this rule. The default leaves it out; `--recog-rt-rule` applies it.
- **Q2. Excluded items in the GLM.** The authors' GLM used all trials ('maxTrials', `contrast_multi_session.m:35–37`), while the plan excludes items.
  - Implemented: excluded items' correct-guess and correct-sure faceRecog trials form an `_excl` part of the split, so no preregistered contrast contains them. All other regressors are unchanged.
  - The alternative is to put them into `_other`. H2r would then use C1's exact trial set, but H2r and H2a would rest on different item sets.
- **Q2b. 'All items' terms of H2r and H3r.** They are the count-weighted sum of the split parts, which estimates the unsplit regressor. For these terms, the ≥ 4 trials rule is applied to the unsplit total, not to each part.
- **Q3. Consolidation run.** It is session 2 in the authors' model, but its onsets are not public and the released dataset has no events file for it. Implemented: the run is left out of the model. The alternatives are to keep it with motion regressors only, or to ask the authors for the onsets.
- **Q4. Late responses at immediate recall.** The authors recovered late immediate-recall responses from raw logs that are not public. A few more items may therefore be excluded here than in their data; the difference will be reported.
- **Q5. Which Bayes factor to report.** The plan says "JZS Bayes factors, r = √2/2" for one-sided tests. Both BF10 and BF+0 are written. Which one is the registered index? BF+0 matches the one-sided tests.
- **Q6. Agreement criterion for RQ3.** The two pipelines are compared on d_z and its 95% CI, because the raw scales may differ between pipelines.
- **Q7. Sure split by arm.** The correct-sure split is made only in the whole-brain arm (the plan says it is "for RQ3").
- **Q8. A primary sphere outside the slab.** If one primary sphere has no coverage in a participant, that participant is missing for the contrast and is reported. The 50% rule is applied to the anatomical ROI only, as written.
- **Q9. Minor details.**
  - H1: a participant with an empty item set is left out of that test (N is reported).
  - *m* is z-scored with the population SD.
  - A 'valid trial' for *m* is a trial whose item is not excluded and that has a status.
  - 'Correct trials only' means correct at the defining test(s); for H1c, both tests.
  - In the composition share, each mean is taken over the participants eligible for that contrast.
