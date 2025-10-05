import geopandas as gpd

SRC = "NUTS_RG_60M_2024_4326.geojson"  # ha máshol van, add meg a teljes elérési utat
DST = "nuts0_countries.geojson"

gdf = gpd.read_file(SRC)
gdf0 = gdf[gdf["LEVL_CODE"] == 0].copy()
keep = [c for c in ["CNTR_CODE","NUTS_ID","NAME_LATN","NUTS_NAME","geometry"] if c in gdf0.columns]
gdf0 = gdf0[keep].to_crs(4326)
gdf0.to_file(DST, driver="GeoJSON")
print(f"Kész: {DST} ({len(gdf0)} ország)")
