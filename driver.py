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
NPROCS = 20
YEAR_RANGE = [1950,2098]


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

def create_control_files():
    '''
    Generate NPROCS number of control files.
    '''

    division = list(range(YEAR_RANGE[0],YEAR_RANGE[1]+1))
    slices = split_seq(division,NPROCS)

    control_files = []

    # Iterate over each processor and generate a relevant control file
    for i in range(NPROCS):
        proc_file = os.path.join(os.path.dirname(BASE_CLASS_FILE),'control_files/proc_%d.cfg' % i)
        shutil.copy(BASE_CLASS_FILE,proc_file)

        cmd1 = "sed -i 's/YEARBEGIN/%d/g' %s" % (slices[i][0],proc_file)
        cmd2 = "sed -i 's/YEAREND/%d/g' %s" % (slices[i][-1],proc_file)

        subprocess.check_output(cmd1, shell=True, stderr=subprocess.STDOUT)
        subprocess.check_output(cmd2, shell=True, stderr=subprocess.STDOUT)

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

    t0 = time.perf_counter()

    args = DummyArgs(cfg)

    # Run the program!!
    vic2netcdf._run(args)

    t1 = time.perf_counter()

    print('SUBPROCESS COMPLETED: %d seconds' % (t1-t0))

if (__name__ == '__main__'):
    # Init global timer and generate control files
    print('Initializing...')
    t0 = time.perf_counter()
    control_files = create_control_files()

    # Run all generated control files among NPROC files
    print('Generating processor pool...')
    pool = Pool(processes=NPROCS)
    pool.map(run_config, control_files)
    print('Done.')

    # Close global timer and print out
    t1 = time.perf_counter()
    print("Total runtime: {}".format(t1-t0))


