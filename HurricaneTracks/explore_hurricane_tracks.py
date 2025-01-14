import pandas as pd
import numpy as np
import geopandas as gpd
from matplotlib import cm, colors, pyplot
from scipy.stats import poisson
import os
import seaborn as sns

# this script calculates and visualizes
# the frequency of atlantic tropical cyclones
###########################################################################################
### Visualizing NHD Track Locations #######################################################
###########################################################################################
# load combined hurricane track file
output_dir = 'combined_tracks'
file_name = os.path.join(output_dir, output_dir + '_lines.shp')
all_hurricane_lines = gpd.read_file(file_name) # read file
all_hurricane_lines = all_hurricane_lines.to_crs(epsg = 3857) # set coordinate projection

# load state boundaries
state_path = 'cb_2018_us_state_500k'
us_states = gpd.read_file(os.path.join(state_path, state_path + '.shp')) # read file
us_states = us_states.to_crs(epsg = 3857) # set coordinate projection

# visualize combined data
fig, ax = pyplot.subplots(figsize = (16, 12))
us_states.plot(ax = ax, edgecolor = 'black') # plot states
all_hurricane_lines.plot(ax = ax, column = 'TCYR', cmap = 'YlOrBr') # plot hurricane tracks

# format plot
ax.set_xlim([-12000000, -6000000])
ax.set_ylim([2000000, 6000000])
ax.axis('off')

# format colorbar
norm = colors.Normalize(vmin=2010, vmax=2025)
cax = ax.inset_axes([-0.125, 0.1, 0.05, 0.8], transform=ax.transAxes)
clb = fig.colorbar(cm.ScalarMappable(norm=norm, cmap='YlOrBr'),
             ax=ax, cax = cax, ticks=[2010, 2015, 2020, 2025])
# save figure
pyplot.savefig('hurricane_tracks_preliminary.png', bbox_inches='tight', dpi = 150)
pyplot.close()

########################################################################################

# now we want to convert the spatial data in the
# above figure into timeseries data
# make a new dataframe to store hurricane frequencies

###########################################################################################
### Creating Tropical Cyclone Timeseries ##################################################
###########################################################################################
hurricane_rates = pd.DataFrame(index = np.arange(2010, 2025),
                               columns = ['Total',])

# make a new column in the dataframe 
# to store all landfalling hurricanes
hurricane_rates['Total'] = np.zeros(len(hurricane_rates.index))

# loop through each row of geodataframe
for index, row in all_hurricane_lines.iterrows():
  # each row represents a separate event
  # the year of the event is stored in the 'TCYR' column
  hurricane_rates.loc[int(row['TCYR']), 'Total'] += 1.0

# visualize timeseries data
# initialize a new figure
fig, ax = pyplot.subplots(figsize = (16,6))

# make a bar chart where each bar corresponds to the year
bar_locations = hurricane_rates.index # index value are years
bar_heights = hurricane_rates['Total'] # 'Total' = number of TCs
ax.bar(bar_locations, bar_heights, width = 0.85, edgecolor = 'black')

# format plot
ax.set_xlim([2009.5, 2024.5])
ax.set_ylabel('Annual Tropical\nCyclones w/NHD Tracks', fontsize = 18)

# save figure
pyplot.savefig('hurricane_count.png', bbox_inches='tight', dpi = 150)
pyplot.close()
########################################################################################

###########################################################################################
### Creating Tropical Cyclone Timeseries By State #########################################
###########################################################################################
# this loops through each row in the 'us_states' geodataframe
# each row represents a single state
for idx, row in us_states.iterrows():
  # use geodataframe index to isolate each state
  # this is called a dataframe 'slice'
  this_state = us_states[us_states.index == idx]
  # find all hurricane tracks that intersect
  # the state with 'sjoin' function in geopandas
  hurricane_state_pth = gpd.sjoin(all_hurricane_lines, this_state, 
                                  how = 'inner', predicate = 'intersects')  
  # add a new column to our hurricane count dataframe
  state_name = row['NAME'] # name of state from us_states dataframe
  hurricane_rates[state_name] = np.zeros(len(hurricane_rates.index))
  # loop through all hurricane events that intersect state
  for idx_event, row_event in hurricane_state_pth.iterrows():
    # find the year of the event
    year_event = int(row_event['TCYR'])
    # record 
    hurricane_rates.loc[year_event, state_name] += 1.0
    
hurricane_rates.to_csv('hurricane_landfall_timeseries.csv')    
########################################################################################

###########################################################################################
### Visualizing Tropical Cyclone Rates By State ##########################################
###########################################################################################
# make same figure with data from only one state
state_use = 'Texas'
# initialize a new figure with 2 panels
fig, ax = pyplot.subplots(2, figsize = (12,12))

