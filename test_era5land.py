# py -3.13 test_era5land.py
import cdsapi
c = cdsapi.Client()
print("Connected to:", c.url)
c.retrieve(
    "reanalysis-era5-land-monthly-means",
    {
        "product_type": "monthly_averaged_reanalysis",
        "variable": ["volumetric_soil_water_layer_1"],
        "year": "2000",
        "month": ["01"],
        "time": "00:00",
        "format": "netcdf",
    },
    "era5land_test_2000_01.nc",
)
print("OK: era5land_test_2000_01.nc downloaded")
