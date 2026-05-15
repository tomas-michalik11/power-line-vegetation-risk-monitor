import numpy as np
import xarray as xr

def calc_ndvi(b08: xr.DataArray, b04: xr.DataArray) -> xr.DataArray:
    nir = b08.squeeze()
    red = b04.squeeze()
    return (nir - red) / (nir + red)

def calc_ndwi(b03: xr.DataArray, b08: xr.DataArray) -> xr.DataArray:
    green = b03.squeeze()
    nir = b08.squeeze()
    return (green - nir) / (green + nir)


def mask_ndvi_by_tree_cover(ndvi: xr.DataArray, worldcover: xr.DataArray) -> xr.DataArray:
    """Zero out NDVI pixels that are not confirmed tree cover (WorldCover class 10)."""
    wc_aligned = worldcover.squeeze().rio.reproject_match(ndvi)
    return ndvi.where(wc_aligned == 10, other=0.0)
