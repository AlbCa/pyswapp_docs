import sys
import copy
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(1, '../../swa')

from geometry import *
from utils import *
from _stream import SeismicStream
from interactive_tools import *

# %% Wavefield transformation and dc picking

# directories
prj_dir = '../data/testdata_ilaria/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_test.csv'
path2fk = f'{prj_dir}/proc/fk_filter/fw_shots/fkfilter_Shot_test.txt'
path2disp = f'{prj_dir}/proc/dc_pick/'
ext = '.sgy' # shot file extension

# processing and plotting settings
settings = create_settings_dict(trafo = 'fdbf',             # transformation type
                         zero_padding=False, freq_step=0.5, # zero padding
                         normalize = True,local_max = True, # amplitude normalization
                         picking = 'manual',                # picking mode ("manual" or "auto")
                         fmin=3, fmax=100,                  # frequency range
                         vmin=50, vmax=1000, velstep=1)     # testing phase velocity range and step

# get paths to shot files, survey geometry from geometry.csv
shot_files, source_coordinates, receiver_coordinates = read_geometry(path2geom)
path2sht = get_shotfiles_from_geometry(path2raw, shot_files, extension = ext, sort_ascending = False)

# %% run the wavefield transformation on the whole data set and show the dispersion image
stream = SeismicStream(path2sht[0][0], settings) # record

# apply the transformation based on the settings in the settings dictionary and show the dispersion image
stream._apply_trafo(show = True, do_pick = False)

# %% run the wavefield transformation on a subset and perform the picking

# define subset range
mintrace = 5
maxtrace = 20

stream = SeismicStream(path2sht[0][0], settings) # record

# select a subset of the data
trace_select = range(mintrace, maxtrace)
stream_sub = copy.deepcopy(stream)
stream_sub._select_traces(trace_select=trace_select)

# apply the transformation based on the settings in the settings dictionary and do the dispersion curve picking
stream_sub._apply_trafo(do_pick = True,       # start the picking
                        save_dc = False,       # save the resulting pick file
                        path2disp = path2disp)# location to save the dispersion curve

# %% compare different transformation functions
stream = SeismicStream(path2sht[1][0], settings) # record

trace_select = range(mintrace, maxtrace)
stream._select_traces(trace_select=trace_select)

fig,ax = plt.subplots(1,3,figsize=(10,5))

# frequency domain beam forming with cylindrical steering vector (Zywicki, 1999)
stream.trafo_type = 'fdbf'
stream._apply_trafo(do_pick = False)
stream._plotDispersionImage(axes=ax[0])

# frequency domain beam forming with plane steering vector (Zywicki, 1999)
stream.trafo_type = 'hdbf'
stream._apply_trafo(do_pick = False)
stream._plotDispersionImage(axes=ax[1])

# phaseshift transformation (Park, 1998)
stream.trafo_type = 'phaseshift'
stream._apply_trafo(do_pick = False)
stream._plotDispersionImage(axes=ax[2])

plt.tight_layout()
plt.show()
