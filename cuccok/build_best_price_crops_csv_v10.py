#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (Same content as previously generated v10; see above.)
# EU crop selling prices by product, per country and year (2000–2024), 6 categories.
# Exports ALL products + a top-only convenience file.

import sys
import re
from typing import List, Optional, Iterable
import pandas as pd

try:
    import eurostat
except Exception as e:
    sys.exit("Please install dependencies first:\n  pip install eurostat pandas\n" + str(e))

DATASET = "apri_ap_crpouta"

EU_LIKE_PREFIXES = {"AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","EL","GR","HU","IE","IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE"}
OTHER_EUROPE = {"NO","IS","CH","UK"}

CATEGORIES = [
    ("arable",     "Arable (cereals/oilseeds)"),
    ("rowCrops",   "Row crops"),
    ("vegetables", "Vegetables (fresh market/transplant)"),
    ("orchards",   "Orchards/Vineyards (perennial)"),
    ("forage",     "Forage crops (fodder/legumes)"),
    ("industrial", "Specialty industrial crops"),
]
CAT_LABEL = dict(CATEGORIES)

KEYWORDS = {
    "arable": [r"wheat|spelt|durum", r"barley", r"rye", r"oats?", r"maize|corn", r"cereal",
               r"rape( seed)?|rapeseed|turnip rape", r"sunflower( s|)(seed|s)?", r"soya|soy( bean|beans)?", r"oilseed"],
    "rowCrops": [r"potato(es)?", r"sugar\s*beet", r"beetroot", r"table beet"],
    "vegetables": [r"tomato(es)?", r"pepper(s)?|capsicum", r"cucumber(s)?", r"onion(s)?", r"carrot(s)?",
                   r"cabbage(s)?|brassica", r"lettuce", r"cauliflower(s)?", r"eggplant|aubergine", r"zucchini|courgette(s)?",
                   r"spinach", r"leek(s)?", r"garlic", r"melon(s)?|watermelon(s)?", r"pumpkin(s)?|squash", r"celery",
                   r"asparagus", r"artichoke(s)?", r"broccoli", r"mushroom(s)?", r"green beans?", r"green peas?"],
    "orchards": [r"apple(s)?", r"pear(s)?", r"peach(es)?|nectarine(s)?", r"cherry|sour cherry|morello", r"plum(s)?",
                 r"apricot(s)?", r"strawberr(y|ies)", r"raspberr(y|ies)", r"currant(s)?|blackcurrant|redcurrant",
                 r"soft\s*fruit", r"orange(s)?", r"lemon(s)?", r"citrus", r"grape(s)?"],
    "forage": [r"forage|fodder|silage|hay", r"lucerne|alfalfa", r"clover", r"grass", r"green\s*maize"],
    "industrial": [r"tobacco", r"hops?", r"flax", r"hemp", r"cotton", r"aromatic|medicinal|spice|industrial"],
}

def classify_product(label: str) -> Optional[str]:
    if not label:
        return None
    text = label.lower()
    for cat in ["arable","rowCrops","vegetables","orchards","forage","industrial"]:
        for pat in KEYWORDS.get(cat, []):
            if re.search(pat, text):
                return cat
    return None

def parse_mass_multiplier(label: str) -> Optional[float]:
    t = (label or "").lower()
    if "per tonne" in t or "per ton" in t:
        return 1.0
    m = re.search(r"per\s*([0-9]+)\s*kg", t)
    if m:
        n = int(m.group(1))
        if n > 0:
            return 1000.0 / n
    if "per kg" in t:
        return 1000.0
    if any(x in t for x in ["per 100 l", "per hl", "per 100 pce", "per pce", "per 1000 pce", "per litre", "per 100 l"]):
        return None
    return None

def wide_to_long(df_raw: pd.DataFrame) -> pd.DataFrame:
    header = df_raw.iloc[0].tolist()
    data = df_raw.iloc[1:].copy()
    data.columns = header
    if "geo\\TIME_PERIOD" in data.columns:
        data.rename(columns={"geo\\TIME_PERIOD":"geo"}, inplace=True)
    year_cols: List[str] = []
    for c in data.columns:
        if isinstance(c, (int, float)) and float(c).is_integer() and 1900 <= int(c) <= 2100:
            year_cols.append(c)
        elif isinstance(c, str) and c.isdigit() and 1900 <= int(c) <= 2100:
            year_cols.append(c)
    id_cols = [c for c in data.columns if c not in year_cols]
    long = data.melt(id_vars=id_cols, value_vars=year_cols, var_name="year", value_name="price")
    long["year"] = long["year"].astype(int)
    return long