# panel 1 - bar chart where each bar corresponds to the year
bar_locations = hurricane_rates.index # index value are years
bar_heights = hurricane_rates[state_use]
ax[0].bar(bar_locations, bar_heights, width = 0.85, edgecolor = 'black', label= 'Annual Total')
# add line for mean annual value
ax[0].plot(bar_locations, np.mean(bar_heights) * np.ones(len(bar_locations)), 
        color = 'red', linewidth = 3.5, linestyle = '--', label = 'Annual Mean')

# panel 2 - make histogram 
hist_bins = np.asarray([-0.5, 0.5, 1.5, 2.5, 3.5, 4.5])
ax[1].hist(bar_heights, bins = hist_bins, width = 0.85, edgecolor = 'black', label = 'Observed')

# fit poisson distribution to data (only need mean value)
poisson_mean = np.mean(bar_heights)
poisson_n = len(bar_heights)
poisson_estimates = poisson.cdf(hist_bins+0.5,poisson_mean) - poisson.cdf(hist_bins-0.5,poisson_mean)
# plot poisson distribution over histogram
ax[1].plot(hist_bins + 0.5, poisson_n*poisson_estimates, color = 'red', label = 'Estimated (Poisson)')

# format plot
ax[0].set_ylabel(state_use + ' Landfalling\nTropical Cyclones w/NHD Tracks', fontsize = 18)
ax[1].set_ylabel('Number of years, 2010 - 2024', fontsize = 18)
ax[1].set_xlabel('Tropical Cyclones per Year', fontsize = 18)
ax[0].legend(fontsize = 14, loc = 'upper left')
ax[1].legend(fontsize = 14, loc = 'upper right')
# save figure
pyplot.savefig('hurricane_count_' + state_use + '.png', bbox_inches='tight', dpi = 150)
pyplot.close()
########################################################################################

###########################################################################################
### Mapping Tropical Cyclone Rates By State ##########################################
###########################################################################################
    
# initialize a new figure for map
fig, ax = pyplot.subplots(figsize = (16, 16))
# colorbar for choropleth
track_colors = sns.color_palette('RdYlBu_r', 30)
# this loops through each row in the 'us_states' geodataframe
# each row represents a single state
for idx, row in us_states.iterrows():
  # use geodataframe index to isolate each state
  # this is called a dataframe 'slice'
  this_state = us_states[us_states.index == idx]
  # find all hurricane tracks that intersect
  # the state with 'overlay' function in geopandas
  # this is like sjoin but it clips the lines inside the state boundary
  hurricane_state_pth = gpd.overlay(all_hurricane_lines, this_state, how = 'intersection')
  # only plot states that intersect iwth hurricane tracks
  if len(hurricane_state_pth) > 0:
    # color state based on the total number of hurricanes tracks that intersect
    number_of_hurricanes = len(hurricane_state_pth.index)
    this_state.plot(ax = ax, facecolor = track_colors[number_of_hurricanes - 1], 
                    edgecolor = 'black', linewidth = 1.0, alpha = 1.0)
    hurricane_state_pth.plot(ax = ax, color = 'slategray', linewidth = 1.5, linestyle = '--')

# Take annual mean of landfalls in each state, sort the states lowest to highest
sorted_hurricane_rates = np.sort(np.asarray(hurricane_rates.mean()))
sorted_hurricanes = np.argsort(np.asarray(hurricane_rates.mean())) # get ordered index
sorted_state_names = hurricane_rates.columns[sorted_hurricanes] # sorted column names
# add text listing highest hurricane landfall states
ax.text(0.75, 0.45, 'Average\nHurricane Landfalls', fontsize = 22, transform = ax.transAxes)
for top_h in range(0, 6): # loop through top five (plus total)
  index_val = (top_h+1) * (-1) # list is low to high, read highest first
  average_val = str(int(10*float(sorted_hurricane_rates[index_val]))/10.0)
  print_val = sorted_state_names[index_val] + ': ' + average_val + '/yr'
  ax.text(0.75, 0.45 - float(top_h + 1) / 25.0, print_val, transform = ax.transAxes, fontsize = 18)

# format colorbar
norm = colors.Normalize(vmin=0, vmax=30)
cax = ax.inset_axes([0.15, 0.1, 0.6, 0.05], transform=ax.transAxes)
clb = fig.colorbar(cm.ScalarMappable(norm=norm, cmap='RdYlBu_r'),
             ax=ax, cax = cax, orientation='horizontal')
clb.ax.tick_params(labelsize=20) 
clb.ax.set_title('Total Hurricane Landfalls, 2010 - 2024',fontsize=22)
# save figure
ax.axis('off')
pyplot.savefig('landfalls_by_state.png', bbox_inches='tight', dpi = 150)
pyplot.close()
########################################################################################

