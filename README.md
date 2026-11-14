# Selective survival or trace change? A re-analysis of the TOAM 7T dataset

This repository holds the code for a preregistered secondary analysis of TOAM (Trajectory of a Memory Trace; Willems et al., 2025). The study asks whether overnight differences in retrieval activity between a 30-minute and a 24-hour memory test reflect change within memory traces, or a change in which items are still remembered (selective survival). Each test's response categories (sure, unsure, guess) contain different items, and the published analyses do not hold item composition constant.

## Status (November 2026)
- **Preregistration:** [TOAM_preregistration_HAV_v2.docx](TOAM_preregistration_HAV_v2.docx), the version submitted to OSF (Secondary Data Preregistration template). The code at registration is tag `prereg-v1`. OSF link: added after registration.
- **Data:** downloaded and verified (266/266 files match their SHA-256).
- **Preprocessing:** SPM12 preprocessing is running. The fMRIPrep robustness run is queued.
- **No outcome analysis has been run.** The confirmatory analyses start only after the preregistration is posted.

## Data and source code
- **Data:** OpenNeuro [ds006265](https://openneuro.org/datasets/ds006265) (small-field-of-view MTL arm, 20 participants) and [ds006266](https://openneuro.org/datasets/ds006266) (whole-brain arm, 20 participants), snapshot 1.0.2, CC0. The data are not included here.
- **Authors' analysis code:** [TomW92/TOAM-fMRI](https://github.com/TomW92/TOAM-fMRI), commit `e257c25`, CC BY 4.0.

## Pipeline
1. **Download** (`code/setup.sh`, `code/make_aria2_input.py`, `code/start_download.sh`, `code/verify.py`). Both datasets are cloned at tag 1.0.2, and the imaging files are fetched from OpenNeuro's S3 bucket. Each file is checked against the SHA-256 in its git-annex key.
2. **Structure check** (`code/structure_check.py`). It counts participants and items and lists the event vocabulary. It prints no outcome data.
3. **SPM12 preprocessing** (`code/spm_prepro/`). This is the authors' chain: slice timing, realignment, coregistration, unified segmentation and normalisation, then smoothing.
   - It is adapted with path changes only; every change is listed in `code/spm_prepro/CHANGES.md`.
   - Software: SPM12 r7771 with MATLAB R2026a, run in the `mathworks/matlab-deps:r2026a` container; the Sun Grid Engine wrapper is `toam_spm.sge`.
   - `qc_pilot.py` and `qc_overlay.py` check preprocessing quality without touching outcome data.
4. **Robustness pipeline for the whole-brain arm** (`code/fmriprep/`). fMRIPrep 25.2.7.
5. **Preregistration document** (`code/docs/build_prereg_docx.py`). Builds the preregistration .docx.

**Running elsewhere:** `code/env.sh` sets the workspace root `TOAM` to the folder that contains `code/`. Copy `code/site.example.sh` to `code/site.local.sh` (not tracked) and set the SGE queue, the MATLAB binary and licence, and the FreeSurfer licence. The SPM12 preprocessing and the fMRIPrep run were started with commit `48d47b1`, before these settings moved out of the scripts; see `code/spm_prepro/CHANGES.md`.

## Licences
- **Our code:** MIT (see [LICENSE](LICENSE)).
- **Adapted files:** the files in `code/spm_prepro/functions/` and `code/spm_prepro/preprocessing/` come from TomW92/TOAM-fMRI and remain under CC BY 4.0.
- **Documents** (the preregistration): CC BY 4.0.

## Citation
Please cite the TOAM preprint and datasets:

Willems, T., Zervas, K., Brogli, L. S., Rabe, F., Federspiel, A., & Henke, K. (2025). *Neural traces of forgotten memories persist in humans and are behaviorally relevant* [Preprint]. bioRxiv. https://doi.org/10.1101/2025.06.02.656652
