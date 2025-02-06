import numpy as np
import geopandas as gpd
from matplotlib import pyplot
import os
###########################################################################################
### Visualizing TC Hazard #######################################################
###########################################################################################
# load combined hurricane track file
output_dir = 'combined_tracks'
# load combined file with points and windspeeds
file_name = os.path.join(output_dir, output_dir + '_points.shp')
all_hurricane_points = gpd.read_file(file_name) # read file
all_hurricane_points = all_hurricane_points.to_crs(epsg = 6343) # set coordinate projection

state_path = 'cb_2018_us_state_500k'
us_states = gpd.read_file(os.path.join(state_path, state_path + '.shp')) # read file
us_states = us_states.to_crs(epsg = 6343) # set coordinate projection
# initialize figure
fig, ax = pyplot.subplots(figsize = (16,16))
# only keep hurricane points within the boundaries of the us
us_hr_pnts = gpd.sjoin(all_hurricane_points, us_states, how = 'inner', predicate = 'within')
# only keep us states with hurricane point contained within boundary
us_bounds = us_states.dissolve()
intensity = []
distances = []
for index, row in us_hr_pnts.iterrows():
  # calculate distance between each point (row['geometry'])
  # and the boundary of the dissolved us shape (us_bounds.geometry[0].boundary)
  distance=row['geometry'].distance(us_bounds.geometry[0].boundary) 
  # store the windspeed in mph
  intensity.append(float(row['INTENSITY'])* 1.15)
  # store the distance
  distances.append(distance)
  
fig, ax = pyplot.subplots()
ax.plot(np.asarray(distances)/1000.0, intensity, marker = 'o', linewidth = 0.0)
ax.set_ylabel('Windspeed (mph)', fontsize = 22) 
ax.set_xlabel('Distance to coast (km)', fontsize = 22) 
pyplot.savefig('wind_hazard_by_distance_to_the_coast.png', bbox_inches='tight', dpi = 150)
pyplot.close()
#################################################################
##################################################################
fig, ax = pyplot.subplots()
# Create histogram
bin_edges = np.arange(10, 180, 10)
legend_label = ['<100km', '100-200km', '200-300km', '300+km']
for distance_bin in range(0, 4):
  intensity = np.asarray(intensity)
  distances = np.asarray(distances)
  if distance_bin < 3:
    current_bin = intensity[np.logical_and(distances >= float(distance_bin) * 100000.0, distances > float(distance_bin) * 100000.0)] * 1.15
  else:
    current_bin = intensity[distances >= float(distance_bin) * 100000.0]* 1.15
    
  ax.hist(current_bin, bins=bin_edges, edgecolor='black', alpha = 0.6, label = legend_label[distance_bin])

# Add titles and labels
pyplot.xlabel('Windspeed (mph)')
pyplot.ylabel('Frequency')

# Show plot
ax.legend(fontsize = 18)
pyplot.savefig('wind_hazard_by_distance_to_the_coast_distribution.png', bbox_inches='tight', dpi = 150)
pyplot.close()
