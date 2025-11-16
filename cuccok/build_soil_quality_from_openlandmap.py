#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, io, json, re, zipfile, tempfile, warnings
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import requests
import geopandas as gpd
import rasterio
from rasterstats import zonal_stats

# ---- Beállítások ------------------------------------------------------------

BOUNDARY_DIR = "data/boundaries"
BOUNDARY_PATH = os.path.join(BOUNDARY_DIR, "nuts0_2024.geojson")
NUTS_GEOJSON_URL = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_60M_2024_4326.geojson"

NE_ZIP_URL = "https://naturalearth.s3.amazonaws.com/50m_cultural/ne_50m_admin_0_countries.zip"
NE_LOCAL_ZIP = os.path.join(BOUNDARY_DIR, "ne_50m_admin_0_countries.zip")

TARGET_CNTR = [
    "AT","BE","BG","CY","CZ","DE","DK","EE","EL","ES","FI","FR","HR","HU","IE",
    "IT","LT","LU","LV","MT","NL","PL","PT","RO","SE","SI","SK","UK"
]

# 1) Helyi fájlok (offline elsőbbség)
LOCAL_RASTERS = {
    "ph_h2o": "data/rasters/ph_h2o_0_5cm.tif",
    "soc_gkg": "data/rasters/soc_0_5cm.tif",   # SOC content (g/kg) 0–5 cm
}

# 2) Közvetlen COG URL-ek (fallback a STAC előtt).
# Ha valamelyik nem él nálad, nyugodtan cseréld más publikus COG-ra vagy mutass a helyi fájlra.
FALLBACK_COGS = {
    "ph_h2o": [
        # példák; ha nem működnek a hálózatodban, használj LOCAL_RASTERS-t
        "https://openlandmap.s3.eu-central-1.wasabisys.com/soil/ph/ph_h2o_sl1_250m.tif",
        "https://storage.googleapis.com/openlandmap/soil/ph/ph_h2o_sl1_250m.tif",
    ],
    "soc_gkg": [
        "https://openlandmap.s3.eu-central-1.wasabisys.com/soil/soc/soc_content_sl1_250m_gkg.tif",
        "https://storage.googleapis.com/openlandmap/soil/soc/soc_content_sl1_250m_gkg.tif",
    ],
}

# 3) (Utolsó) STAC collection URL-ek – csak ha az 1) és 2) nem jön be.
STAC_COLLECTIONS = {
    "ph_h2o": "https://stac.openlandmap.org/ph.h2o_usda.4c1a2a/collection.json",
    "soc_gkg": "https://stac.openlandmap.org/organic.carbon_usda.6a1c/collection.json",
}

OUTPUT_CSV = "soil_quality_country_openlandmap.csv"

# ---- Segédek: határok -------------------------------------------------------

def ensure_dirs():
    os.makedirs(BOUNDARY_DIR, exist_ok=True)
    os.makedirs("data/rasters", exist_ok=True)

def download(url: str, dest: str):
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)

def build_nuts0_from_full(full_geojson_path: str, out_path: str):
    gdf = gpd.read_file(full_geojson_path)
    nuts0 = gdf[gdf["LEVL_CODE"] == 0].copy()
    for c in ["CNTR_CODE", "cntr_code", "CNTRCODE", "ISO2", "ISO2_CODE", "CNTR_ID"]:
        if c in nuts0.columns:
            nuts0 = nuts0.rename(columns={c: "CNTR_CODE"})
            break
    if nuts0.crs is None:
        nuts0.set_crs(epsg=4326, inplace=True)
    else:
        nuts0 = nuts0.to_crs(epsg=4326)
    nuts0[["CNTR_CODE","geometry"]].to_file(out_path, driver="GeoJSON")

def ensure_uk_in_boundaries(nuts0_path: str):
    gdf = gpd.read_file(nuts0_path)
    if "UK" in set(gdf["CNTR_CODE"]):
        return
    if not os.path.exists(NE_LOCAL_ZIP):
        download(NE_ZIP_URL, NE_LOCAL_ZIP)
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(NE_LOCAL_ZIP, "r") as z:
            z.extractall(td)
        shp = [os.path.join(td, f) for f in os.listdir(td) if f.endswith(".shp") and "ne_50m_admin_0_countries" in f][0]
        ne = gpd.read_file(shp).to_crs(epsg=4326)
        name_cols = [c for c in ["ADMIN","NAME","NAME_EN","SOVEREIGNT","ADM0_A3"] if c in ne.columns]
        uk = None
        for c in name_cols:
            cand = ne[ne[c].astype(str).str.lower().isin([
                "united kingdom","uk","gb","great britain","united kingdom of great britain and northern ireland"
            ])]
            if not cand.empty:
                uk = cand; break
        ne_uk = uk[["geometry"]].copy()
        ne_uk["CNTR_CODE"] = "UK"
        out = pd.concat([gdf[["CNTR_CODE","geometry"]], ne_uk], ignore_index=True)
        out = gpd.GeoDataFrame(out, geometry="geometry", crs="EPSG:4326")
        out.to_file(nuts0_path, driver="GeoJSON")

def ensure_boundaries(path: str):
    ensure_dirs()
    if not os.path.exists(path):
        tmp_full = os.path.join(BOUNDARY_DIR, "NUTS_RG_60M_2024_4326.geojson")
        if not os.path.exists(tmp_full):
            download(NUTS_GEOJSON_URL, tmp_full)
        build_nuts0_from_full(tmp_full, path)
    ensure_uk_in_boundaries(path)

