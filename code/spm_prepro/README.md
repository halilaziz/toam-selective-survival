# SPM12 preprocessing of TOAM (adapted from the authors' code)

Preprocessing only: no first-level GLM, contrasts, ROI extraction or anything that uses responses, ratings or accuracy. The study's analyses wait for the preregistration.

## Attribution
The SPM preprocessing code in `functions/` and `preprocessing/` is from **Willems, Zervas, Brogli, Rabe, Federspiel & Henke**, *TOAM - Trajectory of a Memory Trace*: github.com/TomW92/TOAM-fMRI, commit `e257c2508319a3d9127320eac2ae8ac52bffe62f`. Authors of these files: Mirko Bristle and Tom Willems. It is licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**, https://creativecommons.org/licenses/by/4.0/; the licence text is `LICENSE_authors_CC-BY-4.0.txt`.
- Preprint: bioRxiv 10.1101/2025.06.02.656652.
- Data: OpenNeuro ds006265 (small-FOV) and ds006266 (whole-brain), CC0, tag 1.0.2.

Changes to their files are minimal (paths, the `.tsv` reader, where the batch record is saved). Every one is listed in `CHANGES.md`, marked `[TOAM Cn]` in the code, and noted under each changed file's original header. The other files here (`prep_inputs.sh`, `env_spm.sh`, `toam_spm.sge`, `submit_pilot.sh`, `matlab/run_subject.m`, `matlab/qc_subject.m`) are new and belong to the THOUGHTS project.

## Layout (inside the workspace root `$TOAM`)
- **Code:** `code/spm_prepro/`. A full clone of the authors' repository is kept in `code/authors` (not part of this repository).
- **Software:** SPM12 r7771 in `tools/spm12`; the MATLAB container `tools/containers/matlab-deps_r2026a.sif`.
- **Inputs (copies):** `derivatives/spmMB/sub-<id>/preproc/ses-<n>/{anat,func}/<BIDS name>.nii`.
- **Outputs:** next to the inputs, under the authors' prefixes:
  - `a`: slice-timed;
  - `r`, `mean`, `rp_*.txt`: realigned;
  - `c1/c2/c3`, `m`, `y_`, `iy_`, `skullStripped`, `brainMask_`, `rf*`, `wrf*`, `w*`: anatomy and masks;
  - `wra`, `s6wra`, `s3wra`, `s1ra`: normalised and smoothed BOLD;
  - `derivatives/spmMB/sub-<id>/preproc/crossSessionWhiteandGreyMatterMaskMNI.nii`.
- **QC:** `derivatives/spmMB_qc/sub-<id>/`.
- **Logs:** `logs/spm/` (SGE output) and `logs/spm/sub-<id>/` (timing, memory, disk, MATLAB log, `DONE`).

## Run
```bash
source code/env.sh                       # sets $TOAM and reads code/site.local.sh ($SGE_QUEUE, $MLBIN, $MLLIC)
# pilot (first participant of each participants.tsv)
bash code/spm_prepro/submit_pilot.sh
# remaining 38 participants (we ran at most 3 at once)
qsub -N toam_spm -v TOAM -q "$SGE_QUEUE" -pe smp 1 -p -100 -t 1-38 -tc 3 \
     -wd "$TOAM/logs/spm" -o "$TOAM/logs/spm/" -e "$TOAM/logs/spm/" \
     "$TOAM/code/spm_prepro/toam_spm.sge"
```
Each job:
1. `prep_inputs.sh`;
2. MATLAB R2026a + SPM12 r7771: `run_subject(<id>)`, which runs the authors' `smallFOV_preprocessing_1`, `_1s`, then `_2(<id>, 1)`, as in their `prepro.sh`; then `qc_subject(<id>)`.

MATLAB runs in the `matlab-deps` container because the host MATLAB crashed in its licence check on our servers. Each running job needs a free MATLAB licence seat, so keep the number of concurrent jobs below the seats you can use. A job retries every 5 min when no seat is free.
