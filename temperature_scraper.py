import pandas as pd

# 1. Töltsd le a Berkeley Earth fájlt (GlobalLandTemperaturesByCountry.csv)
df = pd.read_csv("GlobalLandTemperaturesByCountry.csv")

# 2. Szűrés: csak az általad kívánt országok (angol nevekkel) és dátum 2000–2024 közé
iso_map = {
    "Austria":"AT", "Belgium":"BE", "Bulgaria":"BG", "Cyprus":"CY",
    "Czech Republic":"CZ", "Germany":"DE", "Denmark":"DK", "Estonia":"EE",
    "Greece":"EL", "Spain":"ES", "Finland":"FI", "France":"FR",
    "Croatia":"HR", "Hungary":"HU", "Ireland":"IE", "Italy":"IT",
    "Lithuania":"LT", "Luxembourg":"LU", "Latvia":"LV", "Malta":"MT",
    "Netherlands":"NL", "Poland":"PL", "Portugal":"PT", "Romania":"RO",
    "Sweden":"SE", "Slovenia":"SI", "Slovakia":"SK", "United Kingdom":"UK"
}

# konvertáljuk dátum évre
df['dt'] = pd.to_datetime(df['dt'])
df['year'] = df['dt'].dt.year

# Leválogatás 2000 ≤ year ≤ 2024, és abban az országokban, amik benne vannak
df2 = df[df['year'].between(2000, 2024) & df['Country'].isin(iso_map.keys())]

# Átlag évre: grup összes hónapból
df_yr = df2.groupby(['year','Country'])['AverageTemperature'].mean().reset_index()

# Add hozzá az iso-kód oszlopot
df_yr['cntry_code'] = df_yr['Country'].map(iso_map)

# Válaszd ki az oszlopokat ebben a sorrendben
df_out = df_yr[['year','cntry_code','AverageTemperature']].rename(columns={'AverageTemperature':'avg_temp_c'})

# Mentés CSV-be
df_out.to_csv("eu_temp_2000_2024.csv", index=False)
