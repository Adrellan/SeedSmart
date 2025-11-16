#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SoilGrids (0–30 cm, vastagság-súlyozott) ország-átlagok (NUTS0),
majd join az ár-CSV-khez úgy, hogy minden évhez ugyanaz a soil baseline kerül.

Bemenet (ugyanabban a mappában):
- nuts0_countries.geojson   (ha nincs, a script legenerálja a NUTS_RG_60M_2024_4326.geojson-ból)
- NUTS_RG_60M_2024_4326.geojson (fallback forrás)
- all_products_prices_6cats_2000_2024.csv
- top_products_prices_6cats_2000_2024.csv
"""

import os
from typing import Dict, List, Tuple

import pandas as pd
import geopandas as gpd
import xarray as xr
import rioxarray as rxr
from rasterstats import zonal_stats
from tqdm import tqdm

# ==== BEMENETI UTAK (ha máshol vannak, állítsd át) ====
COUNTRIES_PATH = "nuts0_countries.geojson"                # ezt preferáljuk
FALLBACK_NUTS_PATH = "NUTS_RG_60M_2024_4326.geojson"      # ha az előző nincs, ebből készítünk NUTS0-t
ALL_CSV = "all_products_prices_6cats_2000_2024.csv"
TOP_CSV = "top_products_prices_6cats_2000_2024.csv"

# ==== KIMENETI FÁJLOK ====
OUT_ALL = "all_products_prices_6cats_2000_2024_with_soil.csv"
OUT_TOP = "top_products_prices_6cats_2000_2024_with_soil.csv"
OUT_SOIL_COUNTRY = "soilgrids_country_baseline_0_30cm.csv"  # csak a talaj baseline országonként

# ---- SoilGrids COG URL-ek (v2.x; 0–5 / 5–15 / 15–30 cm) ----
# A "latest" alias a legfrissebb nyilvános verzióra mutat.
SG_BASE = "https://files.isric.org/soilgrids/latest/data"

# változó: var_key -> (subdir, human_unit_hint)
VARIABLES: Dict[str, Tuple[str, str]] = {
    "ph_h2o":   ("phh2o",   "unitless"),
    "soc":      ("soc",     "g/kg"),
    "cec":      ("cec",     "cmol(+)/kg"),
    "bd":       ("bdod",    "g/cm3"),
    "clay":     ("clay",    "percent"),
    "silt":     ("silt",    "percent"),
    "sand":     ("sand",    "percent"),
    "cfvol":    ("cfvo",    "percent"),  # coarse fragments (vol%)
}

# Mélységek és súlyok a 0–30 cm profilhoz
DEPTHS: List[Tuple[str, int]] = [
    ("0-5cm",   5),
    ("5-15cm", 10),
    ("15-30cm",15),
]
TOTAL_THICK = sum(w for _, w in DEPTHS)


def ensure_countries_geojson(countries_path: str, fallback_nuts_path: str) -> str:
    """
    Ha nincs ország-GeoJSON, készít egyet a NUTS fájlból (LEVL_CODE=0).
    Elvárt kulcsoszlop: CNTR_CODE (ISO2).
    """
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
    keep = [c for c in ["CNTR_CODE", "NUTS_ID", "NAME_LATN", "NUTS_NAME", "geometry"] if c in gdf0.columns]
    gdf0 = gdf0[keep].to_crs(4326)
    gdf0.to_file(countries_path, driver="GeoJSON")
    print(f"Ország-GeoJSON előállítva: {countries_path} ({len(gdf0)} rekord)")
    return countries_path


def cog_url(var_key: str, depth: str) -> str:
    sub, _unit = VARIABLES[var_key]
    # mindenütt a 'mean' réteget használjuk
    return f"{SG_BASE}/{sub}/{sub}_{depth}_mean.tif"


def load_weighted_0_30(var_key: str) -> xr.DataArray:
    """
    Betölti a három mélységi rasztert és vastagság-súlyozott átlagot képez (0–30 cm).
    A visszatérő DataArray 2D (y, x), CRS/EPSG:4326.
    """
    arrays = []
    for depth, w in DEPTHS:
        url = cog_url(var_key, depth)
        da = rxr.open_rasterio(url, masked=True).squeeze()  # (y,x)
        # biztos ami biztos: legyen térinformatikai meta
        if not da.rio.crs:
            da = da.rio.write_crs(4326)
        arrays.append((da, w))

    # illesszük egymáshoz és számoljuk a súlyozott átlagot
    base = arrays[0][0]
    acc = xr.zeros_like(base, dtype="float32")
    wsum = 0.0
    for da, w in arrays:
        if (da.rio.crs != base.rio.crs) or (da.rio.transform() != base.rio.transform()):
            da = da.rio.reproject_match(base)
        acc = xr.where(da.notnull(), acc + da * w, acc)
        wsum += w

    out = acc / wsum
    out.name = f"{var_key}_0_30cm"
    return out


def country_zonal_mean(da: xr.DataArray, gdf: gpd.GeoDataFrame, key_col: str = "CNTR_CODE") -> pd.DataFrame:
    """
    Zónastatisztika: országpoligonokra átlag a megadott DataArray-ből.
    A rasterstats-hoz ideiglenes GeoTIFF-et írunk.
    """
    tmp_path = f"_tmp_{da.name}.tif"
    da.rio.to_raster(tmp_path)
    try:
        zs = zonal_stats(
            vectors=gdf,            # GeoDataFrame vagy iterable geometria
            raster=tmp_path,
            stats=["mean"],
            nodata=None,
            geojson_out=False,
            all_touched=False,
            raster_out=False
        )
        vals = [z["mean"] if z and ("mean" in z) else None for z in zs]
        df = pd.DataFrame({key_col: gdf[key_col].values, da.name: vals})
        return df
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def main():
    # 0) Fájl-létezés ellenőrzések
    for csv in (ALL_CSV, TOP_CSV):
        if not os.path.exists(csv):
            raise SystemExit(f"Hiányzik a bemeneti CSV: {csv}")

    # 1) Országpoligonok betöltése (ISO2 a CNTR_CODE oszlopban)
    countries_path = ensure_countries_geojson(COUNTRIES_PATH, FALLBACK_NUTS_PATH)
    gdf = gpd.read_file(countries_path).to_crs(4326)
    if "CNTR_CODE" not in gdf.columns:
        raise SystemExit("A countries fájlban hiányzik a 'CNTR_CODE' oszlop (ISO2 országkód).")

    # 2) SoilGrids 0–30 cm súlyozott raszterek + zónastatisztikák
    soil_tables: List[pd.DataFrame] = []
    print("Letöltés és zónastatisztika (0–30 cm) országonként...")
    for var_key in tqdm(VARIABLES.keys()):
        da = load_weighted_0_30(var_key)
        tbl = country_zonal_mean(da, gdf, key_col="CNTR_CODE")
        soil_tables.append(tbl)

    # 3) Ország-szintű talaj baseline tábla összeillesztése
    soil_df = soil_tables[0]
    for t in soil_tables[1:]:
        soil_df = soil_df.merge(t, on="CNTR_CODE", how="outer")

    # emberbarát oszlopnevek
    rename_map = {
        "ph_h2o_0_30cm":  "soil_ph_h2o",
        "soc_0_30cm":     "soil_soc_gkg",
        "cec_0_30cm":     "soil_cec_cmolkg",
        "bd_0_30cm":      "soil_bd_gcm3",
        "clay_0_30cm":    "soil_clay_pct",
        "silt_0_30cm":    "soil_silt_pct",
        "sand_0_30cm":    "soil_sand_pct",
        "cfvol_0_30cm":   "soil_cf_vol_pct",
    }
    soil_df = soil_df.rename(columns=rename_map).sort_values("CNTR_CODE")
    soil_df.to_csv(OUT_SOIL_COUNTRY, index=False, encoding="utf-8")
    print(f"Ország-szintű SoilGrids baseline mentve: {OUT_SOIL_COUNTRY}  ({soil_df.shape[0]} sor)")

    # 4) Ár-CSV-k betöltése és join (minden évhez ugyanaz a soil baseline kerül ország szerint)
    for in_csv, out_csv in [(ALL_CSV, OUT_ALL), (TOP_CSV, OUT_TOP)]:
        df = pd.read_csv(in_csv)
        if "geo" not in df.columns:
            raise SystemExit(f"A {in_csv} fájlban nincs 'geo' oszlop.")

        merged = df.merge(soil_df, left_on="geo", right_on="CNTR_CODE", how="left")
        # Ha van olyan geo, ami nem ISO2 (pl. NUTS2 kód), itt NaN lesz a soil -> ez rendben van ország-szintnél.
        missing = merged["soil_ph_h2o"].isna().sum()
        if missing:
            print(f"Figyelem: {missing} sorban nincs soil baseline (valszeg nem ország ISO2 a 'geo').")

        merged = merged.drop(columns=["CNTR_CODE"])
        merged.to_csv(out_csv, index=False, encoding="utf-8")
        print(f"Kiírva: {out_csv}  ({merged.shape[0]} sor, {merged.shape[1]} oszlop)")

    print("Kész ✅")


if __name__ == "__main__":
    main()
