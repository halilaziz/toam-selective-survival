# Changes to the authors' SPM preprocessing code

Source: github.com/TomW92/TOAM-fMRI at commit `e257c2508319a3d9127320eac2ae8ac52bffe62f` (CC BY 4.0; a full clone is kept in `$TOAM/code/authors`).
Adapted copies live in `functions/` and `preprocessing/`. Every changed line carries a `[TOAM Cn]` comment. The authors' headers are kept; each changed file has a short adaptation note under its header.

## Edits to the authors' files

| # | File (adapted copy) | Line now (original line) | Original | New | Reason |
|---|---|---|---|---|---|
| C1 | `functions/setup_config.m` | 82 (76) | `addpath('/storage/homefs/tw18a205/toolboxes/spm12')` | `addpath(fullfile(toam,'tools','spm12'))`, with `toam = getenv('TOAM')` and an assert (lines 80–81, new) | SPM12 r7771 installed inside TOAM; the UBELIX path does not exist. |
| C2 | `functions/setup_config.m` | 83–85 (77–79) | `fmriPath = '/storage/research/.../data/fMRI/'; basePath = fullfile(fmriPath, seq{1}); config.data.path = fullfile(basePath,'bids');` | `fmriPath = <TOAM>/derivatives/authors_storage_placeholder/`; `arm_ds = struct('hipp','ds006265','wb','ds006266')`; `config.data.path = <TOAM>/raw/<ds>` | The BIDS root of each sequence is now the OpenNeuro clone (hipp = ds006265, wb = ds006266). `fmriPath` only builds behavioural file names (lines 176–189), which preprocessing never opens; the placeholder folder is never created. |
| C3 | `functions/setup_config.m` | 86 (80) | `config.data.workspace = '/storage/workspaces/.../fMRI/<seq>'` | `config.data.workspace = <TOAM>/derivatives/workspace/<seq>` | Workspace path for the FreeSurfer/searchlight entries (lines 192–196). Not used by preprocessing; kept inside TOAM. |
| C4 | `functions/setup_config.m` | 88 (82) and 123 (117) | `tdfread(<participants.tsv>)`, `tdfread(<sub>_ses-1_scans.tsv)` | `readtable(<same file>,'FileType','text','Delimiter','\t')` | `tdfread` is in the Statistics Toolbox and would check out one of the lab's shared Statistics_Toolbox licences for the whole run. `readtable` is base MATLAB and gives the same columns (`participant_id`, `filename`), which the next lines pass through `cellstr` as before. |
| C5 | `functions/setup_config.m` | 151 (145) | `config.data.deriv.folder = fullfile(config.data.path,'derivatives')` | `config.data.deriv.folder = fullfile(getenv('TOAM'),'derivatives')` | Outputs must not be written inside the raw clone. All outputs now go to `TOAM/derivatives/spmMB/<sub>/preproc/<ses>/{anat,func}`, the layout `setup_config.m` (lines 160–166) and the authors' first level expect. |
| C6 | `preprocessing/smallFOV_preprocessing_1.m` | 50 (46) | `save(fullfile(config.data.bold,'1_slicerealign'),'matlabbatch')` | `save(fullfile(config.data.bold,config.strID,'preproc','1_slicerealign'),'matlabbatch')` | One record per participant. The original wrote one file in `spmMB/`, overwritten by every participant, and written at the same time by parallel jobs. Only the saved record changes; the batch that runs is identical. |
| C6 | `preprocessing/smallFOV_preprocessing_2.m` | 216 (212) | `save(fullfile(config.data.bold,'2_restofpreprocessing'),'matlabbatch')` | `save(fullfile(config.data.bold,config.strID,'preproc','2_restofpreprocessing'),'matlabbatch')` | Same as above. |

Not changed: `preprocessing/smallFOV_preprocessing_1s.m`, `functions/realign.m`, `functions/slice_time_correction.m` (byte-identical copies). No parameter of the SPM chain was changed (slice timing, realignment, segmentation, coregistration, normalisation bounding box and voxel sizes, smoothing kernels, masks).

## New files (the authors' versions are SLURM/UBELIX-specific or not public)

