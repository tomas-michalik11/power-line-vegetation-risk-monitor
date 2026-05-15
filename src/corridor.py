import geopandas as gpd

def create_corridor_buffer(lines: gpd.GeoDataFrame, buffer_m: float) -> gpd.GeoDataFrame:
    # reproject to metric CRS (Finnish national grid) to buffer in metres
    lines_metric = lines.to_crs(epsg=3067)
    
    # buffer each line segment — result is a polygon around each line
    buffered = lines_metric.copy()
    buffered["geometry"] = lines_metric.geometry.buffer(buffer_m)
    
    # reproject back to WGS84 for compatibility with satellite data
    return buffered.to_crs(epsg=4326)


from shapely.geometry import LineString

def split_line(line, segment_length_m: float) -> list:
    """Split a single LineString into segments of roughly segment_length_m metres."""
    total_length = line.length
    segments = []
    distance = 0.0
    while distance < total_length:
        start = line.interpolate(distance)
        end = line.interpolate(min(distance + segment_length_m, total_length))
        segments.append(LineString([start, end]))
        distance += segment_length_m
    return segments


def split_lines(lines_gdf: gpd.GeoDataFrame, segment_length_m: float) -> gpd.GeoDataFrame:
    """Split all lines into segments, preserving attributes. Returns GeoDataFrame in EPSG:4326."""
    lines_metric = lines_gdf.to_crs(epsg=3067)
    rows = []
    for _, row in lines_metric.iterrows():
        for seg in split_line(row.geometry, segment_length_m):
            rows.append({
                "geometry": seg,
                "voltage": row.get("voltage"),
                "operator": row.get("operator"),
                "ref": row.get("ref"),
            })
    return gpd.GeoDataFrame(rows, crs="EPSG:3067").to_crs(epsg=4326)