def try_get_dic(dataset: str, candidates):
    for par in candidates:
        try:
            df = eurostat.get_dic(dataset, par, frmt="df")
            if isinstance(df, list):
                df = pd.DataFrame(df)
            if isinstance(df, pd.DataFrame) and not df.empty and "val" in df.columns:
                return df
        except Exception:
            continue
    return None

def main():
    raw = eurostat.get_data(DATASET)
    df_raw = pd.DataFrame(raw)
    if df_raw.empty:
        sys.exit("Eurostat returned empty dataset.")
    df = wide_to_long(df_raw)

    colmap = {c.lower(): c for c in df.columns}
    def ensure_col(name: str, cands):
        for cand in cands:
            if cand in colmap:
                if name != colmap[cand]:
                    df.rename(columns={colmap[cand]: name}, inplace=True)
                return
        sys.exit(f"Could not find '{name}' column among: {list(df.columns)}")

    ensure_col("prod", ["prod","p","product","prod_veg"])
    ensure_col("currency", ["currency","c","curr"])
    ensure_col("geo", ["geo","g"])

    df = df[df["currency"] == "EUR"].copy()
    df = df[df["geo"].apply(lambda g: isinstance(g,str) and (g[:2] in EU_LIKE_PREFIXES or g in OTHER_EUROPE))]
    df = df[(df["year"] >= 2000) & (df["year"] <= 2024)].copy()

    df = df[df["price"].notna() & (df["price"] != ":")].copy()
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price"])

    pars = eurostat.get_pars(DATASET)
    dim_codes = [p[0] for p in pars] if pars else []
    prod_candidates = ["prod","p","prod_veg"] + dim_codes
    geo_candidates  = ["geo","g"] + dim_codes

    prod_dic = try_get_dic(DATASET, prod_candidates)
    geo_dic  = try_get_dic(DATASET, geo_candidates)

    prod_map = dict(zip(prod_dic.get("val",[]), prod_dic.get("descr",[]))) if prod_dic is not None else {}
    geo_map  = dict(zip(geo_dic.get("val",[]),  geo_dic.get("descr",[]))) if geo_dic is not None else {}

    df["prod_label"] = df["prod"].map(prod_map).fillna(df["prod"])
    df["country"]    = df["geo"].map(geo_map).fillna(df["geo"])

    df["mult"] = df["prod_label"].map(parse_mass_multiplier)
    df = df.dropna(subset=["mult"]).copy()
    df["price_eur_t"] = df["price"] * df["mult"]

    df["category_key"] = df["prod_label"].map(classify_product)
    df = df[df["category_key"].notna()].copy()
    df["category_label"] = df["category_key"].map(CAT_LABEL)

    full = df[[
        "year","country","geo","category_key","category_label","prod_label","prod","price_eur_t"
    ]].rename(columns={
        "prod_label":"product","prod":"prod_code","price_eur_t":"price_eur_tonne"
    }).sort_values(["year","country","category_key","product"])

    full.to_csv("all_products_prices_6cats_2000_2024.csv", index=False, encoding="utf-8")

    idx = df.groupby(["geo","year","category_key"])["price_eur_t"].idxmax()
    best = df.loc[idx].sort_values(["year","geo","category_key"])
    top = best[[
        "year","country","geo","category_key","category_label","prod_label","prod","price_eur_t"
    ]].rename(columns={
        "prod_label":"product","prod":"prod_code","price_eur_t":"price_eur_tonne"
    })
    top.to_csv("top_products_prices_6cats_2000_2024.csv", index=False, encoding="utf-8")

    print("Wrote:")
    print(" - all_products_prices_6cats_2000_2024.csv  (ALL products)")
    print(" - top_products_prices_6cats_2000_2024.csv  (TOP per geo/year/category)")

if __name__ == "__main__":
    main()
