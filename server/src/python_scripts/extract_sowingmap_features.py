#!/usr/bin/env python3
"""Extract colored crop polygons that intersect a bounding box."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Tuple

import geopandas as gpd
from shapely.geometry import box, mapping

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SHAPEFILE = PROJECT_ROOT / 'shapes/crops/colored_crops.shp'

def parse_coordinates(value: str) -> Tuple[float, float, float, float]:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 4:
        raise ValueError("coordinates must contain four comma-separated numbers: minLon,minLat,maxLon,maxLat")
    try:
        min_lon, min_lat, max_lon, max_lat = map(float, parts)
    except ValueError as exc:
        raise ValueError("coordinates must be numeric") from exc
    if min_lon >= max_lon or min_lat >= max_lat:
        raise ValueError("Invalid bounds: expected min < max for both longitude and latitude")
    return min_lon, min_lat, max_lon, max_lat

def load_crops(shapefile: Path) -> gpd.GeoDataFrame:
    if not shapefile.exists():
        raise FileNotFoundError(f"Shapefile not found: {shapefile}")
    gdf = gpd.read_file(shapefile)
    if gdf.crs is None:
        raise ValueError("Shapefile has no CRS defined; cannot interpret coordinates")
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    return gdf

def filter_crops(gdf: gpd.GeoDataFrame, bounds: Tuple[float, float, float, float]) -> gpd.GeoDataFrame:
    min_lon, min_lat, max_lon, max_lat = bounds
    bbox = box(min_lon, min_lat, max_lon, max_lat)
    return gdf[gdf.intersects(bbox)].copy()

def to_features(gdf: gpd.GeoDataFrame) -> List[dict]:
    features: List[dict] = []
    crop_field = "crop_group" if "crop_group" in gdf.columns else None
    for _, row in gdf.iterrows():
        feature = {
            "geometry": mapping(row.geometry),
        }
        if crop_field:
            feature["crop_group"] = row[crop_field]
        else:
            feature["properties"] = row.drop(labels="geometry").to_dict()
        features.append(feature)
    return features

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coordinates", required=True, help="Bounding box as minLon,minLat,maxLon,maxLat")
    parser.add_argument("--shapefile", default=str(DEFAULT_SHAPEFILE), help="Path to colored crops shapefile")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    bounds = parse_coordinates(args.coordinates)
    gdf = load_crops(Path(args.shapefile))
    filtered = filter_crops(gdf, bounds)
    result = {
        "count": int(len(filtered)),
        "features": to_features(filtered),
    }
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
