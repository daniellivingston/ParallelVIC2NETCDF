#!/bin/bash

# ====================================== #
#                                        #
#  VIC to NETCDF BATCH CONVERSION SCRIPT #
#           ----------------             #
#  This should be called instead of the  #
#  Python script when trying to do a     #
#  large-scale conversion of all VIC     #
#  files.                                #
#           ----------------             #
#  TO USE:                               #
#    1. Change the variables to fit your #
#       specific needs.                  #
#    2. MAKE SURE to change the year     #
#       range! Use the same script on 4  #
#       different machines, with years:  #
#          machine_1: (1950 1990)        #
#          machine_2: (1991 2030)        #
#          machine_3: (2031 2070)        #
#          machine_4: (2071 2098)        #
#  Assuming the global range (1950 2098) #
# ====================================== #

source activate tonic2

# How many processors should run?
nprocs=20

# The year range should be no more than a 40 year span.
# Use other machines to do the others.
declare -a year_range=(1950 1990)

# Define the GCMs to iterate over.
declare -a gcm_list=("CSIRO-Mk3-6-0" "GFDL-ESM2G" "GFDL-ESM2M" "HadGEM2-CC365"
                     "HadGEM2-ES365" "IPSL-CM5A-LR" "IPSL-CM5B-LR" "MIROC-ESM-CHEM"
                     "MIROC-ESM" "MPI-ESM-LR" "NorESM1-M")


# Iterate over each GCM and run.
for gcm in "${gcm_list[@]}" ; do

    prefix="vic_$gcm" 
    in_dir="/scratch/hydroclimate/vic/colorado/results/$gcm/bal_*"
    out_dir="/scratch/hydroclimate/vic/colorado/results/testing/$gcm/"

    # Run Python script
    python driver.py -np $nprocs -g $gcm -y0 ${year_range[0]} -y1 ${year_range[1]} -in $in_dir -out $out_dir -p $prefix
done