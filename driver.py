#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

""" CONCURRENCY DRIVER FOR VIC2NETCDF """

from __future__ import print_function
from multiprocessing import Pool
import argparse
import subprocess
import datetime
import time
import shutil
import os
from tonic import version
from tonic.models.vic import netcdf2vic, compare_soil_params, grid_params, \
    ncparam2ascii, vic2netcdf


# Define global 'constants'
BASE_CLASS_FILE = os.path.join(os.getcwd(),'control.cfg')
#NPROCS = 20
#YEAR_RANGE = [1950,1990]


def split_seq(seq, rank):
    '''
    Given a sequence of numbers (i.e. the range of years),
    split close-to-equal among `rank` number of processors.

    :param seq: a list of numbers to be divided amongst ranks
    :type seq: list <int>
    :param rank: number of divisions (here, the NPROC count)
    :type rank: int

    Returns:
    :param newseq: a list of length(list)==rank containing the seq split
    :type newseq: list<list<int>>
    '''

    newseq = []
    splitsize = 1.0/rank*len(seq)
    for i in range(rank):
        newseq.append(seq[int(round(i*splitsize)):int(round((i+1)*splitsize))])
    return newseq

def create_control_files(nprocs,year_range,gcm):
    '''
    Generate NPROCS number of control files.

    :param nprocs: number of processors used
    :type nprocs: int
    :param year_range: [starting year, ending year]
    :type year_range: list<int>
    :param gcm: the GCM name to convert
    :type gcm: str
    '''

    division = list(range(year_range[0],year_range[1]+1))
    slices = split_seq(division,nprocs)

    control_files = []

    # Iterate over each processor and generate a relevant control file
    for i in range(nprocs):
        proc_file = os.path.join(os.path.dirname(BASE_CLASS_FILE),'control_files/proc_%d.cfg' % i)
        shutil.copy(BASE_CLASS_FILE,proc_file)

        cmd1 = "sed -i 's/YEARBEGIN/%d/g' %s" % (slices[i][0],proc_file)
        cmd2 = "sed -i 's/YEAREND/%d/g' %s" % (slices[i][-1],proc_file)
        cmd3 = "sed -i 's/PROCESSGCM/%s/g' %s" % (gcm,proc_file)

        subprocess.check_output(cmd1, shell=True, stderr=subprocess.STDOUT)
        subprocess.check_output(cmd2, shell=True, stderr=subprocess.STDOUT)
        subprocess.check_output(cmd3, shell=True, stderr=subprocess.STDOUT)

        control_files.append(proc_file)

    return control_files

class DummyArgs():
    '''
    Dummy class to trick vic2netcdf into thinking that argparse has passed
    command-line arguments to it.
    '''
    def __init__(self,cfg):
        self.config_file = cfg
        self.create_batch = False
        self.batch_dir = "./"

def run_config(cfg):
    '''
    Run a configuration file.

    :param cfg: path to configuration file
    :type cfg: str
    '''

    t0 = time.perf_counter()
    args = DummyArgs(cfg)

    # Run the program!!
    vic2netcdf._run(args)

    t1 = time.perf_counter()
    print('SUBPROCESS COMPLETED: %d seconds' % round((t1-t0),3))

arg_help = [
'''Parallel batch conversion from VIC to netCDF file formats.
Given initial parameters, will convert (in parallel!) requested files to the binary netCDF format.

Uses the big memory mode - be careful how many years and processes you allocate! (20 processors will require approximately 150 GB of RAM - keep an eye on htop - this program WILL slow to a crawl if swap space becomes required!) 
''',
'Beginning year of conversions',
'Ending year of conversions',
'Name of GCM (i.e., CCSM4)',
'Number of processors to request in pool',
'Path to infiles. Wildcard (*) required!',
'Base directory to write netCDF files to. Will automatically append GCM name to the dir.',
'desired prefix for the written netCDF files.']

if (__name__ == '__main__'):

    # Parse command line arguments
    parser = argparse.ArgumentParser(description=arg_help[0])
    parser.add_argument('-y0','--year_begin',type=int,help=arg_help[1],default=1950)
    parser.add_argument('-y1','--year_end',type=int,help=arg_help[2],default=2098)
    parser.add_argument('-g','--gcm',type=str,help=arg_help[3],default='')
    parser.add_argument('-np','--nprocs',type=int,help=arg_help[4],default=20)
    parser.add_argument('-in','--infiles',type=str,help=arg_help[5],default='/scratch/hydroclimate/vic/colorado/results/PROCESSGCM/bal_*')
    parser.add_argument('-out','--outdir',type=str,help=arg_help[6],default='/scratch/hydroclimate/vic/colorado/results/testing')
    parser.add_argument('-p','--prefix',type=str,help=arg_help[7],default='vic_COL_CanESM2_rcp85')
    args = parser.parse_args()

    # Init global timer and generate control files
    print('Initializing...')
    t0 = time.perf_counter()
    control_files = create_control_files(args.nprocs,args.gcm,[args.year_begin,args.year_end])

    # Run all generated control files among NPROC files
    print('Generating processor pool...')
    pool = Pool(processes=args.nprocs)
    pool.map(run_config, control_files)
    print('Done.')

    # Close global timer and print out
    t1 = time.perf_counter()
    print("Total runtime: {} hrs".format(round((t1-t0)/60./60.,3))