###########################################################################################
### Visualizing TC Hazard #######################################################
###########################################################################################
# load combined hurricane track file
output_dir = 'combined_tracks'
# load combined file with points and windspeeds
file_name = os.path.join(output_dir, output_dir + '_points.shp')
all_hurricane_points = gpd.read_file(file_name) # read file
all_hurricane_points = all_hurricane_points.to_crs(epsg = 3857) # set coordinate projection
# initialize figure
fig, ax = pyplot.subplots(figsize = (16,16))
# only keep hurricane points within the boundaries of the us
us_hr_pnts = gpd.sjoin(all_hurricane_points, us_states, how = 'inner', predicate = 'within')
# only keep us states with hurricane point contained within boundary
states_hr = gpd.sjoin(us_states, all_hurricane_points, how = 'inner', predicate = 'contains')
#plot clipped states + hurricane points
states_hr.plot(ax = ax, facecolor = 'steelblue', edgecolor = 'black')
# color hurricane points by INTENSITY (windspeed in knots)
us_hr_pnts.plot(ax = ax, column = 'INTENSITY', cmap = 'rocket', s = 50)
# format colorbar
norm = colors.Normalize(vmin=0, vmax=140)
cax = ax.inset_axes([0.15, 0.1, 0.6, 0.05], transform=ax.transAxes)
clb = fig.colorbar(cm.ScalarMappable(norm=norm, cmap='rocket'),
             ax=ax, cax = cax, orientation='horizontal')
clb.ax.tick_params(labelsize=20) 
clb.ax.set_title('6-hour Average Windspeed',fontsize=22)
# save figure
ax.axis('off')
pyplot.savefig('windspeeds.png', bbox_inches='tight', dpi = 150)
pyplot.close()
###########################################################################################

###########################################################################################
### Visualizing TC Wind Hazard by State ###################################################
###########################################################################################
# initialize figure
fig, ax = pyplot.subplots(figsize = (12,6))
other_states = gpd.GeoDataFrame() # dataframe to store hurricanes in minor states
cumulative_hours = np.zeros(30) # forms the bottom of the stacked bar chart
state_colors = sns.color_palette('cubehelix', 10) # colors for plot
st_cnt = 0 # state counter
# loop through all states
for idx, row in us_states.iterrows():
  # use geodataframe index to isolate each state
  # this is called a dataframe 'slice'
  this_state = us_states[us_states.index == idx]
  # find all hurricane tracks that intersect
  # the state with 'overlay' function in geopandas
  # this is like sjoin but it clips the lines inside the state boundary
  hurricane_state_pnts = gpd.sjoin(all_hurricane_points, this_state, how = 'inner', 
                                   predicate = 'within')
  # if only a small number of landfalling hurricanes
  # add points to 'other' geodataframe
  if len(hurricane_state_pnts.index) < 21:
    other_states = pd.concat([other_states, hurricane_state_pnts])
  else:
    total_hours = np.zeros(30) # initialize array for number of hours
    knot_vals = np.zeros(30) # initialize array for windspeeds
    # loop through different windspeeds, find total number
    # of 6-hour timesteps where hurricane track windspeeds were abnove threshold
    for step in range(0, 30):
      timestep_above = len(hurricane_state_pnts[hurricane_state_pnts['INTENSITY'] > (step + 1) * 5])
      # each timestep is 6 hours, divided by 15 year timeperiod
      total_hours[step] = timestep_above * 6.0 / 15.0
      knot_vals[step] = (step + 1) * 5 # use five knot time step
    if len(hurricane_state_pnts.index) > 0:
      start_position = 0 # set to 11 to plot > 60 knots only
      ax.bar(knot_vals[start_position:], total_hours[start_position:], 
             bottom = cumulative_hours[start_position:], label = row['NAME'], color = state_colors[st_cnt], 
             width = 4.5)
      st_cnt += 1
      cumulative_hours += total_hours # bottom of next bar
# plot bars for 'other' category
total_hours = np.zeros(30)
knot_vals = np.zeros(30)
for step in range(0, 30):
  timestep_above = len(other_states[other_states['INTENSITY'] > (step + 1) * 5])
  total_hours[step]= timestep_above * 0.25
  knot_vals[step] = (step + 1)*5
if len(other_states.index) > 0:
  ax.bar(knot_vals[start_position:], total_hours[start_position:], bottom = cumulative_hours[start_position:], 
         label = 'Other States', width = 4.5)
# format plot
ax.legend(fontsize = 18, ncol = 2)
ax.set_ylabel('Hours per Year Above Windspeed', fontsize = 22) 
ax.set_xlabel('Windspeed Threshold (knots)', fontsize = 22) 
ax.set_xlim([(start_position+1)*5, 140])
pyplot.savefig('wind_hazard_by_state.png', bbox_inches='tight', dpi = 150)
pyplot.close()
