# RQ2 secondary ROI (anatomical hippocampal head): specification before computing

- **Written** 2026-11-22 14:17 EST, while FreeSurfer runs (array 150768) and before any value of this ROI exists.
- **Already known at this point:** the primary RQ2 results (field-of-view version, "Trace change supported"). This is why the details below are fixed now.

## Registered text
"The secondary ROI for RQ2 is the anatomical hippocampal head from the FreeSurfer 7 hippocampal subfield segmentation of each participant's T1 image, warped to MNI space with the participant's SPM12 deformation, as in the authors' normalisation_spm.m. A participant is included only if at least 50% of the ROI voxels lie inside the slab's field of view in both sessions."

## Implementation
1. **Segmentation.** FreeSurfer 7.2.0, the FreeSurfer 7 release on the server.
   - `recon-all -all` on the session-1 SPM bias-corrected T1 (`msub-*T1w.nii`). The authors' normalisation_spm.m states that recon-all was run on the bias-corrected image.
   - Then `segmentHA_T1.sh` (subfield atlas v21). Job: `code/analysis/anat_roi/fs_hippo.sge`.
2. **Head label.** HP_head (label 232) in `?h.hippoAmygLabels-T1.v21.HBT.mgz`, both hemispheres combined into one bilateral mask.
3. **Native mask.** The binary head mask (`mri_binarize --match 232`) is resampled to the grid of the bias-corrected T1 with `mri_vol2vol --regheader --interp nearest`.
4. **Warp, with the settings of the authors' normalisation_spm.m.** SPM12 r7771 Normalise: Write.
   - Deformation: the session-1 deformation `y_` of the same T1.
   - Bounding box [−90 −126 −72; 90 90 108], 0.8-mm voxels, 4th-degree B-spline, prefix `w`.
   - Then binarisation at i1 > 0.2 (imcalc), the authors' threshold.
   - The output lies on the grid of the first-level contrast images (asserted).
5. **Field of view.** The same definition as the primary ROI correction (ROI_FOV_CORRECTION_PLAN.md): voxels non-zero in the first volume of each retrieval run's normalised images (`wra*`).
   - A participant is included only if at least 50% of the mask voxels lie inside the 30-min field of view and at least 50% inside the 24-h field of view (the registered rule).
   - The ROI value is the mean contrast over the mask voxels inside both fields of view.
6. **Contrasts and tests.** H2r, H2a and H2b, with the same tests as the primary ROI (`run_toam.py group`), on the 16 participants included in the primary analysis. This ROI is a registered robustness check: its results are reported beside the primary ROI, and the Table 3 decision is taken on the primary ROI only.

No other variant (another label, threshold, session or hemisphere split) is run unless it is specified here first.