| File | Replaces | What it does |
|---|---|---|
| `prep_inputs.sh` | `utilities/gunziploopHIPP.m`, called in `fmri/preprocessing/prepro.sh` line 37 (commented out) and not in the repository | Gunzips (or copies, for the 20 whole-brain ses-2 BOLD files stored as `.nii`) the 2 T1w and 4 BOLD images of one participant to `derivatives/spmMB/<sub>/preproc/<ses>/{anat,func}/<BIDS name>.nii`, then checks each copy's size against its NIfTI header. The BIDS names are kept: the authors' code selects `^sub.*<task>.*\.nii$` and `^sub.*T1w.nii$`, and their plotting code reads `spmMB/sub-60601/preproc/ses-1/anat/wskullStrippedsub-60601_ses-1_acq-t1csmp2ragesag06mmUNIDEN_T1w.nii` (`fmri/plotting/figure_6-7_plot_ers_rois.py` line 43). |
| `matlab/run_subject.m` | the three `srun ... matlab -r "settings; run('.../smallFOV_preprocessing_X(...)')"` lines of `prepro.sh` (39, 40, 42) | Runs `smallFOV_preprocessing_1(subj)`, `_1s(subj)`, `_2(subj, 1)` in that order in ONE MATLAB session, from `preprocessing/` (the authors' scripts add `../functions` relative to `pwd`). SPM is initialised as `setup_config.m` does it (`spm('Defaults','fMRI'); spm_jobman('initcfg')`), and `global initspm` is set so `setup_config.m` does not repeat it. `spm_get_defaults('cmdline', true)` reproduces the authors' `-nodisplay` runs (no graphics windows). The authors' `settings;` call (MATLAB's settings object, no effect on SPM) is dropped. Asserts SPM12 r7771. |
| `matlab/qc_subject.m` | (new) | Header/affine, realignment-parameter and normalisation checks. Writes only to `derivatives/spmMB_qc/<sub>/`. Reads no events or responses. |
| `env_spm.sh` | `module load MATLAB/2021b` in `prepro.sh` line 31 | Paths, write guard, and `ml_exec`: MATLAB R2026a (`/misc/opt/matlab2026a`, the binary behind `/misc/bin/matlab`, with the same licence file) run inside `mathworks/matlab-deps:r2026a` with `-nojvm -singleCompThread`, HOME/TMPDIR in an overlay image inside TOAM, `raw/` bound read-only. |
| `toam_spm.sge` | `prepro.sh` (SLURM array, 20 tasks, 12 GB/CPU, 3.5 h limit) | SGE job `toam_spm`, one participant per job, 1 slot on `all.q@milner`, priority −100, `nice 19`, `ionice -c 3`. Records wall time, peak memory (`/usr/bin/time -v` and a 60 s RSS sampler), disk by output type, and a check that nothing was written to `/tmp`, `/var/tmp` or `/dev/shm`. |
| `submit_pilot.sh`, `subjects_batch.txt` | `participants.tsv` line = `SLURM_ARRAY_TASK_ID + 1` | Pilot submission (first participant of each `participants.tsv`); list of the remaining 38 participants for the array job (arms interleaved). |

## Runtime differences from the authors' environment

- MATLAB: R2026a (26.1.0.3203278) in an Ubuntu 24.04 container. The authors used `MATLAB/2021b` on UBELIX for preprocessing (`prepro.sh` line 31). The host MATLAB on milner crashes during the licence checkout (FlexLM `lc_new_job` segfault under glibc 2.44).
- SPM12: r7771 (GitHub release `r7771`, commit `3085dac`, tarball SHA-256 `5cf7f88f…13cb4`). The authors' SPM12 revision is not recorded in the repository. `/misc/opt/spm12`, which `/misc/bin/matlab` puts on the path, is r7219 and is not used.
- `-nojvm` instead of `-nodisplay`. SPM's batch code needs no Java.

## Site configuration (2026-11-14)
The SPM12 preprocessing (all 40 participants) and the fMRIPrep run were started with the scripts of commit `48d47b1`, in which the workspace root, the SGE queue, the MATLAB binary and licence and the FreeSurfer licence were written into the scripts. From commit `prereg-v1` on, `code/env.sh` sets `$TOAM` to the folder that contains `code/` and reads these values from `code/site.local.sh` (not tracked; template `code/site.example.sh`), and the SGE scripts receive `TOAM`, the queue and the log folder from the `qsub` command. The values on our server are unchanged, so the computation is unchanged.

## fMRIPrep option (2026-11-15)
The first fMRIPrep submission (job 150696, 2026-11-15) stopped at argument parsing for all 20 participants, before any processing: fMRIPrep 25.2.7 no longer has the authors' `--bold2t1w-init register`. `code/fmriprep/fmriprep_wb.sge` now uses `--bold2anat-init t1w`, which in 25.2.7 "forces use of the T1w" for the initial BOLD-to-anatomical registration: the same choice as the authors' (registration rather than header). No other option changed.
