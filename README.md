# RiskDataScienceAI
Contains code for analysis covered in DATA/ENVR/ENEC 543. 

### Dependencies

Python Libraries:

* geopandas
* requests
* matplotlib
* scipy
* seaborn

### Executing program

For Hurricane Track Analysis, navigate to the HurricaneTracks directory in the Anaconda prompt using the command:
```
cd HurricaneTracks
```
* get gis data on hurricane tracks from NHC API:
```
python -W ignore read_nhc_api.py
```
* combine all track data into single shapefile:
```
python -W ignore combine_nhc_tracks.py
```
* create tropical cyclone hazard figures:
```
python -W ignore explore_hurricane_tracks.py
```
