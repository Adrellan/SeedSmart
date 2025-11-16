# make_eu_countries_from_nuts.py
# pip install geopandas shapely pyproj

import geopandas as gpd

nuts = gpd.read_file("NUTS_RG_60M_2024_4326.geojson").to_crs(4326)

# ország szint (LEVL_CODE==0) + szükséges oszlopok
nuts0 = nuts[nuts["LEVL_CODE"]==0][["CNTR_CODE","geometry"]].copy()
nuts0 = nuts0.rename(columns={"CNTR_CODE":"geo"})

# csak a kívánt országok (EU27 + NO, IS, CH, UK)
keep = {'AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','EL','HU','IE','IT','LV','LT','LU','MT','NL','PL','PT','RO','SK','SI','ES','SE','NO','IS','CH','UK'}
nuts0 = nuts0[nuts0["geo"].isin(keep)].copy()

# multipoligonok egységesítése (ha szükséges)
nuts0 = nuts0.dissolve(by="geo", as_index=False)

nuts0.to_file("eu_countries.geojson", driver="GeoJSON")
print("OK → eu_countries.geojson (NUTS alapján)")
