import pandas as pd
import geopandas as gpd
import os
import matplotlib.pyplot as plt
import seaborn as sns

from exposure_functions import get_hurricane_exposure
full_exposure_df = pd.DataFrame()
for nc_county in ['brunswick', 'newhanover']:
  print(nc_county)
  file_pathway = os.path.join('Parcels', 'nc_' + nc_county + '_parcels_pt.shp')
  columns_keep = ['IMPROVVAL', 'geometry']
  i = 0
  chunk_size = 10000
  while True:
    chunk = slice(i, i + chunk_size, 1)
    exposure_int = gpd.read_file(file_pathway, rows=chunk)
    print(chunk)
    if exposure_int.shape[0] == 0:
      break
    full_exposure_df = pd.concat([full_exposure_df, exposure_int[columns_keep]], axis = 0)
    i += chunk_size
full_exposure_gdf = gpd.GeoDataFrame(full_exposure_df, crs = exposure_int.crs, geometry = full_exposure_df.geometry)
print(full_exposure_gdf.head())
full_exposure_gdf = full_exposure_gdf.to_crs(epsg = 32618)
get_hurricane_exposure(full_exposure_gdf, 'IMPROVVAL', 'structure_value')