def load_nuts0_subset(path: str, targets: List[str]) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    gdf = gdf[gdf["CNTR_CODE"].isin(targets)].copy()
    return gdf.to_crs(epsg=4326)

# ---- Forrásválasztó: helyi -> fallback COG -> STAC --------------------------

def first_existing(paths: List[str]) -> Optional[str]:
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None

def try_open_as_raster(path_or_url: str) -> bool:
    try:
        with rasterio.open(path_or_url) as src:
            _ = src.count
        return True
    except Exception:
        return False

def pick_from_fallback_cogs(layer_key: str) -> Optional[str]:
    for url in FALLBACK_COGS.get(layer_key, []):
        if try_open_as_raster(url):
            return url
    return None

def pick_from_local(layer_key: str) -> Optional[str]:
    p = LOCAL_RASTERS.get(layer_key)
    if p and os.path.exists(p) and try_open_as_raster(p):
        return p
    return None

def pick_from_stac(collection_url: str, prefer_depth_patterns: List[str]) -> Optional[str]:
    try:
        r = requests.get(collection_url, timeout=120)
        r.raise_for_status()
        coll = r.json()
    except Exception:
        return None

    candidates = []
    assets = coll.get("assets", {})
    for k, a in assets.items():
        href = a.get("href", "")
        title = (a.get("title") or k or "").lower()
        if href.lower().endswith((".tif",".tiff",".vrt","/cog")):
            candidates.append((title, href))

    if not candidates:
        for l in coll.get("links", []):
            if l.get("rel") not in ("item","items"): 
                continue
            href = l.get("href")
            if not href: 
                continue
            try:
                r2 = requests.get(href, timeout=120); r2.raise_for_status()
                item = r2.json()
                for k, a in (item.get("assets") or {}).items():
                    ahref = a.get("href","")
                    atitle = (a.get("title") or k or "").lower()
                    if ahref.lower().endswith((".tif",".tiff",".vrt")):
                        candidates.append((atitle, ahref))
            except Exception:
                continue

    if not candidates:
        return None

    depth_regex = re.compile("|".join(prefer_depth_patterns), flags=re.IGNORECASE)
    for title, href in candidates:
        if depth_regex.search(title) or depth_regex.search(href):
            if try_open_as_raster(href):
                return href
    # végső
    for _, href in candidates:
        if try_open_as_raster(href):
            return href
    return None

def select_raster(layer_key: str) -> str:
    # 1) helyi
    p = pick_from_local(layer_key)
    if p: 
        print(f"[SRC] {layer_key}: helyi fájl -> {p}")
        return p
    # 2) fallback COG lista
    p = pick_from_fallback_cogs(layer_key)
    if p:
        print(f"[SRC] {layer_key}: fallback COG -> {p}")
        return p
    # 3) STAC
    p = pick_from_stac(
        STAC_COLLECTIONS[layer_key],
        prefer_depth_patterns=["0-5","0cm","sl1","top","0_5"]
    )
    if p:
        print(f"[SRC] {layer_key}: STAC -> {p}")
        return p
    raise RuntimeError(f"Nincs elérhető raszter a(z) {layer_key} réteghez. Adj meg helyi fájlt a LOCAL_RASTERS-ben.")

# ---- Zónastatisztika --------------------------------------------------------

def zonal_mean_for_raster(path_or_url: str, nuts0: gpd.GeoDataFrame, nodata: Optional[float]=None) -> pd.DataFrame:
    # rasterio megnyitás csak validálásra kell; a rasterstats közvetlenül a path_or_url-t is eszi
    try:
        with rasterio.open(path_or_url) as src:
            nodata_val = nodata if nodata is not None else src.nodata
    except Exception as e:
        raise RuntimeError(f"Nem tudom megnyitni a rasztert: {path_or_url}\n{e}")

    records = []
    for _, row in nuts0.iterrows():
        geom = json.loads(gpd.GeoSeries([row.geometry]).to_json())["features"][0]["geometry"]
        zs = zonal_stats([geom], path_or_url, stats="mean", nodata=nodata_val, all_touched=False)
        records.append({"CNTR_CODE": row["CNTR_CODE"], "mean": zs[0].get("mean")})
    return pd.DataFrame.from_records(records)

# ---- Fő ---------------------------------------------------------------------

def main():
    warnings.filterwarnings("ignore")
    ensure_boundaries(BOUNDARY_PATH)
    nuts0 = load_nuts0_subset(BOUNDARY_PATH, TARGET_CNTR)
    if nuts0.empty:
        raise RuntimeError("A NUTS0 ország subset üres.")

    ph_src  = select_raster("ph_h2o")
    soc_src = select_raster("soc_gkg")

    df_ph  = zonal_mean_for_raster(ph_src, nuts0)
    df_soc = zonal_mean_for_raster(soc_src, nuts0)

    # SOC már g/kg egységű fallback COG-oknál. Ha olyan forrást adsz meg, ami "x5 g/kg",
    # akkor itt szorozd meg 5-tel (pl. df_soc['mean'] *= 5.0).
    out = nuts0[["CNTR_CODE"]].drop_duplicates()
    out = out.merge(df_ph.rename(columns={"mean":"ph_h2o"}), on="CNTR_CODE", how="left")
    out = out.merge(df_soc.rename(columns={"mean":"soc_gkg"}), on="CNTR_CODE", how="left")

    out.sort_values("CNTR_CODE", inplace=True)
    out.to_csv(OUTPUT_CSV, index=False)
    print(f"[OK] Kimentve: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
