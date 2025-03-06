import numpy as np
import pandas as pd
import geopandas as gpd
import os
import matplotlib.pyplot as plt
import seaborn as sns



print('Reading Population Data....')
# load census tract population data
# from https://data.census.gov
population_data = pd.read_csv('ACSDT5Y2023.B01003-Data.csv', header = 0)
# split census tract id number into state, county, and tract FIPS ID
# initialize array for each FIPS ID
state_fip = np.zeros(len(population_data.index))
county_fip = np.zeros(len(population_data.index))
tract_fip = np.zeros(len(population_data.index))
population = np.zeros(len(population_data.index))
counter = 0
# read population data row by row
for index, row in population_data.iterrows():
  # we want to read the part of the GEO_ID that
  # comes after the letters 'US'
  # so we split the string in 2 and take the second half
  tract_id = row['GEO_ID'].split('US')[1]
  # split FIPS codes into state, county, tract #s
  state_fip[counter] = int(tract_id[:2])
  county_fip[counter] = int(tract_id[2:5])
  tract_fip[counter] = int(tract_id[5:11])
  population[counter] = int(row['Estimate!!Total']) * 1
  counter += 1

# initalize lists for storing 
# data for new shapefile
all_population = []
all_tract = []
all_geom = []
print('Reading Census Data....')
# read original census tract block
# shapefiles from CensusTracts folder
shapefile_folder = 'CensusTracts'
# find all census tracts
for census_tract in os.listdir(shapefile_folder):
  print(census_tract)
  tract_path = os.path.join(shapefile_folder, census_tract)
  if os.path.isdir(tract_path):
    # read state-level tract data
    state_tract = gpd.read_file(os.path.join(tract_path, census_tract + '_tract.shp'))
    state_tract = state_tract.to_crs(epsg = 32618)
    # loop through each tract in the state
    for index, row in state_tract.iterrows():
      # save full tract id
      all_tract.append(row['STATEFP'] + row['COUNTYFP'] + row['TRACTCE'])
      all_geom.append(row['geometry']) # save geometry
      # find rows in population dataframe corresponding to state/county fip
      county_condition = np.logical_and(state_fip == int(row['STATEFP']), county_fip == int(row['COUNTYFP']))
      # find rows that meet the above condition and have the correct tract fip code
      tract_condition = np.logical_and(county_condition, tract_fip == int(row['TRACTCE']))
      # the row that meets all three conditions
      # will have the correct population value
      this_pop = population[tract_condition]
      # if no tract is found, print error statement
      if len(this_pop) > 0:
        current_pop = population[tract_condition][0] * 1
      else:
        current_pop = 0
        print('No pop data for:', end = " ")
        print(row['STATEFP'], end = " ")
        print(row['COUNTYFP'], end = " ")
        print(row['TRACTCE'])
      # add population of census tract to list
      all_population.append(current_pop)
# create new dataframe, use tract ids as index
population_tracts_df = pd.DataFrame(index = all_tract)
# create first column with population values
population_tracts_df['Population'] = all_population
# create geodataframe with census tract shapes and population data
population_tracts_gdf = gpd.GeoDataFrame(population_tracts_df, crs = state_tract.crs, geometry = all_geom)
population_gdf_path = os.path.join(shapefile_folder, 'census_tracts_with_population.shp')
population_tracts_gdf.to_file(population_gdf_path)



