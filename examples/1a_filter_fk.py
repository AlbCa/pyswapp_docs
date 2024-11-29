import sys
import copy
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(1, '../../swa')

from geometry import *
from utils import *
from _stream import SeismicStream
from _curve import Curve
from _combineCurves import CombineCurves


# %% Create and apply filter in fk domain

# directories
prj_dir = '../data/testdata_ilaria/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_test.csv'
path2fk = f'{prj_dir}/proc/fk_filter/fw_shots/fkfilter_Shot_test.txt'
ext = '.sgy' # shot file extension

# processing and plotting settings
settings = create_settings_dict(trafo = 'fdbf',             # transformation type
                         zero_padding=False, freq_step=0.5,  # zero padding
                         normalize = True,local_max = True, # amplitude normalization
                         picking = 'manual',                # picking mode ("manual" or "auto")
                         fmin=3, fmax=100,                  # frequency range
                         vmin=50, vmax=1000, velstep=1)     # testing phase velocity range and step


# get paths to shot files, survey geometry from geometry.csv
shot_files, source_coordinates, receiver_coordinates = read_geometry(path2geom)
path2sht = get_shotfiles_from_geometry(path2raw, shot_files, extension = ext, sort_ascending = False)

mintrace = 4
maxtrace = 28

# run the fk filtering for each file
for i in range(0,len(path2sht)):

    stream = SeismicStream(path2sht[i][0], settings) # record
    trace_select = range(mintrace, maxtrace)
    stream._select_traces(trace_select=trace_select)

    stream_cp = copy.deepcopy(stream)

    # load fk filter from file and apply
    stream_cp._fk_filter_from_file(fname='test_fk.txt', show=False)

    # pick fk filter and apply
    #stream_cp._fk_filter_from_pick(fname=path2fk, show=False)
    #stream_cp._fk_filter_from_pick(show=False) # if fname is not provided, no file will be generated

    # show the seismogram
    fig,ax = plt.subplots()
    stream._plotSeismogram(axes = ax, show_map = False, color = 'r')
    stream_cp._plotSeismogram(axes=ax, show_map=False, color='b')
    plt.show()

    # show the dispersion image
    fig, ax = plt.subplots(1, 2, figsize=(10, 5))
    stream._apply_trafo(do_pick=False)
    stream._plotDispersionImage(axes=ax[0])
    stream_cp._apply_trafo(do_pick=False)
    stream_cp._plotDispersionImage(axes=ax[1])
    plt.tight_layout()
    plt.show()

