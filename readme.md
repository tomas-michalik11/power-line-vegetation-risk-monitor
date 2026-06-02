# Powerline Vegetation Risk Monitor

Detects high-risk segments of power lines threatened by vegetation using open satellite data.

## What it does

1. Fetches power line geometry from OSM (swappable with real company GIS data)
2. Creates a configurable corridor buffer around each line
3. Downloads Sentinel-2 imagery and Copernicus DEM from Microsoft Planetary Computer
4. Calculates NDVI (vegetation density) and slope per corridor segment
5. Scores each 100m segment with a weighted risk score (0–1)
6. Classifies segments into `critical`, `elevated`, and `routine` priority tiers
7. Outputs an interactive map and GeoPackage for use in GIS tools

## Setup

```bash
conda create -n powerline-veg python=3.11
conda activate powerline-veg
pip install -r requirements.txt
```

## Run

```bash
python run_pipeline.py
```

The pipeline runs all steps end-to-end and saves outputs to `data/processed/`.

Alternatively, run the notebooks in order for a step-by-step walkthrough:

| Notebook | What it does |
|----------|-------------|
| `01_data_acquisition.ipynb` | Download power lines, Sentinel-2 bands, DEM |
| `02_indices_dem.ipynb` | Calculate NDVI, NDWI, slope |
| `03_risk_scoring.ipynb` | Segment lines, sample indices, compute risk score |
| `04_visualization.ipynb` | Interactive map, risk distribution plot |

## Configuration

All parameters are in `config.yaml`:

```yaml
input:
  source: "osm"          # "osm" or a file path e.g. "data/raw/my_lines.gpkg"

area:
  bbox: [23.5, 61.3, 24.1, 61.7]   # test area: Tampere, Finland

corridor:
  buffer_m: 50                       # corridor width on each side

sentinel2:
  cloud_cover_max: 20                # max cloud cover %

risk:
  weights:
    ndvi: 0.8                        # vegetation density
    ndwi: 0.0                        # moisture content
    slope: 0.2                       # terrain steepness
  thresholds:
    critical: 0.10                   # top 10% — inspect this season
    elevated: 0.25                   # top 25% — inspect next season
```

## Outputs

| File | Description |
|------|-------------|
| `data/processed/segments_risk.gpkg` | 100m segments with risk scores and priority (for QGIS) |
| `data/processed/segments_risk.geojson` | Same, for web maps |
| `data/processed/risk_map.html` | Interactive Leaflet map |
| `data/processed/risk_distribution.png` | Risk score histogram |

## Using real company data

Change one line in `config.yaml`:

```yaml
input:
  source: "data/raw/my_lines.gpkg"  # .gpkg, .shp, or .geojson
```

The rest of the pipeline runs unchanged.

## Tests

```bash
pytest tests/ -v
```

## Limitations

This is a proof of concept. Known limitations:

- **No ground truth validation** — risk scores are based on satellite indices and have not been verified against real inspection records or outage history. Weights should be calibrated per DSO using historical data.
- **Midpoint sampling** — each 100m segment is scored using a single pixel at its midpoint. Segments where the midpoint lands on a gap or clearing may be underscored even if the surrounding area has dense trees.
- **Single date imagery** — uses one Sentinel-2 scene (June–August). Seasonal variation is not accounted for.
- **CRS assumption** — metric calculations (buffer, segmentation, slope) use EPSG:3067 (Finnish national grid). Accuracy decreases for areas far from Finland.
- **Voltage agnostic** — all lines are scored equally regardless of voltage. In practice, 400kV transmission lines require stricter vegetation clearance than 20kV distribution lines.

## Tech stack

`osmnx` · `pystac-client` · `planetary-computer` · `rioxarray` · `geopandas` · `shapely` · `numpy` · `folium` · `branca` · `matplotlib`
