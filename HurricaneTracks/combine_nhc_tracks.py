import pandas as pd
import numpy as np
import geopandas as gpd
import os

# this code reads each individual 
# hurricane event shapefile and 
# combines them into one geodataframe

# local directory for extracted data
# this should be the same as local directory
# for read_nhc_api.py
output_dir = 'nhd_tracks'

# local directory for combined tracks
combined_dir = 'combined_tracks'
os.makedirs(combined_dir, exist_ok = True)

# each hurricane data type has different labels
# (some w/ two options over the time period)
data_type_list = ['points', 'lines']
ender_list = [['position', 'pts'], ['lin', 'track']]

# there are four different kinds of nhd track data
# for each event in database:
# points, lines, radii, and shape
# we want to read and combine each separately
for dt, ender in zip(data_type_list, ender_list):
  # initialized combined gdf
  all_tracks = gpd.GeoDataFrame()
  all_geoms = [] # list to store geometries
  # loop through all event folders
  # each folder contains nhd data from a single event
  tot_len = 0
  for hurricane_event in os.listdir(output_dir):
    if os.path.isdir(os.path.join(output_dir, hurricane_event)):
      
      # filenames can change over the course of the simulation
      # loop through each potential name - try to find one that
      # exists
      pt_cnt = 0
      for shp_end in ender:
        try:
          # read single-event data
          hurricane_path = gpd.read_file(os.path.join(output_dir, hurricane_event, hurricane_event + '_' + shp_end + '.shp'))
        except:
          pt_cnt += 1
      # if at least one of the files exist,
      # add it to the combined dataset
      if pt_cnt < len(ender):
        tot_len += len(hurricane_path.index)
        # extract year from event name
        year_use = int(hurricane_event[4:8])
        # combine each line or windswath into a
        # single geometry for each event
        # points/radii are left as multiple geometries
        if dt == 'shape' or dt == 'lines':
          hurricane_path = hurricane_path.dissolve()
        # add in a data column for the year of the event
        year_col = pd.DataFrame(np.ones(len(hurricane_path.index)) * year_use, columns = ['TCYR'])
        hurricane_path = pd.concat([hurricane_path,year_col], axis = 1)
        # add in this event to combined gdf
        all_tracks = pd.concat([all_tracks, hurricane_path], axis = 0)
        # keep track of geometry
        for index, row in hurricane_path.iterrows():
          all_geoms.append(row.geometry)
      else:
        print('no data ' + hurricane_event + ' ' + dt) # make note if data reads an error
  # use all_geoms to make the new geodataframe
  all_tracks = gpd.GeoDataFrame(all_tracks, geometry = all_geoms, crs = hurricane_path.crs)
  all_tracks = all_tracks.to_crs(epsg = 3857)
  # write to file
  all_tracks.to_file(os.path.join(combined_dir, 'combined_tracks_' + dt + '.shp'))
