#!/usr/bin/bash
source /exports/csce/datastore/geos/users/s1332488/minibonda/etc/profile.d/conda.sh
cd /disk/scratch/local.4/harry/DEM/noSRTM/

toNC=/home/s1332488/code/tandex/export_netcdf.py
deramp=/home/s1332488/code/tandex/remove_plane.py

conda activate pysnap
for file in ./*.dim
do
python $toNC $file
done

mkdir NETCDF
mv *.nc NETCDF/
cd NETCDF

conda activate XR
for file in ./*.nc
do
python $deramp $file 1000
done


