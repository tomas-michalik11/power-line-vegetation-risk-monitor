import pystac_client
import planetary_computer
import rioxarray
from rioxarray.merge import merge_arrays
from pathlib import Path


def get_sentinel2_item(bbox: list, date_range: str, cloud_cover_max: int):
    """Search Planetary Computer and return the lowest-cloud-cover Sentinel-2 scene."""
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=date_range,
        query={"eo:cloud_cover": {"lt": cloud_cover_max}},
    )
    items = sorted(search.items(), key=lambda x: x.properties["eo:cloud_cover"])
    if not items:
        raise ValueError(f"No Sentinel-2 scenes found for bbox={bbox}, date={date_range}, cloud<{cloud_cover_max}%")
    best = items[0]
    print(f"Selected: {best.id}  ({best.properties['eo:cloud_cover']:.2f}% cloud)")
    return best


def download_sentinel2_bands(item, bbox: list, output_dir: Path) -> dict:
    """Download B03, B04, B08 clipped to bbox. Returns dict of band name → file path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    min_lon, min_lat, max_lon, max_lat = bbox
    paths = {}

    for band in ["B03", "B04", "B08"]:
        href = planetary_computer.sign(item.assets[band].href)
        da = rioxarray.open_rasterio(href, masked=True).rio.clip_box(
            minx=min_lon, miny=min_lat, maxx=max_lon, maxy=max_lat, crs="EPSG:4326"
        )
        out_path = output_dir / f"{band}.tif"
        da.rio.to_raster(out_path)
        paths[band] = out_path
        print(f"Saved {band} → {out_path}  shape={da.shape}")

    return paths


def download_dem(bbox: list, output_path: Path) -> Path:
    """Download Copernicus DEM tiles covering bbox, merge them, save as single TIF."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    min_lon, min_lat, max_lon, max_lat = bbox

    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )
    items = list(catalog.search(collections=["cop-dem-glo-30"], bbox=bbox).items())
    print(f"Found {len(items)} DEM tile(s)")

    tiles = []
    for item in items:
        href = planetary_computer.sign(item.assets["data"].href)
        tile = rioxarray.open_rasterio(href, masked=True).rio.clip_box(
            minx=min_lon, miny=min_lat, maxx=max_lon, maxy=max_lat, crs="EPSG:4326"
        )
        tiles.append(tile)

    dem = merge_arrays(tiles)
    dem.rio.to_raster(output_path)
    print(f"Saved DEM → {output_path}  shape={dem.shape}")
    return output_path


def download_worldcover(bbox: list, output_path: Path) -> Path:
    """Download ESA WorldCover 2021 land cover map clipped to bbox."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    min_lon, min_lat, max_lon, max_lat = bbox

    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )
    items = list(catalog.search(
        collections=["esa-worldcover"],
        bbox=bbox,
    ).items())

    # prefer 2021 version, fall back to whatever is available
    items_2021 = [i for i in items if "2021" in i.id]
    item = items_2021[0] if items_2021 else sorted(items, key=lambda x: x.id, reverse=True)[0]
    print(f"Using WorldCover: {item.id}")

    href = planetary_computer.sign(item.assets["map"].href)
    wc = rioxarray.open_rasterio(href, masked=True).rio.clip_box(
        minx=min_lon, miny=min_lat, maxx=max_lon, maxy=max_lat, crs="EPSG:4326"
    )
    wc.rio.to_raster(output_path)
    print(f"Saved WorldCover → {output_path}  shape={wc.shape}")
    return output_path
