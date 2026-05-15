import yaml
import rioxarray
from pathlib import Path

from src.osm import load_lines
from src.corridor import create_corridor_buffer, split_lines
from src.stac import get_sentinel2_item, download_sentinel2_bands, download_dem
from src.indices import calc_ndvi, calc_ndwi
from src.dem import calc_slope
from src.risk import score_segments, classify_segments
from src.visualize import save_risk_map, save_risk_plot



def main():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    bbox = config["area"]["bbox"]
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1 — power lines
    print("\n[1/8] Loading power lines...")
    lines = load_lines(config)
    lines.to_file(raw_dir / "power_lines.gpkg", driver="GPKG")
    print(f"  {len(lines)} lines")

    # 2 — corridor buffer
    print("\n[2/8] Creating corridor buffer...")
    corridor = create_corridor_buffer(lines, config["corridor"]["buffer_m"])
    corridor.to_file(processed_dir / "corridor_buffer.gpkg", driver="GPKG")

    # 3 — Sentinel-2 bands
    print("\n[3/8] Downloading Sentinel-2 bands...")
    item = get_sentinel2_item(bbox, "2023-06-01/2023-08-31", config["sentinel2"]["cloud_cover_max"])
    download_sentinel2_bands(item, bbox, raw_dir / "sentinel2")

    # 4 — DEM
    print("\n[4/8] Downloading DEM...")
    download_dem(bbox, raw_dir / "dem" / "dem_30m.tif")

    # 5 — NDVI and NDWI
    print("\n[5/8] Calculating NDVI and NDWI...")
    s2_dir = raw_dir / "sentinel2"
    b03 = rioxarray.open_rasterio(s2_dir / "B03.tif", masked=True)
    b04 = rioxarray.open_rasterio(s2_dir / "B04.tif", masked=True)
    b08 = rioxarray.open_rasterio(s2_dir / "B08.tif", masked=True)
    ndvi = calc_ndvi(b08, b04)
    ndwi = calc_ndwi(b03, b08)
    ndvi.rio.to_raster(processed_dir / "ndvi.tif")
    ndwi.rio.to_raster(processed_dir / "ndwi.tif")


    # 6 — slope (reprojected to match NDVI grid)
    print("\n[6/8] Calculating slope...")
    dem = rioxarray.open_rasterio(raw_dir / "dem" / "dem_30m.tif", masked=True)
    slope = calc_slope(dem)
    slope.rio.to_raster(processed_dir / "slope.tif")
    slope = slope.rio.reproject_match(ndvi)  # align to Sentinel-2 grid for sampling

    # 7 — segment lines, sample rasters, score risk
    print("\n[7/8] Segmenting and scoring...")
    segments = split_lines(lines, segment_length_m=100)
    segs_utm = segments.to_crs(ndvi.rio.crs)

    ndvi_vals, ndwi_vals, slope_vals = [], [], []
    for geom in segs_utm.geometry:
        mid = geom.interpolate(0.5, normalized=True)
        ndvi_vals.append(float(ndvi.sel(x=mid.x, y=mid.y, method="nearest")))
        ndwi_vals.append(float(ndwi.sel(x=mid.x, y=mid.y, method="nearest")))
        slope_vals.append(float(slope.sel(x=mid.x, y=mid.y, method="nearest")))

    segments["ndvi"] = ndvi_vals
    segments["ndwi"] = ndwi_vals
    segments["slope"] = slope_vals
    segments = score_segments(segments, config["risk"]["weights"])
    segments = classify_segments(segments, config["risk"]["thresholds"])


    segments.to_file(processed_dir / "segments_risk.gpkg", driver="GPKG")
    segments.to_file(processed_dir / "segments_risk.geojson", driver="GeoJSON")
    print(f"  {len(segments)} segments scored")
    print(f"  {(segments['priority']=='critical').sum()} critical, {(segments['priority']=='elevated').sum()} elevated, {(segments['priority']=='routine').sum()} routine")


    # 8 — outputs
    print("\n[8/8] Saving map and plot...")
    save_risk_map(segments, processed_dir / "risk_map.html")
    save_risk_plot(segments, processed_dir / "risk_distribution.png")

    print("\nDone.")
    print(f"  Map:  {processed_dir / 'risk_map.html'}")
    print(f"  Data: {processed_dir / 'segments_risk.gpkg'}")


if __name__ == "__main__":
    main()
