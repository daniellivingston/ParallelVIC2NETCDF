# pV2N #
### Parallel Vic-to-netCDF batch conversion ###

Performs a batch (parallel) conversion of VIC files to netCDF using the [tonic](https://github.com/UW-Hydro/tonic/tree/master/tonic) library. 

To use, simply edit `run.sh` to match your specific configuration. In particular, change the `year_range` variable: to circumvent memory issues, the range should not extend more than 40 years. Use other machines to run the remaining years.

To run, call `run.sh`. Note that it will iterate over all GCMs defined in the `gcm_list` variable.

To run a single, specific configuration, call `python driver.py` with the specific arguments you desire:

    usage: driver.py [-h] [-y0 YEAR_BEGIN] [-y1 YEAR_END] [-g GCM] [-np NPROCS]
                     [-in INFILES] [-out OUTDIR] [-p PREFIX]

    Parallel batch conversion from VIC to netCDF file formats. Given initial
    parameters, will convert (in parallel!) requested files to the binary netCDF
    format. Uses the big memory mode - be careful how many years and processes you
    allocate! (20 processors will require approximately 150 GB of RAM. Keep an eye
    on htop - this program WILL slow to a crawl if swap space becomes required!)

    optional arguments:
      -h, --help            show this help message and exit
      -y0 YEAR_BEGIN, --year_begin YEAR_BEGIN
                            Beginning year of conversions
      -y1 YEAR_END, --year_end YEAR_END
                            Ending year of conversions
      -g GCM, --gcm GCM     Name of GCM (i.e., CCSM4)
      -np NPROCS, --nprocs NPROCS
                            Number of processors to request in pool
      -in INFILES, --infiles INFILES
                            Path to infiles. Wildcard (*) required!
      -out OUTDIR, --outdir OUTDIR
                            Base directory to write netCDF files to. Will
                            automatically append GCM name to the dir.
      -p PREFIX, --prefix PREFIX
                            desired prefix for the written netCDF files.