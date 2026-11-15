"""Sphere ROIs on synthetic contrast images with known values."""
import numpy as np
import nibabel as nib
import pytest

from toam_analysis import roi


def _img(data, vox=2.0, origin=(-40.0, -40.0, -40.0)):
    aff = np.diag([vox, vox, vox, 1.0])
    aff[:3, 3] = origin
    return nib.Nifti1Image(np.asarray(data, dtype=np.float32), aff)


def test_sphere_voxel_count_exact():
    img = _img(np.zeros((41, 41, 41)))
    # 6-mm sphere on a 2-mm grid centred on a voxel: lattice points with i^2+j^2+k^2 <= 9 -> 123
    assert roi.sphere_mask(img, (0, 0, 0), 6).sum() == 123


def test_mean_of_a_linear_field_is_its_centre():
    shape = (41, 41, 41)
    img0 = _img(np.zeros(shape))
    ijk = np.indices(shape).reshape(3, -1)
    x = (img0.affine @ np.vstack([ijk, np.ones(ijk.shape[1])]))[0].reshape(shape)
    img = _img(x + 100)
    val, sv = roi.roi_mean(img, [(-10, 2, 4), (12, -6, 0)])
    assert sv[0]["mean"] == pytest.approx(90) and sv[1]["mean"] == pytest.approx(112)
    assert val == pytest.approx((90 + 112) / 2)  # spheres weighted equally (averaged across hemispheres)
    assert all(s["coverage"] == 1.0 for s in sv)


def test_partial_coverage_and_missing_sphere():
    data = np.full((41, 41, 41), 5.0)
    data[:, :, :20] = np.nan  # SPM writes NaN outside the analysis mask
    img = _img(data)
    val, sv = roi.roi_mean(img, [(0, 0, 0)])
    assert 0.3 < sv[0]["coverage"] < 0.7 and val == pytest.approx(5.0)
    val2, sv2 = roi.roi_mean(img, [(0, 0, 0), (0, 0, -30)])
    assert np.isnan(val2) and sv2[1]["coverage"] == 0.0


def test_anatomical_roi_coverage_rule():
    data = np.full((41, 41, 41), 3.0)
    mask = np.zeros_like(data)
    mask[10:20, 10:20, 10:20] = 1
    data[10:20, 10:20, 10:16] = np.nan  # 60% of the ROI outside the slab
    v, cov = roi.anatomical_roi_mean(_img(data), _img(mask))
    assert cov == pytest.approx(0.4) and np.isnan(v)
    data[10:20, 10:20, 10:14] = 3.0  # now 20% outside
    v, cov = roi.anatomical_roi_mean(_img(data), _img(mask))
    assert cov == pytest.approx(0.8) and v == pytest.approx(3.0)


def test_published_peaks():
    assert roi.RQ2_PEAKS == ((-27, -16, -14), (39, -22, -12))
    assert roi.RQ3_PEAKS == ((-28, -44, 42), (-38, -2, 22), (32, 12, 36))
