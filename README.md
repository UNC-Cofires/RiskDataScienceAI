# RiskDataScienceAI
code for DATA/ENVR/ENEC 543

### Dependencies

Python Libraries:

* geopandas
* requests
* matplotlib
* scipy
* seaborn

### Executing program

* For Hurricane Track Analysis:
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

* go to US Fire Service data website at https://www.fs.usda.gov/rds/archive/catalog/RDS-2013-0009.6:
* download fire data file FPA_FOD_20221014.gpkg, put in repository
* disaggregate file into state-level shapefiles using
```
python -W ignore spark_disagg.py
```
* create html files mapping wildfire data:
```
python -W ignore spark_analysis.py
```
