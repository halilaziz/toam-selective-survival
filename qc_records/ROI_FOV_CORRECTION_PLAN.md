# RQ2 ROI restricted to the field of view of both retrieval runs: specification before running

- **Written** 2026-11-22 13:15 EST.
- **Already read at this point:**
  - the primary RQ2 values computed with `run_toam.py roi` (`results/rq2_spm/group_hipp.json`: H2r d_z 1.02, H2a 0.76, H2b −0.15, "Trace change supported");
  - the sensitivity values (`results/sensitivity_coregfix/`).
- **Not yet computed:** the corrected values below.

## Problem found after the primary values were read
- **The rule.** Implementation note 8 counts a sphere voxel as covered when it lies inside the slab.
- **The assumption in `roi.py`.** It counted a voxel as covered when it is finite in the contrast image, assuming that SPM's analysis mask is the intersection of the sessions. That assumption is wrong for this pipeline:
  - the authors' explicit mask is the union of two session masks (`(i1 + i2) >= 1`, built from the learning-run and 24-h means), so the 30-minute field of view never enters it;
  - the normalised data are int16, with exact zeros outside the field of view (checked);
  - `mthresh = -Inf`.
- **Consequence.** A voxel outside the 30-minute slab but inside the 24-hour slab enters H2r and H2a as "24 h minus a zero-data estimate", which biases them towards the 24-hour estimate. The reverse case biases them the other way. H2b compares two conditions within the 24-hour run and is not affected.
- **Size, measured without any contrast value** (fraction of sphere voxels inside each run's field of view):
  - Most participants: 100% in both runs for both spheres.
  - sub-65837, left sphere: 80% inside the 30-min slab, 100% inside the 24-h slab.
  - sub-66299, left sphere: 88% and 93%.
  - sub-64763, left sphere: 100% and 93%.
  - Others: 96–99%.

## Correction
- Each sphere is restricted to voxels that are non-zero in the first volume of both retrieval runs' normalised images (`wra*`, the input of the 6-mm smoothing).
- Everything else is unchanged: 6-mm spheres at the published peaks, mean over voxels, spheres averaged with equal weight, a participant missing when a sphere keeps no voxel (note 8), the four-trial rule, and `run_toam.py group` for tests, Table 3 decision and composition share.
- **Code:** `code/analysis/tools/roi_fov.py`. It also writes a per-sphere coverage table.
- **Run on:**
  - (a) the primary set (16 participants) → `results/rq2_spm_fov/`;
  - (b) the sensitivity set (20 participants) → `results/sensitivity_coregfix/roi_fov/`.

## Caveat, measured but not corrected
The 6-mm smoothing mixes the zeros outside a slab into voxels near its edge, as in the authors' pipeline. For each run and each sphere we report the ratio of the smoothed to the unsmoothed mean intensity over the kept voxels. A ratio below 1 in only one run marks a participant whose estimate for that run is damped.

## Reporting
- Both versions are reported: `run_toam.py roi` as implemented, and the field-of-view version.
- The field-of-view version is the one that implements note 8 as intended. It is our recommendation for the RQ2 result, listed in the deviations table with the reason above.
- Which version the paper calls primary is Halil's decision.
- No other ROI variant is run unless it is specified here first.
