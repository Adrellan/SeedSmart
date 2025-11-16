#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Európai országok SoilGrids 0–5 cm ország-átlagok egy CSV-be.
Kimenet: soilgrids_europe_0_5cm.csv  (CNTR_CODE + soil_* oszlopok)
"""

import os
from typing import Dict, List
import pandas as pd
import geopandas as gpd
import xarray as xr
import rioxarray as rxr
from rasterstats import zonal_stats
from tqdm import tqdm

# ----- Fájlok -----
COUNTRIES_PATH = "nuts0_countries.geojson"
FALLBACK_NUTS_PATH = "NUTS_RG_60M_2024_4326.geojson"
OUT_CSV = "soilgrids_europe_0_5cm.csv"

# ----- Európa / EU kódok (ISO2) -----
EU_LIKE_PREFIXES = {
    "AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","EL","GR","HU","IE","IT",
    "LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE"
}
OTHER_EUROPE = {"NO","IS","CH","UK"}
KEEP_COUNTRIES = EU_LIKE_PREFIXES | OTHER_EUROPE

# ----- SoilGrids „latest” gyökér -----
SG_BASE = "https://files.isric.org/soilgrids/latest/data"

# var_key -> (subdir, friendly_unit_hint)
VARIABLES: Dict[str, tuple] = {
    "ph_h2o": ("phh2o", "unitless"),
    "soc":    ("soc",   "g/kg"),
    "cec":    ("cec",   "cmol(+)/kg"),
    "bd":     ("bdod",  "g/cm3"),
    "clay":   ("clay",  "percent"),
    "silt":   ("silt",  "percent"),
    "sand":   ("sand",  "percent"),
    "cfvol":  ("cfvo",  "percent"),  # coarse fragments (vol%)
}
DEPTH = "0-5cm"  # most csak ez kell

def ensure_countries_geojson(countries_path: str, fallback_nuts_path: str) -> str:
    """Ha nincs ország-GeoJSON, készít egyet a NUTS fájlból (LEVL_CODE=0)."""
    if os.path.exists(countries_path):
        print(f"Ország-GeoJSON megvan: {countries_path}")
        return countries_path
    if not os.path.exists(fallback_nuts_path):
        raise SystemExit(
            f"Hiányzik a {countries_path}, és a fallback NUTS fájl sem található: {fallback_nuts_path}"
        )
    print(f"{countries_path} nem található – előállítás {fallback_nuts_path} alapján (LEVL_CODE=0)...")
    gdf = gpd.read_file(fallback_nuts_path)
    if "LEVL_CODE" not in gdf.columns:
        raise SystemExit("A NUTS forrásban nincs 'LEVL_CODE' oszlop.")
    gdf0 = gdf[gdf["LEVL_CODE"] == 0].copy()
    keep = [c for c in ["CNTR_CODE","NUTS_ID","NAME_LATN","NUTS_NAME","geometry"] if c in gdf0.columns]
    gdf0 = gdf0[keep].to_crs(4326)
    gdf0.to_file(countries_path, driver="GeoJSON")
    print(f"Ország-GeoJSON előállítva: {countries_path} ({len(gdf0)} rekord)")
    return countries_path

def raster_url(var_key: str) -> str:
    """VRT URL a 0–5 cm mean rétegre."""
    sub, _ = VARIABLES[var_key]
    return f"{SG_BASE}/{sub}/{sub}_{DEPTH}_mean.vrt"

def zonal_mean_1var(gdf: gpd.GeoDataFrame, var_key: str, key_col: str = "CNTR_CODE") -> pd.DataFrame:
    """Betölti a VRT-et és országokra átlagol (0–5 cm). Egy sor / ország."""
    url = raster_url(var_key)
    try:
        da = rxr.open_rasterio(url, masked=True).squeeze()
        if not da.rio.crs:
            da = da.rio.write_crs(4326)
    except Exception as e:
        raise SystemExit(f"Hiba a raszter megnyitásakor: {url}\n{e}")

    tmp = f"_tmp_{var_key}_{DEPTH}.tif"
    da.rio.to_raster(tmp)
    try:
        zs = zonal_stats(
            vectors=gdf,
            raster=tmp,
            stats=["mean"],
            nodata=None,
            geojson_out=False,
            all_touched=False,
            raster_out=False
        )
        colname = f"{var_key}_0_5cm"
        vals = [z["mean"] if z and ("mean" in z) else None for z in zs]
        return pd.DataFrame({key_col: gdf[key_col].values, colname: vals})
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass

def main():
    # 1) Országok beolvasása / előállítása
    countries_path = ensure_countries_geojson(COUNTRIES_PATH, FALLBACK_NUTS_PATH)
    gdf = gpd.read_file(countries_path).to_crs(4326)
    if "CNTR_CODE" not in gdf.columns:
        raise SystemExit("A countries fájlban hiányzik a 'CNTR_CODE' oszlop (ISO2).")

    # 2) EU/Európa szűrés és DISSOLVE -> 1 sor / ország
    gdf = gdf[gdf["CNTR_CODE"].isin(KEEP_COUNTRIES)].copy()
    gdf = gdf.dissolve(by="CNTR_CODE", as_index=False)  # <<< kritikus a duplikátumok ellen
    gdf = gdf.to_crs(4326).sort_values("CNTR_CODE").reset_index(drop=True)
    if gdf.empty:
        raise SystemExit("A szűrés után nincs ország a GeoJSON-ban. Ellenőrizd a CNTR_CODE értékeket.")

    print(f"Európai országok száma: {len(gdf)}  -> {', '.join(sorted(gdf['CNTR_CODE'].unique()))}")
    print("Downloading SoilGrids 0-5 cm layers and computing country-level means...")

    # 3) Változók zónastatisztikája (0–5 cm, 1 sor / ország)
    tables: List[pd.DataFrame] = []
    pbar = tqdm(list(VARIABLES.keys()), desc="Soil variable")
    for var_key in pbar:
        pbar.set_postfix_str(f"{var_key} (0-5cm)")
        tbl = zonal_mean_1var(gdf, var_key, key_col="CNTR_CODE")
        tables.append(tbl)

    # 4) Összeolvasztás biztonságosan (LEFT merge egy alaptáblára)
    soil_df = gdf[["CNTR_CODE"]].drop_duplicates().copy()
    for t in tables:
        soil_df = soil_df.merge(t, on="CNTR_CODE", how="left")

    # 5) Barátságos oszlopnevek
    rename_map = {
        "ph_h2o_0_5cm": "soil_ph_h2o",
        "soc_0_5cm":    "soil_soc_gkg",
        "cec_0_5cm":    "soil_cec_cmolkg",
        "bd_0_5cm":     "soil_bd_gcm3",
        "clay_0_5cm":   "soil_clay_pct",
        "silt_0_5cm":   "soil_silt_pct",
        "sand_0_5cm":   "soil_sand_pct",
        "cfvol_0_5cm":  "soil_cf_vol_pct",
    }
    soil_df = soil_df.rename(columns=rename_map).sort_values("CNTR_CODE")

    soil_df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"Kész: {OUT_CSV}  ({soil_df.shape[0]} sor, {soil_df.shape[1]} oszlop)")

if __name__ == "__main__":
    main()
