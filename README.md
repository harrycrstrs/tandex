# TanDEM-X Degradation Experiment

This repository contains code relating to "InSAR Quantification of Tropical ForestDegradation in Hilly Terrain" by Harry Carstairs et. al.

## Dependencies

ESA SNAP 7.0 is required, as well as the snappy - the SNAP-Python interface.
Inside the "environments" folder, two yml files contain details of all the python dependencies.
Conda can be used to create envinroments with all the correct dependencies:
    *conda env create --file envname.yml*
The "SNAP_env" should be used for all scripts that make use of snappy.
The "xarray_env" should be used for all scripts that make use of the package xarray.


## Image Processing

The "Image Processing" folder contains scripts for creating interferograms and calculating phase height from TanDEM-X CoSSC image pairs.

The processing chain follows this order:
- make_ifgs.py (create interferograms)
- get_metadata.py (extract image metadat into a csv file)
- remove_SRTM.py (remove phase associated with topography)
- make_DEMs.py (multi-looking, filtering, unwrapping, phase-to-height conversion and georeferencing)
- export_netcdf.py (convert to Net-CDF files)
- merge_datasets.py (collect time series into single files)
- subset.py (create spatial subset)


## Analysis 

The "analysis" folder contains ipython notebooks used to analyse the results and create figures.