# load us states
us_state_path = os.path.join('cb_2018_us_state_500k', 'cb_2018_us_state_500k.shp')
us_states = gpd.read_file(us_state_path)
us_states = us_states.to_crs(epsg = 32618)
# read all hurricane paths
hurricane_pathway = os.path.join('combined_tracks', 'combined_tracks_points.shp')
all_hurricane_points = gpd.read_file(hurricane_pathway) # read file
all_hurricane_points = all_hurricane_points.to_crs(epsg = 32618)
# find only points that fall within one of the census tracts
inland_points = gpd.sjoin(all_hurricane_points, population_tracts_gdf, how = 'inner', predicate = 'intersects')
# get a list of the range of years
all_years = inland_points['TCYR'].unique()
# initialize dataframe to store populations
hurricane_classification_df = pd.DataFrame()
hurricane_counter = 0 # count of hurricanes
# loop through all years in range
map_output_dir = 'HurricaneExposures'
os.makedirs(map_output_dir, exist_ok = True)
for year_num in all_years:
  # find all the hurricanes that occurred in an individual years
  this_yr_hurricanes = inland_points[inland_points['TCYR'] == year_num]
  # stormnum gives the order that the hurricanes happened within an individual year
  hurricane_nums = this_yr_hurricanes['STORMNUM'].unique()
  # loop through storms in the current year one-by-one
  for strm_num in hurricane_nums:
    # select points from current storm
    this_hurricane = this_yr_hurricanes[this_yr_hurricanes['STORMNUM'] == strm_num]
    # each storm has multiple points, find point of highest windspeed
    # argsort orders from smallest to largest
    ordered_intensity = np.argsort(this_hurricane['INTENSITY'])
    # timing of highest windspeed
    new_val = ordered_intensity.iloc[-1]
    # find value of highest windspeed
    hurricane_classification_df.loc[hurricane_counter, 'Landfall Windspeed'] = this_hurricane.loc[this_hurricane.index[new_val], 'INTENSITY'] * 1.15
    # find location (point geometry) of highest windspeed
    point_geom = this_hurricane.loc[this_hurricane.index[new_val], 'geometry']
    # create figure with four separate axis (organized 2 rows x 2 columns)
    fig, ax = plt.subplots(2,2)
    x_cnt = 0 # keep track of plot axis (row)
    y_cnt = 0 # keep track of plot axis (column)
    # loop through hurricane radius sizes
    for buffer_radius in [200000.0, 150000.0, 100000.0, 50000.0]:
      # buffer radius around landfalling point
      buffer_geom = point_geom.buffer(buffer_radius)
      # create new dataframe for circle created by radius
      gdf_point_buffer = gpd.GeoDataFrame([0,], crs = this_hurricane.crs, geometry = [buffer_geom,])      
      # find intersection of hurricane radius with census tracts
      exposed_tracts = gpd.sjoin(population_tracts_gdf, gdf_point_buffer, how = 'inner', predicate = 'intersects')
      # find total population contained in those census tracts
      total_population = 0 
      for index, row in exposed_tracts.iterrows():
        total_population += np.sum(row['Population'])
      # find background states (to show where hurricane lands)
      if x_cnt == 0 and y_cnt == 0:
        exposed_states = gpd.sjoin(us_states, gdf_point_buffer, how = 'inner', predicate = 'intersects')
      exposed_states.plot(ax = ax[x_cnt][y_cnt], facecolor = 'steelblue', alpha = 0.2) # plot states in background
      # plot tracts as a cholorpleth
      exposed_tracts.plot(ax = ax[x_cnt][y_cnt], column='Population', legend = True, cmap = 'inferno', vmin = 0, vmax = 10000)
      # show location of hurricane radius area
      gdf_point_buffer.plot(ax = ax[x_cnt][y_cnt], facecolor = 'none', linewidth = 1.0, edgecolor = 'black')
      hurricane_classification_df.loc[hurricane_counter, 'Exposed Population < ' + str(int(buffer_radius/1000.0)) + 'km'] = total_population
      # remove axis ticks/labels
      ax[x_cnt][y_cnt].set_xticks([])
      ax[x_cnt][y_cnt].set_yticks([])
      ax[x_cnt][y_cnt].set_xticklabels('')
      ax[x_cnt][y_cnt].set_yticklabels('')
      x_cnt += 1
      if x_cnt == 2:
        y_cnt += 1
        x_cnt = 0
    # save figure
    plt.savefig(os.path.join(map_output_dir, 'hurricane_' + str(year_num) + '_' + str(strm_num) + '.png'))
    plt.close()
    hurricane_counter += 1

# write population/windspeed data to file    
hurricane_classification_df.to_csv('hurricane_exposed_populations.csv') 
fig, ax = plt.subplots()
sns.kdeplot(ax = ax, x=hurricane_classification_df['Landfall Windspeed'], 
            y=hurricane_classification_df['Exposed Population < 50km']/1000000.0, 
            cmap="Blues", shade=True, bw_adjust=.5)
ax.plot(hurricane_classification_df['Landfall Windspeed'], 
        hurricane_classification_df['Exposed Population < 50km']/1000000.0, 
        marker = 'o', linewidth = 0.0, color = 'red', label = '<50km')
plt.show()
plt.close()
fig, ax = plt.subplots()
sns.kdeplot(ax = ax, x=hurricane_classification_df['Landfall Windspeed'], 
            y=hurricane_classification_df['Exposed Population < 100km']/1000000.0, 
            cmap="Blues", shade=True, bw_adjust=.5)
ax.plot(hurricane_classification_df['Landfall Windspeed'], 
        hurricane_classification_df['Exposed Population < 100km']/1000000.0, 
        marker = 'o', linewidth = 0.0, color = 'red', label = '<100km')
plt.show()
plt.close()
fig, ax = plt.subplots()
sns.kdeplot(ax = ax, x=hurricane_classification_df['Landfall Windspeed'], 
            y=hurricane_classification_df['Exposed Population < 150km']/1000000.0, 
            cmap="Blues", shade=True, bw_adjust=.5)        
ax.plot(hurricane_classification_df['Landfall Windspeed'], 
        hurricane_classification_df['Exposed Population < 150km']/1000000.0, 
        marker = 'o', linewidth = 0.0, color = 'red', label = '<100km')
plt.show()
plt.close()







