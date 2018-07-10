#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

""" CONCURRENCY DRIVER FOR VIC2NETCDF """

from __future__ import print_function
from random import randint
import multiprocessing
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
SEED = randint(1,1e4)
BASE_CLASS_FILE = os.path.join(os.getcwd(),'control.cfg')

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

def create_control_files(args):
    '''
    Generate NPROCS number of control files.
    '''

    # Temporary control file directory
    cfile_dir = os.path.join(os.path.dirname(BASE_CLASS_FILE),'control_files/')

    # Generate year range
    year_range = [args.year_begin,args.year_end]

    # Check if exists - if not, create
    if not os.path.exists(cfile_dir):
        os.mkdir(cfile_dir)
    if not os.path.exists(args.outdir):
        print(args.outdir)

    assert isinstance(args.nprocs,int), 'nprocs must be an integer'
    assert isinstance(args.gcm,str), 'GCM must be a string'
    assert isinstance(year_range,list), 'year_range must be a list<int,int>'

    division = list(range(year_range[0],year_range[1]+1))
    slices = split_seq(division,args.nprocs)

    control_files = []

    # Iterate over each processor and generate a relevant control file
    for i in range(args.nprocs):
        proc_file = os.path.join(cfile_dir,'%s_%d_proc_%d.cfg' % (args.gcm,SEED,i))
        shutil.copy(BASE_CLASS_FILE,proc_file)

        # Generate all sed commands
        cmds = ["sed -i 's/YEARBEGIN/%d/g' %s" % (slices[i][0],proc_file),
                "sed -i 's/YEAREND/%d/g' %s" % (slices[i][-1],proc_file),
                "sed -i 's/PROCESSGCM/%s/g' %s" % (args.gcm,proc_file),
                "sed -i 's,GCMINDIRECTORY,%s,g' %s" % (args.infiles,proc_file),
                "sed -i 's,GCMOUTDIRECTORY,%s,g' %s" % (args.outdir,proc_file),
                "sed -i 's,GCMOUTPREFIX,%s,g' %s" % (args.prefix,proc_file)]

        # Run all sed commands
        for cmd in cmds:
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)

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
    fake_args = DummyArgs(cfg)

    # Run the program!!
    vic2netcdf._run(fake_args)

    t1 = time.perf_counter()
    process = multiprocessing.current_process().name
    print('%s completed in %d seconds' % (process,round((t1-t0),3)))

arg_help = ['''Parallel batch conversion from VIC to netCDF file formats.
Given initial parameters, will convert (in parallel!) requested files to the binary netCDF format.

Uses the big memory mode - be careful how many years and processes you allocate!
(20 processors will require approximately 150 GB of RAM. Keep an eye on htop - this program WILL
slow to a crawl if swap space becomes required!)''',
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
    parser.add_argument('-g','--gcm',type=str,help=arg_help[3],default='Can-ES-M2')
    parser.add_argument('-np','--nprocs',type=int,help=arg_help[4],default=20)
    parser.add_argument('-in','--infiles',type=str,help=arg_help[5],default='/scratch/hydroclimate/vic/colorado/results/PROCESSGCM/bal_*')
    parser.add_argument('-out','--outdir',type=str,help=arg_help[6],default='/scratch/hydroclimate/vic/colorado/results/testing')
    parser.add_argument('-p','--prefix',type=str,help=arg_help[7],default='vic_COL_CanESM2_rcp85')
    args = parser.parse_args()

    # Init global timer and generate control files
    print('Initializing...')
    print("GCM: {}\nSEED: {}\nOUT_DIR: {}\nNPROCS: {}\nYEAR_RANGE: ({},{})\n".format(
        args.gcm,SEED,args.outdir,args.nprocs,args.year_begin,args.year_end))

    t0 = time.perf_counter()
    control_files = create_control_files(args)

    # Run all generated control files among NPROC files
    print('Generating processor pool...')
    pool = multiprocessing.Pool(processes=args.nprocs)
    pool.map(run_config, control_files)
    print('Done.')

    # Cleanup
    for file in control_files:
        os.remove(file)

    # Close global timer and print out
    t1 = time.perf_counter()
    print("Total runtime: {} hrs".format(round((t1-t0)/60./60.,3)))
