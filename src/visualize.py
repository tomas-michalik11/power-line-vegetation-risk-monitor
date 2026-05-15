import folium
import branca.colormap as cm
import matplotlib.pyplot as plt
import geopandas as gpd
from pathlib import Path


def save_risk_map(segments: gpd.GeoDataFrame, output_path: Path) -> Path:
    """Save an interactive folium map of risk segments colored green→yellow→red."""
    output_path = Path(output_path)

    # drop segments where risk_score could not be computed (raster had no data)
    segments = segments.dropna(subset=["risk_score"])

    center_geom = segments.to_crs(epsg=3067).geometry.centroid.to_crs(epsg=4326)
    center = [center_geom.y.mean(), center_geom.x.mean()]
    m = folium.Map(location=center, zoom_start=10, tiles="CartoDB positron")

    vmin = float(segments["risk_score"].min())
    vmax = float(segments["risk_score"].max())
    if vmin >= vmax:
        vmax = vmin + 0.01  # prevent degenerate colormap when all scores are equal

    colormap = cm.LinearColormap(
        colors=["green", "yellow", "red"],
        vmin=vmin,
        vmax=vmax,
        caption="Vegetation Risk Score",
    )

    for _, row in segments.iterrows():
        folium.GeoJson(
            row["geometry"].__geo_interface__,
            style_function=lambda feat, score=row["risk_score"]: {
                "color": colormap(score),
                "weight": 3,
                "opacity": 0.8,
            },
        ).add_to(m)

    colormap.add_to(m)
    m.save(output_path)
    print(f"Saved map → {output_path}")
    return output_path


def save_risk_plot(segments: gpd.GeoDataFrame, output_path: Path) -> Path:
    """Save a histogram of risk score distribution with 75th and 90th percentile lines."""
    output_path = Path(output_path)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(segments["risk_score"], bins=40, color="steelblue", edgecolor="white")
    ax.axvline(segments["risk_score"].quantile(0.75), color="orange", linestyle="--", label="75th percentile")
    ax.axvline(segments["risk_score"].quantile(0.90), color="red", linestyle="--", label="90th percentile")
    ax.set_xlabel("Risk Score")
    ax.set_ylabel("Number of Segments")
    ax.set_title("Vegetation Risk Score Distribution")
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"Saved plot → {output_path}")
    return output_path
