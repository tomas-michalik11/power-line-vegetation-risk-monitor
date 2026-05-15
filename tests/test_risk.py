import geopandas as gpd
import pytest
from src.risk import score_segments

def test_risk_score_uses_weights():
    segments = gpd.GeoDataFrame({
        "ndvi":  [0.0, 1.0],
        "ndwi":  [0.0, 0.0],
        "slope": [0.0, 0.0],
    })
    weights = {"ndvi": 1.0, "ndwi": 0.0, "slope": 0.0}

    result = score_segments(segments, weights)

    assert result["risk_score"].iloc[0] == pytest.approx(0.0)
    assert result["risk_score"].iloc[1] == pytest.approx(1.0)
