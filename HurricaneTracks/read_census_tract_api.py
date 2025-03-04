import requests
import zipfile
import os
import io

# read census tract data
# partial api path
url = 'https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_'
url_ender = '_tract.zip' # file ending
output_dir = 'CensusTracts'
os.makedirs(output_dir, exist_ok = True)

# loop through all states
for state_fip in range(1, 73):
  # fip codes are always two digits
  state_fip_code = str(state_fip).zfill(2)

  # full api url
  url_total = url + state_fip_code + url_ender
  
  # Send a GET request to the URL
  response = requests.get(url_total)
  # Check if the request was successful
  if response.status_code == 200:
    # unzip compressed folder that was called with api
    # (if file doesn't exist, file_found gets set to false)
    file_found = True
    try:
      z = zipfile.ZipFile(io.BytesIO(response.content))
    except:
      file_found = False
    
    # if data exists, store in unique folder
    if file_found:
      filename = 'tl_2024_' + state_fip_code
      print(filename)
      # create dir and extract data
      output_directory = os.path.join(output_dir, filename)
      os.makedirs(output_directory, exist_ok = True)
      z.extractall(output_directory)
  else:
    print("Failed to download file " + url + state_fip_code + url_ender)
