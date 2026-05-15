import numpy as np
import xarray as xr
import pytest
from src.indices import calc_ndvi, calc_ndwi


def make_band(values):
    """Wrap a 2D numpy array into a DataArray shaped (1, rows, cols)."""
    arr = np.array(values, dtype=float)
    return xr.DataArray(arr[np.newaxis, :, :])


def test_ndvi_pure_vegetation():
    # NIR=1, Red=0 → NDVI should be 1.0
    b08 = make_band([[1.0, 1.0], [1.0, 1.0]])
    b04 = make_band([[0.0, 0.0], [0.0, 0.0]])
    result = calc_ndvi(b08, b04)
    assert float(result.mean()) == pytest.approx(1.0)


def test_ndvi_no_vegetation():
    # NIR=Red → NDVI should be 0.0
    b08 = make_band([[0.5, 0.5], [0.5, 0.5]])
    b04 = make_band([[0.5, 0.5], [0.5, 0.5]])
    result = calc_ndvi(b08, b04)
    assert float(result.mean()) == pytest.approx(0.0)
