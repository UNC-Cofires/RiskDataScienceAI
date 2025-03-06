import numpy as np
import pandas as pd
import geopandas as gpd
import os
import matplotlib.pyplot as plt
import seaborn as sns
#import pyproj
#pyproj.network.set_network_enabled(False)

def get_hurricane_exposure(exposure_gdf, exposure_column, exposure_label): 
  hurricane_pathway = os.path.join('combined_tracks', 'combined_tracks_points.shp')
  all_hurricane_points = gpd.read_file(hurricane_pathway) # read file
  all_hurricane_points = all_hurricane_points.to_crs(epsg = 32618)
  # find only points that fall within one of the census tracts
  # get a list of the range of years
  all_years = all_hurricane_points['TCYR'].unique()
  # initialize dataframe to store populations
  hurricane_classification_df = pd.DataFrame()
  hurricane_counter = 0 # count of hurricanes
  # loop through all years in range
  map_output_dir = 'HurricaneExposures'
  os.makedirs(map_output_dir, exist_ok = True)
  for year_num in all_years:
    # find all the hurricanes that occurred in an individual years
    this_yr_hurricanes = all_hurricane_points[all_hurricane_points['TCYR'] == year_num]
    # stormnum gives the order that the hurricanes happened within an individual year
    hurricane_nums = this_yr_hurricanes['STORMNUM'].unique()
    # loop through storms in the current year one-by-one
    for strm_num in hurricane_nums:
      print(year_num, end = " ")
      print(strm_num)
      # select points from current storm
      this_hurricane = this_yr_hurricanes[this_yr_hurricanes['STORMNUM'] == strm_num]
      # each storm has multiple points, find point of highest windspeed
      # argsort orders from smallest to largest
      ordered_intensity = np.argsort(this_hurricane['INTENSITY'])
      # timing of highest windspeed
      new_val = ordered_intensity.iloc[-1]
      # find value of highest windspeed
      hurricane_classification_df.loc[hurricane_counter, 'Year'] = year_num * 1
      hurricane_classification_df.loc[hurricane_counter, 'HurricaneNo'] = strm_num * 1
      hurricane_classification_df.loc[hurricane_counter, 'Name'] = this_hurricane.loc[this_hurricane.index[new_val], 'STORMNAME']
      hurricane_classification_df.loc[hurricane_counter, 'Landfall Windspeed'] = this_hurricane.loc[this_hurricane.index[new_val], 'INTENSITY'] * 1.15
      # find location (point geometry) of highest windspeed
      point_geom = this_hurricane.loc[this_hurricane.index[new_val], 'geometry']
      # loop through hurricane radius sizes
      for buffer_radius in [200000.0, 150000.0, 100000.0, 50000.0]:
        # buffer radius around landfalling point
        buffer_geom = point_geom.buffer(buffer_radius)
        # create new dataframe for circle created by radius
        gdf_point_buffer = gpd.GeoDataFrame([0,], crs = this_hurricane.crs, geometry = [buffer_geom,])      
        # find intersection of hurricane radius with census tracts
        exposed_shapes = gpd.sjoin(exposure_gdf, gdf_point_buffer, how = 'inner', predicate = 'intersects')
        # find total population contained in those census tracts
        total_exposure = 0 
        for index, row in exposed_shapes.iterrows():
          total_exposure += np.sum(row[exposure_column])
        hurricane_classification_df.loc[hurricane_counter, 'Exposed ' + exposure_label + ' < ' + str(int(buffer_radius/1000.0)) + 'km'] = total_exposure * 1.0
        # remove axis ticks/labels
      hurricane_counter += 1

  # write population/windspeed data to file    
  hurricane_classification_df.to_csv('hurricane_exposed_' + exposure_label + '.csv') 
  hurricane_exposures = hurricane_classification_df[hurricane_classification_df['Exposed ' + exposure_label + ' < 200km'] > 0.0]
  fig, ax = plt.subplots(2,2)
  x_cnt = 0
  y_cnt = 0
  for distance in ['50km', '100km', '150km', '200km']:
    sns.kdeplot(ax = ax[x_cnt][y_cnt], x=hurricane_exposures['Landfall Windspeed'], 
                y=hurricane_exposures['Exposed ' + exposure_label + ' < ' + distance], 
                cmap="Blues", shade=True, bw_adjust=.5)
    ax[x_cnt][y_cnt].plot(hurricane_exposures['Landfall Windspeed'], 
            hurricane_exposures['Exposed ' + exposure_label + ' < ' + distance], 
            marker = 'o', linewidth = 0.0, color = 'red', label = '<' + distance)
    x_cnt += 1
    if x_cnt == 2:
      y_cnt += 1
      x_cnt = 0
  plt.savefig(os.path.join('HurricaneExposures', 'exposure_' + exposure_label + '.png'))

