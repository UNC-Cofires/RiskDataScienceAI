import requests
import zipfile
import io
import os

# this code reads hurricane track data from nhc
# unzips the drives and stores the shapefiles
# including points, lines, radius, and windswath

# web address of data directory
url = 'https://www.nhc.noaa.gov/gis/best_track/'
ender = '_best_track.zip' # multiple file types in directory

# local directory for extracted data
output_dir = 'nhd_tracks'

# data availability on web directory is 2010-2025
start_year = 2010
end_year = 2025

# create directory for storing shapefile output
os.makedirs(output_dir, exist_ok = True)

# loop through years
for year_use in range(start_year, end_year + 1):
  # keep track of progress
  print('Reading Hurricane Tracks from year ' + str(year_use))
  # loop through up to 31 hurricanes in a given year
  # not every year has 31 hurricanes
  for hurricane_no in range(0, 31):
    file_found = True
    hurricane_index = str(hurricane_no + 1).zfill(2)
    # nhc naming convention
    # al = atlantic
    # hurricane index = count of hurricanes in year
    # year_use = year
    filename = 'al' + hurricane_index + str(year_use)
    # call nhc api
    response = requests.get(url + filename + ender, stream=True)

    # unzip compressed folder that was called with api
    # (if file doesn't exist, file_found gets set to false)
    try:
      z = zipfile.ZipFile(io.BytesIO(response.content))
    except:
      file_found = False
      
    # if data exists, store in unique folder
    if file_found:
      # create dir and extract data
      output_directory = os.path.join(output_dir, filename)
      os.makedirs(output_directory, exist_ok = True)
      z.extractall(output_directory)
