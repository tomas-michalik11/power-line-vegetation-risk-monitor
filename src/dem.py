import numpy as np
import xarray as xr


def calc_slope(dem: xr.DataArray, crs_metric: str = "EPSG:3067") -> xr.DataArray:
    dem_metric = dem.squeeze().rio.reproject(crs_metric)
    pixel_size = abs(dem_metric.rio.resolution()[0])
    elevation = dem_metric.values
    elev_filled = np.where(np.isnan(elevation), np.nanmean(elevation), elevation)
    dzdx = np.gradient(elev_filled, pixel_size, axis=1)
    dzdy = np.gradient(elev_filled, pixel_size, axis=0)
    slope_arr = np.degrees(np.arctan(np.sqrt(dzdx**2 + dzdy**2)))
    slope_arr = np.where(np.isnan(elevation), np.nan, slope_arr)
    return dem_metric.copy(data=slope_arr)

