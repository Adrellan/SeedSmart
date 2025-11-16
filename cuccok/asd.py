import pandas as pd
import numpy as np
from pathlib import Path

# ---- 1) Fájlnevek (ha máshol vannak, add meg teljes úttal) ----
TEMP_CSV   = "eu_temp_2000_2024.csv"
PRICE_CSV  = "all_products_prices_6cats_2000_2024.csv"
OUT_CSV    = "all_products_prices_6cats_2000_2024_with_temp.csv"

# ---- 2) Hőmérséklet adatok beolvasása ----
# Elvárt oszlopok: year, cntry_code, avg_temp_c
temps = pd.read_csv(TEMP_CSV)

# Takarítás: biztosítsuk a kulcsok típusát és a kódok körüli whitespace-ek eltűnjenek
temps['year'] = temps['year'].astype(int)
temps['cntry_code'] = temps['cntry_code'].astype(str).str.strip().str.upper()

# (Opcionális) gyors sanity-check: 2000–2024 és 27 ország
# print(temps['cntry_code'].nunique(), temps['year'].min(), temps['year'].max())

# ---- 3) Termékáras fájl beolvasása ----
# Ez lehet vessző- vagy pontosvessző-szeparált is, és decimális vesszőt használhat.
# A sep=None + engine='python' általában jól auto-detekál.
prices = pd.read_csv(PRICE_CSV, sep=None, engine='python')

# Kulcsmezők rendbetétele
prices['year'] = prices['year'].astype(int)
prices['geo']  = prices['geo'].astype(str).str.strip().str.upper()

# Ha a price_eur_tonne decimális VESSZŐS (pl. "4 733,9" vagy "4733,9"),
# alakítsuk át float-tá. Ha már float, ez nem fog ártani.
if prices['price_eur_tonne'].dtype == object:
    prices['price_eur_tonne'] = (
        prices['price_eur_tonne']
        .astype(str)
        .str.replace('\u00A0', '', regex=False)  # nem törő szóköz
        .str.replace(' ', '', regex=False)       # ezreselválasztó
        .str.replace('.', '', regex=False)       # néha pontot használnak ezreselválasztónak
        .str.replace(',', '.', regex=False)      # decimális vessző -> pont
    )
    # ami konvertálható, az float lesz; ami nem, az NaN
    prices['price_eur_tonne'] = pd.to_numeric(prices['price_eur_tonne'], errors='coerce')

# ---- 4) Merge year+geo (→ cntry_code) alapon ----
merged = prices.merge(
    temps[['year', 'cntry_code', 'avg_temp_c']],
    left_on=['year', 'geo'],
    right_on=['year', 'cntry_code'],
    how='left',
)

# Nem kell kétszer a kód: a cntry_code helper oszlopot el lehet dobni, ha zavar
merged = merged.drop(columns=['cntry_code'])

# ---- 5) Gyors ellenőrzések ----
# a) Van-e olyan sor, ahol nem talált hőmérséklet?
missing = merged[merged['avg_temp_c'].isna()]
if not missing.empty:
    missing_pairs = (
        missing[['year', 'geo']]
        .drop_duplicates()
        .sort_values(['year', 'geo'])
        .head(20)  # csak az első 20 párt mutatnánk
    )
    print("FIGYELEM: volt olyan (year, geo) pár, amihez nem találtunk avg_temp_c-t.")
    print(missing_pairs)

# b) Anomália-keresés: extrém kicsi/nagy éves átlagok
anom = merged[['geo','year','avg_temp_c']].dropna()
weird = anom[(anom['avg_temp_c'] < -5) | (anom['avg_temp_c'] > 35)]
if not weird.empty:
    print("\nFIGYELEM: valószínűtlen avg_temp_c érték(ek) találhatók, pl.:")
    print(weird.sort_values('avg_temp_c').head(10))

# ---- 6) Mentés ----
merged.to_csv(OUT_CSV, index=False)
print(f"\n✅ Kész: {OUT_CSV}")
