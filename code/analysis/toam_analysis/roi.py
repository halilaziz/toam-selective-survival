"""ROI extraction from first-level contrast images (preregistration Part 3, "Neural variables").

Primary RQ2 ROI: two 6-mm spheres at the published hippocampal peaks, averaged across hemispheres.
RQ3 ROI: 6-mm spheres at the peaks of the three Table S8 clusters that survive cluster-level FWE, averaged.
Secondary RQ2 ROI: the FreeSurfer 7 hippocampal head warped to MNI; a participant counts only if >= 50% of its voxels
lie in the slab in both sessions (anatomical_roi_mean; the masks are made after registration, see README).
SPM writes NaN outside the analysis mask, which is the intersection of all sessions, so 'finite' = covered.
"""
from __future__ import annotations

import numpy as np
import nibabel as nib

RADIUS_MM = 6.0
RQ2_PEAKS = ((-27, -16, -14), (39, -22, -12))                 # Table S9 (small-FOV arm)
RQ3_PEAKS = ((-28, -44, 42), (-38, -2, 22), (32, 12, 36))     # Table S8 clusters with cluster-level p(FWE) < .05


def sphere_mask(img: nib.spatialimages.SpatialImage, centre_mm, radius_mm: float = RADIUS_MM) -> np.ndarray:
    """Voxels whose centre lies within radius_mm of centre_mm (world coordinates of the image affine)."""
    shape = img.shape[:3]
    ijk = np.indices(shape).reshape(3, -1)
    xyz = (img.affine @ np.vstack([ijk, np.ones(ijk.shape[1])]))[:3]
    d2 = ((xyz - np.asarray(centre_mm, float)[:, None]) ** 2).sum(0)
    return (d2 <= radius_mm ** 2).reshape(shape)


def sphere_values(img, centres, radius_mm: float = RADIUS_MM):
    """Per sphere: mean over covered voxels and the covered fraction."""
    data = np.asarray(img.dataobj, dtype=float)
    out = []
    for c in centres:
        m = sphere_mask(img, c, radius_mm)
        vals = data[m]
        cov = np.isfinite(vals) & (vals != 0) if np.isnan(data).sum() == 0 else np.isfinite(vals)
        out.append({"centre": tuple(c), "n_voxels": int(m.sum()), "coverage": float(cov.mean()) if m.any() else 0.0,
                    "mean": float(vals[cov].mean()) if cov.any() else float("nan")})
    return out


def roi_mean(img, centres, radius_mm: float = RADIUS_MM) -> tuple[float, list]:
    """Average of the sphere means (each sphere weighted equally, i.e. averaged across hemispheres). NaN if any
    sphere has no covered voxel (the participant is then missing for that contrast and reported)."""
    sv = sphere_values(img, centres, radius_mm)
    means = [s["mean"] for s in sv]
    return (float(np.mean(means)) if all(np.isfinite(means)) else float("nan")), sv


def anatomical_roi_mean(img, roi_mask_img, min_coverage: float = 0.5) -> tuple[float, float]:
    """Secondary ROI: mean over covered voxels of a participant's hippocampal-head mask (MNI space, resampled to the
    contrast image grid beforehand). Returns (mean, coverage); mean is NaN below min_coverage (Part 3: >= 50%)."""
    data = np.asarray(img.dataobj, dtype=float)
    mask = np.asarray(roi_mask_img.dataobj) > 0.5
    if mask.shape != data.shape[:3]:
        raise ValueError("resample the ROI mask to the contrast image grid first")
    vals = data[mask]
    cov = np.isfinite(vals)
    coverage = float(cov.mean()) if mask.any() else 0.0
    return (float(vals[cov].mean()) if coverage >= min_coverage else float("nan")), coverage
