import geopandas as gpd


def _minmax(series):
    rng = series.max() - series.min()
    if rng == 0:
        return series * 0.0  # no variation — contribute 0 to risk score
    return (series - series.min()) / rng



def score_segments(segments: gpd.GeoDataFrame, weights: dict) -> gpd.GeoDataFrame:
    """Add normalized columns and risk_score to segments GeoDataFrame."""
    result = segments.copy()
    result["ndvi_norm"] = _minmax(result["ndvi"])
    result["ndwi_norm"] = _minmax(result["ndwi"])
    result["slope_norm"] = _minmax(result["slope"])
    result["risk_score"] = (
        weights["ndvi"]  * result["ndvi_norm"] +
        weights["ndwi"]  * result["ndwi_norm"] +
        weights["slope"] * result["slope_norm"]
    )
    return result


def classify_segments(segments: gpd.GeoDataFrame, thresholds: dict) -> gpd.GeoDataFrame:
    result = segments.copy()
    critical_cutoff = result["risk_score"].quantile(1 - thresholds["critical"])
    elevated_cutoff = result["risk_score"].quantile(1 - thresholds["elevated"])

    
    result["priority"] = "routine"
    result.loc[result["risk_score"] >= elevated_cutoff, "priority"] = "elevated"
    result.loc[result["risk_score"] >= critical_cutoff, "priority"] = "critical"
    return result

