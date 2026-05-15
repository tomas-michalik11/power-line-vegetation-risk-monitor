import osmnx as ox
import geopandas as gpd
from pathlib import Path
from shapely.geometry import box


def load_lines(config: dict) -> gpd.GeoDataFrame:
    source = config["input"]["source"]

    if source == "osm":
        return _load_from_osm(config)
    else:
        return _load_from_file(source)


def _load_from_osm(config: dict) -> gpd.GeoDataFrame:
    min_lon, min_lat, max_lon, max_lat = config["area"]["bbox"]
    lines = ox.features_from_bbox(
        bbox=(min_lon, min_lat, max_lon, max_lat),
        tags={"power": "line"}
    )
    cols = ["geometry", "voltage", "cables", "circuits", "wires", "operator", "name", "ref"]
    lines_clean = lines[[c for c in cols if c in lines.columns]].copy()
    return lines_clean.clip(box(min_lon, min_lat, max_lon, max_lat))


def _load_from_file(path: str) -> gpd.GeoDataFrame:
    return gpd.read_file(Path(path))
